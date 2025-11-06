# nlp/dataset_ingestor.py
import os
import pandas as pd
import numpy as np
from tqdm import tqdm
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.exceptions import ResponseError
from redis_config import get_redis_client
from nlp.embedding_model import get_model
from core.config import INDEX_NAME, DATASETS_DIR, BATCH_SIZE

os.makedirs(DATASETS_DIR, exist_ok=True)

def _ensure_index(redis_client, embed_dim: int):
    """
    Create RediSearch index if it doesn't exist.
    Uses HNSW vector field named `query_embedding`.
    """
    SCHEMA = [
        TextField("query"),
        TextField("api"),
        TextField("endpoint"),
        TextField("request"),
        TextField("response"),
        VectorField(
            "query_embedding",
            "HNSW",
            {
                "TYPE": "FLOAT32",
                "DIM": embed_dim,
                "DISTANCE_METRIC": "COSINE",
                "M": 16,
                "EF_CONSTRUCTION": 200,
            },
        ),
    ]
    definition = IndexDefinition(prefix=["api:"], index_type=IndexType.HASH)
    ft = redis_client.ft(INDEX_NAME)
    try:
        ft.create_index(SCHEMA, definition=definition)
        return {"created": True}
    except ResponseError as e:
        if "Index already exists" in str(e):
            return {"created": False}
        raise

def ingest_csv_to_redis(csv_path: str, max_records: int = None):
    """
    Read CSV file, generate embeddings, and insert to Redis in batches.
    Returns a summary dict.
    Expected CSV columns: query, api, endpoint, request, response
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(csv_path)

    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["query"])
    df["query"] = df["query"].astype(str)

    if max_records:
        df = df.head(max_records)

    n = len(df)
    if n == 0:
        return {"status": "empty", "records": 0}

    model = get_model()
    embed_dim = model.get_sentence_embedding_dimension()

    # generate embeddings in batches to limit memory usage
    all_queries = df["query"].tolist()
    embeddings = model.encode(
        all_queries, normalize_embeddings=True, batch_size=256, show_progress_bar=False, convert_to_numpy=True
    ).astype(np.float32)

    r = get_redis_client()
    _ensure_index(r, embed_dim)

    inserted = 0
    total_batches = (n + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_idx in range(total_batches):
        start = batch_idx * BATCH_SIZE
        end = min(start + BATCH_SIZE, n)
        pipe = r.pipeline(transaction=False)
        for i in range(start, end):
            row = df.iloc[i]
            key = f"api:{inserted + i - start}"  # unique-ish key (can adjust if you want timestamps)
            vec_bytes = embeddings[i].tobytes()
            mapping = {
                "query": row.get("query", ""),
                "api": row.get("api", ""),
                "endpoint": row.get("endpoint", ""),
                "request": row.get("request", ""),
                "response": row.get("response", ""),
                "query_embedding": vec_bytes,
            }
            pipe.hset(key, mapping=mapping)
        try:
            pipe.execute()
            inserted = end
        except Exception as e:
            # partial failure handling
            return {"status": "error", "message": str(e), "inserted": inserted}
    return {"status": "success", "records": inserted, "csv_path": csv_path}

import pandas as pd
import numpy as np
import redis
import os
from sentence_transformers import SentenceTransformer
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from redis.exceptions import ResponseError
from redis_config import get_redis_client

CSV_PATH = os.getenv("CSV_PATH", "./csv_dataset.csv")
USERNAME = os.getenv("REDIS_USERNAME")
PASSWORD = os.getenv("REDIS_PASSWORD")

model = SentenceTransformer("all-MiniLM-L6-v2")
model.max_seq_length = 512
EMBED_DIM = model.get_sentence_embedding_dimension()

df = pd.read_csv(CSV_PATH)
embeddings = model.encode(df["query"].tolist(), normalize_embeddings=True)
embeddings = np.asarray(embeddings, dtype=np.float32)

r = get_redis_client()

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
            "DIM": EMBED_DIM,
            "DISTANCE_METRICS": "COSINE",
            "M": 16,
            "EF_CONSTRUCT": 200
        }
    )
]

INDEX_NAME = "idx:apis"
definition = IndexDefinition(prefix=["api:"], index_type = IndexType.HASH)

ft = r.ft(INDEX_NAME)
try:
    ft.create_index(SCHEMA, definition=definition)
    print(f"Created index{INDEX_NAME}")
except ResponseError as e:
    if "Index already exists" in str(e):
        print(f"Index {INDEX_NAME} already exits")
    else:
        raise

pipe = r.pipeline(transaction=False)
for i, row in enumerate(df.itertuples(index=False), start=0):
    vec_bytes = embeddings[i].tobytes()  # float32 bytes, length = 4*EMBED_DIM
    key = f"api:{i}"
    pipe.hset(
        key,
        mapping={
            "query": row.query,
            "api": row.api,
            "endpoint": row.endpoint,
            "request": row.request,
            "response": row.response,
            "query_embedding": vec_bytes,
        },
    )
pipe.execute()
print(f"Inserted {len(df)} hashes into Redis.")

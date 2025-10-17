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
from tqdm import tqdm

CSV_PATH = os.getenv("CSV_PATH", "./csv_dataset.csv")
USERNAME = os.getenv("REDIS_USERNAME")
PASSWORD = os.getenv("REDIS_PASSWORD")

print("Loading model...")
model = SentenceTransformer("BAAI/bge-small-en-v1.5")
model.max_seq_length = 256  
EMBED_DIM = model.get_sentence_embedding_dimension()

print("Loading CSV...")
df = pd.read_csv(CSV_PATH)
df = df.dropna(subset=['query'])
df['query'] = df['query'].astype(str)

print(f"Loaded {len(df)} valid records from CSV")

print("Generating embeddings...")
embeddings = model.encode(
    df["query"].tolist(), 
    normalize_embeddings=True,
    batch_size=256,  
    show_progress_bar=True,  
    convert_to_numpy=True  
)
embeddings = np.asarray(embeddings, dtype=np.float32)
print(f"Generated {len(embeddings)} embeddings")

print("Connecting to Redis...")
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
            "DISTANCE_METRIC": "COSINE",  
            "M": 16,
            "EF_CONSTRUCTION": 200
        }
    )
]

INDEX_NAME = "idx:apis"
definition = IndexDefinition(prefix=["api:"], index_type = IndexType.HASH)

ft = r.ft(INDEX_NAME)
try:
    ft.create_index(SCHEMA, definition=definition)
    print(f"Created index {INDEX_NAME}")
except ResponseError as e:
    if "Index already exists" in str(e):
        print(f"Index {INDEX_NAME} already exists")
    else:
        raise

print("Inserting into Redis...")
BATCH_SIZE = 500  
total_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE
inserted_count = 0

for batch_num in tqdm(range(total_batches), desc="Inserting batches"):
    start_idx = batch_num * BATCH_SIZE
    end_idx = min(start_idx + BATCH_SIZE, len(df))
    
    pipe = r.pipeline(transaction=False)
    
    for i in range(start_idx, end_idx):
        row = df.iloc[i]
        vec_bytes = embeddings[i].tobytes()
        key = f"api:{i}"
        pipe.hset(
            key,
            mapping={
                "query": row['query'],
                "api": row['api'],
                "endpoint": row['endpoint'],
                "request": row['request'],
                "response": row['response'],
                "query_embedding": vec_bytes,
            },
        )
    
    try:
        pipe.execute()
        inserted_count = end_idx
    except Exception as e:
        print(f"\n Error at batch {batch_num + 1}: {e}")
        print(f"Successfully inserted {inserted_count} records before error.")
        print("\n Your Redis instance has limited memory. Try:")
        print(f"   1. Reduce MAX_RECORDS in the script (currently {len(df)})")
        print(f"   2. Upgrade Redis plan for more memory")
        print(f"   3. Use a local Redis instance")
        break

print(f" Successfully inserted {inserted_count} records into Redis!")

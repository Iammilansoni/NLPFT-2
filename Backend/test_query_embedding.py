"""Test query embedding for NaN values"""
import numpy as np
from app.nlp.embedding_model import get_model

model = get_model()

# Test embedding generation
query = "login"
print(f"Query: {query}")

embedding = model.encode([query], normalize_embeddings=True)
print(f"Embedding shape: {embedding.shape}")
print(f"Embedding dtype: {embedding.dtype}")
print(f"Has NaN: {np.isnan(embedding).any()}")
print(f"Has Inf: {np.isinf(embedding).any()}")
print(f"First 10 values: {embedding[0][:10]}")
print(f"Norm: {np.linalg.norm(embedding[0])}")

# Test the bytes conversion
vec_bytes = np.asarray(embedding, dtype=np.float32).tobytes()
print(f"\nBytes length: {len(vec_bytes)} (expected: {768 * 4} = 3072)")

# Parse back
parsed = np.frombuffer(vec_bytes, dtype=np.float32)
print(f"Parsed shape: {parsed.shape}")
print(f"Parsed has NaN: {np.isnan(parsed).any()}")

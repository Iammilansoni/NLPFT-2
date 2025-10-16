import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import pipeline, logging as hf_logging
from redis_config import get_redis_client

hf_logging.set_verbosity_error()

# -------------------------------
# Redis
# -------------------------------
r = get_redis_client()
INDEX_NAME = "idx:apis"
VECTOR_FIELD = "query_embedding"

# -------------------------------
# Embedder (always L4)
# -------------------------------
encoder = SentenceTransformer("all-MiniLM-L4-v2")
encoder.max_seq_length = 512

# -------------------------------
# QA model
# -------------------------------
QA_MODEL = "mrm8488/bert-tiny-finetuned-squadv2"
qa = pipeline("question-answering", model=QA_MODEL)

# -------------------------------
# Encode query
# -------------------------------
def encode_bytes(text: str) -> bytes:
    vec = encoder.encode([text], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)[0]
    return vec.tobytes()

# -------------------------------
# Vector search
# -------------------------------
def vector_search(qvec: bytes, top_k: int = 5):
    res = r.execute_command(
        "FT.SEARCH", INDEX_NAME,
        f'*=>[KNN {top_k} @{VECTOR_FIELD} $vec AS score]',
        "PARAMS", "2", "vec", qvec,
        "SORTBY", "score",
        "RETURN", "6", "query", "api", "endpoint", "request", "response", "score",
        "DIALECT", "2"
    )
    hits = []
    if not res or len(res) < 2:
        return hits
    for i in range(1, len(res), 2):
        f = res[i+1]
        doc = {}
        for j in range(0, len(f), 2):
            key = f[j].decode() if isinstance(f[j], (bytes, bytearray)) else f[j]
            val = f[j+1]
            if isinstance(val, (bytes, bytearray)):
                try: val = val.decode()
                except: pass
            doc[key] = val
        hits.append(doc)
    return hits

# -------------------------------
# QA field extraction
# -------------------------------
class TinyQAExtractor:
    def __init__(self, qa_pipe, threshold: float = 0.2):
        self.qa = qa_pipe
        self.threshold = threshold

    def extract(self, text: str):
        questions = {
            "username": "What is the username?",
            "password": "What is the password?",
            "base_url": "What is the website or base URL?"
        }
        slots = {}
        for k, q in questions.items():
            ans = self.qa(question=q, context=text)
            if ans.get("score", 0) >= self.threshold:
                slots[k] = ans["answer"].strip()
        return slots

extractor = TinyQAExtractor(qa)

# -------------------------------
# Orchestrator
# -------------------------------
def answer(query: str, top_k: int = 5):
    qvec = encode_bytes(query)
    hits = vector_search(qvec, top_k=top_k)
    best = hits[0] if hits else {"api": "search", "endpoint": "<base_url>/api/search", "score": "inf"}

    slots = extractor.extract(query)
    base_url = slots.get("base_url", "<base_url>")
    endpoint = best.get("endpoint", "<base_url>/api").replace("<base_url>", base_url)

    request_payload = {k: v for k, v in slots.items() if k != "base_url"}

    return {
        "api": best.get("api", "search"),
        "endpoint": endpoint,
        "request": request_payload,
        "search_meta": {"matched_query": best.get("query", ""), "score": best.get("score")}
    }

# -------------------------------
# CLI example
# -------------------------------
if __name__ == "__main__":
    query = input("Enter your query: ")
    result = answer(query)
    import json
    print(json.dumps(result, indent=2))

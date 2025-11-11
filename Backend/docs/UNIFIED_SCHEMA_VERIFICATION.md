# Unified Schema Verification

## ✅ YES - All Three Paths Use the Same Redis Schema

All embeddings stored in Redis will have the **exact same schema structure**, regardless of their source:

### 1. Your Own csv_dataset.csv
**Path:** `csv_dataset.csv` → `dataset_ingestor.py` → `embedding_manager.upsert_batch()`

**CSV Format:**
```csv
query,api,endpoint,request,response
"login -> user name=avsinghal pass=Secure*888",login,<base_url>/api/login,"{""username"": ""avsinghal"", ""password"": ""Secure*888""}","{""definition"": ""..."}"
```

**Redis Storage:**
```python
{
    "query": "login -> user name=avsinghal pass=Secure*888",
    "api": "login",
    "endpoint": "<base_url>/api/login",
    "request": "{\"username\": \"avsinghal\", \"password\": \"Secure*888\"}",
    "response": "{\"definition\": \"...\"}",
    "query_embedding": <384-dim vector>,
    # ... additional fields
}
```

### 2. User Uploaded CSV
**Path:** User uploads CSV → `dataset_ingestor.py` → `embedding_manager.upsert_batch()`

**CSV Format (Old):**
```csv
query,api,endpoint,request,response
```

**CSV Format (New):**
```csv
query,intent,slots,api_name,endpoint
```

**Conversion:** `dataset_ingestor.py` automatically converts both formats to unified schema:
- Old format: `api` → `api`, `request` → `request`
- New format: `intent` → `api`, `slots` → `request`

**Redis Storage (Same as #1):**
```python
{
    "query": "...",
    "api": "...",
    "endpoint": "...",
    "request": "...",
    "response": "...",  # Generated if not present
    "query_embedding": <384-dim vector>,
    # ... additional fields
}
```

### 3. Gemini Generated Dataset
**Path:** User input query → `dataset_generator.generate_from_plain_english()` → Saves CSV → `dataset_ingestor.py` → `embedding_manager.upsert_batch()`

**Generated CSV Format:**
```csv
query,intent,slots,api_name,endpoint
"login with john","login","{\"username\":\"john\"}","login","/api/login"
```

**Conversion:** `dataset_ingestor.py` converts to unified schema:
- `intent` → `api`
- `slots` → `request` (as JSON string)
- Generates default `response` if not present

**Redis Storage (Same as #1 and #2):**
```python
{
    "query": "login with john",
    "api": "login",
    "endpoint": "/api/login",
    "request": "{\"username\":\"john\"}",
    "response": "{\"definition\": \"API endpoint for login\"}",  # Auto-generated
    "query_embedding": <384-dim vector>,
    # ... additional fields
}
```

## Key Points

1. **Single Entry Point:** All three paths go through `embedding_manager.upsert_batch()` which uses the same schema
2. **Automatic Conversion:** `dataset_ingestor.py` handles format conversion automatically
3. **Unified Schema:** All embeddings stored with:
   - `query`, `api`, `endpoint`, `request`, `response`, `query_embedding`
   - Plus compatibility fields: `intent`, `slots_json`, `hash_id`, etc.
4. **Hash-based Deduplication:** All use `api:{hash_id}` key format, preventing duplicates
5. **Same Vector Field:** All use `query_embedding` as the vector field name

## Verification

You can verify by checking any embedding in Redis:

```python
# All embeddings will have the same structure:
redis_key = "api:{hash_id}"
data = redis_client.hgetall(redis_key)

# All will have:
assert "query" in data
assert "api" in data
assert "endpoint" in data
assert "request" in data
assert "response" in data
assert "query_embedding" in data
```

## Conclusion

✅ **YES** - All three sources (your csv_dataset.csv, user uploaded CSV, Gemini generated dataset) will produce embeddings with the **exact same schema structure** in Redis vector DB.


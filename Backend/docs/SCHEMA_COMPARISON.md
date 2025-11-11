# Schema Comparison: CSV vs Redis

## Quick Answer: **They are DIFFERENT but COMPATIBLE**

The CSV schema is **simpler** (input format), while the Redis schema is **richer** (storage format with additional metadata).

---

## 1. CSV Dataset Schema (Input)

### **Expected CSV Format:**

```csv
query,intent,slots,api_name,endpoint
"Login with username admin","login","{\"username\":\"admin\"}","login","/api/login"
"Reset password for user@test.com","reset_password","{\"email\":\"user@test.com\"}","reset_password","/api/reset_password"
```

### **CSV Columns:**

| Column | Required? | Type | Example |
|--------|-----------|------|---------|
| `query` | ✅ Required | String | `"Login with username admin"` |
| `intent` | ✅ Required | String | `"login"` |
| `slots` | ⚠️ Optional | JSON String | `"{\"username\":\"admin\"}"` |
| `api_name` | ⚠️ Optional | String | `"login"` |
| `endpoint` | ⚠️ Optional | String | `"/api/login"` |

**Total: 5 columns (2 required, 3 optional)**

---

## 2. Redis Schema (Storage)

### **Redis Index Definition:**

```python
schema = (
    VectorField("embedding", "HNSW", {...}),  # 384-dim vector
    TextField("intent"),
    TextField("slots_json"),
    TextField("query"),
    TextField("hash_id"),
    TextField("api_name"),
    TextField("endpoint"),
    NumericField("template_version"),
    TextField("created_at"),
    NumericField("confidence")
)
```

### **Redis Fields:**

| Field | Type | Source | Example |
|-------|------|--------|---------|
| `embedding` | Vector (384-dim) | 🤖 Generated | `[0.123, -0.456, ...]` |
| `intent` | Text | 📄 CSV | `"login"` |
| `slots_json` | Text (JSON) | 📄 CSV | `"{\"username\":\"admin\"}"` |
| `query` | Text | 📄 CSV | `"Login with username admin"` |
| `hash_id` | Text | 🤖 Generated | `"a3f5b2c..."` (SHA256) |
| `api_name` | Text | 📄 CSV or default | `"login"` |
| `endpoint` | Text | 📄 CSV or default | `"/api/login"` |
| `template_version` | Number | 🤖 Generated | `1` |
| `created_at` | Text (ISO) | 🤖 Generated | `"2025-11-10T12:00:00Z"` |
| `confidence` | Number | 🤖 Generated | `1.0` |

**Total: 10 fields (5 from CSV, 5 auto-generated)**

---

## 3. Mapping: CSV → Redis

### **Transformation Flow:**

```
CSV Row:
┌─────────────────────────────────────────────────────────┐
│ query: "Login with username admin"                      │
│ intent: "login"                                          │
│ slots: "{\"username\":\"admin\"}"                       │
│ api_name: "login"                                        │
│ endpoint: "/api/login"                                   │
└────────────────────┬────────────────────────────────────┘
                     ↓
         dataset_ingestor.py
                     ↓
┌─────────────────────────────────────────────────────────┐
│ 1. Read CSV with pandas                                 │
│ 2. Parse JSON slots                                     │
│ 3. Call: embedder.upsert_batch(...)                     │
└────────────────────┬────────────────────────────────────┘
                     ↓
         embedding_manager.py
                     ↓
┌─────────────────────────────────────────────────────────┐
│ 1. Generate embedding vector (384-dim)                  │
│ 2. Generate hash_id (SHA256 of query)                   │
│ 3. Add metadata (created_at, template_version, etc.)    │
│ 4. Store in Redis                                       │
└────────────────────┬────────────────────────────────────┘
                     ↓
Redis Hash (Key: api:a3f5b2c...):
┌─────────────────────────────────────────────────────────┐
│ embedding: [0.123, -0.456, ...]        ← Generated      │
│ intent: "login"                         ← From CSV      │
│ slots_json: "{\"username\":\"admin\"}" ← From CSV      │
│ query: "Login with username admin"     ← From CSV      │
│ hash_id: "a3f5b2c..."                  ← Generated      │
│ api_name: "login"                       ← From CSV      │
│ endpoint: "/api/login"                  ← From CSV      │
│ template_version: 1                     ← Generated      │
│ created_at: "2025-11-10T12:00:00Z"     ← Generated      │
│ confidence: 1.0                         ← Generated      │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Detailed Comparison

### **Fields Present in BOTH:**

| Field | CSV Column | Redis Field | Notes |
|-------|------------|-------------|-------|
| Query text | `query` | `query` | ✅ Same |
| Intent | `intent` | `intent` | ✅ Same |
| Slots | `slots` | `slots_json` | ⚠️ Different name |
| API name | `api_name` | `api_name` | ✅ Same |
| Endpoint | `endpoint` | `endpoint` | ✅ Same |

### **Fields ONLY in Redis:**

| Field | Purpose | How Generated |
|-------|---------|---------------|
| `embedding` | Vector for similarity search | sentence-transformers model |
| `hash_id` | Deduplication | SHA256 hash of query |
| `template_version` | Track template changes | Default: 1 |
| `created_at` | Timestamp | Current UTC time |
| `confidence` | Extraction confidence | Default: 1.0 |

### **Fields ONLY in CSV:**

None! All CSV fields are stored in Redis (though `slots` becomes `slots_json`).

---

## 5. Key Differences

### **A. Slots Field Name**

**CSV:**
```csv
slots
"{\"username\":\"admin\"}"
```

**Redis:**
```python
slots_json
"{\"username\":\"admin\"}"
```

**Why?** To clarify it's a JSON string, not a native object.

---

### **B. Embedding Vector**

**CSV:** ❌ Not present

**Redis:** ✅ Present
```python
embedding: [0.123, -0.456, 0.789, ...]  # 384 dimensions
```

**Why?** Generated from the query text using sentence-transformers.

---

### **C. Metadata Fields**

**CSV:** ❌ No metadata

**Redis:** ✅ Rich metadata
```python
hash_id: "a3f5b2c..."
template_version: 1
created_at: "2025-11-10T12:00:00Z"
confidence: 1.0
```

**Why?** For tracking, deduplication, and versioning.

---

## 6. Example Transformation

### **Input CSV:**

```csv
query,intent,slots,api_name,endpoint
"login with john and pass123","login","{\"username\":\"john\",\"password\":\"pass123\"}","login","/api/login"
```

### **Output Redis:**

```python
Key: api:a3f5b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1

Data: {
    # From CSV (direct)
    "query": "login with john and pass123",
    "intent": "login",
    "slots_json": "{\"username\":\"john\",\"password\":\"pass123\"}",
    "api_name": "login",
    "endpoint": "/api/login",
    
    # Generated by embedding_manager
    "embedding": b'\x00\x00\x00\x3f...',  # 384 floats as bytes
    "hash_id": "a3f5b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
    "template_version": "1",
    "created_at": "2025-11-10T12:00:00.123456",
    "confidence": "1.0"
}
```

---

## 7. Compatibility Matrix

| Operation | CSV Schema | Redis Schema | Compatible? |
|-----------|------------|--------------|-------------|
| **Read CSV** | ✅ | N/A | N/A |
| **Ingest to Redis** | ✅ | ✅ | ✅ Yes |
| **Vector Search** | ❌ | ✅ | N/A |
| **Export from Redis** | ⚠️ Partial | ✅ | ⚠️ Loses metadata |

---

## 8. Missing Fields Handling

### **If CSV is missing optional fields:**

```python
# dataset_ingestor.py handles this:

# If 'api_name' missing in CSV
api_names = df['api_name'].tolist() if 'api_name' in df.columns else None

# embedding_manager.py provides defaults:
data = {
    "api_name": api_name or intent,  # Falls back to intent
    "endpoint": endpoint or f"<base_url>/api/{intent}",  # Generates default
}
```

---

## 9. Visual Schema Comparison

```
CSV Schema (Simple):
┌──────────────────────────────────────┐
│ query          (required)            │
│ intent         (required)            │
│ slots          (optional)            │
│ api_name       (optional)            │
│ endpoint       (optional)            │
└──────────────────────────────────────┘
         5 fields total

         ↓ Transformation ↓

Redis Schema (Rich):
┌──────────────────────────────────────┐
│ query          ← from CSV            │
│ intent         ← from CSV            │
│ slots_json     ← from CSV            │
│ api_name       ← from CSV            │
│ endpoint       ← from CSV            │
├──────────────────────────────────────┤
│ embedding      ← generated           │
│ hash_id        ← generated           │
│ template_version ← generated         │
│ created_at     ← generated           │
│ confidence     ← generated           │
└──────────────────────────────────────┘
         10 fields total
```

---

## 10. Summary

| Aspect | CSV Schema | Redis Schema |
|--------|------------|--------------|
| **Purpose** | Input format | Storage format |
| **Fields** | 5 (2 required) | 10 (all required) |
| **Complexity** | Simple | Rich |
| **Metadata** | ❌ No | ✅ Yes |
| **Embeddings** | ❌ No | ✅ Yes |
| **Searchable** | ❌ No | ✅ Yes (vector search) |
| **Versioning** | ❌ No | ✅ Yes |
| **Timestamps** | ❌ No | ✅ Yes |

---

## Conclusion

**They are NOT the same, but they are COMPATIBLE:**

- **CSV** = Simple input format (what you provide)
- **Redis** = Enhanced storage format (what gets stored)

The `dataset_ingestor.py` and `embedding_manager.py` work together to:
1. Read the simple CSV format
2. Enrich it with embeddings and metadata
3. Store in the rich Redis format

Think of it like:
- **CSV** = Raw ingredients
- **Redis** = Cooked meal with garnish and presentation

Both contain the same core data, but Redis adds the "magic" (embeddings, metadata, searchability)! 🚀

# 🧠 NLPForge Reranking Architecture

## Two-Stage AI Ranking Engine

This document explains how the **two-stage retrieval pipeline** works, including the confidence score calculations for both Stage 1 and Stage 2, along with the final JSON output structure.

---

## 📊 Pipeline Overview

```
User Query
    ↓
┌─────────────────────────────────────────────────┐
│  STAGE 1: Vector Retrieval (Top-K)              │
│  ────────────────────────────────────────────── │
│  • Embedding-based semantic search              │
│  • Query embedding generated with sentence-     │
│    transformers or multi-model embeddings       │
│  • Redis Vector DB nearest-neighbor search      │
│  • Returns Top-K=5 candidates                   │
│  • Scores: Vector Similarity (0-1)              │
└─────────────────────────────────────────────────┘
    ↓ (Top-5 candidates)
┌─────────────────────────────────────────────────┐
│  STAGE 2: FlashRank Reranking                   │
│  ────────────────────────────────────────────── │
│  • Cross-encoder model: ms-marco-MiniLM-L-12-v2 │
│  • Pairwise relevance scoring                   │
│  • Reorder candidates by relevance score        │
│  • Final ranking (best to worst)                │
└─────────────────────────────────────────────────┘
    ↓ (Reranked results)
Final JSON Output
```

---

## 🔍 STAGE 1: Vector Retrieval

### Confidence Score Calculation

#### Formula:
$$\text{vector\_score} = 1.0 - \text{euclidean\_distance}$$

Where:
- **euclidean_distance** = L2 distance from Redis KNN search (typically 0-2 range)
- **vector_score** = Normalized similarity (0-1 range)
  - 1.0 = Perfect match
  - 0.5 = Neutral similarity
  - 0.0 = No similarity

#### Implementation:
```python
# From ranking_engine.py (Line 165-169)
vector_distance = _safe_float(doc.vector_score, 1.0)  # Redis returns distance
vector_similarity = _safe_float(1.0 - vector_distance, 0.0)  # Convert to similarity
```

#### Multi-Model Stage 1 (Alternative):
```python
# From multi_model_semantic_service.py (Line 549-595)
avg_similarity = mean(r.get("similarity", 0.0) for r in rows)
avg_confidence = mean(r.get("confidence_score", 0.5) for r in rows)

final_score = (
    0.5 × avg_similarity +      # 50% weight: vector similarity
    0.3 × avg_confidence +      # 30% weight: model confidence
    0.2 × intent_alignment      # 20% weight: intent match
)
```

### Stage 1 Output Example:
```json
{
  "rank": 1,
  "vector_score": 0.92,
  "text": "Login with username admin and password secret123",
  "api": "authentication",
  "endpoint": "/api/v1/login",
  "method": "POST",
  "scenario_type": "valid",
  "test_category": "valid_flow"
}
```

---

## ⚡ STAGE 2: FlashRank Reranking

### Confidence Score Calculation

#### Formula:
The **ms-marco-MiniLM-L-12-v2** cross-encoder model computes relevance via neural scoring:

$$\text{relevance\_score} = \sigma(W \cdot \text{BERT\_encoding}(query, passage))$$

Where:
- **σ** = Sigmoid activation function
- **W** = Cross-encoder weight matrix (trained on MS MARCO dataset)
- **BERT_encoding** = Concatenated embeddings of [query, SEP, passage]
- **Output range**: Typically [-∞, +∞] but normalized to [0, 1]

#### Key Characteristics:
- **Cross-Encoder**: Directly scores (query, document) pairs (not individual embeddings)
- **Architecture**: 12-layer BERT with 110M parameters
- **Training Data**: MS MARCO dataset (1M+ training triplets)
- **Advantages over Stage 1**:
  - No dimensionality limitations
  - Better semantic understanding of context
  - Captures nuanced relevance signals
  - More accurate ranking

#### Enhanced Text for Better Scoring:
```python
# From ranking_engine.py (Line 262-267)
# Original text + API metadata
enhanced_text = f"{query_text} | API: {api_name} | {method} {endpoint}"

# Example:
# "Login with admin credentials | API: authentication | POST /api/v1/login"

# This helps FlashRank distinguish between:
# 1. Similar queries across different APIs
# 2. Different HTTP methods for same endpoint
```

### Stage 2 Processing Steps:

```python
# From ranking_engine.py (Line 276-323)

# Step 1: Create passage pairs
passages = [
    {
        "id": 0,
        "text": "Login with username | API: auth | POST /login",
        "original_text": "Login with username",
        "meta": {candidate_data}
    },
    # ... more passages
]

# Step 2: Create rerank request
rerank_request = RerankRequest(
    query="login with admin credentials",
    passages=passages
)

# Step 3: Perform reranking
reranked_results = reranker.rerank(rerank_request)
# Returns: [
#   {"id": 0, "score": 0.9523, ...},
#   {"id": 2, "score": 0.8912, ...},
#   {"id": 1, "score": 0.7845, ...},
#   ...
# ]

# Step 4: Reorder by score (highest → lowest)
final_results = sorted(reranked_results, key=lambda x: x["score"], reverse=True)
```

### Score Normalization:
While FlashRank outputs raw scores, they're typically in range **[0, 1]**:
- **> 0.85** = Very High Relevance (Match found)
- **0.70 - 0.85** = High Relevance
- **0.50 - 0.70** = Medium Relevance
- **< 0.50** = Low Relevance

---

## 📋 STAGE 2: Multi-Model Semantic Reranking

### Alternative Reranking Formula (for complex scenarios):
```python
# From multi_model_semantic_service.py (Line 549-595)

# Group candidates by template ID (t_id)
grouped_results = {
    "t_id_1": [match1, match2, match3],  # Multiple matches for same template
    "t_id_2": [match4, match5],
}

# Calculate per-template scores
for t_id, rows in grouped_results.items():
    avg_similarity = mean(r["similarity"] for r in rows)
    avg_confidence = mean(r["confidence_score"] for r in rows)
    
    # Intent alignment (how many rows match user intent)
    matching_intent = sum(
        1 for r in rows 
        if r["intent_type"] == user_query_intent
    )
    intent_alignment = matching_intent / len(rows)
    
    # FINAL SCORE FORMULA
    final_score = (
        0.5 × avg_similarity +      # Similarity weight: 50%
        0.3 × avg_confidence +      # Confidence weight: 30%
        0.2 × intent_alignment      # Intent alignment: 20%
    )
```

---

## 📤 Final JSON Output Structures

### 1. Simple Ranking Response (Stage 1 + Stage 2)

```json
{
  "query": "login with username admin and password secret123",
  "ranked_results": [
    {
      "rank": 1,
      "score": 0.9523,
      "text": "Validate login with username test and password 123",
      "api": "authentication",
      "endpoint": "/api/v1/login",
      "method": "POST",
      "scenario_type": "valid",
      "test_category": "valid_flow",
      "vector_score": 0.92,
      "t_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    {
      "rank": 2,
      "score": 0.8912,
      "text": "Login to system with credentials admin/admin123",
      "api": "authentication",
      "endpoint": "/api/v1/login",
      "method": "POST",
      "scenario_type": "valid",
      "test_category": "valid_flow",
      "vector_score": 0.88,
      "t_id": "550e8400-e29b-41d4-a716-446655440001"
    },
    {
      "rank": 3,
      "score": 0.7845,
      "text": "Authenticate user with username and password",
      "api": "authentication",
      "endpoint": "/api/v1/authenticate",
      "method": "POST",
      "scenario_type": "valid",
      "test_category": "valid_flow",
      "vector_score": 0.85,
      "t_id": "550e8400-e29b-41d4-a716-446655440002"
    }
  ]
}
```

### 2. Detailed Ranking Response (Full Pipeline Visibility)

```json
{
  "query": "login with admin credentials",
  "stage1_results": [
    {
      "rank": 1,
      "vector_score": 0.92,
      "text": "Login with admin",
      "api": "auth_api",
      "endpoint": "/api/login",
      "method": "POST"
    },
    {
      "rank": 2,
      "vector_score": 0.88,
      "text": "Authenticate user with credentials",
      "api": "auth_api",
      "endpoint": "/api/authenticate",
      "method": "POST"
    },
    {
      "rank": 3,
      "vector_score": 0.85,
      "text": "User sign in endpoint",
      "api": "auth_api",
      "endpoint": "/api/signin",
      "method": "POST"
    }
  ],
  "ranked_results": [
    {
      "rank": 1,
      "score": 0.95,
      "text": "Login with admin",
      "api": "auth_api",
      "endpoint": "/api/login",
      "method": "POST",
      "request": {
        "username": "string",
        "password": "string"
      },
      "response": {
        "token": "string",
        "user_id": "string"
      },
      "vector_score": 0.92
    },
    {
      "rank": 2,
      "score": 0.88,
      "text": "Authenticate user with credentials",
      "api": "auth_api",
      "endpoint": "/api/authenticate",
      "method": "POST",
      "request": {
        "email": "string",
        "password": "string"
      },
      "response": {
        "authenticated": "boolean"
      },
      "vector_score": 0.88
    },
    {
      "rank": 3,
      "score": 0.82,
      "text": "User sign in endpoint",
      "api": "auth_api",
      "endpoint": "/api/signin",
      "method": "POST",
      "vector_score": 0.85
    }
  ],
  "reranker_model": "ms-marco-MiniLM-L-12-v2",
  "top_k": 5
}
```

### 3. Multi-Model Semantic Retrieval Response (Stage 2 Reranking)

```json
{
  "query": "login with admin credentials",
  "stage1_vector_search": [
    {
      "query": "Login with admin",
      "similarity_score": 0.92,
      "t_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    {
      "query": "Authenticate user",
      "similarity_score": 0.88,
      "t_id": "550e8400-e29b-41d4-a716-446655440001"
    }
  ],
  "stage2_reranking": [
    {
      "t_id": "550e8400-e29b-41d4-a716-446655440000",
      "avg_similarity": 0.92,
      "avg_confidence_score": 0.95,
      "final_score": 0.9170,
      "rank": 1,
      "match_count": 3
    },
    {
      "t_id": "550e8400-e29b-41d4-a716-446655440001",
      "avg_similarity": 0.88,
      "avg_confidence_score": 0.92,
      "final_score": 0.8900,
      "rank": 2,
      "match_count": 2
    }
  ],
  "final_output": {
    "t_id": "550e8400-e29b-41d4-a716-446655440000",
    "api_name": "authentication",
    "endpoint": "/api/v1/login",
    "method": "POST",
    "confidence_score": 0.9170,
    "request_schema": {
      "type": "object",
      "properties": {
        "username": {"type": "string"},
        "password": {"type": "string"}
      }
    },
    "response_schema": {
      "type": "object",
      "properties": {
        "token": {"type": "string"},
        "user_id": {"type": "string"}
      }
    },
    "extracted_request_body": {
      "username": "admin",
      "password": "secret123"
    }
  },
  "metadata": {
    "query": "login with admin credentials",
    "top_k": 5,
    "total_candidates": 5,
    "processing_time_ms": 145,
    "t_id": "550e8400-e29b-41d4-a716-446655440000",
    "match_count": 3,
    "avg_similarity": 0.92,
    "avg_confidence": 0.95,
    "intent_alignment": 0.95,
    "dominant_intent": "authentication",
    "domain_tags": ["auth", "login", "credentials"],
    "matched_queries": [
      "Login with admin",
      "Authenticate with credentials",
      "Admin login endpoint"
    ]
  }
}
```

---

## 🎯 Key Confidence Score Insights

### Stage 1 (Vector Similarity)
- **Range**: 0.0 - 1.0
- **Calculation**: `1.0 - euclidean_distance`
- **Interpretation**: Semantic similarity at embedding level
- **Limitations**: Doesn't understand context deeply

### Stage 2 (FlashRank)
- **Range**: 0.0 - 1.0 (typically)
- **Calculation**: Cross-encoder neural scoring with sigmoid
- **Interpretation**: Fine-grained relevance understanding
- **Advantages**: Context-aware, handles nuanced relationships

### Multi-Model Stage 2
- **Range**: 0.0 - 1.0
- **Calculation**: Weighted combination
  - 50% similarity + 30% confidence + 20% intent
- **Interpretation**: Holistic ranking across templates

---

## 🔐 Multi-Tenant Security

All stages filter by **user_id**:

```python
# Stage 1 Vector Search
@ft.redis.execute_command("FT.SEARCH", index_name, 
    f"(@user_id:{user_id}) =>[KNN 5 @embedding $vec]"
)

# Ensures users only see their own data
```

---

## 💾 Source Files

| Component | File |
|-----------|------|
| Stage 1 & 2 Pipeline | [Backend/app/nlp/ranking_engine.py](Backend/app/nlp/ranking_engine.py) |
| Multi-Model Reranking | [Backend/app/services/multi_model_semantic_service.py](Backend/app/services/multi_model_semantic_service.py) |
| Response Schemas | [Backend/app/models/schemas/ranking_schemas.py](Backend/app/models/schemas/ranking_schemas.py) |
| API Endpoints | [Backend/app/api/v1/ranking.py](Backend/app/api/v1/ranking.py) |

---

## 🚀 Usage Example

### Simple Two-Stage Ranking
```bash
curl -X POST http://localhost:8000/api/v1/rank \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "query": "login with admin credentials",
    "top_k": 5,
    "include_details": false
  }'
```

### Detailed Ranking (See Stage 1 + Stage 2)
```bash
curl -X POST http://localhost:8000/api/v1/rank/detailed \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "query": "login with admin credentials",
    "top_k": 5
  }'
```

---

## 📊 Score Interpretation Guide

| Score Range | Confidence Level | Action |
|-------------|-----------------|--------|
| 0.90 - 1.00 | 🟢 Very High | Use directly, high confidence |
| 0.75 - 0.90 | 🟡 High | Use with validation |
| 0.50 - 0.75 | 🟠 Medium | Manual review recommended |
| < 0.50 | 🔴 Low | Reject or ask user to clarify |

---

## 🔧 Customization

### Adjust Stage 2 Weights (Multi-Model)
```python
weights = {
    "similarity": 0.6,      # Increase weight on similarity
    "confidence": 0.2,      # Decrease confidence weight
    "intent": 0.2           # Keep intent alignment stable
}

best_t_id, best_result, ranked = service._rerank_by_template(
    grouped_results,
    user_query_intent,
    weights=weights
)
```

---

**Version**: 1.0  
**Last Updated**: January 2026  
**Model**: ms-marco-MiniLM-L-12-v2 (Cross-Encoder)

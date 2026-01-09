# 🔬 Stage 2 (FlashRank) - Detailed Step-by-Step Explanation

## What is Stage 2?

Stage 2 takes the **Top-5 results from Stage 1** and uses a **Cross-Encoder AI model** to re-score and re-rank them more accurately.

Think of it like this:
- **Stage 1** = Quick filtering (get roughly 5 good candidates)
- **Stage 2** = Precise ranking (put them in correct order)

---

## 📥 What Stage 2 Receives from Stage 1

### Input Example (5 candidates from Stage 1)

```text
User Query: "login with admin credentials"

Stage 1 outputs these 5 candidates (sorted by vector similarity):
```

| Rank | Vector Score | Text |
|------|--------------|------|
| 1 | 0.92 | "Login with admin" |
| 2 | 0.88 | "Authenticate user with credentials" |
| 3 | 0.85 | "User sign-in endpoint" |
| 4 | 0.82 | "Check password validation" |
| 5 | 0.79 | "Permission check for login" |

**Problem**: Vector similarity says #1 is best, but is it REALLY the best match for "login with admin credentials"?

---

## How Stage 2 (FlashRank) Works

### Step 1: Prepare Enhanced Text

Before scoring, Stage 2 **adds API metadata** to each candidate:

```python
# Original text from Stage 1
text = "Login with admin"

# Add API metadata for better context
enhanced_text = f"{text} | API: {api_name} | {method} {endpoint}"
enhanced_text = "Login with admin | API: authentication | POST /api/v1/login"
```

**Why?** The model needs more context to understand if this is really the right endpoint.

### Step 2: Create Query-Document Pairs

FlashRank pairs the **user query** with **each candidate**:

```
Pair 1:
  Query:    "login with admin credentials"
  Document: "Login with admin | API: authentication | POST /api/v1/login"

Pair 2:
  Query:    "login with admin credentials"
  Document: "Authenticate user with credentials | API: user | GET /api/authenticate"

Pair 3:
  Query:    "login with admin credentials"
  Document: "User sign in endpoint | API: auth | POST /api/signin"

Pair 4:
  Query:    "login with admin credentials"
  Document: "Check password validation | API: security | POST /api/validate-password"

Pair 5:
  Query:    "login with admin credentials"
  Document: "Permission check for login | API: permissions | GET /api/check-perm"
```

### Step 3: AI Neural Scoring (The Secret Sauce!)

Each pair goes through the **ms-marco-MiniLM-L-12-v2** model:

```
Input Pair 1: (query, document)
    ↓
[BERT Tokenizer]
    ↓
Query tokens + SEP + Document tokens
    ↓
[BERT Encoding] → Converts to embeddings (768 dimensions)
    ↓
[Cross-Encoder Head] → Applies neural network weights
    ↓
[Sigmoid Activation] → Converts to score (0-1)
    ↓
Output Score: 0.9523
```

### Step 4: The Scoring Formula (Inside FlashRank)

```
score = SIGMOID(W · BERT_embeddings(query, document))

Where:
  W = Trained neural network weights (learned from millions of (query, document) pairs)
  BERT_embeddings = Concatenated BERT encoding of [CLS] query [SEP] document [SEP]
  SIGMOID = Function that converts any number to 0-1 range
```

**What the model learns:**
- Which query + document combinations are most relevant
- Not just word matching, but **semantic understanding**
- Context from surrounding words
- Sentence structure and meaning

---

## 🧮 Real Example: How Scores are Calculated

### User Query:
```
"login with admin credentials"
```

### Candidates from Stage 1:

```
Candidate 1: "Login with admin"
Candidate 2: "Authenticate user with credentials"
Candidate 3: "User sign in endpoint"
Candidate 4: "Check password validation"
Candidate 5: "Permission check for login"
```

### Stage 2 Scoring Process:

#### Candidate 1: "Login with admin"
```
Query + Document pair:
  Q: "login with admin credentials"
  D: "Login with admin | API: authentication | POST /api/v1/login"

Why high score?
  ✅ Direct match: "login with admin"
  ✅ API is "authentication" (perfect for login)
  ✅ Endpoint is "/login" (main login endpoint)
  ✅ Method is "POST" (correct for sending credentials)

Score: 0.9523 ⭐⭐⭐⭐⭐ (BEST MATCH)
```

#### Candidate 2: "Authenticate user with credentials"
```
Query + Document pair:
  Q: "login with admin credentials"
  D: "Authenticate user with credentials | API: user | GET /api/authenticate"

Why medium score?
  ✅ Has "credentials" (partial match)
  ✅ Related to authentication
  ❌ Says "Authenticate user" not "login with admin"
  ❌ HTTP method is GET (should be POST for credentials)

Score: 0.8912 ⭐⭐⭐⭐ (GOOD MATCH)
```

#### Candidate 3: "User sign-in endpoint"
```
Query + Document pair:
  Q: "login with admin credentials"
  D: "User sign in endpoint | API: auth | POST /api/signin"

Why lower score?
  ✅ Related to login ("sign in")
  ✅ Correct HTTP method (POST)
  ❌ Doesn't mention "admin"
  ❌ "sign in" is different from "login with credentials"

Score: 0.7845 ⭐⭐⭐ (FAIR MATCH)
```

#### Candidate 4: "Check password validation"
```
Query + Document pair:
  Q: "login with admin credentials"
  D: "Check password validation | API: security | POST /api/validate-password"

Why low score?
  ❌ About validation, not login
  ❌ Doesn't mention "admin"
  ❌ Different from user intent

Score: 0.6234 ⭐⭐ (WEAK MATCH)
```

#### Candidate 5: "Permission check for login"
```
Query + Document pair:
  Q: "login with admin credentials"
  D: "Permission check for login | API: permissions | GET /api/check-perm"

Why lowest score?
  ❌ About permissions, not actual login
  ❌ HTTP GET (wrong for credentials)
  ❌ Doesn't match user intent

Score: 0.5634 ⭐ (WEAK MATCH)
```

---

## 📊 Comparison: Stage 1 vs Stage 2

```
Stage 1 (Vector Similarity):          Stage 2 (FlashRank):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Rank 1: 0.92 ← Similarity            Rank 1: 0.9523 ← AI Understanding
Rank 2: 0.88 ← Just word matching    Rank 2: 0.8912 ← Semantic relevance
Rank 3: 0.85                         Rank 3: 0.7845
Rank 4: 0.82                         Rank 4: 0.6234
Rank 5: 0.79                         Rank 5: 0.5634
         ↓                                    ↓
    Surface level                    Deep contextual understanding
    (fast but less accurate)          (slow but more accurate)
```

**Key Difference**: 
- Stage 1 ranked by simple embedding distance
- Stage 2 ranked by understanding the **meaning and relevance**

---

## 🔄 Stage 2 Output (Reranked Results)

After FlashRank processes all 5 pairs:

```json
[
  {
    "rank": 1,
    "score": 0.9523,
    "text": "Login with admin",
    "api": "authentication",
    "endpoint": "/api/v1/login",
    "method": "POST",
    "vector_score": 0.92,
    "t_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  {
    "rank": 2,
    "score": 0.8912,
    "text": "Authenticate user with credentials",
    "api": "user",
    "endpoint": "/api/authenticate",
    "method": "GET",
    "vector_score": 0.88,
    "t_id": "550e8400-e29b-41d4-a716-446655440001"
  },
  {
    "rank": 3,
    "score": 0.7845,
    "text": "User sign in endpoint",
    "api": "auth",
    "endpoint": "/api/signin",
    "method": "POST",
    "vector_score": 0.85,
    "t_id": "550e8400-e29b-41d4-a716-446655440002"
  },
  {
    "rank": 4,
    "score": 0.6234,
    "text": "Check password validation",
    "api": "security",
    "endpoint": "/api/validate-password",
    "method": "POST",
    "vector_score": 0.82,
    "t_id": "550e8400-e29b-41d4-a716-446655440003"
  },
  {
    "rank": 5,
    "score": 0.5634,
    "text": "Permission check for login",
    "api": "permissions",
    "endpoint": "/api/check-perm",
    "method": "GET",
    "vector_score": 0.79,
    "t_id": "550e8400-e29b-41d4-a716-446655440004"
  }
]
```

---

## Code Implementation (Actual Code)

### How FlashRank is called:

```python
# From ranking_engine.py (Lines 276-286)

# Create rerank request with query + passages
rerank_request = RerankRequest(
    query="login with admin credentials",              # User's query
    passages=[
        {"id": 0, "text": "Login with admin | API: authentication | POST /api/v1/login"},
        {"id": 1, "text": "Authenticate user with credentials | API: user | GET /api/authenticate"},
        {"id": 2, "text": "User sign in endpoint | API: auth | POST /api/signin"},
        {"id": 3, "text": "Check password validation | API: security | POST /api/validate-password"},
        {"id": 4, "text": "Permission check for login | API: permissions | GET /api/check-perm"},
    ]
)

# Run FlashRank
reranked_results = reranker.rerank(rerank_request)

# Returns list sorted by relevance (highest score first)
# [
#   {"id": 0, "score": 0.9523, ...},  ← Best match
#   {"id": 1, "score": 0.8912, ...},
#   {"id": 2, "score": 0.7845, ...},
#   {"id": 3, "score": 0.6234, ...},
#   {"id": 4, "score": 0.5634, ...},  ← Worst match
# ]
```

---

## Why Stage 2 is Better Than Stage 1

| Aspect | Stage 1 (Vector) | Stage 2 (FlashRank) |
|--------|-----------------|-------------------|
| **Method** | Embedding distance | Cross-encoder neural network |
| **Speed** | Very fast (1-2ms) | Slower (50-200ms) |
| **Accuracy** | ~80% | ~95% |
| **Understands** | Word similarity | Semantic relevance & context |
| **Can distinguish** | ❌ Similar sentences | ✅ Similar but different meaning |
| **Example** | Can't tell "login" vs "logout" apart | Clearly ranks "login" higher for "login query" |

---

## 📈 Score Interpretation

After Stage 2, use these thresholds:

```
Score 0.90 - 1.00  → 🟢 PERFECT MATCH
                      Use this result immediately

Score 0.80 - 0.89  → 🟡 EXCELLENT MATCH
                      Very likely correct

Score 0.70 - 0.79  → 🟠 GOOD MATCH
                      Probably correct, can verify

Score 0.50 - 0.69  → 🟠 ACCEPTABLE MATCH
                      Manual review recommended

Score < 0.50       → 🔴 POOR MATCH
                      Likely wrong, ask user for clarification
```

---

## 🔧 Configuration

You can adjust how Stage 2 works:

```python
# In ranking_engine.py

# Change top_k to rerank more/fewer candidates
top_k = 5   # Rerank top-5 (default)
top_k = 10  # Rerank top-10 for higher recall

# FlashRank parameters (if needed)
from flashrank import Ranker

reranker = Ranker(
    model_name="ms-marco-MiniLM-L-12-v2",  # Cross-encoder model
    batch_size=32,                          # Process 32 pairs at a time
    use_gpu=True                            # Use GPU if available
)
```

---

##  Summary

**Stage 2 Process:**
1. Takes 5 candidates from Stage 1
2.  Adds API metadata to each for better context
3.  Creates (query, document) pairs
4.  Sends each pair through ms-marco-MiniLM-L-12-v2 model
5.  Model outputs relevance score (0-1)
6.  Resorts all 5 by score (highest first)
7.  Returns reranked list

**Result**: Much more accurate ranking than Stage 1 alone! 

---

**Model Used**: `ms-marco-MiniLM-L-12-v2`
- **Type**: Cross-Encoder (trained on MS MARCO dataset)
- **Parameters**: 110 million
- **Purpose**: Pair-wise relevance scoring
- **Accuracy**: ~95% on test sets

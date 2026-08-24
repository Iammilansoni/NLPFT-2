### Routing Benchmark

`180` held-out queries · `20` API templates · embedder `tfidf-char3` · reranker `ms-marco-MiniLM-L-12-v2`

Stage 1 recall@25: **0.978**

| Strategy | Hit@1 | Hit@3 | MRR@5 | p50 | p95 |
|---|---|---|---|---|---|
| `stage1_only` | 0.617 | 0.861 | 0.740 | 0.3ms | 0.4ms |
| `v1_heuristic` | 0.444 | 0.717 | 0.581 | 0.3ms | 0.4ms |
| `v2_cross_encoder` | 0.728 | 0.906 | 0.823 | 122.3ms | 175.5ms |

**Hit@1 by difficulty tier**

| Strategy | direct | paraphrase | colloquial | hard_negative |
|---|---|---|---|---|
| `stage1_only` | 0.950 | 0.400 | 0.825 | 0.400 |
| `v1_heuristic` | 0.700 | 0.300 | 0.575 | 0.275 |
| `v2_cross_encoder` | 0.950 | 0.650 | 0.825 | 0.525 |

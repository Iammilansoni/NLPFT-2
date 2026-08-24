### Routing Benchmark

`180` held-out queries · `20` API templates · embedder `bge-small-en-v1.5` · reranker `ms-marco-MiniLM-L-12-v2`

Stage 1 recall@25: **1.000**

| Strategy | Hit@1 | Hit@3 | MRR@5 | p50 | p95 |
|---|---|---|---|---|---|
| `stage1_only` | 0.822 | 0.983 | 0.896 | 167.4ms | 262.7ms |
| `bm25_only` | 0.600 | 0.861 | 0.727 | 0.2ms | 0.4ms |
| `v1_heuristic` | 0.589 | 0.828 | 0.705 | 167.4ms | 262.7ms |
| `hybrid_rrf` | 0.806 | 0.956 | 0.880 | 147.8ms | 222.4ms |
| `v2_cross_encoder` | 0.739 | 0.944 | 0.836 | 320.9ms | 589.6ms |
| `hybrid_rrf_cross_encoder` | 0.733 | 0.917 | 0.830 | 273.4ms | 550.3ms |

**Hit@1 by difficulty tier**

| Strategy | direct | paraphrase | colloquial | hard_negative |
|---|---|---|---|---|
| `stage1_only` | 0.950 | 0.900 | 0.800 | 0.600 |
| `bm25_only` | 0.900 | 0.417 | 0.700 | 0.475 |
| `v1_heuristic` | 0.775 | 0.583 | 0.600 | 0.400 |
| `hybrid_rrf` | 1.000 | 0.717 | 0.900 | 0.650 |
| `v2_cross_encoder` | 0.975 | 0.683 | 0.800 | 0.525 |
| `hybrid_rrf_cross_encoder` | 0.950 | 0.683 | 0.800 | 0.525 |

"""
BM25 Lexical Retrieval
======================

The lexical arm of hybrid retrieval.

WHY A LEXICAL ARM AT ALL
------------------------
The routing benchmark localises the weakness precisely: the `paraphrase` tier
sits at 0.400 Hit@1 for vector-only recall, and hard negatives at 0.400. Dense
embeddings smear rare, high-signal tokens - an API name like `SKU-44`, an
endpoint fragment like `/auth/token/refresh`, an identifier like `pay_331` - into
a general "sounds like commerce" region. Those tokens are exactly what BM25
weights most heavily, because rarity IS its scoring signal.

Dense and lexical retrieval fail on DIFFERENT queries. That is the precondition
for fusion helping; if they failed on the same ones, fusing would only average
two views of the same mistake.

SCORING
-------
Standard BM25-Okapi:

    score(D,Q) = SUM_q  IDF(q) * ( f(q,D) * (k1 + 1) )
                              / ( f(q,D) + k1 * (1 - b + b * |D| / avgdl) )

    IDF(q) = ln( 1 + (N - n(q) + 0.5) / (n(q) + 0.5) )

k1=1.5 controls term-frequency saturation, b=0.75 controls length normalisation.
These are the standard defaults and were not tuned - tuning them against the same
180 queries used to report results would be fitting the benchmark.

PRODUCTION FIDELITY - READ THIS
-------------------------------
This implementation is dense-matrix and holds the full term-document matrix in
memory. That is correct for the eval harness (100 utterances) and for a single
tenant's template catalogue, but it does NOT scale to a multi-tenant corpus.

In production the lexical arm should be PostgreSQL full-text search
(`tsvector` + `ts_rank_cd`), which lives in the database already holding the
vectors, respects the same RLS policies, and needs no new service.

BM25 and `ts_rank_cd` are both lexical but are not the same function. This
harness therefore predicts the DIRECTION and rough magnitude of the hybrid gain,
not its exact value. Re-measure after the Postgres implementation lands.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

K1 = 1.5
B = 0.75

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> List[str]:
    """
    Lowercase alphanumeric tokens, plus sub-tokens split on digit boundaries.

    `pay_331` yields ["pay331", "pay", "331"] so a query mentioning either the
    whole identifier or its prefix can match. Identifier-shaped tokens are the
    main thing lexical retrieval contributes over dense, so splitting them is
    where the value is.
    """
    out: List[str] = []
    for tok in _TOKEN_RE.findall(text.lower()):
        out.append(tok)
        if any(c.isdigit() for c in tok) and any(c.isalpha() for c in tok):
            parts = re.findall(r"[a-z]+|[0-9]+", tok)
            out.extend(p for p in parts if len(p) > 1)
    return out


class BM25Index:
    """In-memory BM25-Okapi index over a fixed document set."""

    def __init__(self, k1: float = K1, b: float = B) -> None:
        self.k1 = k1
        self.b = b
        self.vocab: Dict[str, int] = {}
        self.tf: Optional[np.ndarray] = None        # (n_docs, n_terms)
        self.idf: Optional[np.ndarray] = None       # (n_terms,)
        self.doc_len: Optional[np.ndarray] = None   # (n_docs,)
        self.avgdl: float = 0.0
        self.n_docs: int = 0

    def build(self, corpus: Sequence[str]) -> "BM25Index":
        tokenised = [tokenize(doc) for doc in corpus]
        self.n_docs = len(tokenised)
        if self.n_docs == 0:
            return self

        df: Dict[str, int] = defaultdict(int)
        for toks in tokenised:
            for term in set(toks):
                df[term] += 1
        self.vocab = {t: i for i, t in enumerate(sorted(df))}

        self.tf = np.zeros((self.n_docs, len(self.vocab)), dtype=np.float32)
        for row, toks in enumerate(tokenised):
            for term in toks:
                self.tf[row, self.vocab[term]] += 1.0

        self.doc_len = self.tf.sum(axis=1)
        self.avgdl = float(self.doc_len.mean()) if self.n_docs else 0.0

        self.idf = np.zeros(len(self.vocab), dtype=np.float32)
        for term, i in self.vocab.items():
            n_q = df[term]
            self.idf[i] = math.log(1.0 + (self.n_docs - n_q + 0.5) / (n_q + 0.5))
        return self

    def score(self, query: str) -> np.ndarray:
        """BM25 score of every document against `query`. Shape (n_docs,)."""
        if self.tf is None or self.n_docs == 0:
            return np.zeros(0, dtype=np.float32)

        cols = [self.vocab[t] for t in tokenize(query) if t in self.vocab]
        if not cols:
            return np.zeros(self.n_docs, dtype=np.float32)

        # Length normalisation denominator, shared across query terms.
        norm = self.k1 * (1.0 - self.b + self.b * (self.doc_len / max(self.avgdl, 1e-9)))

        scores = np.zeros(self.n_docs, dtype=np.float32)
        for col in cols:
            f = self.tf[:, col]
            scores += self.idf[col] * (f * (self.k1 + 1.0)) / (f + norm + 1e-9)
        return scores

    def search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """Top-k (doc_index, score), descending. Zero-scoring docs are dropped."""
        scores = self.score(query)
        if scores.size == 0:
            return []
        k = min(top_k, scores.size)
        idx = np.argpartition(-scores, k - 1)[:k]
        idx = idx[np.argsort(-scores[idx])]
        return [(int(i), float(scores[i])) for i in idx if scores[i] > 0.0]

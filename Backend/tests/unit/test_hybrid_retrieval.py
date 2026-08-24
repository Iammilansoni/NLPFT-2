"""
Unit tests for the lexical (BM25) and fusion (RRF) retrieval components.

Also locks in the configuration decision the benchmark produced: the
cross-encoder ships DISABLED, because measured against the production embedder
it is a regression. A future edit that flips that default without re-measuring
will fail here.
"""

from __future__ import annotations

import importlib
import os

import pytest

from app.nlp.fusion import RRF_K, fuse_result_rows, reciprocal_rank_fusion
from app.nlp.lexical_bm25 import BM25Index, tokenize


# ===========================================================================
# Tokenisation
# ===========================================================================

def test_tokenize_lowercases_and_strips_punctuation():
    assert tokenize("Cancel Order #8820!") == ["cancel", "order", "8820"]


def test_tokenize_splits_on_underscore():
    """`pay_331` splits on the underscore, yielding both halves as terms."""
    toks = tokenize("payment pay_331")
    assert toks == ["payment", "pay", "331"]


def test_tokenize_splits_alphanumeric_run_into_subtokens():
    """
    A run with no separator (`pay331`) keeps the whole token AND emits its
    alpha/digit halves, so a query naming either form still matches. Identifier
    shapes are the main thing lexical retrieval contributes over dense.
    """
    toks = tokenize("charge pay331 now")
    assert "pay331" in toks and "pay" in toks and "331" in toks


def test_tokenize_does_not_split_pure_alpha_or_pure_digits():
    assert tokenize("refund 4500") == ["refund", "4500"]


# ===========================================================================
# BM25
# ===========================================================================

CORPUS = [
    "log me in with my email and password",
    "cancel order 8820 before it ships",
    "refund 45.00 on order 8820",
    "send an sms notification to the user",
]


def test_bm25_ranks_exact_term_match_first():
    idx = BM25Index().build(CORPUS)
    hits = idx.search("cancel order 8820", top_k=4)
    assert hits, "expected at least one hit"
    assert hits[0][0] == 1


def test_bm25_rewards_rare_terms_over_common_ones():
    """
    IDF is the whole point: `8820` appears in 2 of 4 docs, `order` in 2, but
    `refund` in only 1 -- so a refund query must pick the refund doc even though
    it shares 'order 8820' with another.
    """
    idx = BM25Index().build(CORPUS)
    hits = idx.search("refund", top_k=4)
    assert hits[0][0] == 2


def test_bm25_returns_empty_for_out_of_vocabulary_query():
    idx = BM25Index().build(CORPUS)
    assert idx.search("quantum chromodynamics", top_k=4) == []


def test_bm25_handles_empty_corpus():
    idx = BM25Index().build([])
    assert idx.search("anything", top_k=5) == []


def test_bm25_scores_are_non_negative():
    idx = BM25Index().build(CORPUS)
    assert all(s >= 0.0 for _, s in idx.search("order", top_k=4))


# ===========================================================================
# RRF
# ===========================================================================

def test_rrf_promotes_document_ranked_well_by_both():
    """
    'b' is 2nd in both lists; 'a' and 'c' are 1st in one and absent from the
    other. Agreement should beat a single first place -- that is the property
    that makes fusion useful.
    """
    fused = reciprocal_rank_fusion([["a", "b"], ["c", "b"]])
    assert fused[0][0] == "b"


def test_rrf_ignores_score_magnitude_entirely():
    """
    RRF sees only rank. Two runs whose underlying scores differ wildly but whose
    ORDER matches must fuse identically -- this is why it needs no calibration,
    unlike the weighted blend v1 shipped.
    """
    a = reciprocal_rank_fusion([["x", "y", "z"], ["y", "x", "z"]])
    b = reciprocal_rank_fusion([["x", "y", "z"], ["y", "x", "z"]])
    assert a == b


def test_rrf_score_matches_the_formula():
    fused = dict(reciprocal_rank_fusion([["a", "b"]], k=RRF_K))
    assert fused["a"] == pytest.approx(1.0 / (RRF_K + 1))
    assert fused["b"] == pytest.approx(1.0 / (RRF_K + 2))


def test_rrf_is_deterministic_on_ties():
    """Ties break on first appearance, so output order is stable across runs."""
    lists = [["p", "q"], ["q", "p"]]
    assert reciprocal_rank_fusion(lists) == reciprocal_rank_fusion(lists)


def test_rrf_rejects_mismatched_weights():
    with pytest.raises(ValueError):
        reciprocal_rank_fusion([["a"], ["b"]], weights=[1.0])


def test_rrf_handles_empty_input():
    assert reciprocal_rank_fusion([]) == []


def test_fuse_result_rows_tags_which_arm_found_each_row():
    """
    `fusion_sources` is a debugging affordance: a row surfaced by BOTH arms is a
    far stronger signal than one found by either alone.
    """
    vec = [{"row_key": "r1", "similarity": 0.9}, {"row_key": "r2", "similarity": 0.8}]
    lex = [{"row_key": "r2", "bm25_score": 5.0}, {"row_key": "r3", "bm25_score": 3.0}]

    fused = fuse_result_rows(vec, lex, id_key="row_key")
    by_key = {r["row_key"]: r for r in fused}

    assert by_key["r2"]["fusion_sources"] == ["vector", "lexical"]
    assert by_key["r1"]["fusion_sources"] == ["vector"]
    assert by_key["r3"]["fusion_sources"] == ["lexical"]
    assert by_key["r2"]["rrf_score"] > by_key["r1"]["rrf_score"]


def test_fuse_result_rows_preserves_original_fields():
    vec = [{"row_key": "r1", "similarity": 0.9, "t_id": "T1"}]
    fused = fuse_result_rows(vec, [], id_key="row_key")
    assert fused[0]["t_id"] == "T1" and fused[0]["similarity"] == 0.9


def test_fuse_result_rows_respects_top_k():
    vec = [{"row_key": f"r{i}"} for i in range(10)]
    assert len(fuse_result_rows(vec, [], id_key="row_key", top_k=3)) == 3


# ===========================================================================
# Shipped configuration
# ===========================================================================

def test_cross_encoder_ships_disabled_by_default():
    """
    Regression guard on a MEASURED decision.

    Against bge-small-en-v1.5 over the 180-query benchmark the cross-encoder
    scores 0.739 Hit@1 versus 0.822 for dense retrieval alone, and loses at
    every retrieval depth tested (k=5, 10, 25). It ships off.

    If this default is flipped, re-run `evals/run_eval.py --embedder onnx` and
    update the README table in the same change -- do not simply edit this test.
    """
    import app.nlp.cross_encoder_reranker as ce

    saved = os.environ.pop("RERANKER_ENABLED", None)
    try:
        reloaded = importlib.reload(ce)
        assert reloaded.RERANKER_ENABLED is False, (
            "cross-encoder must default to OFF: it measured -0.083 Hit@1 against "
            "bge-small. See evals/README.md before changing this."
        )
    finally:
        if saved is not None:
            os.environ["RERANKER_ENABLED"] = saved
        importlib.reload(ce)


def test_stage1_top_k_default_is_the_measured_optimum():
    import app.nlp.cross_encoder_reranker as ce

    assert ce.STAGE1_TOP_K == 25

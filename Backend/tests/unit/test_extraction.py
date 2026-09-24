"""Hybrid extraction: rules, grounding, value repair, and the model fallback chain."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.extraction_rules import (
    extract_by_rules,
    grounding_problem,
    refine_llm_value,
)
from app.services.structured_extraction_service import StructuredExtractionService

LOGIN = {"properties": {"email": {"type": "string", "format": "email"}, "password": {"type": "string"}},
         "required": ["email", "password"]}
CHANGE = {"properties": {"current_password": {"type": "string"}, "new_password": {"type": "string"}},
          "required": ["current_password", "new_password"]}
REFUND = {"properties": {"order_id": {"type": "string"}, "amount": {"type": "number"}}, "required": ["order_id"]}
NOTIFY = {"properties": {"user_id": {"type": "string"},
                         "channel": {"type": "string", "enum": ["email", "sms", "push"]},
                         "body": {"type": "string"}},
          "required": ["user_id", "channel", "body"]}
PREFS = {"properties": {"user_id": {"type": "string"}, "email_enabled": {"type": "boolean"},
                        "sms_enabled": {"type": "boolean"}}, "required": ["user_id"]}


def values(query, schema):
    return {k: v.value for k, v in extract_by_rules(query, schema).items()}


# -- rules ---------------------------------------------------------------------

def test_rules_read_email_and_password():
    assert values("log in as maria@acme.io with password Tr0ub4dor&3", LOGIN) == {
        "email": "maria@acme.io", "password": "Tr0ub4dor&3"}


def test_identifier_after_its_noun_and_leftover_number():
    # "8820" is claimed by order_id first, so the only free number is the amount.
    assert values("refund 25 dollars on order #8820", REFUND) == {"order_id": "8820", "amount": 25}


def test_number_inside_an_identifier_is_not_an_amount():
    assert values("refund $12.50 for ORD-771", REFUND) == {"amount": 12.5}


def test_shared_keyword_is_left_to_the_model():
    # Both fields contain "password": guessing which one is meant is the model's job.
    assert values("change my password from oldpass1 to NewPass#9", CHANGE) == {}
    assert values("my current password is abc123", CHANGE) == {"current_password": "abc123"}


def test_enum_value_named_in_the_request():
    assert values("send an sms to user 4821", NOTIFY) == {"user_id": "4821", "channel": "sms"}


def test_plain_words_are_never_identifiers():
    assert values("show me my profile", {"properties": {"user_id": {"type": "string"}}}) == {}


# -- grounding -----------------------------------------------------------------

@pytest.mark.parametrize("field,value,spec,query", [
    ("email", "user@example.com", {"type": "string", "format": "email"}, "I can't remember my password"),
    ("password", "log me in please", {"type": "string"}, "log me in please"),
    ("page", 1, {"type": "integer"}, "list the users"),
    ("email_enabled", True, {"type": "boolean"}, "change my notification settings"),
    ("channel", "email", {"type": "string", "enum": ["email", "sms"]}, "send a notification"),
    ("reason", "cancel order 8820", {"type": "string"}, "cancel order 8820"),
])
def test_invented_values_are_not_accepted(field, value, spec, query):
    command = {"cancel", "order", "8820", "orders", "reason", "user", "notification", "send"}
    assert grounding_problem(field, value, spec, query, command) is not None


@pytest.mark.parametrize("field,value,spec,query", [
    ("amount", 12.5, {"type": "number"}, "refund $12.50 for ORD-771"),
    ("sms_enabled", False, {"type": "boolean"}, "disable sms for user 1200"),
    ("reason", "found it cheaper", {"type": "string"}, "cancel ORD-2291, reason: found it cheaper"),
])
def test_values_from_the_request_are_accepted(field, value, spec, query):
    assert grounding_problem(field, value, spec, query, {"cancel", "order"}) is None


# -- value repair --------------------------------------------------------------

def test_clipped_secret_is_snapped_to_the_whole_token():
    assert refine_llm_value("new_password", "4ever", {"type": "string"},
                            "new signup: tom@garden.net / Tulips#4ever", set()) == "Tulips#4ever"


def test_command_words_are_trimmed_from_free_text():
    command = {"user", "88", "send", "notification"}
    assert refine_llm_value("body", "user 88 that the meeting moved", {"type": "string"},
                            "text user 88 that the meeting moved", command) == "the meeting moved"
    assert refine_llm_value("body", "notify user 3003: Your ride is here", {"type": "string"},
                            "push notify user 3003: Your ride is here", command) == "Your ride is here"


# -- hybrid flow ---------------------------------------------------------------

class FakeLLM:
    name = "fake/model"

    def __init__(self, answer=None, error=None):
        self.answer, self.error, self.calls = answer, error, 0

    async def generate_json(self, prompt, schema):
        self.calls += 1
        if self.error:
            raise self.error
        return json.dumps(self.answer)


@pytest.mark.asyncio
async def test_model_is_skipped_when_rules_explain_the_whole_request():
    llm = FakeLLM({"reason": "should not be asked"})
    result = await StructuredExtractionService().extract(
        "cancel order 8820", {"properties": {"order_id": {"type": "string"}, "reason": {"type": "string"}},
                              "required": ["order_id"]}, "Cancel_Order", "/orders/{order_id}/cancel", llm=llm)
    assert result.values == {"order_id": "8820"} and llm.calls == 0
    assert result.fields["order_id"]["source"] == "rule"


@pytest.mark.asyncio
async def test_invented_model_values_are_reported_not_used():
    llm = FakeLLM({"email": "user@example.com", "password": "hunter2"})
    result = await StructuredExtractionService().extract(
        "I forgot my login", LOGIN, "User_Login", "/auth/login", llm=llm)
    assert result.values == {}
    assert set(result.unverified) == {"email", "password"}
    assert result.missing_required == ["email", "password"] and not result.ok


@pytest.mark.asyncio
async def test_model_values_carry_source_and_confidence():
    llm = FakeLLM({"current_password": "oldpass1", "new_password": "NewPass#9"})
    result = await StructuredExtractionService().extract(
        "change my password from oldpass1 to NewPass#9", CHANGE, "Password_Change", "/auth/password/change", llm=llm)
    assert result.ok and result.values == {"current_password": "oldpass1", "new_password": "NewPass#9"}
    assert {f["source"] for f in result.fields.values()} == {"llm"}
    assert result.confidence == pytest.approx(0.85)


@pytest.mark.asyncio
async def test_failing_user_model_falls_back_to_the_local_one():
    service = StructuredExtractionService()
    llm = FakeLLM(error=TimeoutError("slow"))

    async def local(prompt, schema):
        return json.dumps({"current_password": "oldpass1", "new_password": "NewPass#9"})

    with patch.object(service, "_generate", local):
        result = await service.extract(
            "change my password from oldpass1 to NewPass#9", CHANGE, "Password_Change", "/x", llm=llm)
    assert result.ok and result.model == f"ollama/{service.model}"


@pytest.mark.asyncio
async def test_rules_strategy_never_calls_a_model():
    llm = FakeLLM({"password": "x"})
    result = await StructuredExtractionService().extract(
        "login for anna@shop.io", LOGIN, "User_Login", "/auth/login", strategy="rules", llm=llm)
    assert result.values == {"email": "anna@shop.io"} and llm.calls == 0


# -- benchmark regression ------------------------------------------------------

def test_rules_never_invent_or_misread_on_the_benchmark():
    """The rules pass is trusted without checks, so on 100 labelled requests it must never be wrong."""
    evals = Path(__file__).resolve().parents[3] / "evals"
    if not (evals / "extraction_cases.py").exists():
        pytest.skip("evals/ is not available (running inside the container)")
    sys.path.insert(0, str(evals))
    import run_extraction_eval as ev

    outputs = [values(c["query"], ev.SCHEMAS[c["api"]]) for c in ev.CASES]
    metrics = ev.score(ev.CASES, outputs)
    assert metrics["invented"] == 0 and metrics["wrong"] == 0
    assert metrics["recall"] >= 0.65


@pytest.mark.asyncio
async def test_hybrid_reports_degraded_when_every_model_is_down():
    service = StructuredExtractionService()

    async def down(prompt, schema):
        raise ConnectionError("ollama is down")

    with patch.object(service, "_generate", down):
        result = await service.extract(
            "change my password from oldpass1 to NewPass#9", CHANGE, "Password_Change", "/x",
            llm=FakeLLM(error=TimeoutError("slow")),
        )
    assert result.degraded and not result.ok
    assert "llm_unreachable" in result.reason

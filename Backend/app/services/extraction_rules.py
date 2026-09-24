"""
Deterministic extraction and grounding
======================================

Two jobs, both without a model:

1. RULES: fill the fields whose values can be read straight off the request,
   using only what the template's JSON Schema says about each field (its name,
   type, format and enum). No per-API code: "order_id" looks for an identifier
   after the word "order", "email" for an email address, "page" for a number
   next to the word "page", an enum field for one of its values.

   Rules only fire when the answer is unambiguous. When two fields could claim
   the same value, or a keyword is shared, the field is left for the model.
   A rule-extracted value is exact text from the request, so it is trusted.

2. GROUNDING: check a model's values against the request. A value the user
   never typed is not accepted as fact; it is reported as unverified. This is
   what stops a small model from filling "email" with user@example.com or a
   password field with the whole sentence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

RULE_CONFIDENCE = 0.99
GROUNDED_CONFIDENCE = 0.85
INFERRED_CONFIDENCE = 0.7  # enum choices and on/off switches the model inferred

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+")
NUMBER_RE = re.compile(r"(?<![\w.\-])[$€£₹]?\s?(\d+(?:[.,]\d+)?)(?![\w@\-])")
TIMEZONE_RE = re.compile(r"\b[A-Z][A-Za-z]+/[A-Za-z_]+(?:/[A-Za-z_]+)?\b")
CURRENCY_CODE_RE = re.compile(r"\b[A-Z]{3}\b")
# Words that are never a value on their own ("reset password for the user").
STOPWORDS = {
    "a", "an", "the", "my", "me", "is", "to", "for", "of", "and", "or", "with", "on", "in",
    "it", "this", "that", "be", "please", "id", "number", "no", "new", "current", "old",
    "from", "using", "use", "via", "by", "as", "at", "reset", "link", "code", "account",
}


@dataclass
class FieldValue:
    value: Any
    source: str          # "rule" | "llm"
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "source": self.source, "confidence": self.confidence}


def _field_type(spec: Dict[str, Any]) -> str:
    jtype = spec.get("type") or "string"
    if isinstance(jtype, list):
        jtype = next((t for t in jtype if t != "null"), "string")
    return jtype


def _words(name: str) -> List[str]:
    return [w for w in re.split(r"[_\-\s]+", name.lower()) if w]


def _is_identifier_field(name: str) -> bool:
    words = _words(name)
    return len(words) >= 2 and words[-1] == "id"


def _is_secret_field(name: str) -> bool:
    return any(w in ("password", "token", "otp", "secret", "pin", "code") for w in _words(name))


def _looks_like_value(token: str) -> bool:
    """A secret or identifier: has a digit or symbol, or mixes case. Plain words are not values."""
    if not token or token.lower() in STOPWORDS:
        return False
    return bool(re.search(r"\d", token) or re.search(r"[^A-Za-z]", token) or re.search(r"[a-z][A-Z]", token))


def _clean_token(token: str) -> str:
    # Sentence punctuation after a value is not part of it; symbols inside it are.
    return token.rstrip(",;:?)\"'").rstrip(".") if not token.endswith("...") else token


class _Spans:
    """Character ranges of the request already claimed by a field."""

    def __init__(self) -> None:
        self.taken: List[Tuple[int, int]] = []

    def free(self, start: int, end: int) -> bool:
        return all(end <= a or start >= b for a, b in self.taken)

    def take(self, start: int, end: int) -> None:
        self.taken.append((start, end))


def _keyword_value(query: str, keyword: str, spans: _Spans, *, number: bool = False) -> List[Tuple[str, int, int]]:
    """Values right after `keyword` ("order #8820", "password is x", "page 3")."""
    kw = r"\s+".join(re.escape(w) for w in keyword.split())
    value = r"(\d+(?:\.\d+)?)" if number else r"(\S+)"
    pattern = rf"\b{kw}s?\b(?:\s+(?:id|number|no\.?|code))?\s*(?:is|was|=|:|to|of)?\s*#?\s*{value}"
    found = []
    for m in re.finditer(pattern, query, flags=re.IGNORECASE):
        raw = m.group(1)
        token = raw if number else _clean_token(raw)
        start = m.start(1)
        if token and spans.free(start, start + len(token)):
            found.append((token, start, start + len(token)))
    return found


def extract_by_rules(query: str, schema: Dict[str, Any]) -> Dict[str, FieldValue]:
    """Values that can be read off the request without a model. Unambiguous ones only."""
    props: Dict[str, Dict[str, Any]] = {
        k: v for k, v in (schema.get("properties") or {}).items() if isinstance(v, dict)
    }
    spans = _Spans()
    out: Dict[str, FieldValue] = {}

    def claim(field: str, value: Any, start: int, end: int) -> None:
        spans.take(start, end)
        out[field] = FieldValue(value, "rule", RULE_CONFIDENCE)

    # 1. Email addresses: one email field and one address, or one-to-one in order.
    email_fields = [
        k for k, v in props.items()
        if v.get("format") == "email" or ("email" in _words(k) and _field_type(v) == "string")
    ]
    emails = list(EMAIL_RE.finditer(query))
    if email_fields and len(emails) == len(email_fields):
        for field, m in zip(email_fields, emails):
            claim(field, m.group(0), m.start(), m.end())

    # 2. Identifiers: the value after the field's own noun ("order" for order_id).
    for field in [k for k in props if _is_identifier_field(k) and _field_type(props[k]) == "string"]:
        noun = " ".join(_words(field)[:-1])
        # An identifier has a digit or a separator ("8820", "u_77af", "pm_card_visa"), never a plain word.
        hits = [h for h in _keyword_value(query, noun, spans) if _looks_like_value(h[0]) and re.search(r"[\d_\-]", h[0])]
        if len(hits) == 1:
            claim(field, *hits[0])

    # 3. Secrets and codes: after their full name ("new password", "refresh token"),
    #    or after their last word when no other field shares it.
    secret_fields = [k for k in props if _is_secret_field(k) and _field_type(props[k]) == "string" and k not in out]
    for field in secret_fields:
        words = _words(field)
        keywords = [" ".join(words)]
        if not any(words[-1] in _words(other) for other in props if other != field):
            keywords.append(words[-1])
        for keyword in keywords:
            hits = [h for h in _keyword_value(query, keyword, spans) if _looks_like_value(h[0])]
            if len(hits) == 1:
                claim(field, *hits[0])
                break

    # 4. Enums: exactly one allowed value appears as a word.
    for field, spec in props.items():
        if field in out or not spec.get("enum"):
            continue
        hits = [
            (str(option), m.start(), m.end())
            for option in spec["enum"]
            for m in re.finditer(rf"\b{re.escape(str(option))}\b", query, flags=re.IGNORECASE)
            if spans.free(m.start(), m.end())
        ]
        if len({h[0] for h in hits}) == 1:
            claim(field, *hits[0])

    # 5. Formats recognisable from the field name: IANA timezones, currency codes.
    for field, spec in props.items():
        if field in out or _field_type(spec) != "string":
            continue
        words = _words(field)
        regex = TIMEZONE_RE if ("timezone" in words or "tz" in words) else CURRENCY_CODE_RE if "currency" in words else None
        if regex:
            hits = [m for m in regex.finditer(query) if spans.free(m.start(), m.end())]
            if len(hits) == 1:
                claim(field, hits[0].group(0), hits[0].start(), hits[0].end())

    # 6. Numbers: next to the field's name ("page 3", "limit 20"), then, if exactly
    #    one numeric field and one unclaimed number remain, that pair ("refund 25 on order 8820").
    numeric = [k for k, v in props.items() if _field_type(v) in ("integer", "number") and k not in out]
    for field in list(numeric):
        hits = _keyword_value(query, " ".join(_words(field)), spans, number=True)
        if len(hits) == 1:
            token, start, end = hits[0]
            claim(field, _as_number(token, props[field]), start, end)
            numeric.remove(field)
    if len(numeric) == 1:
        free_numbers = [m for m in NUMBER_RE.finditer(query) if spans.free(m.start(1), m.end(1))]
        if len(free_numbers) == 1:
            m = free_numbers[0]
            claim(numeric[0], _as_number(m.group(1), props[numeric[0]]), m.start(1), m.end(1))

    return out


def _as_number(token: str, spec: Dict[str, Any]) -> Any:
    value = float(token.replace(",", "."))
    return int(value) if _field_type(spec) == "integer" or value.is_integer() else value


# ---------------------------------------------------------------------------
# Grounding
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).lower()).strip(" .,!?;:\"'")


# Words that introduce a message rather than belong to it ("text user 88 that ...").
_LEAD_INS = {"that", "saying", "says", "say", "telling", "tell", "message", "text", "reading", "with"}


def refine_llm_value(
    field: str, value: Any, spec: Dict[str, Any], query: str, command_words: Set[str]
) -> Any:
    """
    Repair two habits of small models before grounding:

    * clipping a single-token value ("Autumn2026" for "Autumn2026!", "4ever" for
      "Tulips#4ever"): snap it to the whole token of the request that contains it;
    * dragging the command into free text ("user 88 that the meeting moved"):
      drop leading command words, already-extracted values and lead-ins.
    """
    if not isinstance(value, str) or _field_type(spec) != "string" or spec.get("enum"):
        return value
    text = value.strip()
    if _is_secret_field(field) or _is_identifier_field(field):
        tokens = [_clean_token(t) for t in query.split()]
        containing = [t for t in tokens if text and text in t]
        if len(containing) == 1:
            return containing[0]
        return text
    if ":" in text:
        head, tail = text.split(":", 1)
        if tail.strip() and len(head.split()) <= 4:
            text = tail.strip()
    words = text.split()
    droppable = command_words | _LEAD_INS
    while len(words) > 1 and re.sub(r"[^a-z0-9]", "", words[0].lower()) in droppable:
        words = words[1:]
    return " ".join(words)


def grounding_problem(
    field: str, value: Any, spec: Dict[str, Any], query: str, command_words: Optional[Set[str]] = None
) -> Optional[str]:
    """
    Why a model's value can't be accepted as fact, or None when it can.

    Accepted only what the request supports: text it contains, numbers it
    states, an enum option it names, an on/off setting whose subject it
    mentions ("no more emails" -> email_enabled). `command_words` are the
    words of the API itself ("cancel", "order"); a free-text value made only
    of those is the command echoed back, not a value.
    """
    jtype = _field_type(spec)
    q = _normalise(query)
    q_words = set(re.findall(r"[a-z0-9]+", q))
    if jtype == "boolean":
        subject = [w for w in _words(field) if w not in ("enabled", "enable", "is", "has", "allow", "on", "flag")]
        return None if any(w in q_words or w + "s" in q_words for w in subject) else "the request doesn't mention it"
    if spec.get("enum"):
        if value not in spec["enum"]:
            return f"not one of {spec['enum']}"
        return None if str(value).lower() in q_words else "inferred, not stated"
    if jtype in ("integer", "number"):
        try:
            target = float(value)
        except (TypeError, ValueError):
            return "not a number"
        stated = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", query.replace(",", "."))]
        return None if any(abs(n - target) < 1e-9 for n in stated) else "that number is not in the request"
    if jtype in ("array", "object"):
        # Structured values: at least one value inside must come from the request.
        leaves = [_normalise(leaf) for leaf in _leaves(value)]
        return None if any(leaf and leaf in q for leaf in leaves) else "none of it appears in the request"
    text = _normalise(value)
    if not text:
        return "empty"
    if text == q and len(q.split()) > 2:
        return "the model copied the whole request"
    if (_is_secret_field(field) or _is_identifier_field(field) or spec.get("format") == "email") and " " in text:
        return "a single value was expected, not a phrase"
    if spec.get("format") == "email" and not EMAIL_RE.fullmatch(str(value).strip()):
        return "not an email address"
    if text not in q:
        return "not in the request"
    content = set(re.findall(r"[a-z0-9]+", text)) - STOPWORDS - (command_words or set())
    if not content:
        return "only repeats the command"
    return None


def _leaves(value: Any) -> List[str]:
    if isinstance(value, dict):
        return [leaf for v in value.values() for leaf in _leaves(v)]
    if isinstance(value, list):
        return [leaf for v in value for leaf in _leaves(v)]
    return [] if value is None else [str(value)]


def confidence_for(spec: Dict[str, Any]) -> float:
    return INFERRED_CONFIDENCE if _field_type(spec) == "boolean" else GROUNDED_CONFIDENCE


def command_words(api_name: str, endpoint: str, schema: Dict[str, Any], extracted: Dict[str, Any]) -> Set[str]:
    """Words that name the operation or its fields, plus values already extracted."""
    words = set(_words(api_name)) | set(re.findall(r"[a-z0-9]+", endpoint.lower()))
    for name in (schema.get("properties") or {}):
        words |= set(_words(name))
    for value in extracted.values():
        words |= set(re.findall(r"[a-z0-9]+", str(value).lower()))
    return words


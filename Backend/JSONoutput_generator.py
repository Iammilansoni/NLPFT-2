from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from redis_config import get_redis_client

_encoder = None
_templates: Optional[Dict[str, Any]] = None
_embedding_cache: Dict[str, bytes] = {}
MAX_CACHE_SIZE = 1000

r = get_redis_client()
INDEX_NAME = "idx:apis"
VECTOR_FIELD = "query_embedding"

EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
URL_PATTERN = re.compile(r'https?://[^\s]+|www\.[^\s]+|(?:[a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}(?:/[^\s]*)?')
WORD_PATTERN = re.compile(r'\S+')
PASSWORD_PATTERN = re.compile(r'[A-Za-z].*[\d@#$%^&*!_\-+=/\\.,;:]|[\d@#$%^&*!_\-+=/\\.,;:].*[A-Za-z]')
TOKEN_PATTERN = re.compile(r'\b(?:bearer|token|session|auth|jwt)[\s_-]?\w+', re.IGNORECASE)
FILE_ID_PATTERN = re.compile(r'\b[A-Z]{1,10}\d{3,10}\b')
FILENAME_PATTERN = re.compile(r'\b[\w-]+\.(pdf|docx|xlsx|csv|txt|png|jpg|jpeg|mp4|zip|sql|pptx)\b', re.IGNORECASE)


def load_templates() -> Dict[str, Any]:
    global _templates
    if _templates is None:
        path = Path(__file__).parent / "api_template.json"
        _templates = json.load(open(path, "r", encoding="utf-8"))
    return _templates


def get_api_config(api_name: str) -> Optional[Dict[str, Any]]:
    for api in load_templates().get("apis", []):
        if api.get("name") == api_name:
            return api
    return None


def get_encoder():
    global _encoder
    if _encoder is None:
        from sentence_transformers import SentenceTransformer
        _encoder = SentenceTransformer("BAAI/bge-small-en-v1.5")
        _encoder.max_seq_length = 128
    return _encoder


def encode_bytes(text: str) -> bytes:
    key = hashlib.md5(text.lower().strip().encode()).hexdigest()
    if key in _embedding_cache:
        return _embedding_cache[key]

    vec = get_encoder().encode([text], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)[0]
    if len(_embedding_cache) >= MAX_CACHE_SIZE:
        _embedding_cache.pop(next(iter(_embedding_cache)))
    _embedding_cache[key] = vec.tobytes()
    return _embedding_cache[key]


def _decode_field(val: Any) -> Any:
    return val.decode() if isinstance(val, (bytes, bytearray)) else val


def _decode_document(flat_fields: List[Any]) -> Dict[str, Any]:
    it = iter(flat_fields)
    return { _decode_field(k): _decode_field(v) for k, v in zip(it, it) }


def vector_search(qvec: bytes, top_k: int = 5) -> List[Dict[str, Any]]:
    res = r.execute_command(
        "FT.SEARCH", INDEX_NAME,
        f'*=>[KNN {top_k} @{VECTOR_FIELD} $vec AS score]',
        "PARAMS", "2", "vec", qvec,
        "SORTBY", "score",
        "RETURN", "6", "query", "api", "endpoint", "request", "response", "score",
        "DIALECT", "2"
    )
    if not res or len(res) < 2:
        return []
    hits: List[Dict[str, Any]] = []
    for i in range(1, len(res), 2):
        fields = res[i + 1]
        hits.append(_decode_document(fields))
    return hits


def _score_keywords(query_lower: str, keywords: List[str]) -> tuple[int, List[str]]:
    score, matched = 0, []
    padded = f" {query_lower} "
    for kw in keywords:
        if kw in query_lower:
            kw_score = len(kw) * 2
            if f" {kw} " in padded:
                kw_score += 10
            if query_lower.startswith(kw):
                kw_score += 5
            score += kw_score
            matched.append(kw)
    return score, matched


def detect_intent(query: str, redis_hits: List[Dict[str, Any]]) -> Dict[str, Any]:
    ql = query.lower()
    templates = load_templates().get("apis", [])

    scored = []
    for api in templates:
        s, _ = _score_keywords(ql, api.get("intent_keywords", []))
        if s:
            scored.append((s, api))

    if scored:
        scored.sort(key=lambda t: t[0], reverse=True)
        best = scored[0][1]
        return {"api": best["name"], "endpoint": best["endpoint_template"], "config": best, "score": "0.95"}

    if redis_hits:
        return redis_hits[0]

    return {
        "api": "search",
        "endpoint": "<base_url>/api/search",
        "config": get_api_config("search"),
        "score": "0.5",
    }


def _find(pattern: re.Pattern, text: str) -> Optional[re.Match]:
    return pattern.search(text)


def extract_url(text: str) -> Optional[str]:
    m = _find(URL_PATTERN, text)
    if not m:
        return None
    url = m.group(0).rstrip(".,;:!?)")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url.lstrip("www.")
    return url


def extract_email(text: str) -> Optional[str]:
    m = _find(EMAIL_PATTERN, text)
    if not m:
        return None
    email = m.group(0)
    if 6 <= len(email) <= 254 and "@" in email and "." in email.split("@", 1)[1]:
        return email
    return None


def extract_token(text: str) -> Optional[str]:
    tl = text.lower()
    markers = ["token", "bearer", "session", "authentication token", "auth token", "jwt"]
    for marker in markers:
        if marker in tl:
            idx = tl.find(marker)
            words = WORD_PATTERN.findall(text[idx + len(marker):].strip())
            for w in words[:3]:
                w = w.strip(',:;!?()[]{}"\'=:')
                if len(w) >= 8 and w.lower() not in {"token", "bearer", "session", "with", "using"}:
                    return w
    return None


def extract_file_id(text: str) -> Optional[str]:
    m = _find(FILE_ID_PATTERN, text)
    if not m:
        return None
    fid = m.group(0)
    if any(k in text.lower() for k in ("file", "download", "doc")):
        return fid
    return None


def extract_user_id(text: str) -> Optional[str]:
    words = WORD_PATTERN.findall(text)
    tl = text.lower()
    for w in words:
        cand = w.strip(',:;!?()[]{}"\'=:')
        if (len(cand) >= 3 and cand[0].isalpha() and any(c.isdigit() for c in cand)
                and "." not in cand and "@" not in cand):
            if any(k in tl for k in ("user", "account", "userid", "id")):
                return cand
    return None


def extract_filename(text: str) -> Optional[str]:
    m = _find(FILENAME_PATTERN, text)
    return m.group(0) if m else None


def extract_confirmation(text: str) -> bool:
    tl = text.lower()
    return any(w in tl for w in ["confirmed", "confirm", "yes", "true"])


def is_valid_password(word: str) -> bool:
    return 6 <= len(word) <= 128 and bool(PASSWORD_PATTERN.search(word))


def score_password(word: str) -> int:
    score = 0
    n = len(word)
    score += 5 if 8 <= n <= 20 else (2 if 6 <= n < 8 else 0)
    has_upper = any(c.isupper() for c in word)
    has_lower = any(c.islower() for c in word)
    has_digit = any(c.isdigit() for c in word)
    has_special = any(c in '@#$%^&*!_-+=/\\' for c in word)
    score += (has_upper + has_lower + has_digit + has_special) * 2
    if has_upper and has_lower:
        score += 3
    if has_special and has_digit:
        score += 3
    wl = word.lower()
    if wl in {"password", "username", "user", "admin", "test", "confedential", "confidential"}:
        score -= 20
    if word.isalpha():
        score -= 10
    return score


def extract_password(text: str) -> Optional[str]:
    tl = text.lower()
    markers = ["password", "pass", "pwd", "with password", "secret", "and"]
    for marker in markers:
        if marker in tl:
            idx = tl.find(marker)
            words = WORD_PATTERN.findall(text[idx + len(marker):].strip())
            for w in words[:3]:
                w = w.strip(',:;!?()[]{}"\'=:')
                if is_valid_password(w):
                    return w
    best, best_score = None, -100
    for w in WORD_PATTERN.findall(text):
        cand = w.strip(',:;!?()[]{}"\'=:')
        if is_valid_password(cand):
            s = score_password(cand)
            if s > best_score:
                best, best_score = cand, s
    return best if best_score > 0 else None


def is_valid_username(word: str) -> bool:
    return bool(
        word and 2 <= len(word) <= 50
        and (word[0].isalpha() or word[0].isdigit())
        and all(c.isalnum() or c in "._-" for c in word)
    )


def extract_username(text: str, email: Optional[str] = None, password: Optional[str] = None) -> Optional[str]:
    tl = text.lower()
    
    has_explicit_username_marker = any(marker in tl for marker in ["username", "user name", "user", "as"])

    if any(k in tl for k in ("validate", "credentials", "check", "verify")) and password:
        words = WORD_PATTERN.findall(text)
        try:
            v_idx = next(i for i, w in enumerate(words) if w.lower() in {"validate", "check", "verify"})
        except StopIteration:
            v_idx = -1
        try:
            p_idx = next(i for i, w in enumerate(words) if w.lower() == password.lower())
        except StopIteration:
            p_idx = -1
        if 0 <= v_idx < p_idx:
            for w in words[v_idx + 1:p_idx]:
                cand = w.strip(',:;!?()[]{}"\'=:')
                if is_valid_username(cand) and cand.lower() not in {"and", "with", "user", "username", "password", "credentials"}:
                    return cand

    for marker in ["username", "user name", "user", "login", "account", "as"]:
        if marker in tl:
            idx = tl.find(marker)
            after_text = text[idx + len(marker):].strip()
            words_after = WORD_PATTERN.findall(after_text)
            
            for w in words_after[:3]:
                w = w.strip(',:;!?()[]{}"\'=:')
                if password and w.lower() == password.lower():
                    continue
                if '@' in w:
                    continue
                if w.lower() == 'email':
                    continue
                if is_valid_username(w) and w.lower() not in {"and", "with", "password", "pass", "pwd"}:
                    return w

   
    if password:
        pidx = tl.find(password.lower())
        if pidx > 0:
            for w in reversed(WORD_PATTERN.findall(text[:pidx])[-5:]):
                w = w.strip(',:;!?()[]{}"\'=:')
                if '@' in w:
                    continue
                if is_valid_username(w) and w.lower() not in {
                    "please", "validate", "confedential", "confidential", "and", "with",
                    "password", "login", "user", "username", "to", "on", "at", "email"
                }:
                    return w

    
    if email and not has_explicit_username_marker:
        u = email.split("@", 1)[0]
        if is_valid_username(u):
            return u
    return None


def extract_search_query(query: str) -> Optional[str]:
    ql = query.lower()
    for marker in ["search for", "look for", "search", "find", "locate", "about", "type:"]:
        if marker in ql:
            after = query[ql.find(marker) + len(marker):].strip()
            if after:
                return after
    words = [w for w in WORD_PATTERN.findall(query) if w.lower() not in {"find", "search", "for", "the", "a", "an"}]
    return " ".join(words) if words else None


def extract_filters(query: str) -> Optional[Dict[str, str]]:
    return dict(re.findall(r'(\w+):(\w+)', query)) or None


def extract_slots(query: str, api_config: Dict[str, Any]) -> Dict[str, Any]:
    slots: Dict[str, Any] = {}
    if not api_config or "slots" not in api_config:
        return slots

    api_name = api_config.get("name", "")
    url = extract_url(query)
    email = extract_email(query)
    password = extract_password(query)
    username = extract_username(query, email, password)
    token = extract_token(query)
    file_id = extract_file_id(query)
    user_id = extract_user_id(query)
    filename = extract_filename(query)
    confirmation = extract_confirmation(query)

    if api_name == "login":
        if url: slots["base_url"] = url
        if username: slots["username"] = username
        if password: slots["password"] = password

    elif api_name == "logout":
        if url: slots["base_url"] = url
        if token: slots["token"] = token

    elif api_name == "register":
        if url: slots["base_url"] = url
        if username and (not email or username != email.split("@", 1)[0]):
            slots["username"] = username
        if email: slots["email"] = email
        if password: slots["password"] = password

    elif api_name == "reset_password":
        if url: slots["base_url"] = url
        if email: slots["email"] = email

    elif api_name == "update_profile":
        if url: slots["base_url"] = url
        if user_id: slots["user_id"] = user_id
        nm = re.search(r'name\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', query, re.IGNORECASE)
        if nm: slots["name"] = nm.group(1)
        ph = re.search(r'phone\s+([\+\-\d\s\(\)]+)', query, re.IGNORECASE)
        if ph: slots["phone"] = ph.group(1).strip()

    elif api_name == "upload_file":
        if url: slots["base_url"] = url
        if filename:
            slots["file_name"] = filename
            slots["file_type"] = filename.split(".")[-1]

    elif api_name == "download_file":
        if url: slots["base_url"] = url
        if file_id: slots["file_id"] = file_id

    elif api_name == "search":
        if url: slots["base_url"] = url
        terms = extract_search_query(query)
        if terms: slots["query"] = terms
        flt = extract_filters(query)
        if flt: slots["filters"] = flt

    elif api_name == "get_user":
        if url: slots["base_url"] = url
        if user_id: slots["user_id"] = user_id

    elif api_name == "delete_account":
        if url: slots["base_url"] = url
        if user_id: slots["user_id"] = user_id
        if confirmation: slots["confirm"] = True

    return slots


def answer(query: str, top_k: int = 5, include_meta: bool = False) -> Dict[str, Any]:
    import time
    t0 = time.perf_counter()

    qvec = encode_bytes(query)
    redis_hits = vector_search(qvec, top_k=top_k)

    intent = detect_intent(query, redis_hits)
    api_name = intent["api"]
    api_config = intent.get("config") or get_api_config(api_name) or get_api_config("search") or {}

    slots = extract_slots(query, api_config)

    endpoint_template = intent.get("endpoint", "<base_url>/api")
    base_url = slots.get("base_url", "<missed>")
    endpoint = endpoint_template.replace("<base_url>", base_url)

    request: Dict[str, Any] = {}
    
    for slot_def in api_config.get("slots", []):
        key = slot_def["key"]
        if key == "base_url":
            continue
        
        if key in slots:
            request[key] = slots[key]
        elif "default" in slot_def:
            if slot_def.get("required") or api_name in {
                "login", "logout", "reset_password", "upload_file", 
                "download_file", "get_user", "delete_account"
            }:
                request[key] = slot_def["default"]

    result: Dict[str, Any] = {"api": api_name, "endpoint": endpoint, "request": request}

    if include_meta:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        result["meta"] = {
            "processing_time_ms": elapsed_ms,
            "confidence_score": float(intent.get("score", 0.5)),
            "template_used": api_config.get("name"),
            "slots_extracted": list(slots.keys()),
        }
    return result


def batch_answer(queries: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
    return [answer(q, top_k=top_k) for q in queries]


def clear_cache() -> None:
    _embedding_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    used = len(_embedding_cache)
    return {"cache_size": used, "max_cache_size": MAX_CACHE_SIZE, "utilization": f"{used / MAX_CACHE_SIZE * 100:.1f}%"}


if __name__ == "__main__":
    import sys

    print(" JSON Output Generator v3.0 (Template-Based, Refactor)")
    print("=" * 70)
    try:
        q = input("\n Enter your query: ")
    except KeyboardInterrupt:
        print()
        raise SystemExit(0)

    verbose = any(f in sys.argv for f in ("--verbose", "-v"))
    print("\n  Processing...")
    result = answer(q, include_meta=verbose)

    print("\n" + "=" * 70)
    print(" RESULT:")
    print("=" * 70)
    print(json.dumps(result, indent=2))
    print("=" * 70)
    if not verbose:
        print("\n Tip: Run with --verbose to see performance metrics")

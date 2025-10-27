from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import numpy as np

# ----------------------------
# Redis (REQUIRED)
# ----------------------------
try:
    from redis_config import get_redis_client
except Exception:
    print("❌ redis_config.get_redis_client is required but not importable. Provide redis_config.py.", file=sys.stderr)
    raise

INDEX_NAME, VECTOR_FIELD, EMBED_MODEL_NAME = "idx:apis", "query_embedding", "BAAI/bge-small-en-v1.5"

# ----------------------------
# Embeddings (must match DB)
# ----------------------------
_encoder, _embedding_cache, MAX_CACHE_SIZE = None, {}, 1000

def get_encoder():
    global _encoder
    if _encoder is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            print("❌ sentence_transformers is required for vector search. Install it first.", file=sys.stderr)
            raise e
        _encoder = SentenceTransformer(EMBED_MODEL_NAME)
        _encoder.max_seq_length = 256
    return _encoder

def encode_bytes(text: str) -> bytes:
    normalized = text.lower().strip()
    cache_key = hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    if vec_bytes := _embedding_cache.get(cache_key):
        return vec_bytes
    
    vec_bytes = get_encoder().encode([normalized], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)[0].tobytes()
    
    if len(_embedding_cache) >= MAX_CACHE_SIZE:
        _embedding_cache.pop(next(iter(_embedding_cache)))
    _embedding_cache[cache_key] = vec_bytes
    return vec_bytes

# ----------------------------
# Load api_template.json
# ----------------------------
_templates: Optional[Dict[str, Any]] = None

def load_templates() -> Dict[str, Any]:
    global _templates
    if _templates is not None:
        return _templates

    candidate_paths = [Path(__file__).parent / "api_template.json", Path.cwd() / "api_template.json", Path("/mnt/data/api_template.json")]
    
    if not (found_path := next((p for p in candidate_paths if p.exists()), None)):
        error_msg = f"❌ api_template.json is MANDATORY but not found.\n   Searched locations:\n" + "\n".join(f"     - {p}" for p in candidate_paths) + "\n   Please provide api_template.json in one of these locations."
        print(error_msg, file=sys.stderr)
        raise FileNotFoundError(error_msg)
    
    try:
        with open(found_path, "r", encoding="utf-8") as f:
            _templates = json.load(f)
        print(f"✅ Loaded api_template.json from: {found_path}")
    except json.JSONDecodeError as e:
        print(f"❌ api_template.json contains invalid JSON: {e}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"❌ Failed to load api_template.json: {e}", file=sys.stderr)
        raise
    
    return _templates

def get_api_config(api_name: str) -> Optional[Dict[str, Any]]:
    return next(
        (api for api in load_templates().get("apis", []) if api.get("name") == api_name),
        None
    )

# ----------------------------
# QA Model
# ----------------------------
_QA, _QA_threshold = None, 0.2

def _init_qa() -> None:
    global _QA, _QA_threshold
    if _QA is not None:
        return
    
    defaults = load_templates().get("defaults", {})
    _QA_threshold = float(defaults.get("qa_threshold", 0.2))
    model_name = defaults.get("qa_model", "deepset/minilm-uncased-squad2")
    
    try:
        from transformers import pipeline
    except ImportError:
        print("❌ transformers is required for QA model. Install it with: pip install transformers torch", file=sys.stderr)
        raise
    
    try:
        _QA = pipeline("question-answering", model=model_name, device=-1)
        print(f"✅ QA Model loaded: {model_name}")
    except Exception as e:
        print(f"❌ Failed to load QA model '{model_name}': {e}", file=sys.stderr)
        raise

def qa_answer(context: str, question: str) -> Tuple[str, float]:
    _init_qa()
    if _QA is None:
        raise RuntimeError("QA model initialization failed - cannot proceed without QA capability")
    result = _QA(question=question, context=context)
    return (result.get("answer") or "").strip().strip(',:;.!?()"\''), float(result.get("score", 0.0))

# ----------------------------
# Vector search
# ----------------------------
def _decode_field(val: Any) -> Any:
    return val.decode('utf-8') if isinstance(val, (bytes, bytearray)) else val

def _decode_document(flat_fields: List[Any]) -> Dict[str, Any]:
    return {_decode_field(k): _decode_field(v) for k, v in zip(flat_fields[::2], flat_fields[1::2])}

def vector_search(qvec: bytes, top_k: int = 5) -> List[Dict[str, Any]]:
    try:
        response = get_redis_client().execute_command(
            "FT.SEARCH", INDEX_NAME, f'*=>[KNN {top_k} @{VECTOR_FIELD} $vec AS score]',
            "PARAMS", "2", "vec", qvec, "SORTBY", "score",
            "RETURN", "6", "query", "api", "endpoint", "request", "response", "score", "DIALECT", "2"
        )
    except Exception as e:
        print(f"❌ Redis vector search failed: {e}", file=sys.stderr)
        raise
    return [_decode_document(response[i + 1]) for i in range(1, len(response), 2)] if response and len(response) >= 2 else []

# ----------------------------
# Intent detection
# ----------------------------
def _score_keywords(query_lower: str, keywords: List[str]) -> int:
    score, query_padded = 0, f" {query_lower} "
    for keyword in keywords:
        if (kw_lower := keyword.lower()) in query_lower:
            score += len(kw_lower) + (8 if f" {kw_lower} " in query_padded else 0) + (4 if query_lower.startswith(kw_lower) else 0)
    return score

def _has_search_marker(query_lower: str) -> bool:
    return any(marker in query_lower for marker in {"search", "find", "lookup", "locate", "query"})

def detect_intent(query: str, redis_hits: List[Dict[str, Any]]) -> Dict[str, Any]:
    query_lower = query.lower()
    
    if _has_search_marker(query_lower):
        config = get_api_config("search")
        return {"api": "search", "endpoint": config["endpoint_template"], "config": config, "score": "0.99"}

    templates = load_templates().get("apis", [])
    if scored_apis := [(score, api) for api in templates if (score := _score_keywords(query_lower, api.get("intent_keywords", []))) > 0]:
        best_api = max(scored_apis, key=lambda x: x[0])[1]
        return {"api": best_api["name"], "endpoint": best_api["endpoint_template"], "config": best_api, "score": "0.95"}

    if redis_hits:
        api_name = redis_hits[0].get("api", "search")
        config = get_api_config(api_name) or get_api_config("search")
        return {"api": api_name, "endpoint": config.get("endpoint_template", "<base_url>/api/search") if config else "<base_url>/api/search", "config": config, "score": "0.7"}

    config = get_api_config("search")
    return {"api": "search", "endpoint": config.get("endpoint_template", "<base_url>/api/search") if config else "<base_url>/api/search", "config": config, "score": "0.5"}

# ----------------------------
# Field extraction with typo tolerance (Optimized)
# ----------------------------

# Regex patterns for structured data (compile once, use many times)
_PATTERN_CACHE = {
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
    "url": re.compile(r'https?://[^\s]+|www\.[^\s]+|(?:[a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}(?::\d+)?(?:/[^\s]*)?'),
    "domain": re.compile(r'(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:/[^\s]*)?'),
    "filename": re.compile(r'\b[\w\-]+\.(pdf|docx|xlsx|csv|txt|png|jpg|jpeg|mp4|zip|sql|pptx)\b', re.IGNORECASE),
    "filepath": re.compile(r'(?:[A-Za-z]:\\[^\s]+|\/[^\s]+)'),
    "fileid": re.compile(r'\b[A-Z]{1,10}\d{3,10}\b'),
    "uuid": re.compile(r'\b[0-9a-fA-F\-]{8,}\b'),
    "token_hint": re.compile(r'\b(?:authorization:|bearer|token|session|auth|jwt)\b', re.IGNORECASE),
    "word": re.compile(r'\S+'),
    "ipv4": re.compile(r'^\d{1,3}(?:\.\d{1,3}){3}$'),
    "ipv4_port": re.compile(r'^(?:localhost(?:\:\d+)?|\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?)$'),
    "userid": re.compile(r'\b(?:USER-[A-Za-z0-9]+|ACC-[A-Za-z0-9]+|U\d+|ID\d+)\b', re.IGNORECASE),
    "auth_header": re.compile(r'Authorization\s*:\s*Bearer\s+(\S+)', re.IGNORECASE),
    "name": re.compile(r'\bname\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b'),
    "phone": re.compile(r'\bphone\s+([\+\-\d\s\(\)]+)\b', re.IGNORECASE),
    "user_id_pattern": re.compile(r'\buser\s*id\s*([A-Za-z0-9\-]+)\b', re.IGNORECASE),
    "id_pattern": re.compile(r'\bid\s*([A-Za-z0-9\-]+)\b', re.IGNORECASE),
}

# Typo tolerance with regex optimization (hybrid approach)
_FIELD_PATTERNS = {
    "username": re.compile(r'\b(username|usernme|usrname|user[_-]?name|usename|uname|user)\b', re.IGNORECASE),
    "password": re.compile(r'\b(password|passwrod|pasword|pssword|passwd|pwd|pass)\b', re.IGNORECASE),
    "credentials": re.compile(r'\b(credentials?|credentails|credientials|credintials)\b', re.IGNORECASE),
}

TYPO_MAP: Dict[str, frozenset] = {
    # Credentials field markers (11→18 variations)
    "credentials": frozenset({
        "credential","credentials","credentails","credientials","credintials","credenials",
        "credentals","confedentials","credntials","crendentials","credntial","crediantials",
        "creds","credencial","credencials","crediental","credentual","credetials"
    }),
    
    # Username field markers (8→16 variations)
    "username": frozenset({
        "username","usernme","usrname","user-name","user_name","usename","uname","user",
        "usr","usrnam","usename","usernam","usernm","usrn","username","login-name"
    }),
    
    # Password field markers (7→15 variations)
    "password": frozenset({
        "password","passwrod","pasword","pssword","passwd","pwd","pass",
        "passw","passwrd","paswrd","passwor","pword","psswd","paasword","passowrd"
    }),
    
    # Login/auth markers (10→17 variations)
    "login": frozenset({
        "login","log in","signin","sigin","singin","signn","sign-in","lgin","log-in",
        "authenticate","validate","auth","authenitcate","authentcate","autheticate",
        "sign in","log_in"
    }),
    
    # Confirmation markers (5→12 variations)
    "confirm": frozenset({
        "confirm","confirmed","cnfirm","comfirm","confm","confrm",
        "confrim","cofirm","confirmm","cnfrm","verify","approve"
    }),
    
    # Conjunction markers (4→8 variations) - CRITICAL for pairing
    "and": frozenset({
        "&","&&","n","nd","plus","with","along","alongside"
    }),
    
    # Email field markers (NEW - 10 variations)
    "email": frozenset({
        "email","mail","e-mail","emal","emial","emaill","e mail","electronic mail","mail address","email address"
    }),
    
    # Token/Authorization markers (NEW - 12 variations)
    "token": frozenset({
        "token","tokn","tokan","auth token","authtoken","bearer","bearer token",
        "access token","accesstoken","jwt","session token","api key"
    }),
    
    # Name field markers (NEW - 8 variations)
    "name": frozenset({
        "name","nam","fullname","full name","full-name","user name","display name","realname"
    }),
    
    # Phone field markers (NEW - 10 variations)
    "phone": frozenset({
        "phone","phon","phone number","phonenumber","mobile","cell","telephone",
        "contact","contact number","phone no"
    }),
    
    # File-related markers (NEW - 8 variations)
    "file": frozenset({
        "file","fil","document","doc","attachment","attach","upload file","download file"
    }),
}

CREDENTIALS_LIKE = frozenset({"credentials"}) | TYPO_MAP["credentials"]
PREP_AROUND_URL = frozenset({"on","at","to","with","using","via","against","from","in","into"})
STOPWORDS_FOR_QUERY = frozenset({"the","a","an","for","find","search","lookup","locate","query","please","kindly","me","to","in","on","at","of","www"})


_fuzzy_match_cache: Dict[Tuple[str, str], bool] = {}

def _fuzzy_match_word(word: str, target: str, threshold: float = 0.8) -> bool:
    """Cached fuzzy matching using SequenceMatcher"""
    cache_key = (word.lower(), target.lower())
    if cache_key not in _fuzzy_match_cache:
        _fuzzy_match_cache[cache_key] = difflib.SequenceMatcher(None, cache_key[0], cache_key[1]).ratio() >= threshold
    return _fuzzy_match_cache[cache_key]

def _is_credentialsish(word: str) -> bool:
    return (normalized := word.lower().strip()) in CREDENTIALS_LIKE or _fuzzy_match_word(normalized, "credentials")

_normalize_url = lambda url: (url if url.startswith(("http://", "https://")) else f"https://{url}" if url.startswith("localhost") or not _PATTERN_CACHE["ipv4_port"].fullmatch(url) else f"http://{url}") if (url := url.rstrip(".,;:!?)")) else url
_looks_like_filename = lambda token: bool(_PATTERN_CACHE["filename"].fullmatch(os.path.basename(token)))

def _is_valid_base_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = parsed.netloc or (parsed.path.split('/')[0] if parsed.path else "")
        return bool(host) and not _is_credentialsish(host_no_port := host.split(":")[0]) and (
            host_no_port.lower() == "localhost" or 
            _PATTERN_CACHE["ipv4"].fullmatch(host_no_port) or 
            ("." in host_no_port and len(host_no_port.split(".")[-1]) >= 2))
    except Exception:
        return False

is_valid_username = lambda username: bool(username) and 2 <= len(username) <= 50 and username[0].isalnum() and all(c.isalnum() or c in "._-" for c in username)
is_valid_password = lambda password: 6 <= len(password) <= 128 and any(c.isalpha() for c in password) and any(c.isdigit() for c in password)
_char_classes = lambda text: (sum(c.isalpha() for c in text), sum(c.isdigit() for c in text), sum(c in '@#$%^&*!_-+=/\\.,;:?' for c in text))

def _classify_pair(left: str, right: str) -> Tuple[Optional[str], Optional[str]]:
    lu, lp, ru, rp = is_valid_username(left), is_valid_password(left), is_valid_username(right), is_valid_password(right)
    if lp and ru and not (lu and rp): return right, left
    if lu and rp and not (lp and ru): return left, right
    l_letters, l_digits, l_spec, r_letters, r_digits, r_spec = *_char_classes(left), *_char_classes(right)
    l_pwd_score, r_pwd_score = l_digits + l_spec + (len(left) >= 8), r_digits + r_spec + (len(right) >= 8)
    return (right, left) if l_pwd_score > r_pwd_score and ru else (left, right) if r_pwd_score >= l_pwd_score and lu else ((left if lu else None), (right if rp else None))

_word_list = lambda text: (ow := _PATTERN_CACHE["word"].findall(text), [w.lower() for w in ow])
_next_and_split = lambda words_lower: next((i for i, w in enumerate(words_lower) if w == "and" or w in TYPO_MAP["and"]), None)
_sanitize_username_token = lambda s: s.strip(',:;!?()[]{}"\'=')
_sanitize_password_token = lambda s: (s := s.strip()) and (s[1:-1] if len(s) >= 2 and ((s[0] == s[-1] and s[0] in '"\'') or (s[0] in '([{' and s[-1] in ')]}')) else s)

# Extraction helper functions 
def _extract_base_url_with_preps(text: str, lw_all: List[str], ow_all: List[str]) -> Optional[str]:
    for i, tok in enumerate(lw_all):
        if tok in PREP_AROUND_URL:
            for j in range(1, 3):
                if i + j < len(ow_all) and not _looks_like_filename(cand := ow_all[i + j]):
                    if _PATTERN_CACHE["domain"].fullmatch(cand) or _PATTERN_CACHE["url"].fullmatch(cand) or _PATTERN_CACHE["ipv4_port"].fullmatch(cand):
                        if _is_valid_base_url(url := _normalize_url(cand)):
                            return url
    return None

def _extract_direct_url(text: str) -> Optional[str]:
    for m in _PATTERN_CACHE["url"].finditer(text):
        if (m.start() == 0 or text[m.start() - 1] != '@') and not _looks_like_filename(cand := m.group(0)):
            if _is_valid_base_url(url := _normalize_url(cand)):
                return url
    return None

_extract_authorization_header = lambda text: m.group(1) if (m := _PATTERN_CACHE["auth_header"].search(text)) else None
_basename_if_path = lambda s: os.path.basename(s) if _PATTERN_CACHE["filepath"].search(s) else s
_extract_name = lambda text: m.group(1) if (m := _PATTERN_CACHE["name"].search(text)) else None
_extract_phone = lambda text: re.sub(r'\s+', ' ', m.group(1)).strip() if (m := _PATTERN_CACHE["phone"].search(text)) else None
_extract_user_id = lambda text: next((m.group(grp) for pattern, grp in [(_PATTERN_CACHE["userid"], 0), (_PATTERN_CACHE["user_id_pattern"], 1), (_PATTERN_CACHE["id_pattern"], 1)] if (m := pattern.search(text))), None)
_extract_filters = lambda text: {k: v for k, v in re.findall(r'(\w+):([^\s]+)', text) if k.lower() not in {"http", "https"} and "://" not in v}

def _extract_search_query(text: str, base_url: Optional[str]) -> Optional[str]:
    text_wo_filters = re.sub(r'\b\w+:[^\s]+\b', '', text)
    if base_url:
        text_wo_filters = text_wo_filters.replace((urlparse(base_url).netloc or base_url).replace("www.", ""), " ")
    
    tl = text_wo_filters.lower()
    start_idx = next((tl.find(m) + len(m) for m in ["search for","look for","find","search","lookup","locate","query"] if m in tl), 0)
    return " ".join(w for w in re.findall(r'\w+', text_wo_filters[start_idx:].strip()) if w.lower() not in STOPWORDS_FOR_QUERY) or None

def extract_rules(text: str) -> Dict[str, Any]:
    out, tl, ow_all, lw_all = {}, text.lower(), *_word_list(text)

    # Base URL — 
    if (base_url := _extract_base_url_with_preps(text, lw_all, ow_all) or _extract_direct_url(text)) and _is_valid_base_url(base_url):
        out["base_url"] = base_url

    # Email, Filename, File ID - extraction
    if m := _PATTERN_CACHE["email"].search(text):
        out["email"] = m.group(0)
    
    if (path_m := _PATTERN_CACHE["filepath"].search(text)) and _PATTERN_CACHE["filename"].fullmatch(name := os.path.basename(path_m.group(0))):
        out["file_name"], out["file_type"] = name, name.split(".")[-1].lower()
    elif "file_name" not in out and (m := _PATTERN_CACHE["filename"].search(text)):
        out["file_name"], out["file_type"] = (name := _basename_if_path(m.group(0))), name.split(".")[-1].lower()

    if (m := _PATTERN_CACHE["fileid"].search(text)) or ((m := _PATTERN_CACHE["uuid"].search(text)) and len(m.group(0)) >= 8):
        out["file_id"] = m.group(0)

    # Confirmation 
    confirm_pos = any(x in tl for x in ["confirm", "confirmed", "cnfirm", "comfirm", "confrm", "confm", "yes", "true", "go ahead", "please proceed"])
    confirm_neg = any(x in tl for x in ["don't", "dont", "do not", "cancel", "no", "false", "not confirm", "abort", "stop"])
    if confirm_pos:
        out["confirm"] = True
    if confirm_neg:
        out["confirm"] = False

    # Token extraction
    if auth_tok := _extract_authorization_header(text):
        out["token"] = auth_tok
    elif (tok_m := _PATTERN_CACHE["token_hint"].search(text)) and (tokens := _PATTERN_CACHE["word"].findall(text[tok_m.start():tok_m.start() + 200])):
        out["token"] = next((w for w in tokens[1:8] if len(w) >= 8 and not _PATTERN_CACHE["token_hint"].fullmatch(w)), None) and _sanitize_password_token(tokens[next(i for i, w in enumerate(tokens[1:8], 1) if len(w) >= 8 and not _PATTERN_CACHE["token_hint"].fullmatch(w))])

    # Credentials extraction
    def _has_keyword_approx(text_lower: str, canonical: str, max_dist: int = 2) -> Optional[int]:
        if (idx := text_lower.find(canonical)) != -1:
            return idx
        for var in TYPO_MAP.get(canonical, []):
            if (idx := text_lower.find(var)) != -1:
                return idx
        for tok in text_lower.split():
            if _fuzzy_match_word(tok, canonical) and (pos := text_lower.find(tok)) != -1:
                return pos
        return None

    cred_idx = _has_keyword_approx(tl, "credentials") or (_has_keyword_approx(tl, "login") is not None and any(x in tl for x in ["validate", "signin", "sigin", "sign in"]) and max((tl.find(x) for x in ["validate", "signin", "sigin", "sign in"] if x in tl), default=-1))
    cred_idx = 0 if cred_idx and cred_idx < 0 else cred_idx
        
    if cred_idx is not None:
        ow, lw = _word_list(text[cred_idx: cred_idx + 240])
        if (and_i := _next_and_split(lw)) is not None:
            left_raw, right_raw = ow[max(0, and_i - 1)], (ow[and_i + 1] if and_i + 1 < len(ow) else "")
            left_u, right_u, left_p, right_p = _sanitize_username_token(left_raw), _sanitize_username_token(right_raw), _sanitize_password_token(left_raw), _sanitize_password_token(right_raw)
            
            if (u := _classify_pair(left_u, right_u if is_valid_password(right_p) else right_u)[0]) and is_valid_username(u):
                out.setdefault("username", u)
            if is_valid_password(pwd := (right_p if out.get("username") == left_u else left_p)):
                out.setdefault("password", pwd)

    # Username/password markers  - pairing extraction
    for i, w in enumerate(lw_all):
        if i + 1 < len(ow_all):
            if w in TYPO_MAP["username"] and is_valid_username(cand := _sanitize_username_token(ow_all[i + 1])):
                out.setdefault("username", cand)
            elif w in TYPO_MAP["password"] and is_valid_password(cand := _sanitize_password_token(ow_all[i + 1])):
                out.setdefault("password", cand)

    # User ID, Name, Phone, Filters, Query - extraction
    out.update({k: v for k, v in [("user_id", _extract_user_id(text)), ("name", _extract_name(text)), ("phone", _extract_phone(text)), ("filters", _extract_filters(text)), ("query", _extract_search_query(text, out.get("base_url")))] if v})

    return out

# ----------------------------
# QA-assisted slots
# ----------------------------
SENSITIVE_KEYS = {"username", "password", "email", "token", "name", "phone", "confirm"}

def _clean_qa_answer(key: str, ans: str) -> str:
    if key == "password":
        low = ans.lower()
        for prefix in ("password", "pwd", "pass"):
            if low.startswith(prefix):
                return ans[len(prefix):].strip(" :.-")
    return ans

def extract_slots(query: str, api_config: Dict[str, Any]) -> Dict[str, Any]:
    slots = extract_rules(query)

    _init_qa()
    if _QA is None:
        raise RuntimeError("QA model is mandatory but failed to initialize")
    
    for slot_def in (api_config.get("slots") or []):
        key = slot_def.get("key")
        if key in slots or (key in ("name", "phone") and not re.search(rf'\b{key}\b', query, re.IGNORECASE)):
            continue

        for q in (slot_def.get("questions") or []):
            ans, score = qa_answer(query, q)
            if score < _QA_threshold or not ans or (key in SENSITIVE_KEYS and ans not in query):
                continue
            
            # Key-specific validation and transformation
            if key == "password":
                ans = _clean_qa_answer(key, ans)
            elif key == "base_url":
                ans = _normalize_url(ans)
                if not _is_valid_base_url(ans):
                    continue
            elif key == "file_name":
                ans = _basename_if_path(ans)
                if not _PATTERN_CACHE["filename"].fullmatch(ans):
                    continue
            elif key == "file_type":
                ans = ans.strip(".").lower()
            
            # Validation checks
            if ((key == "username" and not is_valid_username(ans)) or
                (key == "password" and not is_valid_password(ans)) or
                (key == "email" and not _PATTERN_CACHE["email"].fullmatch(ans))):
                continue
            
            slots[key] = ans
            break
    return slots

# ----------------------------
# Endpoint normalization
# ----------------------------
def _normalize_endpoint_path(api_name: str, endpoint: str) -> str:
    if api_name == "upload_file" and endpoint.endswith("/api/upload_file"):
        return endpoint[:-len("/api/upload_file")] + "/api/upload"
    if api_name == "download_file" and endpoint.endswith("/api/download_file"):
        return endpoint[:-len("/api/download_file")] + "/api/download"
    return endpoint

# ----------------------------
# Build result
# ----------------------------
def answer(query: str, top_k: int = 5, include_meta: bool = False) -> Dict[str, Any]:
    start_time = time.perf_counter()

    query_vector = encode_bytes(query)
    redis_hits = vector_search(query_vector, top_k=top_k)

    intent = detect_intent(query, redis_hits)
    api_name, api_config = intent["api"], intent.get("config") or get_api_config(intent["api"]) or {}

    slots = extract_slots(query, api_config)

    endpoint = _normalize_endpoint_path(api_name, 
        intent.get("endpoint", "<base_url>/api").replace("<base_url>", slots.get("base_url", "<missed>")))

    request = {slot_def["key"]: slots.get(slot_def["key"], slot_def.get("default"))
               for slot_def in api_config.get("slots", [])
               if slot_def["key"] != "base_url" and (slot_def["key"] in slots or "default" in slot_def)}

    # API-specific defaults
    if api_name == "register" and "email" in request and "username" not in request:
        if is_valid_username(email_local := request["email"].split("@", 1)[0]):
            request["username"] = email_local
    
    if api_name == "delete_account" and "confirm" not in request:
        request["confirm"] = False

    result = {"api": api_name, "endpoint": endpoint, "request": request}

    if include_meta:
        result["meta"] = {
            "processing_time_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            "template_used": api_config.get("name"),
            "slots_extracted": sorted(slots.keys()),
            "qa_model_used": True,
            "vector_search": True,
        }
    
    return result

def batch_answer(queries: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
    return [answer(query, top_k=top_k) for query in queries]

def clear_cache() -> None:
    _embedding_cache.clear()

def get_cache_stats() -> Dict[str, Any]:
    cache_size = len(_embedding_cache)
    return {"cache_size": cache_size, "max_cache_size": MAX_CACHE_SIZE, "utilization": f"{(cache_size / MAX_CACHE_SIZE) * 100:.1f}%"}

# ----------------------------
# CLI
# ----------------------------
def _read_stdin_if_piped() -> Optional[str]:
    try:
        return (data.strip() if data else None) if not sys.stdin.isatty() and (data := sys.stdin.read()) else None
    except Exception:
        return None

def main():
    print(" JSON Output Generator v4.0 (Optimized - Redis & QA MANDATORY)")
    print("=" * 70)
    print("\n🔍 Initializing mandatory components...")
    
    try:
        get_redis_client().ping()
        print("✅ Redis connection established")
    except Exception as e:
        print(f"❌ Redis connection FAILED: {e}\n   Redis vector search is MANDATORY. Fix Redis and try again.", file=sys.stderr)
        raise SystemExit(1)
    
    try:
        _init_qa()
        print("✅ QA Model initialized successfully")
    except Exception as e:
        print(f"❌ QA Model initialization FAILED: {e}\n   QA model is MANDATORY. Install dependencies and try again.", file=sys.stderr)
        raise SystemExit(1)
    
    print("✅ All mandatory components ready!")
    print("=" * 70)

    try:
        query = _read_stdin_if_piped() or input("\n📝 Enter your query: ")
    except KeyboardInterrupt:
        print()
        raise SystemExit(0)

    print("\n⏳ Processing...")
    print("\n" + "=" * 70)
    print("✅ RESULT:")
    print("=" * 70)
    print(json.dumps(answer(query, include_meta=True), indent=2))
    print("=" * 70)

if __name__ == "__main__":
    main()

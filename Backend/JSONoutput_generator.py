from __future__ import annotations

import argparse
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

INDEX_NAME = "idx:apis"
VECTOR_FIELD = "query_embedding"
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# ----------------------------
# Embeddings (must match DB)
# ----------------------------
_encoder = None
_embedding_cache: Dict[str, bytes] = {}
MAX_CACHE_SIZE = 1000

def get_encoder():
    global _encoder
    if _encoder is None:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            print("❌ sentence_transformers is required for vector search. Install it first.", file=sys.stderr)
            raise
        _encoder = SentenceTransformer(EMBED_MODEL_NAME)
        _encoder.max_seq_length = 256
    return _encoder

def encode_bytes(text: str) -> bytes:
    enc = get_encoder()
    key = hashlib.md5(text.lower().strip().encode()).hexdigest()
    if key in _embedding_cache:
        return _embedding_cache[key]
    vec = enc.encode([text], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)[0]
    if len(_embedding_cache) >= MAX_CACHE_SIZE:
        _embedding_cache.pop(next(iter(_embedding_cache)))
    _embedding_cache[key] = vec.tobytes()
    return _embedding_cache[key]

# ----------------------------
# Load api_template.json
# ----------------------------
_templates: Optional[Dict[str, Any]] = None

def _first_existing(paths: List[Path]) -> Optional[Path]:
    for p in paths:
        if p.exists():
            return p
    return None

def load_templates() -> Dict[str, Any]:
    global _templates
    if _templates is not None:
        return _templates

    candidate_paths = [
        Path(__file__).parent / "api_template.json",
        Path(os.getcwd()) / "api_template.json",
        Path("/mnt/data/api_template.json"),
    ]
    found = _first_existing(candidate_paths)
    if not found:
        _templates = {
            "version": 1,
            "defaults": {"qa_model": "deepset/minilm-uncased-squad2", "qa_threshold": 0.2},
            "apis": [
                {"name": "login", "endpoint_template": "<base_url>/api/login",
                 "intent_keywords": ["login","sign in","log in","credentials","validate","authenticate","signin","sigin","singin","sign-in"],
                 "slots": [{"key":"base_url","required": True},{"key":"username","required": True},{"key":"password","required": True}]},
                {"name": "logout", "endpoint_template": "<base_url>/api/logout",
                 "intent_keywords": ["logout","log out","sign out","disconnect","end session","invalidate token"],
                 "slots": [{"key":"base_url","required": True},{"key":"token","required": True}]},
                {"name": "register", "endpoint_template": "<base_url>/api/register",
                 "intent_keywords": ["register","sign up","signup","create account"],
                 "slots": [{"key":"base_url","required": True},{"key":"email","required": True},{"key":"password","required": True},{"key":"username","required": False}]},
                {"name": "reset_password", "endpoint_template": "<base_url>/api/reset_password",
                 "intent_keywords": ["reset password","forgot password","recover password","reset my login"],
                 "slots": [{"key":"base_url","required": True},{"key":"email","required": True}]},
                {"name": "update_profile", "endpoint_template": "<base_url>/api/update_profile",
                 "intent_keywords": ["update profile","edit profile","change profile"],
                 "slots": [{"key":"base_url","required": True},{"key":"user_id","required": True},{"key":"name","required": False},{"key":"phone","required": False}]},
                {"name": "upload_file", "endpoint_template": "<base_url>/api/upload",
                 "intent_keywords": ["upload file","attach file","send file","push file"],
                 "slots": [{"key":"base_url","required": True},{"key":"file_name","required": True},{"key":"file_type","required": True,"default":"txt"}]},
                {"name": "download_file", "endpoint_template": "<base_url>/api/download",
                 "intent_keywords": ["download file","get file","fetch file"],
                 "slots": [{"key":"base_url","required": True},{"key":"file_id","required": True}]},
                {"name": "search", "endpoint_template": "<base_url>/api/search",
                 "intent_keywords": ["search","find","lookup","locate","query"],
                 "slots": [{"key":"base_url","required": True},{"key":"query","required": True},{"key":"filters","required": False}]},
                {"name": "get_user", "endpoint_template": "<base_url>/api/get_user",
                 "intent_keywords": ["get user","fetch user","retrieve user","user details"],
                 "slots": [{"key":"base_url","required": True},{"key":"user_id","required": True}]},
                {"name": "delete_account", "endpoint_template": "<base_url>/api/delete_account",
                 "intent_keywords": ["delete account","remove account","terminate account","close account","deactivate account"],
                 "slots": [{"key":"base_url","required": True},{"key":"user_id","required": True},{"key":"confirm","required": True,"default": False}]},
            ],
        }
    else:
        with open(found, "r", encoding="utf-8") as f:
            _templates = json.load(f)
        _augment_intent_keywords(_templates)
    return _templates

def _augment_intent_keywords(templates: Dict[str, Any]) -> None:
    extra = {
        "login": ["signin","sigin","singin","sign-in","log in","sign in","authenticate","validate","credentials"],
        "logout": ["log out","sign out","disconnect","end session","invalidate token"],
        "register": ["sign up","signup","create account"],
        "reset_password": ["reset password","forgot password","recover password","reset my login"],
        "update_profile": ["edit profile","change profile"],
        "upload_file": ["attach file","send file","push file"],
        "download_file": ["get file","fetch file"],
        "search": ["find","lookup","locate","query"],
        "get_user": ["fetch user","retrieve user","user details"],
        "delete_account": ["remove account","terminate account","close account","deactivate account"],
    }
    for api in templates.get("apis", []):
        name = api.get("name")
        if name in extra:
            kws = set(api.get("intent_keywords", []))
            kws.update(extra[name])
            api["intent_keywords"] = sorted(kws)

def get_api_config(api_name: str) -> Optional[Dict[str, Any]]:
    for api in load_templates().get("apis", []):
        if api.get("name") == api_name:
            return api
    return None

# ----------------------------
# Optional QA (safe)
# ----------------------------
_QA = None
_QA_threshold = 0.2

def _maybe_init_qa():
    global _QA, _QA_threshold
    if _QA is not None:
        return
    defaults = load_templates().get("defaults", {})
    _QA_threshold = float(defaults.get("qa_threshold", 0.2))
    model_name = defaults.get("qa_model", "deepset/minilm-uncased-squad2")
    try:
        from transformers import pipeline
        _QA = pipeline("question-answering", model=model_name, device=-1)
    except Exception:
        _QA = None

def qa_answer(context: str, question: str) -> Tuple[str, float]:
    _maybe_init_qa()
    if _QA is None:
        return "", 0.0
    out = _QA(question=question, context=context)
    ans = (out.get("answer") or "").strip().strip(',:;.!?()"\'')
    score = float(out.get("score", 0.0))
    return ans, score

# ----------------------------
# Vector search (MANDATORY)
# ----------------------------
def _decode_field(val: Any) -> Any:
    return val.decode() if isinstance(val, (bytes, bytearray)) else val

def _decode_document(flat_fields: List[Any]) -> Dict[str, Any]:
    it = iter(flat_fields)
    return { _decode_field(k): _decode_field(v) for k, v in zip(it, it) }

def vector_search(qvec: bytes, top_k: int = 5) -> List[Dict[str, Any]]:
    r = get_redis_client()
    try:
        res = r.execute_command(
            "FT.SEARCH", INDEX_NAME,
            f'*=>[KNN {top_k} @{VECTOR_FIELD} $vec AS score]',
            "PARAMS", "2", "vec", qvec,
            "SORTBY", "score",
            "RETURN", "6", "query", "api", "endpoint", "request", "response", "score",
            "DIALECT", "2"
        )
    except Exception as e:
        print(f"❌ Redis vector search failed: {e}", file=sys.stderr)
        raise

    if not res or len(res) < 2:
        return []
    hits: List[Dict[str, Any]] = []
    for i in range(1, len(res), 2):
        fields = res[i + 1]
        hits.append(_decode_document(fields))
    return hits

# ----------------------------
# Intent detection
# ----------------------------
def _score_keywords(query_lower: str, keywords: List[str]) -> int:
    score = 0
    padded = f" {query_lower} "
    for kw in keywords:
        kwl = kw.lower()
        if kwl in query_lower:
            kw_score = len(kwl)
            if f" {kwl} " in padded:
                kw_score += 8
            if query_lower.startswith(kwl):
                kw_score += 4
            score += kw_score
    return score

def _has_search_marker(ql: str) -> bool:
    return any(x in ql for x in ["search", "find", "lookup", "locate", "query"])

def detect_intent(query: str, redis_hits: List[Dict[str, Any]]) -> Dict[str, Any]:
    ql = query.lower()
    templates = load_templates().get("apis", [])
    if _has_search_marker(ql):
        cfg = get_api_config("search")
        return {"api": "search", "endpoint": cfg["endpoint_template"], "config": cfg, "score": "0.99"}

    scored = []
    for api in templates:
        kws = api.get("intent_keywords", [])
        s = _score_keywords(ql, kws)
        if s:
            scored.append((s, api))
    if scored:
        scored.sort(key=lambda t: t[0], reverse=True)
        best = scored[0][1]
        return {"api": best["name"], "endpoint": best["endpoint_template"], "config": best, "score": "0.95"}

    if redis_hits:
        api_guess = redis_hits[0].get("api", "search")
        cfg = get_api_config(api_guess) or get_api_config("search")
        endpoint = cfg.get("endpoint_template", "<base_url>/api/search") if cfg else "<base_url>/api/search"
        return {"api": api_guess, "endpoint": endpoint, "config": cfg, "score": "0.7"}

    cfg = get_api_config("search")
    return {"api": "search", "endpoint": cfg.get("endpoint_template", "<base_url>/api/search") if cfg else "<base_url>/api/search", "config": cfg, "score": "0.5"}

# ----------------------------
# Field extraction with typo tolerance + extras
# ----------------------------
EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
URL_RE = re.compile(r'https?://[^\s]+|www\.[^\s]+|(?:[a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}(?::\d+)?(?:/[^\s]*)?')
DOMAIN_RE = re.compile(r'(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:/[^\s]*)?')
# IMPORTANT: no spaces allowed in bare filenames (paths still supported)
FILENAME_RE = re.compile(r'\b[\w\-]+\.(pdf|docx|xlsx|csv|txt|png|jpg|jpeg|mp4|zip|sql|pptx)\b', re.IGNORECASE)
FILEPATH_RE = re.compile(r'(?:[A-Za-z]:\\[^\s]+|\/[^\s]+)')
FILEID_RE = re.compile(r'\b[A-Z]{1,10}\d{3,10}\b')
UUIDLIKE_RE = re.compile(r'\b[0-9a-fA-F\-]{8,}\b')
TOKEN_HINT_RE = re.compile(r'\b(?:authorization:|bearer|token|session|auth|jwt)\b', re.IGNORECASE)
WORD_RE = re.compile(r'\S+')
IPV4_RE = re.compile(r'^\d{1,3}(?:\.\d{1,3}){3}$')
IPV4_PORT_TOKEN_RE = re.compile(r'^(?:localhost(?:\:\d+)?|\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?)$')
USERID_RE = re.compile(r'\b(?:USER-[A-Za-z0-9]+|ACC-[A-Za-z0-9]+|U\d+|ID\d+)\b', re.IGNORECASE)

TYPO_MAP = {
    "credentials": {"credential","credentails","credientials","credintials","credenials","credentals","confedentials","credntials","crendentials","credntial","crediantials"},
    "username": {"usernme","usrname","user-name","user_name","usename","uname","user","username"},
    "password": {"passwrod","pasword","pssword","passwd","pwd","pass","password"},
    "login": {"log in","signin","sigin","singin","signn","sign-in","lgin","log-in","authenticate","validate"},
    "confirm": {"cnfirm","comfirm","confm","confrm","confirmed"},
    "and": {"&","&&","n","nd"},
    "register": {"regster","rigister","signup","sign-up","sign up","create account"},
    "reset": {"resest","re-set","forgot","recover"},
    "profile": {"proifle","profil","prfoile"},
    "download": {"downlaod","dwnld","dload","fetch","get"},
    "upload": {"uplaod","uplod","up-load","attach","send"},
    "search": {"serach","seach","lookup","locate","find"},
    "delete": {"delte","remove","terminate","close","deactivate"},
    "get": {"fetch","retrieve","grab"},
}

CREDENTIALS_LIKE = set().union({"credentials"}, TYPO_MAP["credentials"])
PREP_AROUND_URL = {"on","at","to","with","using","via","against","from","in","into"}
STOPWORDS_FOR_QUERY = {"the","a","an","for","find","search","lookup","locate","query","please","kindly","me","to","in","on","at","of","www"}

def _is_credentialsish(word: str) -> bool:
    w = word.lower().strip()
    if w in CREDENTIALS_LIKE:
        return True
    return difflib.SequenceMatcher(None, w, "credentials").ratio() >= 0.8

def _normalize_url(u: str) -> str:
    u = u.rstrip(".,;:!?)")
    if not u.startswith(("http://", "https://")):
        host = u
        # localhost => https, IPv4 => http, else https
        if host.startswith("localhost"):
            u = "https://" + host
        elif IPV4_PORT_TOKEN_RE.fullmatch(host) and not host.startswith("localhost"):
            u = "http://" + host
        else:
            u = "https://" + host
    return u

def _looks_like_filename(token: str) -> bool:
    return bool(FILENAME_RE.fullmatch(os.path.basename(token)))

def _is_valid_base_url(u: str) -> bool:
    try:
        p = urlparse(u)
        host = p.netloc or (p.path.split('/')[0] if p.path else "")
        if not host:
            return False
        host_stripped = host.split(":")[0]
        if host_stripped.lower() == "localhost":
            return True
        if _is_credentialsish(host_stripped):
            return False
        if IPV4_RE.fullmatch(host_stripped):
            return True
        if "." in host_stripped:
            tld = host_stripped.split(".")[-1]
            if len(tld) >= 2:
                return True
        return False
    except Exception:
        return False

def is_valid_username(s: str) -> bool:
    return bool(s) and 2 <= len(s) <= 50 and s[0].isalnum() and all(c.isalnum() or c in "._-" for c in s)

def is_valid_password(s: str) -> bool:
    if not (6 <= len(s) <= 128):
        return False
    has_alpha = any(c.isalpha() for c in s)
    has_digit = any(c.isdigit() for c in s)
    return has_alpha and has_digit

def _char_classes(s: str) -> Tuple[int, int, int]:
    digits = sum(c.isdigit() for c in s)
    specials = sum(c in '@#$%^&*!_-+=/\\.,;:?' for c in s)
    letters = sum(c.isalpha() for c in s)
    return letters, digits, specials

def _classify_pair(left: str, right: str) -> Tuple[Optional[str], Optional[str]]:
    lu, lp = is_valid_username(left), is_valid_password(left)
    ru, rp = is_valid_username(right), is_valid_password(right)
    if lp and ru and not (lu and rp):
        return right, left
    if lu and rp and not (lp and ru):
        return left, right
    l_letters, l_digits, l_spec = _char_classes(left)
    r_letters, r_digits, r_spec = _char_classes(right)
    l_pwd_score = l_digits + l_spec + (1 if len(left) >= 8 else 0)
    r_pwd_score = r_digits + r_spec + (1 if len(right) >= 8 else 0)
    if l_pwd_score > r_pwd_score and ru:
        return right, left
    if r_pwd_score >= l_pwd_score and lu:
        return left, right
    return (left if lu else None), (right if rp else None)

def _word_list(text: str) -> Tuple[List[str], List[str]]:
    ow = WORD_RE.findall(text)
    lw = [w.lower() for w in ow]
    return ow, lw

def _next_and_split(words_lower: List[str]) -> Optional[int]:
    for i, w in enumerate(words_lower):
        if w == "and" or w in TYPO_MAP["and"]:
            return i
    return None

def _sanitize_username_token(s: str) -> str:
    return s.strip(',:;!?()[]{}"\'=')

def _sanitize_password_token(s: str) -> str:
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1]
    pairs = [('(',')'),('[',']'),('{','}')]
    for l,r in pairs:
        if s.startswith(l) and s.endswith(r) and len(s) > 2:
            s = s[1:-1]
    return s

def _extract_base_url_with_preps(text: str, lw_all: List[str], ow_all: List[str]) -> Optional[str]:
    for i, tok in enumerate(lw_all):
        if tok in PREP_AROUND_URL:
            for j in range(1,3):
                if i+j < len(ow_all):
                    cand = ow_all[i+j]
                    if _looks_like_filename(cand):
                        continue
                    if DOMAIN_RE.fullmatch(cand) or URL_RE.fullmatch(cand) or IPV4_PORT_TOKEN_RE.fullmatch(cand):
                        url = _normalize_url(cand)
                        if _is_valid_base_url(url):
                            return url
    return None

def _extract_direct_url(text: str) -> Optional[str]:
    for m in URL_RE.finditer(text):
        start = m.start()
        if start > 0 and text[start-1] == '@':
            continue
        cand = m.group(0)
        if _looks_like_filename(cand):
            continue
        url = _normalize_url(cand)
        if _is_valid_base_url(url):
            return url
    return None

def _extract_authorization_header(text: str) -> Optional[str]:
    m = re.search(r'Authorization\s*:\s*Bearer\s+(\S+)', text, re.IGNORECASE)
    if m:
        return m.group(1)
    return None

def _basename_if_path(s: str) -> str:
    if FILEPATH_RE.search(s):
        return os.path.basename(s)
    return s

def _extract_name(text: str) -> Optional[str]:
    m = re.search(r'\bname\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b', text)
    return m.group(1) if m else None

def _extract_phone(text: str) -> Optional[str]:
    m = re.search(r'\bphone\s+([\+\-\d\s\(\)]+)\b', text, re.IGNORECASE)
    if not m:
        return None
    return re.sub(r'\s+', ' ', m.group(1)).strip()

def _extract_user_id(text: str) -> Optional[str]:
    m = USERID_RE.search(text)
    if m:
        return m.group(0)
    m = re.search(r'\buser\s*id\s*([A-Za-z0-9\-]+)\b', text, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r'\bid\s*([A-Za-z0-9\-]+)\b', text, re.IGNORECASE)
    if m:
        return m.group(1)
    return None

def _extract_filters(text: str) -> Dict[str, str]:
    flts = {}
    for k, v in re.findall(r'(\w+):([^\s]+)', text):
        if k.lower() in {"http","https"} or "://" in v:
            continue
        flts[k] = v
    return flts

def _extract_search_query(text: str, base_url: Optional[str]) -> Optional[str]:
    text_wo_filters = re.sub(r'\b\w+:[^\s]+\b', '', text)
    if base_url:
        host = urlparse(base_url).netloc or base_url
        host = host.replace("www.", "")
        text_wo_filters = text_wo_filters.replace(host, " ")
    tl = text_wo_filters.lower()
    markers = ["search for","look for","find","search","lookup","locate","query"]
    start_idx = 0
    for m in markers:
        if m in tl:
            start_idx = tl.find(m) + len(m)
            break
    q = text_wo_filters[start_idx:].strip()
    words = [w for w in re.findall(r'\w+', q) if w.lower() not in STOPWORDS_FOR_QUERY]
    return " ".join(words) if words else None

def extract_rules(text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    tl = text.lower()

    # Base URL — prefer prepositional extraction first
    ow_all, lw_all = _word_list(text)
    cand2 = _extract_base_url_with_preps(text, lw_all, ow_all)
    if cand2 and _is_valid_base_url(cand2):
        out["base_url"] = cand2
    else:
        cand = _extract_direct_url(text)
        if cand and _is_valid_base_url(cand):
            out["base_url"] = cand

    # Email
    m = EMAIL_RE.search(text)
    if m:
        out["email"] = m.group(0)

    # Filename (also from path)
    path_m = FILEPATH_RE.search(text)
    if path_m:
        name = os.path.basename(path_m.group(0))
        if FILENAME_RE.fullmatch(name):
            out["file_name"] = name
            out["file_type"] = name.split(".")[-1].lower()
    if "file_name" not in out:
        m = FILENAME_RE.search(text)
        if m:
            name = _basename_if_path(m.group(0))
            out["file_name"] = name
            out["file_type"] = name.split(".")[-1].lower()

    # File ID (code-like or uuid-like)
    m = FILEID_RE.search(text)
    if m:
        out["file_id"] = m.group(0)
    if "file_id" not in out:
        m2 = UUIDLIKE_RE.search(text)
        if m2 and len(m2.group(0)) >= 8:
            out["file_id"] = m2.group(0)

    # Confirmation (typo tolerant + negation)
    if any(x in tl for x in ["confirm","confirmed","cnfirm","comfirm","confrm","confm","yes","true","go ahead","please proceed"]):
        out["confirm"] = True
    if any(x in tl for x in ["don't","dont","do not","cancel","no","false","not confirm","abort","stop"]):
        out["confirm"] = False

    # Token (header or near markers)
    auth_tok = _extract_authorization_header(text)
    if auth_tok:
        out["token"] = auth_tok
    if "token" not in out:
        tok_m = TOKEN_HINT_RE.search(text)
        if tok_m:
            idx = tok_m.start()
            after = text[idx: idx + 200]
            tokens = WORD_RE.findall(after)
            for w in tokens[1:8]:
                if len(w) >= 8 and not TOKEN_HINT_RE.fullmatch(w):
                    out["token"] = _sanitize_password_token(w)
                    break

    # Credentials with typo tolerance & smarter pairing
    def _has_keyword_approx(text_lower: str, canonical: str, max_dist: int = 2) -> Optional[int]:
        idx = text_lower.find(canonical)
        if idx != -1:
            return idx
        for var in TYPO_MAP.get(canonical, []):
            idx = text_lower.find(var)
            if idx != -1:
                return idx
        for tok in text_lower.split():
            if difflib.SequenceMatcher(None, tok, canonical).ratio() >= 1 - (max_dist * 0.2):
                pos = text_lower.find(tok)
                if pos != -1:
                    return pos
        return None

    cred_idx = _has_keyword_approx(tl, "credentials")
    if cred_idx is None:
        if (_has_keyword_approx(tl, "login") is not None) and any(x in tl for x in ["validate","signin","sigin","sign in"]):
            cred_idx = max(tl.find("validate"), tl.find("signin"), tl.find("sigin"), tl.find("sign in"))
            if cred_idx < 0:
                cred_idx = 0
    if cred_idx is not None:
        window = text[cred_idx: cred_idx + 240]
        ow, lw = _word_list(window)
        and_i = _next_and_split(lw)
        if and_i is not None:
            left_raw = ow[max(0, and_i - 1)]
            right_raw = ow[and_i + 1] if and_i + 1 < len(ow) else ""
            left_u = _sanitize_username_token(left_raw)
            right_u = _sanitize_username_token(right_raw)
            left_p = _sanitize_password_token(left_raw)
            right_p = _sanitize_password_token(right_raw)
            u, _ = _classify_pair(left_u, right_u if is_valid_password(right_p) else right_u)
            if u and is_valid_username(u):
                out.setdefault("username", u)
            pwd = right_p if out.get("username") == left_u else left_p
            if is_valid_password(pwd):
                out.setdefault("password", pwd)

    # Username/password markers (typo tolerant)
    for i, w in enumerate(lw_all):
        if w in TYPO_MAP["username"]:
            if i + 1 < len(ow_all):
                cand = _sanitize_username_token(ow_all[i + 1])
                if is_valid_username(cand):
                    out.setdefault("username", cand)
        if w in TYPO_MAP["password"]:
            if i + 1 < len(ow_all):
                cand = _sanitize_password_token(ow_all[i + 1])
                if is_valid_password(cand):
                    out.setdefault("password", cand)

    # User ID (robust)
    uid = _extract_user_id(text)
    if uid:
        out["user_id"] = uid

    # Name / Phone (explicit only)
    nm = _extract_name(text)
    if nm:
        out["name"] = nm
    ph = _extract_phone(text)
    if ph:
        out["phone"] = ph

    # Search extras
    base_for_query = out.get("base_url")
    filters = _extract_filters(text)
    if filters:
        out["filters"] = filters
    q = _extract_search_query(text, base_for_query)
    if q:
        out["query"] = q

    return out

# ----------------------------
# QA-assisted slots (SAFE)
# ----------------------------
# Treat name/phone/confirm as sensitive to avoid hallucination
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

    _maybe_init_qa()
    if _QA is not None:
        for slot_def in (api_config.get("slots") or []):
            key = slot_def.get("key")
            if key in slots:
                continue

            # For name/phone, only try QA if keyword is explicitly present
            if key == "name" and not re.search(r'\bname\b', query, re.IGNORECASE):
                continue
            if key == "phone" and not re.search(r'\bphone\b', query, re.IGNORECASE):
                continue

            for q in (slot_def.get("questions") or []):
                ans, score = qa_answer(query, q)
                if score < _QA_threshold or not ans:
                    continue
                if key in SENSITIVE_KEYS and (ans not in query):
                    continue
                if key == "password":
                    ans = _clean_qa_answer(key, ans)
                if key == "base_url":
                    ans = _normalize_url(ans)
                    if not _is_valid_base_url(ans):
                        continue
                if key == "username" and not is_valid_username(ans):
                    continue
                if key == "password" and not is_valid_password(ans):
                    continue
                if key == "email" and not EMAIL_RE.fullmatch(ans):
                    continue
                if key == "file_name":
                    ans = _basename_if_path(ans)
                    if not FILENAME_RE.fullmatch(ans):
                        continue
                if key == "file_type":
                    ans = ans.strip(".").lower()
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
    t0 = time.perf_counter()

    qvec = encode_bytes(query)
    redis_hits = vector_search(qvec, top_k=top_k)

    intent = detect_intent(query, redis_hits)
    api_name = intent["api"]
    api_config = intent.get("config") or get_api_config(api_name) or {}

    slots = extract_slots(query, api_config)

    endpoint_template = intent.get("endpoint", "<base_url>/api")
    base_url = slots.get("base_url", "<missed>")
    endpoint = endpoint_template.replace("<base_url>", base_url)
    endpoint = _normalize_endpoint_path(api_name, endpoint)

    request: Dict[str, Any] = {}
    for slot_def in api_config.get("slots", []):
        key = slot_def["key"]
        if key == "base_url":
            continue
        if key in slots:
            request[key] = slots[key]
        elif "default" in slot_def:
            request[key] = slot_def["default"]

    # Post: register username from email if missing
    if api_name == "register" and "email" in request and "username" not in request:
        local = request["email"].split("@", 1)[0]
        if is_valid_username(local):
            request["username"] = local

    # Post: delete_account confirm default false
    if api_name == "delete_account" and "confirm" not in request:
        request["confirm"] = False

    result: Dict[str, Any] = {"api": api_name, "endpoint": endpoint, "request": request}

    if include_meta:
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        result["meta"] = {
            "processing_time_ms": elapsed_ms,
            "template_used": api_config.get("name"),
            "slots_extracted": sorted(list(slots.keys())),
            "qa_model_used": _QA is not None,
            "vector_search": True,
        }
    return result

def batch_answer(queries: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
    return [answer(q, top_k=top_k) for q in queries]

def clear_cache() -> None:
    _embedding_cache.clear()

def get_cache_stats() -> Dict[str, Any]:
    used = len(_embedding_cache)
    return {"cache_size": used, "max_cache_size": MAX_CACHE_SIZE, "utilization": f"{used / MAX_CACHE_SIZE * 100:.1f}%"}

# ----------------------------
# CLI
# ----------------------------
def _read_stdin_if_piped() -> Optional[str]:
    try:
        if not sys.stdin.isatty():
            data = sys.stdin.read()
            return data.strip() if data else None
    except Exception:
        pass
    return None

def main():
    parser = argparse.ArgumentParser(description="JSON Output Generator (Redis-required, QA-safe, strict base_url, v3.8)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Include performance metrics")
    args = parser.parse_args()

    print(" JSON Output Generator v3.8 (Redis-required, QA-safe, strict base_url, targeted fixes)")
    print("=" * 70)

    stdin_text = _read_stdin_if_piped()
    if stdin_text:
        q = stdin_text
    else:
        try:
            q = input("\n Enter your query: ")
        except KeyboardInterrupt:
            print()
            raise SystemExit(0)

    print("\n  Processing...")
    result = answer(q, include_meta=args.verbose)

    print("\n" + "=" * 70)
    print(" RESULT:")
    print("=" * 70)
    print(json.dumps(result, indent=2))
    print("=" * 70)
    if not args.verbose:
        print("\n Tip: Run with --verbose to see performance metrics")

if __name__ == "__main__":
    main()

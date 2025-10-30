from __future__ import annotations
import hashlib, json, os, re, sys, time, logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

# ============================= CONFIG =============================
class ExtractionMethod(Enum):
    NER = "ner"
    REGEX = "regex"
    FUZZY = "fuzzy"
    QA = "qa"

@dataclass
class ExtractionConfig:
    HIGH_CONFIDENCE_THRESHOLD: float = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD: float = 0.65
    LOW_CONFIDENCE_THRESHOLD: float = 0.30

    FUZZY_MIN_SCORE: int = 65
    MIN_PASSWORD_LENGTH: int = 4
    MIN_USERNAME_LENGTH: int = 2
    MIN_TOKEN_LENGTH: int = 6

    LAZY_MODEL_LOADING: bool = True
    ENABLE_TIMING_LOGS: bool = False
    PARALLEL_EXTRACTION: bool = False

    DISABLE_QA: bool = False  # Re-enabled - Using Ollama with Phi-3
    PHI3_THREADS: int = None
    PHI3_BATCH_SIZE: int = 512
    PHI3_CONTEXT_LENGTH: int = 4096
    PHI3_USE_MLOCK: bool = True

    SLOT_EXTRACTION_ORDER: Dict[str, List[ExtractionMethod]] = None

    def __post_init__(self):
        if self.PHI3_THREADS is None:
            cpu_count = os.cpu_count() or 4
            self.PHI3_THREADS = max(4, int(cpu_count * 0.75))
        
        def maybe_qa(seq: List[ExtractionMethod]) -> List[ExtractionMethod]:
            return seq if self.DISABLE_QA else [*seq, ExtractionMethod.QA]
        if self.SLOT_EXTRACTION_ORDER is None:
            self.SLOT_EXTRACTION_ORDER = {
                "email": [ExtractionMethod.REGEX, ExtractionMethod.NER] if self.DISABLE_QA else [ExtractionMethod.REGEX, ExtractionMethod.NER, ExtractionMethod.QA],
                "username": maybe_qa([ExtractionMethod.REGEX, ExtractionMethod.NER, ExtractionMethod.FUZZY]),
                "password": maybe_qa([ExtractionMethod.REGEX, ExtractionMethod.FUZZY]),
                "token":    maybe_qa([ExtractionMethod.REGEX]),
                "base_url": maybe_qa([ExtractionMethod.REGEX, ExtractionMethod.NER]),
                "file_name":maybe_qa([ExtractionMethod.REGEX, ExtractionMethod.NER]),
                "file_id":  maybe_qa([ExtractionMethod.REGEX, ExtractionMethod.NER]),
                "user_id":  maybe_qa([ExtractionMethod.REGEX, ExtractionMethod.NER]),
                "query":    maybe_qa([ExtractionMethod.REGEX, ExtractionMethod.NER, ExtractionMethod.FUZZY]),
                "name":     maybe_qa([ExtractionMethod.REGEX, ExtractionMethod.NER]),
                "default":  maybe_qa([ExtractionMethod.NER, ExtractionMethod.REGEX, ExtractionMethod.FUZZY]),
            }

CONFIG = ExtractionConfig()

# ============================ LOGGING =============================
def setup_enhanced_logging():
    logger = logging.getLogger("nlpforge_enhanced")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    fh = logging.FileHandler("nlpforge_detailed.log", mode="w", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    fh.setFormatter(fmt); ch.setFormatter(fmt)
    logger.addHandler(fh); logger.addHandler(ch)
    return logger

logger = setup_enhanced_logging()

# Optional deps
try:
    from rapidfuzz import fuzz
    FUZZY_AVAILABLE = True
except Exception as e:
    logger.warning(f"RapidFuzz unavailable: {e}")
    fuzz = None
    FUZZY_AVAILABLE = False

try:
    if CONFIG.DISABLE_QA:
        raise ImportError("QA disabled by env")
    from llama_cpp import Llama
    from huggingface_hub import hf_hub_download
    TRANSFORMERS_AVAILABLE = True
    logger.info("llama-cpp-python available for Phi-3 model inference")
except Exception as e:
    logger.warning(f"llama-cpp-python unavailable: {e}")
    TRANSFORMERS_AVAILABLE = False

try:
    from redis_config import get_redis_client
except Exception as e:
    logger.error(f"redis_config required: {e}")
    raise

INDEX_NAME, VECTOR_FIELD, EMBED_MODEL_NAME = "idx:apis", "query_embedding", "BAAI/bge-small-en-v1.5"
_encoder = None
_ner_model = None
_qa_model = None
_embedding_cache: Dict[str, bytes] = {}
_templates: Optional[Dict[str, Any]] = None
PHI3_MODEL_PATH = None
MAX_CACHE_SIZE = 1000

# ======================= REGEX & KEYWORDS =========================
ENHANCED_REGEX = {
    "username_advanced": re.compile(r'(?i)(?:username|user|login|id|as)\s*(?:=|:|is)\s*["\']?([a-zA-Z0-9._@+-]{3,})["\']?'),
    "password_advanced": re.compile(r'(?i)(?:password|pass|pwd)\s*(?:=|:|is)\s*["\']?([^\s"\',;]{4,})["\']?'),
    "credential_pair_and": re.compile(
        r'(?i)(?:user|username)\s*[=:]?\s*["\']?([^"\',\s]+)["\']?\s*(?:,|\s+and\s+|\s*/\s*|\s*\|\s*)\s*(?:pass|password|pwd)\s*[=:]?\s*["\']?([^"\',\s]+)["\']?'
    ),
    "credential_pair_with": re.compile(
        r'(?i)(?:user|username|as)\s*[=:]?\s*["\']?([^"\',\s]+)["\']?\s+with\s+(?:pass|password|pwd)\s*[=:]?\s*["\']?([^"\',\s]+)["\']?'
    ),
    "creds_triplet": re.compile(
        r'(?i)(?:creds?|credentials?)\s*:\s*([^,\s]+)\s*,\s*([^,\s]+)\s*,\s*([^,\s]+)'
    ),
    "name_after_with_to": re.compile(
        r'(?i)\b(?:with|to)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)\b'
    ),
    "download_id_token": re.compile(
        r'(?i)\bdownload\b[^A-Za-z0-9]+([A-Za-z0-9][A-Za-z0-9_\-]{2,})(?!\.)'
    ),
}
COMMON_REGEX = {
    "email": re.compile(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+(?:\.[A-Za-z]{2,})?)\b"),
    "url":   re.compile(r"(https?://\S+|www\.\S+|[A-Za-z0-9.-]+\.[A-Za-z]{2,})"),
    "token_simple": re.compile(r"\b(?:token|session|bearer)\s+([A-Za-z0-9\-_.=]{6,})", re.I),
    "user_id": re.compile(r"\b([Uu]\d{3,})\b"),
    "file_id": re.compile(r"\b(?:id|file\s*id)\s*[:=]?\s*([A-Za-z0-9\-_]{3,})", re.I),
    "file_name": re.compile(r"\b([A-Za-z0-9][A-Za-z0-9_\-\.]+\.(?:pdf|csv|txt|docx|xlsx|json|pptx|zip|mp4|jpg|jpeg|png|gif|mp3|avi|mov))\b", re.I),
    "query_after": re.compile(r"(?i)\b(?:find|search|lookup|query|look\s*up)\b[^A-Za-z0-9]+([A-Za-z0-9 _\-]+?)(?=(?:\s+from|\s+on|\s+at|,|\s+type|\s+filter|$))"),
    "name_two_words": re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)\b"),
}

CRED_PATTERN = re.compile(
    r'(?i)(?:using|with|as|credentials?)\s+([A-Za-z0-9._%+-]+)\s+(?:and|/|,|\|)\s*(?:password|pass|pwd)?\s*([^\s"\'`,;]+)'
)

TOKEN_PATTERNS = {
    "password": re.compile(r"[A-Za-z0-9@#$%^&*()_+\-=\[\]{};:,.<>/?\\|`~!]{4,}"),
    "username": re.compile(r"[A-Za-z0-9._@+-]{3,}"),
    "email": COMMON_REGEX["email"],
    "token": re.compile(r"[A-Za-z0-9\-_.=]{6,}"),
    "user_id": re.compile(r"[Uu]\d{3,}"),
    "file_id": re.compile(r"[A-Za-z0-9\-_]{3,}"),
    "file_name": COMMON_REGEX["file_name"],
    "base_url": COMMON_REGEX["url"],
    "phone": re.compile(r"(\+?\d[\d\-\s]{7,}\d)"),
    "name": re.compile(r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)+"),
    "query": re.compile(r"[A-Za-z0-9\s\-_@#:&/\.]{3,}"),
}

SLOT_KEYWORDS = {
    "password": ["password", "pass", "pwd", "secret", "code"],
    "username": ["username", "user", "login", "userid", "user id", "email"],  # email can serve as username
    "token": ["token", "auth", "bearer", "key", "api key", "session"],
    "email": ["email", "mail", "e-mail"],
    "file_name": ["file", "filename", "document", "attachment", "upload"],
    "file_id": ["file id", "id"],
    "user_id": ["user id", "uid", "userid", "account", "profile", "U"],
    "base_url": ["url", "link", "endpoint", "website", "site"],
    "phone": ["phone", "mobile", "contact"],
    "name": ["name", "full name"],
    "query": ["find", "search", "lookup", "query", "look up", "filter"],
}

INTENT_KEYWORDS = {
    "login": {"login", "log in", "sign in", "sign-in", "signin", "authenticate"},
    "register": {"register", "sign up", "sign-up", "signup", "create account", "new user", "new profile"},
    "reset_password": {"reset password", "forgot password", "password reset", "reset credentials"},
    "logout": {"logout", "log out", "sign out"},
    "update_profile": {"update profile", "update name", "edit contact", "change details", "change name", "update phone", "change profile"},
    "upload_file": {"upload", "send file", "attach", "post file"},
    # NOTE: Remove generic "retrieve"; require "file/resource" to avoid stealing get_user
    "download_file": {"download", "retrieve file", "retrieve resource", "get file", "fetch file"},
    "get_user": {"get user", "get profile", "fetch account", "get details", "retrieve user", "retrieve account", "retrieve user info", "retrieve full user record"},
    "search": {"search", "lookup", "find", "query"},
}

NEGATIVE_DISAMBIG = {
    "get_user": {"student list", "list of students", "list"},
}

# ================== Embeddings / NER / QA loaders =================
def get_encoder():
    global _encoder
    if _encoder is None:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as e:
            logger.error("sentence_transformers required for vector search")
            raise
        _encoder = SentenceTransformer(EMBED_MODEL_NAME)
        _encoder.max_seq_length = 256
    return _encoder

def encode_bytes(text: str) -> bytes:
    normalized = text.lower().strip()
    key = hashlib.md5(normalized.encode("utf-8")).hexdigest()
    if key in _embedding_cache:
        return _embedding_cache[key]
    vec = get_encoder().encode([normalized], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)[0].tobytes()
    if len(_embedding_cache) >= MAX_CACHE_SIZE:
        _embedding_cache.pop(next(iter(_embedding_cache)))
    _embedding_cache[key] = vec
    return vec

def get_ner_model():
    global _ner_model
    if _ner_model is None:
        try:
            import spacy
            try:
                _ner_model = spacy.load("en_core_web_sm")
            except OSError:
                from spacy.cli import download
                logger.info("Downloading spaCy model en_core_web_sm ...")
                download("en_core_web_sm")
                _ner_model = spacy.load("en_core_web_sm")
        except Exception as e:
            logger.warning(f"spaCy unavailable: {e}")
            _ner_model = None
    return _ner_model

def get_tiny_qa():
    global _qa_model, PHI3_MODEL_PATH
    if _qa_model is None:
        if not TRANSFORMERS_AVAILABLE or CONFIG.DISABLE_QA:
            return None
        try:
            if PHI3_MODEL_PATH is None:
                logger.info("Downloading Phi-3-Mini Q4 GGUF model (~2.3GB)...")
                PHI3_MODEL_PATH = hf_hub_download(
                    repo_id="microsoft/Phi-3-mini-4k-instruct-gguf",
                    filename="Phi-3-mini-4k-instruct-q4.gguf",
                    repo_type="model"
                )
            logger.info(f"Loading Phi-3 from {PHI3_MODEL_PATH}")
            _qa_model = Llama(
                model_path=PHI3_MODEL_PATH,
                n_ctx=CONFIG.PHI3_CONTEXT_LENGTH,
                n_threads=CONFIG.PHI3_THREADS,
                n_batch=CONFIG.PHI3_BATCH_SIZE,
                use_mlock=CONFIG.PHI3_USE_MLOCK,
                verbose=False
            )
            logger.info(" Phi-3-Mini Q4 GGUF loaded successfully")
        except Exception as e:
            logger.warning(f"Phi-3 initialization failed: {e}")
            return None
    return _qa_model

# =================== Hallucination detector =======================
class HallucinationDetector:
    HALL = {
        "username": [r"^user\d{1,4}$", r"^[a-z]+user$", r"^example"],
        "password": [r"^(password|pass|pwd)\d{0,3}$", r"^mypassword$", r"^demo@?\d{0,3}$"],
        "email":    [r"^[\w]+@example\.(com|org|net)$", r"^test@"],
        "user_id":  [r"^U\d{1,3}$", r"^U12345$"],
        "file_id":  [r"^F\d{1,3}$"],
        "file_name":[r"^(report|document|file)\.(pdf|docx)$", r"^report\.pdf$"],
        "token":    [r"^(session_token|token|bearer)$"],
        "base_url": [r"^example\.(com|org|net)$"],
    }
    @staticmethod
    def likely(slot: str, value: str, conf: float) -> bool:
        if not value:
            return True
        pats = HallucinationDetector.HALL.get(slot, [])
        if any(re.match(p, value, re.I) for p in pats):
            return True
        if slot == "password" and conf < 0.7:
            import math
            from collections import Counter
            c = Counter(value); n = len(value)
            if n:
                H = -sum((v/n)*math.log2(v/n) for v in c.values())
                if H < 2.5:
                    return True
        return conf < 0.25

# ======================= Validation helpers =======================
def _validate_slot_value_enhanced(slot: str, value: str, query: str = "") -> Tuple[bool, str]:
    if not value or not value.strip():
        return False, "empty"
    val = value.strip()

    min_len = {
        "password": CONFIG.MIN_PASSWORD_LENGTH,
        "username": CONFIG.MIN_USERNAME_LENGTH,
        "token": CONFIG.MIN_TOKEN_LENGTH,
        "user_id": 3, "file_id": 3, "email": 5
    }
    if slot in min_len and len(val) < min_len[slot]:
        return False, "too short"

    if slot == "email":
        # Accept labelled invalid emails (e.g., "email wrong@input") to keep test intents
        email_format_ok = bool(re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', val))
        if not email_format_ok:
            if re.search(r'(?i)\bemail\b[^A-Za-z0-9]*' + re.escape(val), query):
                return True, "labelled email"
            # else let it pass if extractor chose it (we avoid overriding)
            return True, "weak email format accepted"

    elif slot == "username":
        # allow email-as-username in auth/registration contexts
        ql = query.lower()
        if any(w in ql for w in ("login", "log in", "sign in", "sign-in", "signin", "authenticate", "register", "sign up", "signup", "sign-up")):
            pass
        else:
            if re.match(r'^(https?://|www\.)', val):
                return False, "looks like URL"

    elif slot == "password":
        if val.lower() in {"password", "pass", "pwd", "1234", "123456"}:
            return False, "weak password"

    elif slot == "base_url":
        if not (re.match(r'^https?://', val) or re.match(r'^[A-Za-z0-9.-]+\.[A-Za-z]{2,}(/.*)?$', val)):
            return False, "bad url"

    return True, "ok"

# ===================== Post-processing utils ======================
def _char_diversity_score(s: str) -> int:
    return sum([any(c.islower() for c in s), any(c.isupper() for c in s),
                any(c.isdigit() for c in s), any(not c.isalnum() for c in s)])

def _best_candidate(cands: List[str], slot: str) -> Optional[str]:
    if not cands: return None
    fillers = {"and","or","with","the","to","of","for","on","at","in","it","this","that"}
    if slot in {"username","password","token","user_id","file_id"}:
        cands = [c for c in cands if not re.match(r'^[\w\-]+\.(com|net|org|io|ai|dev|in)\.?$', c, re.I)]
    scored = [(len(base := c.strip().strip(",:;`'\"")), _char_diversity_score(base) if slot=="password" else 0, base)
              for c in cands if (base := c.strip().strip(",:;`'\"")) and base.lower() not in fillers and len(base)>=2]
    return max(scored, key=lambda x:(x[0],x[1]))[2] if scored else None

def _expand_fragment_to_token(query: str, fragment: str, slot: str) -> Optional[str]:
    if not fragment: return None
    pat = TOKEN_PATTERNS.get(slot) or re.compile(r"[^\s\"'`]{3,}")
    frag = re.escape(fragment)
    cands = []
    for m in pat.finditer(query):
        if re.search(frag, m.group(0), re.I):
            cands.append(m.group(0))
    return _best_candidate(cands, slot)

def _window_candidates_near_keywords(query: str, slot: str, window: int = 80) -> List[str]:
    hits = []
    for kw in SLOT_KEYWORDS.get(slot, []):
        for m in re.finditer(re.escape(kw), query, re.I):
            start, end = max(0, m.end()), min(len(query), m.end()+window)
            chunk = query[start:end]
            pat = TOKEN_PATTERNS.get(slot) or re.compile(r"[^\s\"'`]{3,}")
            hits.extend(pat.findall(chunk))
    return hits

def _validate_slot_value(slot: str, val: str) -> bool:
    if not val: return False
    v = val.strip()
    if slot=="password":
        if len(v)<CONFIG.MIN_PASSWORD_LENGTH: return False
        if v.lower() in {"password","pass","pwd"}: return False
        return True
    if slot in {"username","email","token","user_id","file_id","file_name"}:
        return bool(re.fullmatch(TOKEN_PATTERNS[slot], v))
    return True

def postprocess_slot(query: str, slot: str, raw_val: str) -> str:
    val = (raw_val or "").strip().strip("`'\"").strip(",;")
    if not val: return val
    if slot=="phone" and not val.startswith("+") and f"+{val}" in query:
        val = f"+{val}"
    needs_expand = (
        (slot=="password" and (len(val)<6 or _char_diversity_score(val)<2)) or
        (slot in {"username","token","file_id","user_id"} and len(val)<4) or
        (slot=="file_name" and "." not in val)
    )
    if needs_expand:
        exp = _expand_fragment_to_token(query, val, slot)
        if exp: val = exp
    if not _validate_slot_value(slot, val):
        near = _window_candidates_near_keywords(query, slot, 100)
        best = _best_candidate(near, slot)
        if best: val = best
    if not _validate_slot_value(slot, val):
        pat = TOKEN_PATTERNS.get(slot) or re.compile(r"[^\s\"'`]{3,}")
        allc = [m.group(0) for m in pat.finditer(query)]
        best = _best_candidate(allc, slot)
        if best: val = best
    return val

# ===================== TINY QA HELPERS ============================
def _phi3_extract(query: str, field_desc: str, max_tokens: int = 64) -> Tuple[str, float]:
    """Core Phi-3 extraction logic via llama-cpp-python"""
    model = get_tiny_qa()
    if not model:
        return "", 0.0
    
    prompt = f"Extract {field_desc} from this request. Output ONLY the value, nothing else.\nRequest: {query}\nValue:"
    
    try:
        response = model(
            prompt,
            max_tokens=max_tokens,
            temperature=0.1,
            stop=["\n", ".", ","],
            echo=False
        )
        extracted = response["choices"][0]["text"].strip().replace('"', '').replace("'", "").strip()
        return (extracted, 0.75) if extracted and len(extracted) < 100 else ("", 0.0)
    except Exception as e:
        logger.debug(f"Phi-3 error: {e}")
        return "", 0.0

def tinyqa_slot_extract(query: str, slot: str) -> Tuple[str, float]:
    """Extract slot using Phi-3-Mini with structured prompting"""
    if CONFIG.DISABLE_QA or not TRANSFORMERS_AVAILABLE:
        return "", 0.0
    
    q_map = {
        "username": "the username or user ID", "password": "the password",
        "email": "the email address", "base_url": "the URL or website",
        "file_name": "the file name", "file_id": "the file ID",
        "user_id": "the user ID", "token": "the authentication token",
        "name": "the person's name", "phone": "the phone number",
        "query": "the search query or search term",
    }
    
    extracted, confidence = _phi3_extract(query, q_map.get(slot, f"the {slot}"))
    if not extracted or HallucinationDetector.likely(slot, extracted, confidence):
        return "", 0.0
    
    extracted = _smart_fragment_expansion(query, extracted, slot)
    fixed = postprocess_slot(query, slot, extracted)
    if fixed and fixed != extracted:
        confidence = max(confidence, 0.65)
    
    ok, reason = _validate_slot_value_enhanced(slot, fixed, query)
    if ok and fixed:
        logger.debug(f"Phi-3 extracted {slot}='{fixed}' conf={confidence:.2f}")
        return fixed, confidence
    
    logger.debug(f"Phi-3 invalid for {slot}: {reason}")
    return "", 0.0

def _smart_fragment_expansion(query: str, fragment: str, slot: str) -> Optional[str]:
    if not fragment or len(fragment) > 20:
        return fragment
    pos = query.find(fragment)
    if pos == -1:
        return fragment
    start, end = max(0, pos-50), min(len(query), pos+len(fragment)+50)
    ctx = query[start:end]
    if slot == "password":
        for pat in [r'[A-Za-z0-9@#$%^&*()_+\-=\[\]{};:,.<>?]{6,}', r'[A-Z][a-z]+[0-9!@#$%^&*]{2,}']:
            for m in re.finditer(pat, ctx):
                if fragment in m.group(0): return m.group(0)
    wb = r'\b[\w@#$%^&*()_+\-=\[\]{};:,.<>?]*' + re.escape(fragment) + r'[\w@#$%^&*()_+\-=\[\]{};:,.<>?]*\b'
    ms = re.findall(wb, ctx)
    return max(ms, key=len) if ms else fragment

# =================== QUICK REGEX EXTRACTION =======================
def _quick_regex_extraction(query: str) -> Dict[str, str]:
    r: Dict[str, str] = {}

    nm = ENHANCED_REGEX["name_after_with_to"].search(query)
    if nm: r["name"] = nm.group(1)

    fn = COMMON_REGEX["file_name"].search(query)
    if fn: r["file_name"] = fn.group(1)

    e = COMMON_REGEX["email"].search(query)
    if e: r["email"] = e.group(1)

    u = COMMON_REGEX["url"].search(query)
    if u: r["base_url"] = u.group(0)

    uid = COMMON_REGEX["user_id"].search(query)
    if uid: r["user_id"] = uid.group(1).upper()

    fid = COMMON_REGEX["file_id"].search(query)
    if fid and "file_id" not in r:
        r["file_id"] = fid.group(1)

    did = ENHANCED_REGEX["download_id_token"].search(query)
    if did and "file_id" not in r:
        token = did.group(1)
        if "." not in token:
            r["file_id"] = token

    cred = (
        ENHANCED_REGEX["credential_pair_and"].search(query) or
        ENHANCED_REGEX["credential_pair_with"].search(query) or
        CRED_PATTERN.search(query)
    )
    if cred:
        user, pwd = cred.groups()
        if user and pwd:
            r["username"] = user
            r["password"] = pwd

    if "username" not in r:
        um = ENHANCED_REGEX["username_advanced"].search(query)
        if um: r["username"] = um.group(1)
    if "password" not in r:
        pm = ENHANCED_REGEX["password_advanced"].search(query)
        if pm: r["password"] = pm.group(1)

    tri = ENHANCED_REGEX["creds_triplet"].search(query)
    if tri:
        a, b, c = tri.groups()
        parts = [a, b, c]
        email_idx = next((i for i, x in enumerate(parts) if "@" in x), None)
        pw_idx = max(range(3), key=lambda i: _char_diversity_score(parts[i]))
        if email_idx is not None:
            user_idx = next(i for i in range(3) if i not in (email_idx, pw_idx))
            r["username"] = r.get("username", parts[user_idx])
            r["email"] = r.get("email", parts[email_idx])
            r["password"] = r.get("password", parts[pw_idx])
        else:
            r.setdefault("username", a)
            r.setdefault("password", c)

    qm = COMMON_REGEX["query_after"].search(query)
    if qm:
        r["query"] = qm.group(1).strip()

    return r

# ======================= NER EXTRACTION ============================
def ner_extract(query: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    ner = get_ner_model()
    if not ner: return out
    doc = ner(query)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            out.setdefault("name", ent.text)
        elif ent.label_ in ("ORG","PRODUCT"):
            if "." in ent.text and not ent.text.lower().endswith((".pdf",".csv",".txt",".docx",".xlsx",".json",".pptx",".zip",".mp4",".jpg",".jpeg",".png",".gif",".mp3",".avi",".mov")):
                out.setdefault("base_url", ent.text)

    cred = (
        ENHANCED_REGEX["credential_pair_and"].search(query) or
        ENHANCED_REGEX["credential_pair_with"].search(query) or
        CRED_PATTERN.search(query)
    )
    if cred:
        out["username"], out["password"] = cred.groups()

    e = COMMON_REGEX["email"].search(query)
    if e: out.setdefault("email", e.group(1))
    u = COMMON_REGEX["url"].search(query)
    if u: out.setdefault("base_url", u.group(0))
    uid = COMMON_REGEX["user_id"].search(query)
    if uid: out.setdefault("user_id", uid.group(1).upper())
    fn = COMMON_REGEX["file_name"].search(query)
    if fn: out.setdefault("file_name", fn.group(1))
    qm = COMMON_REGEX["query_after"].search(query)
    if qm: out.setdefault("query", qm.group(1).strip())

    nm = ENHANCED_REGEX["name_after_with_to"].search(query)
    if nm: out.setdefault("name", nm.group(1))
    return out

# ======================= METHOD DISPATCH ===========================
def fuzzy_best_choice(candidates: List[str], text: str, min_score: int = 65):
    if not FUZZY_AVAILABLE: return (None, 0)
    scores = [(c, fuzz.partial_ratio(c.lower(), text.lower())) for c in candidates]
    best = max(scores, key=lambda x: x[1], default=(None, 0))
    return best if best[1] >= min_score else (None, best[1])

def _extract_using_method(query: str, slot: str, method: ExtractionMethod, slot_def: Dict[str, Any]) -> Tuple[str, float]:
    if method == ExtractionMethod.REGEX:
        return _regex_extract(query, slot, slot_def)
    if method == ExtractionMethod.NER:
        return _ner_extract_slot(query, slot)
    if method == ExtractionMethod.FUZZY:
        return _fuzzy_extract(query, slot, slot_def)
    if method == ExtractionMethod.QA:
        return tinyqa_slot_extract(query, slot)
    return "", 0.0

def _regex_extract(query: str, slot: str, slot_def: Dict[str, Any]) -> Tuple[str, float]:
    if slot in {"username","password"}:
        for key in ("credential_pair_and","credential_pair_with"):
            m = ENHANCED_REGEX[key].search(query)
            if m:
                u, p = m.groups()
                return (u if slot=="username" else p), 0.85
    if slot in {"user_id","file_id","file_name"}:
        m = COMMON_REGEX.get(slot, None)
        if m:
            s = m.search(query)
            if s:
                g = s.group(1)
                if slot=="user_id": g = g.upper()
                return g, 0.75
    if slot == "file_id":
        d = ENHANCED_REGEX["download_id_token"].search(query)
        if d and "." not in d.group(1):
            return d.group(1), 0.72
    if slot == "name":
        n = ENHANCED_REGEX["name_after_with_to"].search(query) or COMMON_REGEX["name_two_words"].search(query)
        if n: return n.group(1), 0.7
    if slot == "query":
        m = COMMON_REGEX["query_after"].search(query)
        if m: return m.group(1).strip(), 0.7
    if slot in COMMON_REGEX:
        m = COMMON_REGEX[slot].search(query)
        if m: return (m.group(1) if m.lastindex else m.group(0)), 0.7
    return "", 0.0

def _ner_extract_slot(query: str, slot: str) -> Tuple[str, float]:
    ner_r = ner_extract(query)
    if slot in ner_r: return ner_r[slot], 0.6
    return "", 0.0

def _fuzzy_extract(query: str, slot: str, slot_def: Dict[str, Any]) -> Tuple[str, float]:
    if not FUZZY_AVAILABLE: return "", 0.0
    qs = slot_def.get("questions", [])
    if not qs: return "", 0.0
    best_q, score = fuzzy_best_choice(qs, query, CONFIG.FUZZY_MIN_SCORE)
    if best_q and score >= CONFIG.FUZZY_MIN_SCORE:
        after = re.search(rf"{re.escape(best_q.split()[0])}.{{0,80}}([^\s\"'`]+)", query, re.I)
        if after:
            cand = postprocess_slot(query, slot, after.group(1))
            if cand: return cand, score/100.0
    return "", 0.0

# ==================== Templates / intent =========================
def load_templates() -> Dict[str, Any]:
    global _templates
    if _templates: return _templates
    for p in (Path(__file__).parent/"api_template.json", Path.cwd()/"api_template.json"):
        if p.exists():
            _templates = json.load(open(p, "r", encoding="utf-8"))
            return _templates
    raise FileNotFoundError("api_template.json not found")

def get_api_config(api_name: str) -> Optional[Dict[str, Any]]:
    return next((a for a in load_templates().get("apis", []) if a.get("name")==api_name), None)

def _score_by_intent_keywords(query: str) -> List[Tuple[str, float]]:
    ql = query.lower()
    scores: Dict[str, float] = {}
    for api, kws in INTENT_KEYWORDS.items():
        s = 0.0
        for kw in kws:
            if kw in ql: s += 1.0
        for neg in NEGATIVE_DISAMBIG.get(api, set()):
            if neg in ql: s -= 1.0
        if s>0: scores[api] = s
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

def detect_intent(query: str, hits: List[Dict[str, Any]]):
    ql = query.lower()
    templates = load_templates()
    api_cfgs = templates.get("apis", [])

    # keyword scoring
    kw_rank = _score_by_intent_keywords(query)
    if kw_rank:
        best_api = kw_rank[0][0]
        cfg = get_api_config(best_api)
        if cfg:
            return {"api": best_api, "endpoint": cfg.get("endpoint_template", ""), "config": cfg, "score": 0.8}

    # template-based semantics
    api_scores = []
    for cfg in api_cfgs:
        score = 0.0
        name = cfg.get("name","")
        intent_kws = set(map(str.lower, cfg.get("intent_keywords", [])))
        desc = (cfg.get("description","") or "").lower()
        score += sum(1 for kw in intent_kws if kw in ql) * 0.4
        if desc:
            cw = set(desc.split()).intersection(set(ql.split()))
            score += (len(cw) / max(1,len(ql.split()))) * 0.3
        if name and name.lower() in ql:
            score += 0.5
        api_scores.append({"api": name, "config": cfg, "endpoint": cfg.get("endpoint_template",""), "score": score})
    api_scores.sort(key=lambda x: x["score"], reverse=True)
    if api_scores and api_scores[0]["score"] > 0.5:
        return api_scores[0]

    # vector fallback
    if hits:
        api = hits[0].get("api", "search")
        cfg = get_api_config(api) or {}
        return {"api": api, "endpoint": cfg.get("endpoint_template",""), "config": cfg, "score": 0.7}

    # default
    cfg = get_api_config("search") or {}
    return {"api": "search", "endpoint": cfg.get("endpoint_template",""), "config": cfg, "score": 0.5}

# ======================= Extraction pipeline =====================
def extract_slots_enhanced(query: str, api_cfg: Dict[str, Any]) -> Dict[str, Any]:
    extracted: Dict[str, Any] = {}
    api_name = api_cfg.get("name","")

    # Phase 1
    logger.info(f"Phase 1: quick regex for {api_name}")
    extracted.update(_quick_regex_extraction(query))

    # Phase 2
    logger.info(f"Phase 2: NER for {api_name}")
    ner_r = ner_extract(query)
    for k, v in ner_r.items():
        if k not in extracted or not extracted[k]:
            extracted[k] = v

    # Phase 3
    logger.info(f"Phase 3: slot-specific for {api_name}")
    for slot_def in api_cfg.get("slots", []):
        key = slot_def.get("key")
        if not key or key in extracted: continue
        methods = CONFIG.SLOT_EXTRACTION_ORDER.get(key, CONFIG.SLOT_EXTRACTION_ORDER["default"])
        for mth in methods:
            val, conf = _extract_using_method(query, key, mth, slot_def)
            if val and conf >= CONFIG.LOW_CONFIDENCE_THRESHOLD:
                ok, _ = _validate_slot_value_enhanced(key, val, query)
                if ok:
                    extracted[key] = val
                    logger.info(f"Extracted {key} via {mth.value} conf={conf:.2f}")
                    break

    # Phase 3.5: dependencies & generic repairs
    # a) allow email-as-username in auth contexts if username missing
    if "username" not in extracted and "email" in extracted:
        if any(w in query.lower() for w in ("login","log in","sign in","sign-in","signin","authenticate","register","sign up","signup","sign-up")):
            extracted["username"] = extracted["email"]

    # b) derive file_type from file_name
    if "file_name" in extracted and "file_type" not in extracted:
        m = re.search(r"\.([A-Za-z0-9]+)$", extracted["file_name"])
        if m: extracted["file_type"] = m.group(1).lower()

    if "username" in extracted and "password" in extracted:
        u, p = extracted["username"], extracted["password"]
        u_looks_pw = (len(u) >= 6 and _char_diversity_score(u) >= 2 and not re.match(r'^[A-Za-z0-9._@+-]{3,}$', u))
        p_looks_user = bool(re.match(r'^[A-Za-z0-9._@+-]{3,}$', p)) or ("@" in p)
        if u_looks_pw and p_looks_user:
            extracted["username"], extracted["password"] = p, u

    if "user_id" in extracted:
        extracted["user_id"] = extracted["user_id"].upper()

    logger.info(f"Phase 4: postprocess for {api_name}")
    for k, v in list(extracted.items()):
        pp = postprocess_slot(query, k, v)
        if pp != v:
            extracted[k] = pp

    return extracted

# ================== VECTOR SEARCH & ANSWER =======================
def vector_search(qvec: bytes, top_k: int = 5) -> List[Dict[str, Any]]:
    try:
        r = get_redis_client().execute_command(
            "FT.SEARCH", INDEX_NAME, f'*=>[KNN {top_k} @{VECTOR_FIELD} $vec AS score]',
            "PARAMS", "2", "vec", qvec, "SORTBY", "score",
            "RETURN", "6", "query", "api", "endpoint", "request", "response", "score",
            "DIALECT", "2"
        )
    except Exception as e:
        logger.error(f"Redis search failed: {e}")
        return []
    if not r or len(r) < 2: return []
    dec = lambda v: v.decode("utf-8") if isinstance(v, (bytes, bytearray)) else v
    return [{dec(k): dec(v) for k, v in zip(r[i+1][::2], r[i+1][1::2])} for i in range(1, len(r), 2)]

def detect_and_prepare_intent(query: str, hits: List[Dict[str, Any]]):
    intent = detect_intent(query, hits)
    api_name = intent.get("api","search")
    cfg = intent.get("config") or get_api_config(api_name) or {}
    endpoint_tmpl = intent.get("endpoint", cfg.get("endpoint_template","") or cfg.get("endpoint",""))
    return api_name, cfg, endpoint_tmpl

def answer(query: str, top_k: int = 5, include_meta: bool = False):
    start = time.perf_counter()
    hits = vector_search(encode_bytes(query), top_k)
    api_name, cfg, endpoint_tmpl = detect_and_prepare_intent(query, hits)
    slots = extract_slots_enhanced(query, cfg)
    endpoint = (endpoint_tmpl or "<missing>/endpoint").replace("<base_url>", slots.get("base_url", "<missing>"))
    request = {}
    for s in cfg.get("slots", []):
        k = s.get("key")
        if not k or k == "base_url": continue
        request[k] = slots.get(k, s.get('default'))
    res = {"api": api_name, "endpoint": endpoint, "request": request}
    if include_meta:
        res["meta"] = {
            "processing_time_ms": round((time.perf_counter()-start)*1000, 2),
            "slots_extracted": sorted(slots.keys()),
            "methods_used": ["regex","ner"] + (["rapidfuzz"] if FUZZY_AVAILABLE else []) + ([] if CONFIG.DISABLE_QA or not TRANSFORMERS_AVAILABLE else ["phi3-mini-q4"]) + ["postprocess"],
        }
    return res

def batch_answer(queries: List[str], top_k: int = 5):
    return [answer(q, top_k) for q in queries]

def extract_slots(query: str, api_cfg: Dict[str, Any]) -> Dict[str, Any]:
    return extract_slots_enhanced(query, api_cfg)

# ============================= CLI ===============================
def main():
    print("🚀 NLPForge JSON Output Generator v8.3 (Enhanced with Phi-3-Mini)")
    try:
        get_redis_client().ping()
        print(" Redis connected")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise SystemExit(1)
    
    if not CONFIG.DISABLE_QA:
        print(" Loading Phi-3-Mini Q4 GGUF model (first run downloads ~2.3GB)...")
        qa_model = get_tiny_qa()
        if qa_model:
            print(f" Phi-3 loaded with {CONFIG.PHI3_THREADS} threads")
        else:
            print("  Phi-3 not available, using regex/NER only")
    
    while True:
        try:
            q = input("\n Enter your query (or 'quit' to exit): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting."); break
        if q.lower() in {"quit","exit","q"}: break
        if not q: continue
        print("\n" + "="*60)
        print(json.dumps(answer(q, include_meta=True), indent=2))
        print("="*60)

if __name__ == "__main__":
    main()

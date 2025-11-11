"""
Query Parser - Extract intent and slots from natural language queries
HYBRID: Vector search for intent + spaCy NER + Llama 3.2 3B for slots
(Regex-based slot extraction removed as requested)
"""

from typing import Dict, List, Optional, Tuple
import re
import spacy
from spacy.pipeline import EntityRuler

from app.core.logger import logger
from app.core.config import INTENT_DETECTION_METHOD
from app.services.template_service import get_template_service
from app.nlp.llama_slot_extractor import get_llama_extractor
from app.nlp.embedding_manager import get_embedding_manager

# ---------------------------
# Utilities / validators
# ---------------------------

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+?[0-9\s\-\(\)]{7,}$")

def _load_spacy(spacy_model: str):
    """
    Load spaCy model and add an EntityRuler so EMAIL/PHONE are reliably detected.
    """
    try:
        nlp = spacy.load(spacy_model)
        logger.info(f"Loaded spaCy model: {spacy_model}")
    except OSError:
        logger.warning(f"spaCy model {spacy_model} not found. Using en_core_web_sm as fallback.")
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error("No spaCy model available. Run: python -m spacy download en_core_web_sm")
            return None

    # Ensure EMAIL/PHONE entity detection exists even if base model lacks them
    if "entity_ruler" not in nlp.pipe_names:
        ruler = nlp.add_pipe("entity_ruler", before="ner")
    else:
        ruler = nlp.get_pipe("entity_ruler")

    ruler.add_patterns([
        {"label": "EMAIL", "pattern": [{"LIKE_EMAIL": True}]},
        {"label": "PHONE", "pattern": [{"ORTH": {"REGEX": r"[\+]?[\d\-\s\(\)]{7,}"}}]},
    ])
    return nlp

def _redact(d: Dict[str, str]) -> Dict[str, str]:
    """
    Redact secrets (like passwords) in dict for safe logging/return (optional).
    """
    if not d:
        return d
    secrets = {"password", "pwd", "pass"}
    return {k: ("***" if k.lower() in secrets else v) for k, v in d.items()}

def _typed_ok(key: str, value: str) -> bool:
    """
    Lightweight shape/type validation to reduce junk merges.
    """
    if not isinstance(value, str) or not value.strip():
        return False
    v = value.strip()

    if key == "email":
        return bool(EMAIL_RE.match(v))
    if key == "phone":
        return bool(PHONE_RE.match(v))
    if key == "username":
        return 2 < len(v) <= 64
    if key == "password":
        return 1 <= len(v) <= 256
    if key == "name":
        # allow unicode letters by checking presence of letters
        return bool(re.search(r"[^\W\d_]", v, flags=re.UNICODE))
    return True

def _normalize_slots(d: Dict[str, str]) -> Dict[str, str]:
    """
    Normalize common slots: trimming, lowercasing where appropriate.
    """
    out: Dict[str, str] = {}
    for k, v in (d or {}).items():
        if v is None:
            continue
        val = v.strip()
        if k in {"email", "username"}:
            val = val.lower()
        out[k] = val
    return out

# ---------------------------
# QueryParser
# ---------------------------

class QueryParser:
    """
    Parse natural language queries to extract:
    1) Intent (which API: login, signup, update, etc.)
    2) Slots (fields: username, password, email, etc.)

    Slot extraction now uses ONLY:
      - spaCy NER (+EntityRuler for EMAIL/PHONE)
      - Llama 3.2 3B (with spaCy hints)
    """

    def __init__(self, spacy_model: str = "en_core_web_md", use_llama: bool = True):
        """
        Initialize the query parser.

        Args:
            spacy_model: spaCy model to load (default: en_core_web_md)
            use_llama: Whether to use Llama 3.2 3B for slot extraction (default: True)
        """
        self.nlp = _load_spacy(spacy_model)
        if self.nlp is None:
            logger.error("spaCy initialization failed. NER-based extraction will be disabled.")

        # Initialize Llama extractor
        self.use_llama = use_llama
        if use_llama:
            try:
                self.llama_extractor = get_llama_extractor()
                logger.info(
                    f"Llama 3.2 3B slot extraction: "
                    f"{'✅ enabled' if self.llama_extractor.enabled else '⚠️ disabled (fallback mode)'}"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Llama extractor: {e}")
                self.llama_extractor = None
        else:
            self.llama_extractor = None

        # Load intent patterns dynamically from template service
        self.intent_patterns = self._load_intent_patterns()
        logger.info(f"Loaded {len(self.intent_patterns)} intent patterns from template service")

    # ---------------------------
    # Intent patterns
    # ---------------------------

    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """
        Load intent patterns dynamically from template service.

        Returns:
            Dict[intent, List[regex_patterns]]
        """
        try:
            template_service = get_template_service()
            templates = template_service.get_all_templates()

            patterns: Dict[str, List[str]] = {}
            for intent, template in templates.items():
                keywords = template.get("intent_keywords", [])
                if keywords:
                    patterns[intent] = self._keywords_to_patterns(keywords)

            if not patterns:
                logger.warning("No templates loaded, intent detection may fail")

            return patterns

        except Exception as e:
            logger.error(f"Error loading intent patterns from templates: {e}")
            return {}

    def _keywords_to_patterns(self, keywords: List[str]) -> List[str]:
        """
        Convert intent keywords to regex patterns.

        Single word -> word boundary.
        Multi-word -> allow up to 3 arbitrary tokens between words.
        """
        patterns = []
        for keyword in keywords:
            words = keyword.split()
            if len(words) == 1:
                escaped = re.escape(keyword)
                pattern = rf"\b{escaped}\b"
                patterns.append(pattern)
            else:
                escaped_words = [re.escape(w) for w in words]
                # Allow up to 3 tokens (non-newline) between words
                flexible = r"(?:\s+\S+){0,3}".join(escaped_words)
                pattern = rf"(?<!\w){flexible}(?!\w)"
                patterns.append(pattern)
        return patterns

    def reload_patterns(self):
        """Hot-reload intent patterns."""
        logger.info("Reloading intent patterns...")
        self.intent_patterns = self._load_intent_patterns()
        logger.info(f"Reloaded {len(self.intent_patterns)} intent patterns")

    # ---------------------------
    # Intent detection (vector / pattern)
    # ---------------------------

    def detect_intent_pattern(self, query: str) -> Tuple[str, float]:
        """
        Detect API intent via pattern matching (fallback).
        Returns (intent_name, confidence_score).
        """
        query_lower = query.lower()
        intent_scores: Dict[str, float] = {}

        for intent, patterns in self.intent_patterns.items():
            score = 0.0
            matches = 0
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    matches += 1
                    score += 0.5
            if matches > 0:
                intent_scores[intent] = min(score, 1.0)

        if not intent_scores:
            return "unknown", 0.0

        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent[0], best_intent[1]

    def detect_intent(self, query: str, use_vector_search: bool = True, min_sim: float = 0.35) -> Tuple[str, float]:
        """
        Detect API intent using vector search (preferred) or pattern matching.
        """
        if not use_vector_search:
            return self.detect_intent_pattern(query)

        try:
            embedder = get_embedding_manager()
            search_results = embedder.search(query=query, top_k=5, intent_filter=None)

            if not search_results:
                logger.warning("No vector search results, falling back to pattern matching")
                return self.detect_intent_pattern(query)

            # Filter out noisy low-similarity results
            filtered = [r for r in search_results if r.get("similarity", 0.0) >= min_sim]
            if not filtered:
                logger.info("Vector results below threshold; using pattern matching")
                return self.detect_intent_pattern(query)

            # Aggregate scores per intent
            intent_scores: Dict[str, Dict[str, float]] = {}
            for result in filtered:
                intent = result.get("intent", "unknown")
                sim = result.get("similarity", 0.0)
                stats = intent_scores.setdefault(intent, {"total": 0.0, "count": 0, "max": 0.0})
                stats["total"] += sim
                stats["count"] += 1
                stats["max"] = max(stats["max"], sim)

            final_scores: Dict[str, float] = {}
            for intent, s in intent_scores.items():
                avg = s["total"] / max(1, s["count"])
                final_scores[intent] = (s["max"] * 0.7) + (avg * 0.3)

            if not final_scores:
                return "unknown", 0.0

            best_intent = max(final_scores.items(), key=lambda x: x[1])
            logger.info(f"Vector search detected intent: {best_intent[0]} (confidence: {best_intent[1]:.2f})")
            return best_intent[0], best_intent[1]

        except Exception as e:
            logger.error(f"Error in vector search intent detection: {e}")
            logger.warning("Falling back to pattern matching")
            return self.detect_intent_pattern(query)

    # ---------------------------
    # Slot extraction (NER + Llama only)
    # ---------------------------

    def extract_slots_spacy(self, query: str) -> Dict[str, str]:
        """
        Extract slots using spaCy NER only.
        Recognized labels used: PERSON->name, EMAIL->email, PHONE/CARDINAL->phone, ORG->organization,
        GPE->location, DATE->date, MONEY->amount.
        """
        if not self.nlp:
            return {}

        doc = self.nlp(query)
        slots: Dict[str, str] = {}

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                if "name" not in slots:
                    slots["name"] = ent.text
                elif "username" not in slots:
                    slots["username"] = ent.text
            elif ent.label_ == "EMAIL":
                slots["email"] = ent.text
            elif ent.label_ in ["PHONE", "CARDINAL"] and re.match(r"[\+\d\s\-\(\)]+", ent.text):
                if "phone" not in slots:
                    slots["phone"] = ent.text
            elif ent.label_ == "ORG":
                slots["organization"] = ent.text
            elif ent.label_ == "GPE":
                if "location" not in slots:
                    slots["location"] = ent.text
            elif ent.label_ == "DATE":
                if "date" not in slots:
                    slots["date"] = ent.text
            elif ent.label_ == "MONEY":
                if "amount" not in slots:
                    slots["amount"] = ent.text

        # Heuristic: tokens with '@' or '_' may be usernames
        for token in doc:
            if ("@" in token.text or "_" in token.text) and len(token.text) > 2:
                if "username" not in slots:
                    slots["username"] = token.text

        return slots

    def extract_slots_llama(self, query: str, intent: str, spacy_hints: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Extract slots using Llama 3.2 3B (with optional spaCy hints for gaps).
        Sends a redacted query (password masked) to avoid leaking secrets.
        """
        if not self.llama_extractor or not getattr(self.llama_extractor, "enabled", False):
            return {}

        try:
            # redact password-like segments before sending to LLM
            safe_query = re.sub(r"(password\s*[:=]?\s*)(\S+)", r"\1***", query, flags=re.I)
            slots = self.llama_extractor.extract_slots_for_intent(safe_query, intent) or {}

            # Fill gaps from spaCy hints
            if spacy_hints:
                for k, v in spacy_hints.items():
                    if (k not in slots or not slots[k]) and v:
                        slots[k] = v

            return slots
        except Exception as e:
            logger.error(f"Llama slot extraction failed: {e}")
            return {}

    def _appears_in_query(self, value: str, query: str) -> bool:
        """
        Validate that an extracted value appears in the query text (guard vs hallucinations).
        """
        if not value:
            return False
        q = query.lower()
        v = value.lower()
        if v in q:
            return True

        words = [w for w in re.split(r"\s+", v) if w]
        if len(words) > 1:
            matches = sum(1 for w in words if w in q)
            return matches >= max(1, int(0.6 * len(words)))

        return len(value) <= 3  

    def _merge_slots_intelligently(
        self,
        slots_spacy: Dict[str, str],
        slots_llama: Dict[str, str],
        query: str
    ) -> Dict[str, str]:
        """
        Merge only NER + Llama:
          - Prefer Llama values when valid.
          - Use spaCy to fill gaps.
          - For 'name', prefer spaCy PERSON if present.
        """
        merged: Dict[str, str] = {}

        # Prefer Llama when plausible
        for k, v in (slots_llama or {}).items():
            if v and self._appears_in_query(v, query) and _typed_ok(k, v):
                merged[k] = v

        # Fill gaps with spaCy
        for k, v in (slots_spacy or {}).items():
            if k not in merged and v and self._appears_in_query(v, query) and _typed_ok(k, v):
                merged[k] = v

        # Prefer spaCy PERSON for 'name' if present
        if "name" in (slots_spacy or {}) and slots_spacy.get("name"):
            merged["name"] = slots_spacy["name"]

        return merged

    # ---------------------------
    # Main parse
    # ---------------------------

    def parse(self, query: str, mask_secrets: bool = True) -> Dict:
        """
        Main parsing function.

        Strategy:
        1) Vector Search or pattern-based intent detection (config-controlled).
        2) spaCy NER baseline entities.
        3) Llama extraction (with spaCy hints).
        4) Smart merge: Llama > spaCy, with validation & redaction.

        Returns:
            {
                "intent": str,
                "confidence": float,
                "slots": Dict[str, str],
                "raw_query": str,
                "metadata": {
                    "slots_spacy": Dict,
                    "slots_llama": Dict,
                    "extraction_method": "ner_llama_only"
                }
            }
        """
        use_vector = INTENT_DETECTION_METHOD == "vector_search"
        method_name = "Vector Search" if use_vector else "Pattern Matching"
        logger.info(f" Parsing query (HYBRID {method_name} + NER + Llama): {query}")

        # 1) Detect intent
        intent, confidence = self.detect_intent(query, use_vector_search=use_vector)
        logger.info(f"  Intent ({method_name}): {intent} (confidence: {confidence:.2f})")

        # 2) spaCy NER
        slots_spacy = self.extract_slots_spacy(query)
        if slots_spacy:
            logger.debug(f" spaCy NER found: {_redact(slots_spacy)}")

        # 3) Llama (with spaCy hints)
        slots_llama = self.extract_slots_llama(query, intent, spacy_hints=slots_spacy)
        if slots_llama:
            logger.info(f" Llama extracted: {_redact(slots_llama)}")

        # 4) Merge & normalize
        slots = self._merge_slots_intelligently(
            slots_spacy=slots_spacy,
            slots_llama=slots_llama,
            query=query
        )
        slots = _normalize_slots(slots)
        logger.info(f" Final merged slots: {_redact(slots)}")

        return {
            "intent": intent,
            "confidence": confidence,
            "slots": _redact(slots) if mask_secrets else slots,
            "raw_query": query,
            "metadata": {
                "slots_spacy": _redact(slots_spacy),
                "slots_llama": _redact(slots_llama),
                "extraction_method": "ner_llama_only"
            }
        }

# ---------------------------
# Global singleton (thread-safe)
# ---------------------------

from threading import Lock
_lock = Lock()
_parser_instance = None

def get_query_parser() -> QueryParser:
    """Get or create global QueryParser instance (thread-safe)."""
    global _parser_instance
    if _parser_instance is None:
        with _lock:
            if _parser_instance is None:
                _parser_instance = QueryParser()
    return _parser_instance

def parse_query(query: str, mask_secrets: bool = True) -> Dict:
    """
    Convenience function to parse a query.
    """
    parser = get_query_parser()
    return parser.parse(query, mask_secrets=mask_secrets)

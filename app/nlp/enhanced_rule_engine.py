# app/nlp/enhanced_rule_engine.py
"""
Enhanced Rule Engine (reworked)

Key improvements:
- Robust clause splitting (separators removed)
- Flexible template -> regex conversion (spaces -> \\s+, optional articles)
- Fuzzy matching compares clause to placeholder-free template
- Try template-based extraction after fuzzy hit
- Hot-reload supports async/sync repository get_all_functions
- Metrics increments and better logging
"""
import re
import time
import threading
import inspect
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, TYPE_CHECKING, cast

try:
    from rapidfuzz import fuzz
    fuzzy_available = True
except ImportError:
    fuzz = None
    fuzzy_available = False

from app.models.rule_engine_models import RuleEngineConfig, RuleEngineMetrics
from app.core.logger import logger

# TYPE_CHECKING import to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.core.dictionary_repository import DictionaryRepository
    from app.models.dictionary_models import DictionaryFunction


class EnhancedRuleEngine:
    def __init__(self, dictionary_repository: Optional['DictionaryRepository'] = None, config: Optional[RuleEngineConfig] = None):
        self.config = config or RuleEngineConfig()
        self.dictionary_repository = dictionary_repository
        self._lock = threading.RLock()
        self._patterns: List[Dict[str, Any]] = []
        self._functions: List['DictionaryFunction'] = []
        self._metrics = RuleEngineMetrics(
            total_parses=0,
            successful_parses=0,
            failed_parses=0,
            average_parse_time_ms=0.0,
            average_candidates_per_parse=0.0,
            active_patterns=0,
            patterns_tried=0,
            compilation_failures=0,
            last_hot_reload=None,
            exact_match_rate=0.0,
            fuzzy_match_rate=0.0,
            heuristic_match_rate=0.0,
            unresolved_rate=0.0
        )

        # Clause splitter: separators to split on (these are removed)
        separators = [
            r'\bthen\b', r'\band then\b', r';', r',', r'\bafter\b',
            r'\bonce\b', r'\bwhen\b', r'\bif\b', r'\bbefore\b'
        ]
        self._clause_splitter_re = re.compile(r'(?:' + r'|'.join(separators) + r')', flags=re.IGNORECASE)

        self._init_synonyms()
        self._init_extractors()
        logger.info("EnhancedRuleEngine initialized (reworked)")

    # ---------- init helpers ----------
    def _init_synonyms(self) -> None:
        self._synonyms: Dict[str, Dict[str, Any]] = {
            'login': {'canonical': 'login', 'terms': {'sign in', 'log in', 'authenticate'}, 'boost': 0.08},
            'click': {'canonical': 'click', 'terms': {'press', 'tap', 'select', 'choose', 'hit'}, 'boost': 0.06},
            'type': {'canonical': 'type', 'terms': {'enter', 'input', 'fill', 'write', 'insert'}, 'boost': 0.06},
            'upload': {'canonical': 'upload', 'terms': {'attach', 'add file', 'browse', 'select file'}, 'boost': 0.08},
            'verify': {'canonical': 'verify', 'terms': {'check', 'confirm', 'validate', 'ensure', 'assert'}, 'boost': 0.06},
            'navigate': {'canonical': 'navigate', 'terms': {'go to', 'visit', 'open', 'browse to'}, 'boost': 0.08},
        }

    def _init_extractors(self) -> None:
        self._extractors: Dict[str, re.Pattern[str]] = {
            'url': re.compile(r'https?://[^\s,;]+|www\.[^\s,;]+', re.IGNORECASE),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'file': re.compile(r'\b[\w\-\s]+\.(?:csv|pdf|xls|xlsx|txt|json)\b', re.IGNORECASE),
            'number': re.compile(r'\b\d+(?:\.\d+)?\b'),
            # selector: match #id, .class, or "text" or words followed by 'button'/'link'
            'selector': re.compile(r'(#[-\w]+|\.[-\w]+|"(?:[^"]+)"|\'(?:[^\']+)\'|\b[\w-]+(?: button| link| input| field)?\b)', re.IGNORECASE),
            'username': re.compile(r'\b(?:username|user)\s+([A-Za-z0-9_.-]+)', re.IGNORECASE),
            'password': re.compile(r'\b(?:password|pass|pwd)\s+([^\s,;]+)', re.IGNORECASE),
        }

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty parse result."""
        return {
            'steps': [],
            'unresolved_tokens': [],
            'overall_confidence': 0.0,
            'processing_time_ms': 0.0,
            'metadata': {
                'clauses_processed': 0,
                'patterns_tried': 0,
                'engine_version': 'enhanced_v2',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }

    # ---------- public API ----------
    def parse(self, text: str) -> Dict[str, Any]:
        start = time.time()
        if not text or not text.strip():
            return self._empty_result()

        logger.debug("Parsing: %s", text[:200])
        clauses = self._split_clauses(text)
        steps: List[Dict[str, Any]] = []
        unresolved: List[str] = []
        total_conf = 0.0

        for idx, clause in enumerate(clauses):
            clause_text = clause.strip()
            clause_info: Dict[str, Any] = {'text': clause_text, 'order': idx + 1, 'context': self._detect_context(clause_text)}
            candidates = self._process_clause(clause_info)

            # collect candidates; if multiple, keep them (downstream ranker will choose)
            if candidates:
                for c in candidates:
                    if 'function' in c:
                        steps.append(c)
                        total_conf += float(c.get('confidence', 0.0))
                    elif 'unresolved' in c:
                        unresolved.extend(c.get('unresolved', []))
            else:
                unresolved.append(clause_text)

        steps.sort(key=lambda s: s.get('order', 0))
        # dedupe near-identical steps (helps fix repeated type calls)
        steps = self._dedupe_steps(steps)
        overall_conf = (total_conf / len(steps)) if steps else 0.0
        elapsed_ms = (time.time() - start) * 1000.0
        self._update_metrics(len(steps), elapsed_ms, len(clauses))

        result: Dict[str, Any] = {
            'status': 'success' if steps else 'no_match',
            'steps': steps,
            'candidates': steps,  # For backwards compatibility
            'unresolved_tokens': list(dict.fromkeys(unresolved)),
            'overall_confidence': round(overall_conf, 3),
            'confidence': round(overall_conf, 3),  # For backwards compatibility
            'processing_time_ms': round(elapsed_ms, 2),
            'metadata': {
                'clauses_processed': len(clauses),
                'patterns_tried': self._metrics.patterns_tried,
                'engine_version': 'enhanced_v2',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
        logger.debug("Parse result: steps=%d unresolved=%d conf=%s", len(steps), len(unresolved), result['overall_confidence'])
        return result

    def hot_reload(self) -> Dict[str, Any]:
        logger.info("Hot reload invoked")
        try:
            if not self.dictionary_repository:
                return {'success': False, 'error': 'no repository'}

            # Handle both sync and async repository methods
            funcs: Any = None
            if hasattr(self.dictionary_repository, 'get_all_functions'):
                funcs = self.dictionary_repository.get_all_functions()  # type: ignore[attr-defined]
            elif hasattr(self.dictionary_repository, 'list_all_active_functions'):
                funcs = self.dictionary_repository.list_all_active_functions()
            else:
                return {'success': False, 'error': 'Repository does not have required method'}
                
            # if repository returns coroutine, await it
            if inspect.iscoroutine(funcs):  # type: ignore[arg-type]
                # caller should call hot_reload asynchronously; keep fallback to raise informative error
                raise RuntimeError("dictionary_repository method returned coroutine; call async hot_reload instead")

            with self._lock:
                self._functions = cast(List['DictionaryFunction'], funcs)
                self._compile_patterns()
                self._metrics.last_hot_reload = datetime.now(timezone.utc)

            return {'success': True, 'functions_loaded': len(self._functions)}
        except Exception as e:
            logger.exception("Hot reload failed: %s", e)
            return {'success': False, 'error': str(e)}

    # ---------- internal helpers ----------
    def _split_clauses(self, text: str) -> List[str]:
        """
        Improved clause splitter:
        - Splits on separators but avoids splitting 'username and password' style phrases.
        - Splits on 'and' only when followed by an action verb (then, go, open, click, enter, type, upload, verify, select, wait).
        - Avoids splitting multi-select patterns like "select multiple options apple, banana from..."
        """
        # Normalize whitespace
        txt = re.sub(r'\s+', ' ', text.strip())

        # Check if this looks like a multi-select pattern - if so, don't split
        multi_select_pattern = r'\bselect\s+multiple\s+options?\s+[^,\s]+(?:\s*,\s*[^,\s]+)*\s+from\s+'
        if re.search(multi_select_pattern, txt, flags=re.IGNORECASE):
            return [txt]  # Don't split multi-select patterns

        # Separator pattern: 'then', ';', ',', 'after', 'once', 'when', 'if', 'before' OR 'and' only if followed by action verb
        action_verbs = r'(?:then|go|open|visit|navigate|browse|click|press|enter|type|fill|input|upload|attach|verify|check|uncheck|tick|untick|select|choose|wait|ensure|assert|expect|download|submit|save|delete|remove|add|create|edit|update|modify|refresh|reload|scroll|swipe|drag|drop|hover|focus|blur|clear|reset|login|logout|sign|authenticate|filter|sort|search|find|copy|paste|cut|dismiss|close|take|capture|screenshot|get|set|make|call|post|put|patch)'
        splitter = re.compile(
            rf'(?:\b(?:then|after|once|when|if|before)\b|;|,|\band\b(?=\s+{action_verbs}\b))',
            flags=re.IGNORECASE
        )

        parts = [p.strip() for p in splitter.split(txt) if p and p.strip()]
        final: List[str] = []
        for p in parts:
            # further break on full stops / newlines but keep abbreviations and CSS selectors intact
            # Split on periods that end sentences (word + period + space + capital) but preserve CSS selectors
            for sub in re.split(r'(?<=\w)\.\s+(?=[A-Z])|[\n]+', p):
                s = sub.strip()
                if s:
                    final.append(s)
        return final if final else [text.strip()]

    def _detect_context(self, clause: str) -> Optional[str]:
        low = clause.lower()
        for ctx, keywords in {'after': ['after', 'once'], 'when': ['when', 'whenever'], 'if': ['if', 'provided', 'assuming'], 'before': ['before', 'prior to']}.items():
            if any(k in low for k in keywords):
                return ctx
        return None

    def _process_clause(self, clause_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = clause_info['text']
        # Exact match first
        exact = self._exact_match(text, clause_info)
        if exact:
            return exact
        # Fuzzy
        fuzzy = []
        if fuzzy_available:
            fuzzy = self._fuzzy_match(text, clause_info)
            if fuzzy:
                return fuzzy
        # Heuristic
        heuristic = self._heuristic_match(text, clause_info)
        if heuristic:
            return heuristic
        # unresolved
        return [{'unresolved': [text], 'order': clause_info['order']}]

    def _exact_match(self, text: str, clause_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        matches: List[Dict[str, Any]] = []
        with self._lock:
            patterns = list(self._patterns)
        for entry in patterns:
            self._metrics.patterns_tried += 1
            try:
                m = entry['regex'].search(text)
                if m:
                    args = self._extract_args(m, entry.get('signature', {}))
                    confidence = self._calculate_confidence(entry, m, text, args, exact=True)
                    matches.append({
                        'function': entry['function_name'],
                        'args': args,
                        'confidence': round(min(confidence, 0.99), 3),
                        'provenance': 'rule_exact',
                        'template': entry.get('template', ''),
                        'order': clause_info['order'],
                        'matched_text': m.group(0),
                        'context': clause_info.get('context')
                    })
                    logger.debug("Exact match: func=%s template=%s groups=%s conf=%s", 
                               entry.get('function_name'), entry.get('template'), m.groupdict(), confidence)
                    self._metrics.exact_match_rate += 1
            except re.error as e:
                logger.warning("Regex error for template %s: %s", entry.get('template'), e)
                continue
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        return matches[:3]

    def _fuzzy_match(self, text: str, clause_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        matches: List[Dict[str, Any]] = []
        txt_mod = self._apply_synonyms(text).lower()
        with self._lock:
            patterns = list(self._patterns)
        for entry in patterns:
            template = entry.get('template', '')
            # compute comparable template by removing placeholders and extra punctuation
            template_plain = re.sub(r'\{[^}]+\}', '', template).strip().lower()
            # collapse multiple spaces
            template_plain = re.sub(r'\s+', ' ', template_plain)
            score = (fuzz.partial_ratio(txt_mod, template_plain) / 100.0) if fuzzy_available and fuzz else 0.0
            self._metrics.patterns_tried += 1
            if score >= self.config.fuzzy_threshold:
                # attempt to extract args via template-based regex if possible
                args = {}
                try:
                    # try regex extraction using the compiled regex (may succeed even if fuzzy matched)
                    m = entry['regex'].search(text)
                    if m:
                        args = self._extract_args(m, entry.get('signature', {}))
                except Exception:
                    args = self._extract_args_heuristic(text)
                # base confidence scaled from score with small boost
                base_conf = score * 0.85 + 0.05
                base_conf += self._get_synonym_boost(text, entry['function_name'])
                if base_conf >= self.config.min_fuzzy_confidence:
                    matches.append({
                        'function': entry['function_name'],
                        'args': args,
                        'confidence': round(min(base_conf, 0.89), 3),
                        'provenance': 'rule_fuzzy',
                        'template': template,
                        'order': clause_info['order'],
                        'similarity': round(score, 3),
                        'context': clause_info.get('context')
                    })
                    logger.debug("Fuzzy match: func=%s template=%s score=%s args=%s conf=%s", 
                               entry.get('function_name'), template, score, args, base_conf)
                    self._metrics.fuzzy_match_rate += 1
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        return matches[:3]

    def _heuristic_match(self, text: str, clause_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        matches: List[Dict[str, Any]] = []
        low = text.lower()

        # AS_USER context: "As admin" or "As guest" - should be first to set user context
        as_user_match = re.search(r'\bas\s+(?P<role>admin|guest|user|administrator|moderator|editor|viewer|\w+)', text, flags=re.IGNORECASE)
        if as_user_match:
            role = as_user_match.group('role')
            matches.append({
                'function': 'as_user',
                'args': {'role': role},
                'confidence': 0.85,
                'provenance': 'heuristic_as_user',
                'template': 'heuristic_as_user',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            # Don't return - continue to find additional actions in the same clause

        # FILE upload
        f = self._extractors['file'].search(text)
        if f and any(k in low for k in ['upload', 'attach', 'file', 'add file']):
            matches.append({
                'function': 'upload_file',
                'args': {'file': f.group(0)},
                'confidence': 0.88,
                'provenance': 'heuristic_file',
                'template': 'heuristic_upload',
                'order': clause_info['order']
            })
            logger.debug("Heuristic file match: file=%s text=%s", f.group(0), text)
            self._metrics.heuristic_match_rate += 1
            return matches  # file upload is usually a single action

        # URL open - enhanced to handle URLs without protocol and paths
        u = self._extractors['url'].search(text)
        url_without_protocol = None
        path_url = None
        
        if not u and any(k in low for k in ['navigate', 'go to', 'open', 'visit', 'browse']):
            # Try to match domain.com/path patterns without http://
            url_match = re.search(r'\b([a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)\b', text)
            if url_match:
                url_without_protocol = url_match.group(1)
            else:
                # Also check for path patterns like "/settings" or relative paths
                path_match = re.search(r'/[/\w\-\.]+', text)
                if path_match:
                    path_url = path_match.group(0)
        
        if (u or url_without_protocol or path_url) and any(k in low for k in ['open', 'go to', 'visit', 'navigate', 'browse']):
            if u:
                url_value = self._clean_url(u.group(0))
            elif url_without_protocol:
                url_value = f'https://{url_without_protocol}'
            else:
                url_value = path_url  # Keep path as-is for relative URLs
            
            matches.append({
                'function': 'open_url',
                'args': {'url': url_value},
                'confidence': 0.92,
                'provenance': 'heuristic_url',
                'template': 'heuristic_url',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            # do not return; allow additional actions in same clause (e.g., "go to X and click Y")
        
        # GENERIC SITE open: "open site", "open admin panel", "open dashboard" - without specific URL
        if re.search(r'\b(?:open|visit|go\s+to|navigate\s+to|browse\s+to)\s+(?:the\s+)?(?:site|admin\s*panel|dashboard|settings?|page)\b', text, flags=re.IGNORECASE) and not (u or url_without_protocol or path_url):
            matches.append({
                'function': 'open_url',
                'args': {'url': 'https://example.com'},  # Placeholder URL
                'confidence': 0.75,  # Lower confidence since no specific URL
                'provenance': 'heuristic_generic_site',
                'template': 'heuristic_generic_site',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            # do not return; allow additional actions in same clause
        
        # FILL / TYPE patterns: "enter VALUE in the SELECTOR" or "type VALUE into SELECTOR" or "fill SELECTOR with VALUE"
        m_fill = re.search(
            r'\b(?:enter|type|fill|input|write|insert)\s+(?P<value>["\']?[^,"\']+["\']?)\s+(?:in|into|into the|in the|at|with)\s+(?P<selector>.+)$',
            text, flags=re.IGNORECASE)
        if not m_fill:
            # Try alternative pattern: "fill SELECTOR with VALUE"
            m_fill = re.search(
                r'\b(?:fill)\s+(?P<selector>[^,]+?)\s+(?:with)\s+(?P<value>["\']?[^,"\']+["\']?)$',
                text, flags=re.IGNORECASE)
        if m_fill:
            sel = m_fill.group('selector').strip()
            val = m_fill.group('value').strip().strip('\'"')
            matches.append({
                'function': 'fill',
                'args': {'selector': self._clean_selector(sel), 'value': val},
                'confidence': 0.92,
                'provenance': 'heuristic_fill',
                'template': 'heuristic_fill',
                'order': clause_info['order']
            })
            logger.debug("Heuristic fill match: selector=%s value=%s text=%s", sel, val, text)
            self._metrics.heuristic_match_rate += 1
            return matches

        # MULTI_SELECT patterns: "Select multiple options apple, banana from #fruits multi-select" (check BEFORE single select)
        multi_select_match = re.search(r'\bselect\s+multiple\s+options?\s+([^,\s]+(?:\s*,\s*[^,\s]+)*)\s+from\s+([#.\w\-\[\]\'"\s]+)', text, flags=re.IGNORECASE)
        if multi_select_match:
            options_str = multi_select_match.group(1)
            selector = multi_select_match.group(2).strip()
            
            # Parse comma-separated options
            options = [opt.strip() for opt in options_str.split(',')]
            
            matches.append({
                'function': 'multi_select',
                'args': {'selector': selector, 'options': options},
                'confidence': 0.86,
                'provenance': 'heuristic_multi_select',
                'template': 'heuristic_multi_select',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # ELEMENT STATE CHECKS: "expect #element to be enabled/disabled" or "expect #element enabled"
        # Process before search patterns to avoid "#search" being treated as search query
        state_match = re.search(r'\bexpect\s+(?P<selector>[#.\w-]+)\s+(?:to\s+be\s+)?(?P<state>enabled|disabled|visible|hidden)', text, flags=re.IGNORECASE)
        if state_match:
            state = state_match.group('state').lower()
            function_name = f'expect_{state}'
            matches.append({
                'function': function_name,
                'args': {
                    'selector': state_match.group('selector')
                },
                'confidence': 0.85,
                'provenance': 'heuristic_element_state',
                'template': 'heuristic_element_state',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # SEARCH patterns: "search for 'laptop'" or "search 'product name'"
        # Exclude cases like "click search button" where search refers to UI element
        search_match = re.search(r'\bsearch\s+(?:for\s+)?(?P<value>["\']?[^,"\']+["\']?)(?!\s+(?:button|box|field|input|element))', text, flags=re.IGNORECASE)
        if search_match and not re.search(r'\b(?:click|press|tap)\s+.*search\s+button', text, flags=re.IGNORECASE):
            val = search_match.group('value').strip().strip('\'"')
            matches.append({
                'function': 'type',
                'args': {'selector': '"search box"', 'value': val},
                'confidence': 0.85,
                'provenance': 'heuristic_search',
                'template': 'heuristic_search',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # QUANTITY patterns: "set quantity to 2" or "set quantity to N"
        quantity_match = re.search(r'\bset\s+quantity\s+to\s+(?P<value>\d+)', text, flags=re.IGNORECASE)
        if quantity_match:
            val = quantity_match.group('value')
            matches.append({
                'function': 'type',
                'args': {'selector': '"quantity"', 'value': val},
                'confidence': 0.85,
                'provenance': 'heuristic_quantity',
                'template': 'heuristic_quantity',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # CHECKOUT patterns: "checkout" or "check out"
        if re.search(r'\b(?:checkout|check\s+out)\b', text, flags=re.IGNORECASE):
            matches.append({
                'function': 'click',
                'args': {'selector': '"checkout"'},
                'confidence': 0.85,
                'provenance': 'heuristic_checkout',
                'template': 'heuristic_checkout',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # SELECT dropdown: "select India from country dropdown" OR "choose India in country" (check before click)
        m_select = re.search(r'\b(?:select|choose)\s+(?P<value>[^,]+?)\s+(?:from|in|in the|from the)\s+(?P<selector>.+)', text, flags=re.IGNORECASE)
        if m_select:
            val = m_select.group('value').strip().strip('\'"')
            sel = m_select.group('selector').strip()
            matches.append({
                'function': 'select_dropdown',
                'args': {'selector': self._clean_selector(sel), 'value': val},
                'confidence': 0.88,
                'provenance': 'heuristic_select',
                'template': 'heuristic_select',
                'order': clause_info['order']
            })
            logger.debug("Heuristic select match: selector=%s value=%s text=%s", sel, val, text)
            self._metrics.heuristic_match_rate += 1
            return matches

        # KEYBOARD ACTIONS: "press Enter", "press Ctrl+S", "press Tab key" (check before click pattern)
        key_match = re.search(r'\b(?:press|hit|tap)\s+(?:the\s+)?(?P<key>Enter|Tab|Escape|Space|Ctrl\+\w+|Alt\+\w+|Shift\+\w+|\w+\s+key)\b', text, flags=re.IGNORECASE)
        if key_match:
            key = key_match.group('key').strip()
            if key.lower().endswith(' key'):
                key = key[:-4].strip()  # Remove ' key' suffix
            matches.append({
                'function': 'press_key',
                'args': {'key': key},
                'confidence': 0.90,
                'provenance': 'heuristic_press_key',
                'template': 'heuristic_press_key',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # CLICK action: "click the login button" or "click #submit" or "click on the profile link"
        # NOTE: Exclude keyboard keys from click pattern
        m_click = re.search(r'\b(?:click|tap|choose|hit)\s+(?:on\s+)?(?:the\s+)?(?P<selector>.+)', text, flags=re.IGNORECASE)
        # Additional check to exclude keyboard keys
        if m_click and not re.search(r'\b(?:Enter|Tab|Escape|Space|Ctrl\+\w+|Alt\+\w+|Shift\+\w+|\w+\s+key)\b', text, flags=re.IGNORECASE):
            sel = m_click.group('selector').strip()
            # Try to extract selector token (#id or .class or quoted text)
            sel_m = self._extractors['selector'].search(sel)
            selector_val = sel_m.group(0) if sel_m else sel
            matches.append({
                'function': 'click',
                'args': {'selector': self._clean_selector(selector_val)},
                'confidence': 0.9,
                'provenance': 'heuristic_click',
                'template': 'heuristic_click',
                'order': clause_info['order']
            })
            logger.debug("Heuristic click match: selector=%s text=%s", selector_val, text)
            self._metrics.heuristic_match_rate += 1
            return matches

        # SPECIALIZED VERIFICATION patterns (check BEFORE generic check patterns)
        
        # EXPORT ACTIONS: "export csv", "export to pdf", "download report"  
        export_match = re.search(r'\b(?:export|download)\s+(?:(?:to\s+)?(?P<format>csv|pdf|excel|json|xml|report))?(?:\s+(?:file|data|report))?', text, flags=re.IGNORECASE)
        if export_match:
            format_type = export_match.group('format') if export_match.group('format') else 'csv'
            # For exports, we typically click an export button or make an API call
            matches.append({
                'function': 'click',
                'args': {'selector': f'[data-export="{format_type}"], .export-{format_type}, #export-{format_type}, .export, #export'},
                'confidence': 0.82,
                'provenance': 'heuristic_export',
                'template': 'heuristic_export', 
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # DOWNLOAD VERIFY: "Check X was downloaded within Y seconds", "verify file.pdf downloaded", "verify file downloaded"
        download_match = re.search(r'\b(?:check|verify|ensure)\s+(?:(?P<filename>[^\s]+(?:\.[a-zA-Z]+)?)\s+(?:was\s+)?|file\s+)downloaded(?:\s+within\s+\d+\s+seconds)?', text, flags=re.IGNORECASE)
        if download_match:
            filename = download_match.group('filename') if download_match.group('filename') else 'file'
            matches.append({
                'function': 'download_verify',
                'args': {'filename': filename},
                'confidence': 0.86,
                'provenance': 'heuristic_download_verify',
                'template': 'heuristic_download_verify',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # EXPECT_LOGGED_IN: "verify user is logged in", "check user logged in", "ensure logged in"
        logged_in_match = re.search(r'\b(?:verify|check|ensure|confirm)\s+(?:(?:that\s+)?(?:user\s+is\s+)?|(?:user\s+)?)logged\s+in', text, flags=re.IGNORECASE)
        if logged_in_match:
            matches.append({
                'function': 'expect_logged_in',
                'args': {},
                'confidence': 0.87,
                'provenance': 'heuristic_logged_in',
                'template': 'heuristic_logged_in',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # TABLE_EXPECT_CELL: "Check row X in #table column Y is Z"
        table_cell_match = re.search(r'\b(?:check|verify|ensure)\s+row\s+(\d+)\s+in\s+([#.\w\-\[\]\'"\s]+)\s+column\s+(\w+)\s+is\s+(\w+)', text, flags=re.IGNORECASE)
        if table_cell_match:
            row = int(table_cell_match.group(1))
            table_selector = table_cell_match.group(2).strip()
            column = table_cell_match.group(3)
            expected = table_cell_match.group(4)
            
            matches.append({
                'function': 'table_expect_cell',
                'args': {'selector': table_selector, 'row': row, 'column': column, 'expected': expected},
                'confidence': 0.86,
                'provenance': 'heuristic_table_cell',
                'template': 'heuristic_table_cell',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # ACCESS CONTROL expectations: "verify access granted" or "check permission denied"
        # Place before general CHECK pattern to avoid conflicts
        if re.search(r'\b(?:verify|check|ensure|confirm)\s+(?:access\s+)?(?:granted|allowed|permitted)', text, flags=re.IGNORECASE):
            matches.append({
                'function': 'expect_access_granted',
                'args': {},
                'confidence': 0.86,
                'provenance': 'heuristic_access_granted',
                'template': 'heuristic_access_granted',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        if re.search(r'\b(?:check|verify|ensure|confirm)\s+(?:permission\s+)?(?:denied|forbidden|unauthorized|not\s+allowed)', text, flags=re.IGNORECASE):
            matches.append({
                'function': 'expect_access_denied',
                'args': {},
                'confidence': 0.86,
                'provenance': 'heuristic_access_denied',
                'template': 'heuristic_access_denied',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # CHECK / UNCHECK: "check the terms checkbox" or "uncheck newsletter" (exclude title checks)
        check_pattern = r'\bcheck\s+(?:the\s+)?(?P<target>(?:.*(?:checkbox|button|option|field|element|box)|(?!title\s)(?!that\s).+))'
        if re.search(check_pattern, text, flags=re.IGNORECASE) and not re.search(r'\btitle\s+(?:is|contains)', text, flags=re.IGNORECASE):
            tgt = re.sub(r'check\s+', '', text, flags=re.IGNORECASE).strip()
            matches.append({
                'function': 'check',
                'args': {'selector': self._clean_selector(tgt)},
                'confidence': 0.85,
                'provenance': 'heuristic_check',
                'template': 'heuristic_check',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches
        if re.search(r'\buncheck\s+(?:the\s+)?(?P<target>.+)', text, flags=re.IGNORECASE):
            tgt = re.sub(r'uncheck\s+', '', text, flags=re.IGNORECASE).strip()
            matches.append({
                'function': 'uncheck',
                'args': {'selector': self._clean_selector(tgt)},
                'confidence': 0.85,
                'provenance': 'heuristic_uncheck',
                'template': 'heuristic_uncheck',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # WAIT / ASSERT: "wait for spinner to disappear" "verify Welcome message appears"
        # First check for disappearing elements (exclude "load" which should be "appear")
        if re.search(r'\bwait for\b', low) and re.search(r'\b(disappear|be gone|gone|stop)\b', low):
            # try to extract the element
            spinner = re.search(r'wait for\s+(?P<selector>[^,]+?)\s+(?:to\s+)?(?:disappear|gone|hide|remove)', text, flags=re.IGNORECASE)
            sel = spinner.group('selector').strip() if spinner else 'spinner'
            matches.append({
                'function': 'wait_for_invisible',
                'args': {'selector': self._clean_selector(sel), 'timeout': 10000},
                'confidence': 0.86,
                'provenance': 'heuristic_wait',
                'template': 'heuristic_wait_invisible',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # WAIT FOR VISIBLE: "wait until table appears", "wait for element to appear", "ensure modal appears"
        if (re.search(r'\b(wait|ensure)\b', low) and re.search(r'\b(appear|visible|show|load|display)', low)) or \
           re.search(r'\bwait\s+(for|until)\b', low) or re.search(r'\bshows?\s+up\b', low):
            # Extract the element: "wait until table appears", "wait for modal to appear"
            visible_patterns = [
                # More specific patterns first
                r'wait\s+(?:for|until)\s+(?:the\s+)?(?P<selector>[\w\s]+?)\s+to\s+(?:appear|be\s+visible|show\s+up?|load|display)',
                r'wait\s+(?:for|until)\s+(?:the\s+)?(?P<selector>[\w\s]+?)\s+(?:appear|be\s+visible|show\s+up?|load|display|is\s+visible)',
                # More general patterns
                r'(?:wait\s+(?:until|for)|ensure(?:\s+that)?)\s+(?:the\s+)?(?P<selector>[^,]+?)\s+(?:appears?|is\s+visible|shows?\s+up?|loads?|displays?)',
                r'(?:ensure|verify)\s+(?:that\s+)?(?:the\s+)?(?P<selector>[^,]+?)\s+(?:appears?|is\s+visible|shows?\s+up?)'
            ]
            sel = None
            for pattern in visible_patterns:
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match:
                    sel = match.group('selector').strip()
                    break
            
            if sel:
                matches.append({
                    'function': 'wait_for_visible',
                    'args': {'selector': self._clean_selector(sel), 'timeout': 10000},
                    'confidence': 0.85,
                    'provenance': 'heuristic_wait',
                    'template': 'heuristic_wait_visible',
                    'order': clause_info['order']
                })
                self._metrics.heuristic_match_rate += 1
                return matches

        # TITLE ASSERTIONS: "title should contain X", "assert title is X", "check title contains Y"
        # First check for "title should contain" format
        title_should_match = re.search(r'\btitle\s+should\s+(?:contain|include|have)\s+["\']?(?P<title>[^"\']+)["\']?', text, flags=re.IGNORECASE)
        if title_should_match:
            title = title_should_match.group('title').strip()
            matches.append({
                'function': 'expect_title',
                'args': {'expected': title},
                'confidence': 0.88,
                'provenance': 'heuristic_title_should',
                'template': 'heuristic_title_should',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches
            
        # Standard title patterns: "assert title is X", "check title contains Y" (check before general text)
        title_match = re.search(r'\b(?:assert|check|verify|ensure)\s+(?:that\s+)?(?:the\s+)?title\s+(?:is|contains|equals)\s+["\']?(?P<title>[^"\']+)["\']?', text, flags=re.IGNORECASE)
        if title_match:
            title = title_match.group('title').strip()
            matches.append({
                'function': 'expect_title',
                'args': {'expected': title},
                'confidence': 0.88,
                'provenance': 'heuristic_title',
                'template': 'heuristic_title',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # API REQUESTS: "make get request to /api/users", "post to api endpoint /submit", "send PUT request"
        api_patterns = [
            r'(?:make|send)\s+(?P<method>GET|POST|PUT|DELETE|PATCH)\s+request\s+to\s+(?P<url>[^\s,]+)',
            r'(?P<method>post|get|put|delete|patch)\s+to\s+(?:api\s+endpoint\s+)?(?P<url>[^\s,]+)',
            r'(?:call|invoke)\s+(?:api\s+endpoint\s+)?(?P<url>[^\s,]+)(?:\s+(?:with|using)\s+(?P<method>GET|POST|PUT|DELETE|PATCH))?',
            r'(?:make|send)\s+(?P<method>GET|POST|PUT|DELETE|PATCH)\s+(?:request|call)(?:\s+to\s+(?P<url>[^\s,]+))?'
        ]
        
        for pattern in api_patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                method = match.group('method').upper() if match.group('method') else 'GET'
                # Handle cases where URL is not explicitly specified or is nonsensical 
                url_candidate = match.group('url') if 'url' in match.groupdict() and match.group('url') else None
                
                # Skip if URL looks like a non-URL word (e.g., "with", "data", "payload")
                if url_candidate and url_candidate.lower() in ['with', 'data', 'payload', 'json', 'body']:
                    url_candidate = None
                
                url = url_candidate or '/api'  # Default fallback
                
                # Determine function name based on method
                if method in ['GET']:
                    function_name = 'api_get'
                elif method in ['POST']:
                    function_name = 'api_post'
                elif method in ['PUT']:
                    function_name = 'api_put'
                elif method in ['DELETE']:
                    function_name = 'api_delete'
                else:
                    function_name = 'api_get'  # default fallback
                
                matches.append({
                    'function': function_name,
                    'args': {'url': url},
                    'confidence': 0.86,
                    'provenance': 'heuristic_api',
                    'template': 'heuristic_api',
                    'order': clause_info['order']
                })
                self._metrics.heuristic_match_rate += 1
                return matches

        # TOAST expectations: "verify 'Success' toast appears" or "verify toast says 'Saved'"
        toast_match = re.search(r'\b(?:verify|check|ensure|confirm)\s+(?:.*?)?(?P<message>["\']?[^"\']+["\']?)\s*(?:toast|notification|message)\s+(?:appears?|says?|shows?|is\s+(?:shown|displayed))', text, flags=re.IGNORECASE)
        if not toast_match:
            # Try alternative pattern: "verify toast success says 'Saved'"
            toast_match = re.search(r'\b(?:verify|check|ensure|confirm)\s+(?:toast|notification|message)\s+(?:.*?)?(?:says?|shows?|contains?)\s+(?P<message>["\']?[^"\']+["\']?)', text, flags=re.IGNORECASE)
        if toast_match:
            message = toast_match.group('message').strip().strip('\'"')
            matches.append({
                'function': 'expect_toast',
                'args': {'message': message},
                'confidence': 0.86,
                'provenance': 'heuristic_expect_toast',
                'template': 'heuristic_expect_toast',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # ELEMENT COUNT: "ensure it has at least 1 row", "verify 3 elements exist", "check that there are 5 items"
        # Also handle CSS selectors: "verify 3 .row elements exist in #results"
        # Process before general text expectations to avoid being caught by expect_text
        count_patterns = [
            # CSS selector based: "verify 3 .row elements exist" or "verify 3 .row elements exist in #results"  
            r'(?:ensure|verify|check|assert)\s+(?P<count>\d+)\s+(?P<selector>[#.\w\-]+)\s+elements?\s+exist(?:\s+in\s+[#.\w\-]+)?',
            r'(?:ensure|verify|check|assert)\s+(?:that\s+)?(?:it\s+)?(?:has|there\s+are)\s+(?:at\s+least\s+)?(?P<count>\d+)\s+(?P<element>\w+)',
            r'(?:ensure|verify|check|assert)\s+(?P<count>\d+)\s+(?P<element>\w+)\s+(?:exist|are\s+present|are\s+shown)',
            r'(?:ensure|verify|check|assert)\s+(?:at\s+least\s+)?(?P<count>\d+)\s+(?P<element>\w+)',
        ]
        
        for i, pattern in enumerate(count_patterns):
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                count = match.group('count')
                
                # First pattern captures CSS selectors directly
                if i == 0 and 'selector' in match.groupdict():
                    element_selector = match.group('selector')
                else:
                    # Other patterns use element names
                    element = match.group('element')
                    # Create more appropriate selectors for common element types
                    if element.lower() == 'row':
                        element_selector = 'tr, [data-testid*="row"], .row'
                    elif element.lower() == 'button':
                        element_selector = 'button, [type="button"], [role="button"]'
                    elif element.lower() in ['item', 'items']:
                        element_selector = '.item, [data-testid*="item"], li'
                    elif element.lower() in ['result', 'results']:
                        element_selector = '.result, [data-testid*="result"], .search-result'
                    elif element.lower() in ['element', 'elements']:
                        element_selector = '[data-testid], .element'
                    else:
                        element_selector = f'[data-testid*="{element}"], .{element}'
                
                matches.append({
                    'function': 'expect_element_count',
                    'args': {'selector': element_selector, 'count': int(count)},
                    'confidence': 0.87,
                    'provenance': 'heuristic_count',
                    'template': 'heuristic_count',
                    'order': clause_info['order']
                })
                self._metrics.heuristic_match_rate += 1
                return matches

        # VERIFY / EXPECT text presence - allow "X appears" for text verification, but exclude standalone element visibility
        m_expect = re.search(r'\b(?:verify|check|ensure|confirm|assert)\s+(?:that\s+)?(?P<target>.+?)(?:\s+(?:is present|appears?))?$', text, flags=re.IGNORECASE)
        if m_expect:
            tgt = m_expect.group('target').strip().strip('\'"')
            # if it's a short phrase, assume expect_text, else maybe expect_visible selector
            if len(tgt.split()) <= 6:
                matches.append({
                    'function': 'expect_text',
                    'args': {'selector': 'body', 'expected': tgt},
                    'confidence': 0.88,
                    'provenance': 'heuristic_expect_text',
                    'template': 'heuristic_expect_text',
                    'order': clause_info['order']
                })
            else:
                matches.append({
                    'function': 'expect_visible',
                    'args': {'selector': self._clean_selector(tgt)},
                    'confidence': 0.86,
                    'provenance': 'heuristic_expect_visible',
                    'template': 'heuristic_expect_visible',
                    'order': clause_info['order']
                })
            self._metrics.heuristic_match_rate += 1
            return matches





        # VALUE EXPECTATIONS: "expect #email value test@example.com"
        value_match = re.search(r'\bexpect\s+(?P<selector>[#\.\w\-]+)\s+value\s+(?P<value>.+)', text, flags=re.IGNORECASE)
        if value_match:
            selector = value_match.group('selector').strip()
            value = value_match.group('value').strip()
            matches.append({
                'function': 'expect_value',
                'args': {'selector': self._clean_selector(selector), 'expected': value},
                'confidence': 0.85,
                'provenance': 'heuristic_expect_value',
                'template': 'heuristic_expect_value',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # URL EXPECTATIONS: "expect url contains /dashboard"
        url_expect_match = re.search(r'\bexpect\s+url\s+(?:contains|includes)\s+(?P<url_part>\S+)', text, flags=re.IGNORECASE)
        if url_expect_match:
            url_part = url_expect_match.group('url_part').strip()
            matches.append({
                'function': 'expect_url',
                'args': {'expected': url_part},
                'confidence': 0.85,
                'provenance': 'heuristic_expect_url',
                'template': 'heuristic_expect_url',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # PAGE CONTENT EXPECTATIONS: "expect page contains 'Privacy Policy'"
        page_expect_match = re.search(r'\bexpect\s+page\s+contains\s+["\']?(?P<content>[^"\']+)["\']?', text, flags=re.IGNORECASE)
        if page_expect_match:
            content = page_expect_match.group('content').strip()
            matches.append({
                'function': 'expect_page_contains',
                'args': {'expected': content},
                'confidence': 0.85,
                'provenance': 'heuristic_page_contains',
                'template': 'heuristic_page_contains',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # MODAL/POPUP ACTIONS: "dismiss popup", "close modal"
        modal_match = re.search(r'\b(?:dismiss|close|hide)\s+(?:the\s+)?(?P<target>popup|modal|dialog|confirmation)', text, flags=re.IGNORECASE)
        if modal_match:
            target = modal_match.group('target')
            matches.append({
                'function': 'dismiss_modal',
                'args': {'selector': f'.{target}'},
                'confidence': 0.80,
                'provenance': 'heuristic_dismiss',
                'template': 'heuristic_dismiss',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # SCREENSHOT: "take screenshot", "screenshot as dashboard.png"
        screenshot_match = re.search(r'\btake\s+screenshot|screenshot\s+as\s+(?P<filename>\S+)', text, flags=re.IGNORECASE)
        if screenshot_match:
            filename = screenshot_match.group('filename') if screenshot_match.group().startswith('screenshot') else 'screenshot.png'
            matches.append({
                'function': 'screenshot',
                'args': {'filename': filename},
                'confidence': 0.85,
                'provenance': 'heuristic_screenshot',
                'template': 'heuristic_screenshot',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # COOKIE AND STORAGE PATTERNS: "clear cookies", "set cookie X to Y", "set local storage"
        cookie_clear_match = re.search(r'\bclear\s+cookies?\b', text, flags=re.IGNORECASE)
        if cookie_clear_match:
            matches.append({
                'function': 'clear_cookies',
                'args': {},
                'confidence': 0.87,
                'provenance': 'heuristic_clear_cookies',
                'template': 'heuristic_clear_cookies',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        cookie_set_match = re.search(r'\bset\s+cookie\s+(?P<name>\w+)\s+to\s+(?P<value>[^\s,]+)', text, flags=re.IGNORECASE)
        if cookie_set_match:
            matches.append({
                'function': 'set_cookie',
                'args': {
                    'name': cookie_set_match.group('name'),
                    'value': cookie_set_match.group('value')
                },
                'confidence': 0.87,
                'provenance': 'heuristic_set_cookie',
                'template': 'heuristic_set_cookie',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        storage_match = re.search(r'\bset\s+local\s+storage\s+(?P<key>[\w.]+)\s+to\s+(?P<value>[^\s,]+)', text, flags=re.IGNORECASE)
        if storage_match:
            matches.append({
                'function': 'set_local_storage',
                'args': {
                    'key': storage_match.group('key'),
                    'value': storage_match.group('value')
                },
                'confidence': 0.87,
                'provenance': 'heuristic_local_storage',
                'template': 'heuristic_local_storage',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # TABLE OPERATIONS: "find row in table", "sort table by column"
        table_find_match = re.search(r'\bfind\s+row\s+in\s+(?P<table>[#.\w-]+)\s+where\s+(?P<column>\w+)\s+(?:equals?|is)\s+(?P<value>[^\s,]+)', text, flags=re.IGNORECASE)
        if table_find_match:
            matches.append({
                'function': 'table_find_row',
                'args': {
                    'selector': table_find_match.group('table'),
                    'column': table_find_match.group('column'),
                    'value': table_find_match.group('value')
                },
                'confidence': 0.85,
                'provenance': 'heuristic_table_find',
                'template': 'heuristic_table_find',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        table_sort_match = re.search(r'\bsort\s+(?P<table>[#.\w-]+)\s+by\s+(?P<column>\w+)(?:\s+(?P<order>asc|desc|ascending|descending))?', text, flags=re.IGNORECASE)
        if table_sort_match:
            sort_order = table_sort_match.group('order')
            if sort_order:
                sort_order = 'desc' if sort_order.lower().startswith('desc') else 'asc'
            else:
                sort_order = 'asc'
            
            matches.append({
                'function': 'table_sort',
                'args': {
                    'selector': table_sort_match.group('table'),
                    'column': table_sort_match.group('column'),
                    'order': sort_order
                },
                'confidence': 0.85,
                'provenance': 'heuristic_table_sort',
                'template': 'heuristic_table_sort',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # DRAG AND DROP: "drag X to Y", "drag X onto Y"
        drag_match = re.search(r'\bdrag\s+(?P<source>[\w-]+)\s+(?:to|onto)\s+(?P<target>[\w-]+)', text, flags=re.IGNORECASE)
        if drag_match:
            matches.append({
                'function': 'drag_and_drop',
                'args': {
                    'source': drag_match.group('source'),
                    'target': drag_match.group('target')
                },
                'confidence': 0.83,
                'provenance': 'heuristic_drag_drop',
                'template': 'heuristic_drag_drop',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # SLIDER CONTROL: "set slider X to Y"
        slider_match = re.search(r'\bset\s+slider\s+(?P<selector>[#.\w-]+)\s+to\s+(?P<value>\d+)', text, flags=re.IGNORECASE)
        if slider_match:
            matches.append({
                'function': 'slider_set',
                'args': {
                    'selector': slider_match.group('selector'),
                    'value': int(slider_match.group('value'))
                },
                'confidence': 0.85,
                'provenance': 'heuristic_slider',
                'template': 'heuristic_slider',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # TEXT EXTRACTION: "get text from X", "copy text from X"
        get_text_match = re.search(r'\b(?:get|copy)\s+text\s+from\s+(?P<selector>[#.\w\'"-]+)', text, flags=re.IGNORECASE)
        if get_text_match:
            function_name = 'copy_text' if 'copy' in text.lower() else 'get_text'
            matches.append({
                'function': function_name,
                'args': {
                    'selector': get_text_match.group('selector').strip('\'"')
                },
                'confidence': 0.83,
                'provenance': 'heuristic_get_text',
                'template': 'heuristic_get_text',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # PASTE TEXT: "paste X into Y"
        paste_match = re.search(r'\bpaste\s+[\'"]([^\'"]+)[\'"]\s+into\s+(?P<selector>[#.\w-]+)', text, flags=re.IGNORECASE)
        if paste_match:
            matches.append({
                'function': 'paste_text',
                'args': {
                    'selector': paste_match.group('selector'),
                    'text': paste_match.group(1)
                },
                'confidence': 0.83,
                'provenance': 'heuristic_paste',
                'template': 'heuristic_paste',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # CSS PROPERTY CHECKS: "expect #element background-color to be #ffffff"
        css_match = re.search(r'\bexpect\s+(?P<selector>[#.\w-]+)\s+(?P<property>[\w-]+)\s+to\s+be\s+(?P<value>[#\w-]+)', text, flags=re.IGNORECASE)
        if css_match:
            matches.append({
                'function': 'expect_css_property',
                'args': {
                    'selector': css_match.group('selector'),
                    'property': css_match.group('property'),
                    'expected': css_match.group('value')
                },
                'confidence': 0.85,
                'provenance': 'heuristic_css_property',
                'template': 'heuristic_css_property',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # MODAL VERIFICATION: "verify modal 'X' appears"
        modal_match = re.search(r'\bverify\s+modal\s+[\'"]?(?P<modal>[^\'"]+)[\'"]?\s+appears?', text, flags=re.IGNORECASE)
        if modal_match:
            matches.append({
                'function': 'expect_modal',
                'args': {
                    'modal': modal_match.group('modal')
                },
                'confidence': 0.83,
                'provenance': 'heuristic_modal_verify',
                'template': 'heuristic_modal_verify',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # TOAST VERIFICATION: "verify 'Success' toast", "ensure toast says X"
        toast_match = re.search(r'\b(?:verify|ensure)\s+(?:[\'"]?(?P<type>\w+)[\'"]?\s+)?toast(?:\s+says?\s+[\'"]?(?P<message>[^\'"]+)[\'"]?)?', text, flags=re.IGNORECASE)
        if toast_match:
            args = {}
            if toast_match.group('type'):
                args['type'] = toast_match.group('type')
            if toast_match.group('message'):
                args['message'] = toast_match.group('message')
            
            matches.append({
                'function': 'expect_toast',
                'args': args,
                'confidence': 0.83,
                'provenance': 'heuristic_toast_verify',
                'template': 'heuristic_toast_verify',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # ATTRIBUTE EXTRACTION: "get data-X attribute from Y"
        attr_match = re.search(r'\bget\s+(?P<attribute>[\w-]+)\s+attribute\s+from\s+[\'"]?(?P<selector>[^\'"]+)[\'"]?', text, flags=re.IGNORECASE)
        if attr_match:
            matches.append({
                'function': 'get_attribute',
                'args': {
                    'selector': attr_match.group('selector'),
                    'attribute': attr_match.group('attribute')
                },
                'confidence': 0.83,
                'provenance': 'heuristic_get_attribute',
                'template': 'heuristic_get_attribute',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # ATTACH/UPLOAD FILE REFINEMENT: "attach X to Y"
        attach_match = re.search(r'\battach\s+(?P<file>[\w.\(\)-]+)\s+to\s+(?P<selector>[#.\w\s-]+)', text, flags=re.IGNORECASE)
        if attach_match:
            matches.append({
                'function': 'upload_file',
                'args': {
                    'selector': attach_match.group('selector').strip(),
                    'file': attach_match.group('file')
                },
                'confidence': 0.85,
                'provenance': 'heuristic_attach_file',
                'template': 'heuristic_attach_file',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1
            return matches

        # LOGIN heuristics (existing)
        if any(k in low for k in ['login', 'log in', 'sign in', 'authenticate']):
            args = self._extract_login_args(text)
            matches.append({
                'function': 'login',
                'args': args,
                'confidence': 0.80,
                'provenance': 'heuristic',
                'template': 'heuristic_login',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1

        # LOGOUT heuristics: "sign out", "log out", "logout", "sign off"
        if any(k in low for k in ['sign out', 'log out', 'logout', 'sign off', 'logoff']):
            matches.append({
                'function': 'logout',
                'args': {},
                'confidence': 0.85,
                'provenance': 'heuristic_logout',
                'template': 'heuristic_logout',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1

        # SIMPLE INPUT heuristics: "enter username", "type password", "fill email"
        simple_input_match = re.search(r'\b(?:enter|type|fill|input)\s+(?P<field>\w+)(?:\s+field)?\s*$', text, flags=re.IGNORECASE)
        if simple_input_match:
            field = simple_input_match.group('field')
            # Create selector from field name
            selector = f'#{field.lower()}' if field.lower() in ['username', 'password', 'email'] else f'[name="{field.lower()}"]'
            matches.append({
                'function': 'type',
                'args': {'selector': selector, 'value': f'{{{field.upper()}}}'},
                'confidence': 0.80,
                'provenance': 'heuristic_input',
                'template': 'heuristic_input',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1

        # TYPE_TEXT patterns: "type 'text' slowly", "type 'hello' quickly"
        type_text_match = re.search(r'\btype\s+[\'"]([^\'"]+)[\'"]\s+(slowly|quickly|fast|slow)\s+(?:in|into)\s+([#.\w\-\[\]\'"\s]+)', text, flags=re.IGNORECASE)
        if type_text_match:
            text_to_type = type_text_match.group(1)
            speed = type_text_match.group(2).lower()
            selector = type_text_match.group(3).strip()
            
            matches.append({
                'function': 'type_text',
                'args': {'selector': selector, 'text': text_to_type, 'speed': speed},
                'confidence': 0.87,
                'provenance': 'heuristic_type_text',
                'template': 'heuristic_type_text',
                'order': clause_info['order']
            })
            self._metrics.heuristic_match_rate += 1

        return matches

    # ---------- template compilation ----------
    def _compile_patterns(self) -> None:
        """Compile regex patterns from function templates."""
        logger.debug("Compiling patterns from %d functions", len(self._functions))
        compiled: List[Dict[str, Any]] = []
        failures = 0
        for func in self._functions:
            # Handle function format variations - support both objects and dicts
            templates: List[str] = []
            signature: Dict[str, str] = {}
            func_name: str = 'unknown'
            
            if hasattr(func, 'templates'):
                templates = func.templates
                signature = func.signature if hasattr(func, 'signature') else {}
                func_name = func.name if hasattr(func, 'name') else 'unknown'
            elif isinstance(func, dict):
                # Handle dict-based function definitions
                func_dict = cast(Dict[str, Any], func)
                templates = cast(List[str], func_dict.get('templates', []))
                signature = cast(Dict[str, str], func_dict.get('signature', {}))
                func_name = cast(str, func_dict.get('name', 'unknown'))
            else:
                templates = getattr(func, 'templates', [])
                signature = getattr(func, 'signature', {})
                func_name = getattr(func, 'name', 'unknown')

            for tpl in templates:
                try:
                    regex_str = self._build_flexible_regex_from_template(tpl, signature)
                    compiled.append({
                        'function_name': func_name,
                        'template': tpl,
                        'regex': re.compile(regex_str, flags=re.IGNORECASE),
                        'signature': signature or {}
                    })
                except Exception as e:
                    logger.exception("Failed compile template '%s': %s", tpl, e)
                    failures += 1
        with self._lock:
            self._patterns = compiled
            self._metrics.active_patterns = len(compiled)
            self._metrics.compilation_failures = failures
        logger.info("Compiled %d patterns (%d failures)", len(compiled), failures)

    def _build_flexible_regex_from_template(self, template: str, signature: Dict[str, str]) -> str:
        # escape literal runs and replace placeholders with named groups
        # We'll allow flexible whitespace and optional 'the' between words
        parts: List[str] = []
        cursor = 0
        for m in re.finditer(r'\{(\w+)\}', template):
            start, end = m.span()
            literal = template[cursor:start]
            if literal:
                # escape and replace spaces with \s+
                lit = re.escape(literal)
                lit = re.sub(r'\\\s+', r'\\s+', lit)
                # optional articles (the/a) after verbs (simple heuristic)
                lit = re.sub(r'\\bthe\\b', r'(?:the\\s+)?', lit)
                parts.append(lit)
            arg_name = m.group(1)
            arg_type = signature.get(arg_name, 'str')
            pat = self._type_to_pattern(arg_type)
            parts.append(f'(?P<{arg_name}>{pat})')
            cursor = end
        # tail literal
        tail = template[cursor:]
        if tail:
            t = re.escape(tail)
            t = re.sub(r'\\\s+', r'\\s+', t)
            parts.append(t)
        # combine, allow optional trailing punctuation and word boundaries
        pattern = r'\b' + r'\s*'.join(parts) + r'\b'
        # be permissive with punctuation around edges
        return pattern

    def _type_to_pattern(self, t: str) -> str:
        t = (t or 'str').lower()
        if t in ('int', 'integer'):
            return r'\d+'
        if t in ('float', 'double'):
            return r'\d+(?:\.\d+)?'
        if t in ('bool', 'boolean'):
            return r'(?:true|false|yes|no|on|off)'
        if t in ('url',):
            return r'https?://[^\s,;]+|www\.[^\s,;]+'
        if t in ('email',):
            return r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
        if t in ('file',):
            return r'[\w\-\s]+\.(?:csv|pdf|xls|xlsx|txt|json)'
        # default string: non-greedy capture up to reasonable length
        return r'.+?'

    # ---------- extraction helpers ----------
    def _extract_args(self, match: re.Match[str], signature: Dict[str, str]) -> Dict[str, Any]:
        args: Dict[str, Any] = {}
        if not match:
            return args
        for k, v in match.groupdict().items():
            if v is not None:
                args[k] = self._clean_arg_value(v.strip(), k)
        return args

    def _extract_args_heuristic(self, text: str) -> Dict[str, Any]:
        args: Dict[str, Any] = {}
        for name, pat in self._extractors.items():
            m = pat.search(text)
            if m:
                args[name] = m.group(0).strip()
        return args

    def _extract_login_args(self, text: str) -> Dict[str, Any]:
        # similar with better tokenization
        args: Dict[str, Any] = {}
        u = self._extractors['username'].search(text)
        p = self._extractors['password'].search(text)
        if u:
            args['username'] = u.group(1)
        if p:
            args['password'] = p.group(1)
        # fallback simple tokens
        if 'username' not in args:
            parts = [w.strip(",;") for w in re.split(r'\s+', text) if w]
            for i, w in enumerate(parts):
                if w.lower() in ('as', 'user', 'username') and i + 1 < len(parts):
                    candidate = parts[i + 1]
                    if candidate.lower() not in ('with', 'password', 'pass'):
                        args['username'] = candidate
                        break
        if 'password' not in args:
            for w in re.split(r'\s+', text):
                if w.lower().startswith('password') and len(w) > 8:
                    args['password'] = w[8:]
                    break
        return args

    def _apply_synonyms(self, text: str) -> str:
        out = text.lower()
        for _, info in self._synonyms.items():
            for t in info['terms']:
                out = re.sub(r'\b' + re.escape(t) + r'\b', info['canonical'], out, flags=re.IGNORECASE)
        return out

    def _get_synonym_boost(self, text: str, func_name: str) -> float:
        if func_name not in self._synonyms:
            return 0.0
        for s in self._synonyms[func_name]['terms']:
            if re.search(r'\b' + re.escape(s) + r'\b', text, flags=re.IGNORECASE):
                return self._synonyms[func_name]['boost']
        return 0.0

    # ---------- cleaning ----------
    def _clean_arg_value(self, value: str, arg_name: str) -> str:
        v = value.strip('\'" ')
        if 'url' in arg_name.lower():
            if not v.startswith(('http://', 'https://')):
                if v.startswith('www.') or '.' in v:
                    return 'https://' + v
        if 'selector' in arg_name.lower():
            if not v.startswith(('#', '.', '[')):
                return v if ' ' in v else f'#{v}'
        return v

    def _clean_url(self, url: str) -> str:
        u = url.strip().strip(',.')
        if not u.startswith(('http://', 'https://')) and (u.startswith('www.') or '.' in u):
            return 'https://' + u
        return u

    def _clean_selector(self, selector: str) -> str:
        """Clean and normalize selector strings for UI elements."""
        s = selector.strip().strip('\'" ')
        # If it looks like an ID or class already, return as-is
        if s.startswith(('#', '.', '[')):
            return s
        # If it has quotes, treat as text selector
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return s
        # If it contains common button/input keywords, wrap in quotes for text matching
        if any(word in s.lower() for word in ['button', 'link', 'input', 'field', 'checkbox', 'dropdown']):
            return f'"{s}"'
        # If it looks like an element name without spaces, make it an ID
        if ' ' not in s and not s.startswith(('http', 'www')):
            return f'#{s}' if not s.startswith('#') else s
        # Default: wrap in quotes for text matching
        return f'"{s}"'

    # ---------- confidence ----------
    def _assess_arg_quality(self, args: Dict[str, Any]) -> float:
        if not args:
            return 0.5
        s = 0.0
        for k, v in args.items():
            vstr = str(v)
            if 'url' in k and vstr.startswith(('http://', 'https://')):
                s += 1.0
            elif '@' in vstr:
                s += 1.0
            elif '.' in vstr and len(vstr) > 3:
                s += 0.85
            else:
                s += 0.7
        return s / len(args)

    def _calculate_confidence(self, entry: Dict[str, Any], match: Optional[re.Match[str]], text: str, args: Dict[str, Any], exact: bool = True) -> float:
        # Base
        base = 0.96 if exact else 0.75
        # completeness
        expected = len(entry.get('signature', {})) or 1
        got = len(args) or 0
        completeness = min(1.0, got / expected) if expected > 0 else 1.0
        # arg quality
        quality = self._assess_arg_quality(args)
        # match length coverage (bounded)
        coverage = 0.0
        if match:
            coverage = min(1.0, len(match.group(0)) / max(len(text), 1))
        # combine with simple weighted average
        conf = base * 0.6 + completeness * 0.2 + quality * 0.15 + coverage * 0.05
        return max(0.0, min(conf, 0.99))

    def _update_metrics(self, step_count: int, time_ms: float, clause_count: int):
        with self._lock:
            self._metrics.total_parses += 1
            if step_count > 0:
                self._metrics.successful_parses += 1
            else:
                self._metrics.failed_parses += 1
            t = self._metrics.total_parses
            self._metrics.average_parse_time_ms = ((self._metrics.average_parse_time_ms * (t - 1)) + time_ms) / t
            self._metrics.average_candidates_per_parse = ((self._metrics.average_candidates_per_parse * (t - 1)) + step_count) / t

    def _dedupe_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove consecutive duplicate steps (same function & args)."""
        deduped: List[Dict[str, Any]] = []
        seen: set[tuple[str, tuple[tuple[str, Any], ...]]] = set()
        for s in steps:
            # Convert args to hashable format (convert lists to tuples)
            args = s.get('args', {})
            hashable_args: Dict[str, Any] = {}
            for k, v in args.items():
                if isinstance(v, list):
                    hashable_args[k] = tuple(v)  # type: ignore[assignment]
                else:
                    hashable_args[k] = v
            
            key: tuple[str, tuple[tuple[str, Any], ...]] = (s.get('function', ''), tuple(sorted(hashable_args.items())))  # type: ignore[assignment]
            # Avoid exact duplicates; keep first occurrence
            if key in seen:
                continue
            seen.add(key)  # type: ignore[arg-type]
            deduped.append(s)
        return deduped

    def get_metrics(self) -> RuleEngineMetrics:
        with self._lock:
            return self._metrics


def create_enhanced_rule_engine(dictionary_repository: Optional['DictionaryRepository'] = None, config: Optional[RuleEngineConfig] = None) -> EnhancedRuleEngine:
    return EnhancedRuleEngine(dictionary_repository, config)

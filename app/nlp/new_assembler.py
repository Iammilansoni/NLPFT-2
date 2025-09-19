# app/nlp/new_assembler.py
import re
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger("nlpforge.assembler")

# Canonical action names expected by tests/UI
ACTION_ALIAS = {
    "fill": "type",
    "type": "type",
    "select_dropdown": "select_dropdown",
    "select": "select",
    "expect_text": "expect_text",
    "expect_visible": "assert_visible",
    "wait_for_invisible": "wait_for_invisible",
    "wait_for_disappear": "wait_for_disappear",
    "wait_for_visible": "wait_for_visible",
    "expect_element_count": "expect_element_count",
    "api_get": "api_get",
    "api_post": "api_post",
    "api_put": "api_put",
    "api_delete": "api_delete",
    "upload_file": "upload_file",
    "click": "click",
    "check": "check",
    "uncheck": "uncheck",
    "open_url": "open_url",
    "login": "login",
    "logout": "logout",
    "press_key": "press_key",
    "expect_title": "expect_title",
    "expect_value": "expect_value",
    "expect_url": "expect_url",
    "expect_page_contains": "expect_page_contains",
    "dismiss_modal": "dismiss_modal",
    "screenshot": "screenshot",
    # New function aliases
    "clear_cookies": "clear_cookies",
    "set_cookie": "set_cookie", 
    "set_local_storage": "set_local_storage",
    "table_find_row": "table_find_row",
    "table_sort": "table_sort",
    "drag_and_drop": "drag_and_drop",
    "slider_set": "slider_set",
    "get_text": "get_text",
    "copy_text": "copy_text",
    "paste_text": "paste_text",
    "expect_css_property": "expect_css_property",
    "expect_enabled": "expect_enabled",
    "expect_disabled": "expect_disabled",
    "expect_modal": "expect_modal",
    "expect_toast": "expect_toast",
    "get_attribute": "get_attribute",
    "type_text": "type_text",
    "multi_select": "multi_select",
    "download_verify": "download_verify",
    "expect_logged_in": "expect_logged_in",
    "table_expect_cell": "table_expect_cell",
    # Access control functions
    "as_user": "as_user",
    "expect_access_granted": "expect_access_granted",
    "expect_access_denied": "expect_access_denied"
}

# Primary multi-fill: "enter X in Y" style - be more specific with connectors
_MULTI_FILL_RE = re.compile(
    r'(?:enter|type|insert|input|write)\s+(?P<value>["\']?[^,"\']+["\']?)\s+(?:in|into|at)\s+(?P<selector>[^,;]+)',
    flags=re.IGNORECASE
)

# Fallback multi-fill: repeated "<field> with <value>(?: and <field> with <value>)*"
_MULTI_FILL_REPEATED = re.compile(
    r'(?:^|and\s+)(?P<field>[\w\s\-_#\.\'"]+?)\s+with\s+(?P<value>[^\s,;]+)(?=\s+and\s+|$)',
    flags=re.IGNORECASE
)

# Minimal required args by canonical action
REQUIRED_ARGS: Dict[str, List[str]] = {
    "type": ["selector", "value"],
    "click": ["selector"],
    "open_url": ["url"],
    "upload_file": ["file"],
    "select": ["selector", "value"],
    "check": ["selector"],
    "uncheck": ["selector"],
    "wait_for_disappear": ["selector"],
    "wait_for_invisible": ["selector"],
    "assert_text": ["expected"],
    "expect_text": ["expected"],
    "assert_visible": ["selector"],
    "login": ["username", "password"],
    "press_key": ["key"],
    "expect_title": ["expected"],
    "expect_value": ["selector", "expected"],
    "expect_url": ["expected"],
    "expect_page_contains": ["expected"],
    "dismiss_modal": ["selector"],
    "screenshot": ["filename"],
    "logout": [],
    # New function requirements
    "clear_cookies": [],
    "set_cookie": ["name", "value"],
    "set_local_storage": ["key", "value"],
    "table_find_row": ["selector", "column", "value"],
    "table_sort": ["selector", "column", "order"],
    "drag_and_drop": ["source", "target"],
    "slider_set": ["selector", "value"],
    "get_text": ["selector"],
    "copy_text": ["selector"],
    "paste_text": ["selector", "text"],
    "expect_css_property": ["selector", "property", "expected"],
    "expect_enabled": ["selector"],
    "expect_disabled": ["selector"],
    "expect_modal": ["modal"],
    "expect_toast": [],  # Optional args handled in pattern
    "get_attribute": ["selector", "attribute"],
    "type_text": ["selector", "value"],
    "multi_select": ["selector", "options"],
    "download_verify": ["filename"],
    "expect_logged_in": [],
    "table_expect_cell": ["selector", "row", "column", "expected"],
    # Access control functions
    "as_user": ["role"],
    "expect_access_granted": [],
    "expect_access_denied": []
}

def _strip_outer_quotes(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.strip()
    # remove one layer of surrounding quotes if present
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1].strip()
    return s

def _normalize_selector_text(sel: Optional[str]) -> Optional[str]:
    """
    Normalize selector text:
    - strip existing outer quotes
    - if looks like CSS id/class or attr [..], keep as-is
    - if contains spaces or keywords -> wrap in single quotes "..."
    - else, convert single token to #id if not starting with '#'
    """
    if sel is None:
        return None
    s = _strip_outer_quotes(sel)
    if s is None:
        return None
    s = s.strip()

    if not s:
        return s

    if s.startswith(('#', '.', '[')):
        return s

    if ' ' in s or any(k in s.lower() for k in ['button', 'link', 'input', 'field', 'checkbox', 'dropdown']):
        # use double quotes per your UI needs (single consistent quoting)
        return f'"{s}"'

    # token style, convert to #id unless it already starts with '#'
    if not s.startswith('#'):
        return f'#{s}'
    return s

def _has_required_args(canonical_func: str, args: Dict[str, Any]) -> bool:
    req: Optional[List[str]] = REQUIRED_ARGS.get(canonical_func)
    if req is None:
        return bool(args)
    for r in req:
        if args.get(r) in (None, "", [], {}):
            return False
    return True

def _extract_multi_fill(matched_text: str) -> List[Tuple[str, str]]:
    """
    Extract repeated "<field> with <value>" pairs or "enter X in Y" occurrences.
    Returns list of (selector, value).
    """
    found: List[Tuple[str, str]] = []
    if not matched_text:
        return found

    # Primary pass: patterns like "enter value in selector"
    for m in _MULTI_FILL_RE.finditer(matched_text):
        val = m.group("value").strip().strip('\'"')
        sel = m.group("selector").strip()
        found.append((sel, val))
    if found:
        return found

    # Fallback pass: repeated 'field with value' constructs
    for m in _MULTI_FILL_REPEATED.finditer(matched_text):
        field = m.group("field").strip()
        val = m.group("value").strip().strip('\'"')
        # Clean field: remove action words and connectors
        field = re.sub(r'^(fill|enter|type|input|write|insert|and)\s+', '', field, flags=re.IGNORECASE).strip()
        field = re.sub(r'\b(with|and)\b.*$', '', field, flags=re.IGNORECASE).strip()
        if field:  # Only add if we have a valid field name
            found.append((field, val))
    return found

def assemble_steps(raw_steps: List[Dict[str, Any]], original_text: str = "") -> Dict[str, Any]:
    if not raw_steps:
        return {"steps": [], "unresolved_tokens": [], "overall_confidence": 0.0}

    expanded: List[Dict[str, Any]] = []
    unresolved: List[str] = []

    for step in raw_steps:
        # get original function name and args
        func_raw = step.get("function") or step.get("name") or ""
        args_raw: Dict[str, Any] = step.get("args", {}) or {}
        matched_text = step.get("matched_text") or step.get("template") or ""

        # Strip outer quotes from any selector before normalization
        if isinstance(args_raw.get("selector"), str):
            args_raw["selector"] = _strip_outer_quotes(args_raw["selector"])  # type: ignore[arg-type]

        # Make canonical function name early
        canonical = ACTION_ALIAS.get(func_raw, func_raw)

        # Multi-fill expansion: only for 'fill' or 'type' raw functions or when original text contains ' with ' and multiple pairs
        should_try_multi_fill = (
            func_raw in ("fill", "type") or 
            (" with " in original_text.lower() if original_text else False)
        )
        
        if should_try_multi_fill:
            # Always try original text first for multi-fill patterns
            pairs = _extract_multi_fill(original_text) if original_text else _extract_multi_fill(matched_text)
            if pairs and len(pairs) > 1:  # Only expand if we found multiple pairs
                for sel, val in pairs:
                    s_norm = _normalize_selector_text(sel)
                    new_step: Dict[str, Any] = {
                        "function": ACTION_ALIAS.get(func_raw, canonical),
                        "args": {"selector": s_norm, "value": val},
                        "confidence": float(step.get("confidence", 0.85)),
                        "provenance": step.get("provenance", "assembled_multi_fill"),
                        "template": step.get("template"),
                        "matched_text": matched_text,
                        "order": step.get("order", 0)
                    }
                    expanded.append(new_step)  # type: ignore[arg-type]
                continue  # processed this step fully

        # Normalize selector if present
        if isinstance(args_raw.get("selector"), str):
            args_raw["selector"] = _normalize_selector_text(args_raw["selector"])  # type: ignore[arg-type]

        # Map function name to canonical
        normalized_func = ACTION_ALIAS.get(func_raw, canonical)

        # Special handling for type_text - map 'text' to 'value' for compatibility
        if normalized_func == "type_text" and "text" in args_raw and "value" not in args_raw:
            args_raw["value"] = args_raw["text"]

        # Build normalized step
        normalized: Dict[str, Any] = {
            "function": normalized_func,
            "args": args_raw,
            "confidence": float(step.get("confidence", 0.0)),
            "provenance": step.get("provenance"),
            "template": step.get("template"),
            "matched_text": matched_text,
            "order": step.get("order", 0)
        }

        # If missing required args, push to unresolved (don't silently drop)
        if not _has_required_args(normalized["function"], normalized["args"]):
            unresolved.append(matched_text or str(step))
            logger.debug("Assembler dropping step - missing args: func=%s args=%s matched_text=%s",
                         normalized["function"], normalized["args"], matched_text)  # type: ignore[misc]
            continue

        expanded.append(normalized)  # type: ignore[arg-type]

    # Deduplicate: keep highest-confidence occurrence
    dedup_map: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], Dict[str, Any]] = {}
    ordered_keys: List[Tuple[str, Tuple[Tuple[str, str], ...]]] = []

    for s in expanded:
        key = (s["function"], tuple(sorted((k, str(v)) for k, v in s["args"].items())))
        if key not in dedup_map:
            dedup_map[key] = s
            ordered_keys.append(key)
        else:
            if float(s.get("confidence", 0.0)) > float(dedup_map[key].get("confidence", 0.0)):
                dedup_map[key] = s

    final_steps: List[Dict[str, Any]] = []
    for idx, key in enumerate(ordered_keys, start=1):
        st = dedup_map[key]
        st["order"] = idx
        final_steps.append(st)

    overall_conf = round(sum(float(s.get("confidence", 0.0)) for s in final_steps) / len(final_steps), 3) if final_steps else 0.0

    return {"steps": final_steps, "unresolved_tokens": list(dict.fromkeys(unresolved)), "overall_confidence": overall_conf}
#!/usr/bin/env python3
"""
Large test-suite for NLPForge /convert endpoint.

- Sends 60+ NL inputs to POST /api/v1/convert/
- Parses 'converted_text' JSON (same format your convert endpoint returns)
- Saves full results to results_large.jsonl (one JSON object per line)
- Saves summary CSV to results_summary_large.csv
- Prints readable output and basic expected-action checks if provided
"""

import requests
import json
import csv
import argparse
import time
from typing import List, Dict, Any, Optional

DEFAULT_URL = "http://localhost:8000/api/v1/convert/"
OUTPUT_JSONL = "results_large.jsonl"
OUTPUT_SUMMARY = "results_summary_large.csv"
DEFAULT_TIMEOUT = 15
CONFIDENCE_THRESHOLD = 0.75

# --- Test cases: 60+ natural-language inputs
# Some include 'expected' minimal action names (optional) to assert correctness.
TEST_CASES: List[Dict[str, Any]] = [
    # Basic navigation / click / open_url
    {"input": "Open https://example.com and click on the Sign up link", "expected": ["open_url", "click"]},
    {"input": "Go to https://example.com/login then click the login button", "expected": ["open_url", "click"]},
    {"input": "Navigate to example.com/dashboard and check the title is Dashboard", "expected": ["open_url","expect_title"]},

    # Forms / type / fill
    {"input": "Enter john@example.com in the email field and type secret in the password field", "expected": ["type","type"]},
    {"input": "Fill username with testuser and password with mypass123", "expected": ["type","type"]},
    {"input": "Type Hello World in the search box and click search button", "expected": ["type","click"]},
    {"input": "fill the #first-name field with 'Avadhi' and fill the #last-name with 'Singhal'"},
    {"input": "input 555-1234 into phone input and press Enter", "expected": ["type","press_key"]},
    {"input": "type 'quick brown fox' slowly in #notes", "expected": ["type_text"]},

    # Selects / dropdowns / checkboxes
    {"input": "Select India from country dropdown and check the terms checkbox", "expected": ["select_dropdown","check"]},
    {"input": "choose 'USD' in the currency selector and uncheck subscribe checkbox", "expected": ["select_dropdown","uncheck"]},
    {"input": "Select multiple options apple, banana from #fruits multi-select", "expected": ["multi_select"]},

    # Upload / download
    {"input": "Upload report.csv to the #report-upload input", "expected": ["upload_file"]},
    {"input": "Check report.csv was downloaded within 10 seconds", "expected": ["download_verify"]},

    # Wait / visibility / assertions
    {"input": "Wait for loading spinner to disappear and verify Welcome message appears", "expected": ["wait_for_invisible","expect_text"]},
    {"input": "Wait until the #results table appears and ensure it has at least 1 row", "expected": ["wait_for_visible","expect_element_count"]},
    {"input": "verify that the page contains 'Thank you'"},
    {"input": "assert title is 'Account Summary'", "expected": ["expect_title"]},

    # Authentication
    {"input": "Log in as admin with password password123", "expected": ["login"]},
    {"input": "Sign out", "expected": ["logout"]},
    {"input": "Verify user is logged in", "expected": ["expect_logged_in"]},

    # Cookies / local storage / api calls
    {"input": "Clear cookies and set cookie sessionId to ABC123", "expected": ["clear_cookies","set_cookie"]},
    {"input": "set local storage token to 'abcd1234'"},
    {"input": "make get request to https://api.example.com/users/42", "expected": ["api_get"]},
    {"input": "post to api https://api.example.com/events with {'x':1}", "expected": ["api_post"]},

    # Table operations
    {"input": "Find row in #users-table where email equals test@example.com", "expected": ["table_find_row"]},
    {"input": "Sort #log-table by date descending", "expected": ["table_sort"]},
    {"input": "Check row 1 in #order-table column status is Completed", "expected": ["table_expect_cell"]},

    # Modals / toasts
    {"input": "Close the confirmation modal and verify 'Deleted' toast appears", "expected": ["dismiss_modal","expect_toast"]},
    {"input": "Verify 'Success' toast says data saved"},

    # Screenshot / extraction
    {"input": "Take screenshot as dashboard.png", "expected": ["screenshot"]},
    {"input": "Get text from '#welcome' and save as welcome_msg", "expected": ["get_text"]},
    {"input": "Get data-customer-id attribute from '#profile' and save as cid", "expected": ["get_attribute"]},

    # Drag and drop / slider
    {"input": "Drag file-item to drop-zone", "expected": ["drag_and_drop"]},
    {"input": "Set slider #volume to 70", "expected": ["slider_set"]},

    # RBAC & permissions
    {"input": "As admin, open /settings and verify access granted", "expected": ["as_user","open_url","expect_access_granted"]},
    {"input": "As guest, try to edit settings and check permission denied", "expected": ["as_user","expect_access_denied"]},

    # Assertions & CSS property
    {"input": "expect #banner background-color to be #ffffff", "expected": ["expect_css_property"]},
    {"input": "expect #search to be enabled", "expected": ["expect_enabled"]},

    # Complex multi-step / nested phrasing
    {"input": "Open https://login.example.com, enter admin in username, type password123 in password, and click login button", "expected": ["open_url","type","type","click"]},
    {"input": "Go to the dashboard, wait for widgets to load, then export csv and verify file downloaded", "expected": ["open_url","wait_for_visible","api_get|download_verify"]},

    # Ambiguous / unresolved cases
    {"input": "Please do the obvious check on the main page"},  # intended unresolved
    {"input": "Ensure everything ok and if not report"},         # ambiguous

    # Text-heavy / long multi-actions
    {"input": "Navigate to https://example.com/products, filter by category Electronics, sort price descending, click the first product, add to cart, then go to cart and assert subtotal > 1000"},
    {"input": "Open site, login as 'shopper' with 's3cr3t', search for 'laptop', set quantity to 2, and checkout"},

    # Variety of selectors & patterns
    {"input": "Enter test@email.com in #email and click #submit", "expected": ["type","click"]},
    {"input": "click on the 'profile' link and then take screenshot of profile section"},
    {"input": "paste 'clip text' into #notes", "expected": ["paste_text"]},
    {"input": "copy text from .address and save as addr", "expected": ["copy_text"]},

    # Keyboard / keys / press
    {"input": "Press Enter", "expected": ["press_key"]},
    {"input": "Press Ctrl+S to save the form", "expected": ["press_key"]},

    # Value checks / expect value
    {"input": "expect #email value test@example.com", "expected": ["expect_value"]},
    {"input": "expect url contains /dashboard", "expected": ["expect_url"]},

    # Page-level checks
    {"input": "expect page contains 'Privacy Policy'"},
    {"input": "wait for the loader to be gone, then make sure the data table is visible"},

    # Edge cases: punctuation & symbols
    {"input": "Open https://example.com; then, 'click' the 'Start' button."},
    {"input": "Upload 'my report (final).pdf' to 'Resume' input field"},

    # More function coverage
    {"input": "set cookie theme to dark mode"},
    {"input": "select all in #notes and replace with 'N/A'"},
    {"input": "type 'hello' quickly in #chat"},
    {"input": "verify 3 .row elements exist in #results", "expected": ["expect_element_count"]},
    {"input": "press the Tab key then press Enter"},
    {"input": "drag order-3 onto order-1"},
    {"input": "check the checkbox 'accept terms'"},
    {"input": "uncheck the 'subscribe' option"},
    {"input": "check that #price contains 199.99"},
    {"input": "set local storage user.locale to en-US"},
    {"input": "call get api https://api.example.com/health"},

    # Additional random variations to exercise fuzzy & semantic layers
    {"input": "sign in as john using pass hunter2"},
    {"input": "browse to www.example.org and click register"},
    {"input": "attach resume.docx to cv upload input"},
    {"input": "verify modal 'Confirmation' appears"},
    {"input": "dismiss popup"},
    {"input": "ensure toast success says 'Saved'"},
]

# --- Helper functions
def pretty_print_steps(steps: List[Dict[str, Any]]) -> None:
    for i, step in enumerate(steps, start=1):
        # support multiple output shapes
        action = step.get('action') or step.get('function') or step.get('function_name') or step.get('function')
        conf = step.get('confidence', step.get('confidence_score', step.get('score', 0.0)))
        if action in ('type','fill','type_text','fill'):
            selector = step.get('selector', step.get('args', {}).get('selector', ''))
            value = step.get('value', step.get('args', {}).get('value', '') or step.get('args', {}).get('text', ''))
            print(f"   {i}. {action}(selector={selector}, value={value}) - confidence: {conf:.2f}")
        elif action in ('open_url','api_get','api_post'):
            urlv = step.get('url') or step.get('args', {}).get('url') or step.get('args', {}).get('path','')
            print(f"   {i}. {action}(url={urlv}) - confidence: {conf:.2f}")
        elif action in ('click','check','uncheck','select','select_dropdown','upload_file','download_verify','wait_for_visible','wait_for_invisible','expect_text','expect_visible'):
            S = step.get('selector') or step.get('args', {}).get('selector','') or step.get('args',{}).get('file','')
            V = step.get('value') or step.get('expected') or step.get('args', {}).get('value','')
            print(f"   {i}. {action}(selector={S}, value={V}) - confidence: {conf:.2f}")
        else:
            print(f"   {i}. {action}({step}) - confidence: {conf:.2f}")

def call_convert(url: str, payload: Dict[str, Any], timeout: int) -> Optional[Dict[str, Any]]:
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def evaluate_expected(steps: List[Dict[str, Any]], expected_actions: Optional[List[str]]) -> bool:
    if not expected_actions:
        return True  # no expected -> treat as pass for reporting (still review results)
    # Extract function names directly without normalization
    # Our engine already produces canonical function names
    actual_functions = []
    for s in steps:
        func_name = s.get('action') or s.get('function') or s.get('function_name') or ''
        actual_functions.append(func_name)  # type: ignore[reportUnknownMemberType]
    # Simple sequence match (order-sensitive)
    # If expected contains alternatives (like "api_get|download_verify"), treat as OR if present
    i = 0
    for exp in expected_actions:
        if isinstance(exp, str) and '|' in exp:  # type: ignore[reportUnnecessaryIsInstance]
            candidates = [e.strip() for e in exp.split('|')]
        else:
            candidates = [exp]
        # find next occurrence of any candidate
        found = False
        while i < len(actual_functions):  # type: ignore[reportUnknownArgumentType]
            if actual_functions[i] in candidates:
                found = True
                i += 1
                break
            i += 1
        if not found:
            return False
    return True

# --- Main runner
def run_suite(server_url: str, timeout: int = DEFAULT_TIMEOUT, conf_threshold: float = CONFIDENCE_THRESHOLD):
    results = []
    summary_rows = []

    for idx, case in enumerate(TEST_CASES, start=1):
        txt = case["input"]
        expected = case.get("expected")
        payload = {"text": txt, "target_format": "nlp_steps"}  # type: ignore[reportUnknownVariableType]

        print(f"\n=== CASE {idx}/{len(TEST_CASES)} ===")
        print(f"Input: {txt}")

        start = time.time()
        resp_json = call_convert(server_url, payload, timeout)  # type: ignore[reportUnknownArgumentType]
        elapsed = time.time() - start

        if not resp_json:
            print("❌ No response, skipping")
            summary_rows.append({  # type: ignore[reportUnknownMemberType]
                "index": idx,
                "input": txt,
                "steps_count": 0,
                "overall_confidence": 0.0,
                "status": "error",
                "elapsed_s": round(elapsed, 3),
                "unresolved": ""
            })
            results.append({"input": txt, "error": "no_response"})  # type: ignore[reportUnknownMemberType]
            continue

        # Your convert endpoint returns converted_text as string JSON in prior script — handle both shapes
        converted_raw = resp_json.get("converted_text") or resp_json.get("converted") or resp_json.get("converted_json")
        converted: Dict[str, Any] = {}
        if isinstance(converted_raw, str):
            try:
                converted = json.loads(converted_raw)
            except Exception:
                # maybe server already returned structured
                fallback = resp_json.get("converted_text")
                converted = fallback if isinstance(fallback, dict) else {}  # type: ignore[reportUnknownVariableType]
        elif isinstance(converted_raw, dict):
            converted = converted_raw  # type: ignore[reportUnknownVariableType]
        else:
            # fallback to resp_json if it has the expected structure
            if isinstance(resp_json, dict) and ("steps" in resp_json or "overall_confidence" in resp_json):  # type: ignore[reportUnnecessaryIsInstance]
                converted = resp_json
            else:
                converted = {}

        steps: List[Dict[str, Any]] = converted.get("steps", [])
        overall_conf: float = float(converted.get("overall_confidence", converted.get("confidence", 0.0)))

        print(f"Status: {resp_json.get('status', 'ok')}, Steps ({len(steps)}), Conf: {overall_conf}")
        pretty_print_steps(steps)

        # Evaluate expected if present
        expected_ok = evaluate_expected(steps, expected) if expected else None
        if expected is not None:
            print("Expected:", expected, "=>", ("PASS" if expected_ok else "FAIL"))

        # Determine basic pass/fail for summary
        unresolved_tokens: List[str] = converted.get("unresolved_tokens", [])
        basic_pass: bool = (overall_conf >= conf_threshold) and (not unresolved_tokens) and (expected_ok is not False)

        status = "pass" if basic_pass else "fail"

        summary_rows.append({  # type: ignore[reportUnknownMemberType]
            "index": idx,
            "input": txt,
            "steps_count": len(steps),
            "overall_confidence": float(overall_conf or 0.0),
            "status": status,
            "elapsed_s": round(elapsed, 3),
            "unresolved": ",".join(unresolved_tokens) if unresolved_tokens else ""
        })

        # Save full result for this case
        results.append({  # type: ignore[reportUnknownMemberType]
            "index": idx,
            "input": txt,
            "response": resp_json,
            "converted": converted,
            "expected": expected,
            "expected_ok": expected_ok,
            "basic_pass": basic_pass,
            "elapsed_s": round(elapsed, 3),
        })

    # Write results JSONL
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as fh:
        for r in results:  # type: ignore[reportUnknownVariableType]
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nFull results written to {OUTPUT_JSONL}")

    # Write CSV summary
    with open(OUTPUT_SUMMARY, "w", newline='', encoding="utf-8") as csvf:
        fieldnames = ["index","input","steps_count","overall_confidence","status","elapsed_s","unresolved"]
        writer = csv.DictWriter(csvf, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary_rows:  # type: ignore[reportUnknownVariableType]
            writer.writerow(row)  # type: ignore[reportUnknownArgumentType]
    print(f"Summary CSV written to {OUTPUT_SUMMARY}")

    # Print quick stats
    total = len(summary_rows)  # type: ignore[reportUnknownArgumentType]
    passed = sum(1 for r in summary_rows if r["status"] == "pass")  # type: ignore[reportUnknownVariableType]
    print(f"\n=== SUITE SUMMARY: {passed}/{total} passed (conf >= {conf_threshold}) ===")

# --- CLI
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL, help="Convert API URL")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="HTTP timeout (s)")
    parser.add_argument("--conf", type=float, default=CONFIDENCE_THRESHOLD, help="Confidence threshold for pass")
    args = parser.parse_args()
    run_suite(args.url, timeout=args.timeout, conf_threshold=args.conf)

# test_json_generator.py
# Runs a suite of end-to-end tests against JSONoutput_generator.answer()
# Usage: python test_json_generator.py
from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Tuple

# Import the module under test (must be in the same folder)
import JSONoutput_generator as gen  # v3.6 recommended


Case = Tuple[str, str, Dict[str, Any]]  # (label, input_text, expected_result)


def cases() -> List[Case]:
    return [
        # ---------------- login ----------------
        (
            "login #1",
            "Please validate confedentials avadhi and avdhi@123 on portal.app",
            {"api":"login","endpoint":"https://portal.app/api/login","request":{"username":"avadhi","password":"avdhi@123"}},
        ),
        (
            "login #2",
            "Sigin with the credentials Admin@2024! && admin_user at 10.0.0.5:8080",
            {"api":"login","endpoint":"http://10.0.0.5:8080/api/login","request":{"username":"admin_user","password":"Admin@2024!"}},
        ),
        (
            "login #3",
            "user john.d password P@ssw0rd please",
            {"api":"login","endpoint":"<missed>/api/login","request":{"username":"john.d","password":"P@ssw0rd"}},
        ),

        # ---------------- logout ----------------
        (
            "logout #1",
            "logout from auth.mysite.io Authorization: Bearer eyJabc123...",
            {"api":"logout","endpoint":"https://auth.mysite.io/api/logout","request":{"token":"eyJabc123..."}},
        ),
        (
            "logout #2",
            "sign out using token jwt_987654 on localhost:3000",
            {"api":"logout","endpoint":"https://localhost:3000/api/logout","request":{"token":"jwt_987654"}},
        ),
        (
            "logout #3",
            "end session at 192.168.1.9 Authorization: Bearer tok_xxx_999",
            {"api":"logout","endpoint":"http://192.168.1.9/api/logout","request":{"token":"tok_xxx_999"}},
        ),

        # ---------------- register ----------------
        (
            "register #1",
            "sign up at app.io email neo@matrix.io pass Matrix99",
            {"api":"register","endpoint":"https://app.io/api/register","request":{"email":"neo@matrix.io","password":"Matrix99","username":"neo"}},
        ),
        (
            "register #2",
            "register on https://accounts.example.com username devm email dev@example.com password d3vPass!2",
            {"api":"register","endpoint":"https://accounts.example.com/api/register","request":{"username":"devm","email":"dev@example.com","password":"d3vPass!2"}},
        ),
        (
            "register #3",
            "create account with email user99@test.co and password pass12345",
            {"api":"register","endpoint":"<missed>/api/register","request":{"email":"user99@test.co","password":"pass12345","username":"user99"}},
        ),

        # ---------------- reset_password ----------------
        (
            "reset_password #1",
            "forgot password at www.acme.com for dev@acme.com",
            {"api":"reset_password","endpoint":"https://www.acme.com/api/reset_password","request":{"email":"dev@acme.com"}},
        ),
        (
            "reset_password #2",
            "recover password for user foo email foo@bar.net on api.bar.net",
            {"api":"reset_password","endpoint":"https://api.bar.net/api/reset_password","request":{"email":"foo@bar.net"}},
        ),
        (
            "reset_password #3",
            "reset my login dev@org.org",
            {"api":"reset_password","endpoint":"<missed>/api/reset_password","request":{"email":"dev@org.org"}},
        ),

        # ---------------- update_profile ----------------
        (
            "update_profile #1",
            "on api.local:3000 update profile U123 name John A Doe phone (555) 010-0100",
            {"api":"update_profile","endpoint":"https://api.local:3000/api/update_profile","request":{"user_id":"U123","name":"John A Doe","phone":"(555) 010-0100"}},
        ),
        (
            "update_profile #2",
            "edit profile user id USER-77A at corp.intranet set phone +91 98765 43210",
            {"api":"update_profile","endpoint":"https://corp.intranet/api/update_profile","request":{"user_id":"USER-77A","phone":"+91 98765 43210"}},
        ),
        (
            "update_profile #3",
            "change profile ACC-999",
            {"api":"update_profile","endpoint":"<missed>/api/update_profile","request":{"user_id":"ACC-999"}},
        ),

        # ---------------- upload_file ----------------
        (
            "upload_file #1",
            r"upload C:\Docs\April\invoice-0424.PDF to files.app",
            {"api":"upload_file","endpoint":"https://files.app/api/upload","request":{"file_name":"invoice-0424.PDF","file_type":"pdf"}},
        ),
        (
            "upload_file #2",
            "attach image.png on www.imgbox.com",
            {"api":"upload_file","endpoint":"https://www.imgbox.com/api/upload","request":{"file_name":"image.png","file_type":"png"}},
        ),
        (
            "upload_file #3",
            "send file report.csv",
            {"api":"upload_file","endpoint":"<missed>/api/upload","request":{"file_name":"report.csv","file_type":"csv"}},
        ),

        # ---------------- download_file ----------------
        (
            "download_file #1",
            "download file DOC00987 from 10.0.0.5:8080",
            {"api":"download_file","endpoint":"http://10.0.0.5:8080/api/download","request":{"file_id":"DOC00987"}},
        ),
        (
            "download_file #2",
            "get file 550e8400-e29b-41d4-a716-446655440000 at storage.example.com",
            {"api":"download_file","endpoint":"https://storage.example.com/api/download","request":{"file_id":"550e8400-e29b-41d4-a716-446655440000"}},
        ),
        (
            "download_file #3",
            "fetch file ID UPL1234567",
            {"api":"download_file","endpoint":"<missed>/api/download","request":{"file_id":"UPL1234567"}},
        ),

        # ---------------- search ----------------
        (
            "search #1",
            "search quarterly revenue on portal.app type:pdf year:2024",
            {"api":"search","endpoint":"https://portal.app/api/search","request":{"query":"quarterly revenue","filters":{"type":"pdf","year":"2024"}}},
        ),
        (
            "search #2",
            "lookup docs about reset password at www.example.com status:open tag:security",
            {"api":"search","endpoint":"https://www.example.com/api/search","request":{"query":"docs reset password","filters":{"status":"open","tag":"security"}}},
        ),
        (
            "search #3",
            "find acme invoices 2023",
            {"api":"search","endpoint":"<missed>/api/search","request":{"query":"acme invoices 2023"}},
        ),

        # ---------------- get_user ----------------
        (
            "get_user #1",
            "get user USER-77A at corp.intranet",
            {"api":"get_user","endpoint":"https://corp.intranet/api/get_user","request":{"user_id":"USER-77A"}},
        ),
        (
            "get_user #2",
            "fetch user id U12345 from 127.0.0.1:5000",
            {"api":"get_user","endpoint":"http://127.0.0.1:5000/api/get_user","request":{"user_id":"U12345"}},
        ),
        (
            "get_user #3",
            "retrieve user ACC-9988",
            {"api":"get_user","endpoint":"<missed>/api/get_user","request":{"user_id":"ACC-9988"}},
        ),

        # ---------------- delete_account ----------------
        (
            "delete_account #1",
            "delete account U999 on mysite.com — confirm",
            {"api":"delete_account","endpoint":"https://mysite.com/api/delete_account","request":{"user_id":"U999","confirm":True}},
        ),
        (
            "delete_account #2",
            "close account ID123 at app.io don't confirm",
            {"api":"delete_account","endpoint":"https://app.io/api/delete_account","request":{"user_id":"ID123","confirm":False}},
        ),
        (
            "delete_account #3",
            "terminate account USER-5A",
            {"api":"delete_account","endpoint":"<missed>/api/delete_account","request":{"user_id":"USER-5A","confirm":False}},
        ),
    ]


def run_case(label: str, query: str, expected: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Runs a single case through JSONoutput_generator.answer and compares dict equality."""
    actual = gen.answer(query, include_meta=False)
    # Keep only the keys we care about for comparison (api, endpoint, request)
    actual_reduced = {k: actual.get(k) for k in ("api", "endpoint", "request")}
    ok = actual_reduced == expected
    if not ok:
        print(f"\n[FAIL] {label}")
        print("  Input:   ", query)
        print("  Expected:", json.dumps(expected, indent=2))
        print("  Actual:  ", json.dumps(actual_reduced, indent=2))
    else:
        print(f"[PASS] {label}")
    return ok, actual_reduced


def main() -> None:
    all_cases = cases()
    passed = 0
    for label, query, expected in all_cases:
        ok, _ = run_case(label, query, expected)
        passed += int(ok)

    total = len(all_cases)
    print("\n================ SUMMARY ================")
    print(f"Passed {passed}/{total} cases")
    print("=========================================")

    # Exit non-zero on failures (useful for CI)
    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    main()

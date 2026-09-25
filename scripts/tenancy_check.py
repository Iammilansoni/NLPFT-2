"""
Tenancy check against a running stack: one user can never see or change
another user's templates, datasets, embeddings, jobs or model settings.

    python scripts/tenancy_check.py [http://localhost:8000]

Signs up two fresh users, Alice and Bob. Alice creates a template, switches it
on, uploads utterances (auto-embedded), generates a dataset and adds an LLM
connection. Bob then tries every ID-taking endpoint on Alice's objects and
every list endpoint. Each attempt must fail with 403/404/422 or come back
without any of Alice's data.

Needs a server with no SMTP settings, so sign-up returns the verification code
(the default for a fresh clone). Requires: pip install httpx
"""
import sys
import time
import uuid

import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000") + "/api/v1"
PASSWORD = "Welcome123"
REFUSED = {401, 403, 404, 422}
# Strings only Alice's objects contain. Bob's queries never include them, so a
# response carrying one (an echo of the query can't) means her data leaked.
ALICE_MARKERS = ("Alice_Private_Booking", "api.alice.example", "alice-llm", "alice.csv")


def sign_up(tag):
    email = f"{tag}{uuid.uuid4().hex[:8]}@example.com"
    r = httpx.post(f"{BASE}/auth/register", json={
        "email": email, "username": email.split("@")[0],
        "password": PASSWORD, "confirm_password": PASSWORD,
    })
    r.raise_for_status()
    code = r.json()["verification"]["code"]
    if not code:
        sys.exit("This server e-mails verification codes (SMTP is set). Run against one without SMTP.")
    httpx.post(f"{BASE}/auth/verify-otp", json={"email": email, "otp": code}).raise_for_status()
    r = httpx.post(f"{BASE}/auth/login", data={"username": email, "password": PASSWORD})
    r.raise_for_status()
    return httpx.Client(base_url=BASE, timeout=120,
                        headers={"Cookie": f"nlpf_access={r.cookies['nlpf_access']}"})


alice, bob = sign_up("alice"), sign_up("bob")

# --- Alice builds her own data ------------------------------------------------
sentence = ("This endpoint books a restaurant table for a party of guests at a chosen time "
            "and returns a confirmation with the booking reference. ")
r = alice.post("/templates/", json={
    "api_name": "Alice_Private_Booking",
    "description": (sentence * 30).strip(),
    "base_url": "https://api.alice.example",
    "endpoint": "/v1/bookings",
    "method": "POST",
    "parameters": [{"name": "party_size", "type": "integer", "required": True, "example": 4,
                    "description": "Number of guests at the table"}],
    "sample_requests": [
        {"scenario": "valid", "query": "book a table for 4 at 7pm", "request": {"party_size": 4}},
        {"scenario": "edge", "query": "table for 1", "request": {"party_size": 1}},
        {"scenario": "error", "query": "book a table for zero", "request": {"party_size": 0}},
    ],
    "sample_responses": [{"status": 201}, {"status": 201}, {"status": 422}],
    "domain_tags": ["restaurants"],
})
assert r.status_code == 201, r.text[:300]
template_id = r.json()["template_id"]
alice.post(f"/templates/{template_id}/toggle-visibility").raise_for_status()

rows = "query,api_name\n" + "\n".join(f"alice private booking {n},Alice_Private_Booking" for n in range(12))
r = alice.post("/datasets/upload", params={"template_id": template_id},
               files={"file": ("alice.csv", rows, "text/csv")})
r.raise_for_status()
dataset_id, upload_task = r.json()["dataset_id"], r.json()["task_id"]
for _ in range(60):
    if alice.get(f"/datasets/db/{dataset_id}").json().get("embedding_status") in ("completed", "failed"):
        break
    time.sleep(2)

r = alice.post("/datasets/generate", json={"template_id": template_id, "num_examples": 10,
                                           "user_prompt": "Customers booking tables in casual English"})
generation_task = r.json().get("task_id")
r = alice.post("/llm-config", json={"provider": "ollama", "model_name": "llama3.2:3b", "name": "alice-llm"})
config_id = r.json().get("id") if r.status_code < 300 else None
csv_name = alice.get(f"/datasets/db/{dataset_id}").json().get("csv_path", "").split("/")[-1]

# --- Bob tries to reach it ----------------------------------------------------
failures = []


def attempt(label, method, url, read=False, **kwargs):
    r = bob.request(method, url, **kwargs)
    leaked = any(m in r.text for m in ALICE_MARKERS) or r.status_code not in REFUSED | {200}
    if r.status_code == 200 and method != "GET" and not read:
        leaked = True  # a write on her object went through
    print(("LEAK " if leaked else "ok   ") + f"[{r.status_code}] {label}")
    if leaked:
        failures.append(label)


t, d = template_id, dataset_id
for label, method, url, body in [
    ("list templates", "GET", "/templates/", None),
    ("template stats", "GET", "/templates/stats", None),
    ("read template", "GET", f"/templates/{t}", None),
    ("validate template", "GET", f"/templates/{t}/validate", None),
    ("edit template", "PUT", f"/templates/{t}", {"api_name": "changed"}),
    ("edit draft", "PUT", f"/templates/draft/{t}", {"api_name": "changed"}),
    ("submit template", "POST", f"/templates/{t}/submit", None),
    ("approve template", "POST", f"/templates/{t}/approve", None),
    ("reject template", "POST", f"/templates/{t}/reject", {"reason": "x"}),
    ("disable template", "POST", f"/templates/{t}/disable", None),
    ("enable template", "POST", f"/templates/{t}/enable", None),
    ("switch template on/off", "POST", f"/templates/{t}/toggle-visibility", None),
    ("list datasets", "GET", "/datasets/db/list", None),
    ("list datasets (legacy)", "GET", "/datasets/", None),
    ("list tasks", "GET", "/datasets/tasks", None),
    ("read dataset", "GET", f"/datasets/db/{d}", None),
    ("read dataset rows", "GET", f"/datasets/db/{d}/rows", None),
    ("dataset info", "GET", f"/datasets/{d}/info", None),
    ("embedding status", "GET", f"/datasets/{d}/embedding-status", None),
    ("rename dataset", "PATCH", f"/datasets/db/{d}/rename", {"name": "changed"}),
    ("embed dataset", "POST", f"/embeddings/datasets/{d}/embed", None),
    ("re-embed dataset", "POST", f"/datasets/{d}/reembed", None),
    ("search inside dataset", "POST", f"/datasets/{d}/search", {"query": "private booking", "dataset_id": d}),
    ("datasets by template", "GET", f"/datasets/by-template/{t}", None),
    ("route a request", "POST", "/query/semantic-search", {"query": "private booking 3"}),
    ("route within her dataset", "POST", "/query/semantic-search", {"query": "private booking", "dataset_id": d}),
    ("route within her template", "POST", "/query/semantic-search", {"query": "private booking", "template_id": t}),
    ("upload job status", "GET", f"/datasets/status/{upload_task}", None),
    ("generation job status", "GET", f"/datasets/status/{generation_task}", None),
    ("generation preview", "GET", f"/datasets/preview/task/{generation_task}", None),
    ("generation download", "GET", f"/datasets/download/{generation_task}/csv", None),
    ("download her CSV", "GET", f"/datasets/download-file/{csv_name}", None),
    ("preview her CSV", "GET", f"/datasets/preview/file/{csv_name}", None),
    ("list LLM connections", "GET", "/llm-config", None),
    ("model catalogue", "GET", "/model-catalog", None),
    ("audit log", "GET", "/audit/logs", None),
]:
    attempt(label, method, url, read="search" in url, **({"json": body} if body is not None else {}))
if config_id:
    for label, method, url, body in [
        ("read LLM connection", "GET", f"/llm-config/{config_id}", None),
        ("edit LLM connection", "PUT", f"/llm-config/{config_id}", {"name": "changed"}),
        ("make it default", "POST", f"/llm-config/{config_id}/set-default", None),
        ("test LLM connection", "POST", f"/llm-config/{config_id}/test", None),
        ("delete LLM connection", "DELETE", f"/llm-config/{config_id}", None),
    ]:
        attempt(label, method, url, **({"json": body} if body is not None else {}))
attempt("delete template", "DELETE", f"/templates/{t}")
attempt("delete dataset", "DELETE", f"/datasets/db/{d}")

intact = (alice.get(f"/templates/{t}").status_code == 200
          and alice.get(f"/datasets/db/{d}").status_code == 200
          and alice.get(f"/datasets/status/{upload_task}").status_code == 200)
print(f"\nAlice's data intact and still hers: {intact}")
if failures or not intact:
    sys.exit(f"TENANCY BROKEN: {failures}")
print("PASS: Bob could not see or change anything of Alice's.")

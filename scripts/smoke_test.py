"""
End-to-end smoke test against a running stack, through the Next.js proxy.

    python scripts/smoke_test.py [http://localhost:3000]

Logs in as the demo tenant, routes a request, then exercises the full user loop:
create a template, upload utterances, auto-embed, route to it, delete it.
Requires: pip install httpx
"""
import io
import sys
import time

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
c = httpx.Client(base_url=BASE, timeout=120)


def check(label, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + label + (f"  ({detail})" if detail else ""))
    if not cond:
        sys.exit(1)


r = c.get("/")
check("landing page renders", r.status_code == 200 and "validated API call" in r.text)

r = c.post("/api/v1/auth/login/json", json={"email": "demo@nlpforge.dev", "password": "DemoForge!2026"})
check("demo login", r.status_code == 200, r.status_code)
token = next(v for k, v in c.cookies.items() if "access" in k)
c.headers["Authorization"] = f"Bearer {token}"  # Secure cookies are not replayed over http by httpx

r = c.get("/api/v1/templates")
check("templates list without trailing slash (no 307 to backend:8000)", r.status_code == 200 and len(r.json()) >= 20, r.status_code)

r = c.post("/api/v1/query/semantic-search", json={"query": "Refund 25 dollars on order 8820 because it arrived broken"})
d = r.json()
check("route demo query", d.get("api_name") == "Refund_Order", d.get("api_name"))
check("structured extraction", d["extraction"]["ok"] and d["extracted_request_body"].get("order_id") == "8820", d["extraction"])
check("not degraded", d["degraded"] is False)

# --- The user-data loop: own template -> upload utterances -> route to it ---
desc = ("Track a parcel shipment by its tracking number and return the carrier, current status, "
        "last scan location and estimated delivery date. ") * 30
tpl = {
    "api_name": "Track_Shipment",
    "description": desc,
    "base_url": "https://api.parcels.example",
    "endpoint": "/shipments/{tracking_number}",
    "method": "GET",
    "parameters": [{"name": "tracking_number", "type": "string", "required": True,
                    "example": "1Z999AA10123456784", "description": "Carrier tracking number of the parcel"}],
    "sample_requests": [
        {"scenario": "valid", "request": {"tracking_number": "1Z999AA10123456784"}},
        {"scenario": "edge_case", "request": {"tracking_number": "1z999aa10123456784"}},
        {"scenario": "error_case", "request": {}},
    ],
    "sample_responses": [
        {"status_code": 200, "response_body": {"status": "in_transit"}},
        {"status_code": 200, "response_body": {"status": "delivered"}},
        {"status_code": 422, "response_body": {"error": "VALIDATION_FAILED"}},
    ],
    "json_schema": {"type": "object", "properties": {"tracking_number": {"type": "string"}}, "required": ["tracking_number"]},
    "response_schema": {"type": "object", "properties": {"status": {"type": "string"}}},
    "domain_tags": ["logistics"],
}
r = c.post("/api/v1/templates", json=tpl)
check("create template", r.status_code == 201, f"{r.status_code} {r.text[:200]}")
t_id = r.json().get("template_id") or r.json().get("t_id")

utterances = ["where is my parcel 1Z999AA10123456784", "track shipment 1Z12345E0205271688",
              "has my package arrived yet, tracking 1Z999AA10123456784", "show delivery status for parcel 94001118992231",
              "when will shipment 1Z999AA1 be delivered", "trace my package with tracking number 7489234",
              "what's the latest scan for my parcel", "is my delivery still in transit"]
csv = "query,api_name,endpoint,method\n" + "\n".join(f'"{u}",Track_Shipment,/shipments/{{tracking_number}},GET' for u in utterances)
r = c.post(f"/api/v1/datasets/upload?template_id={t_id}", files={"file": ("../../evil.csv", io.BytesIO(csv.encode()), "text/csv")})
check("upload CSV (hostile filename accepted safely)", r.status_code == 200, f"{r.status_code} {r.text[:200]}")
up = r.json()
check("server-chosen filename", "/" not in up["file"] and ".." not in up["file"], up["file"])
ds_id = up["dataset_id"]

for _ in range(60):
    info = c.get(f"/api/v1/datasets/{ds_id}/embedding-status").json()
    if info.get("status") in ("completed", "failed"):
        break
    time.sleep(2)
check("auto-embed into pgvector", info.get("status") == "completed" and info.get("embedded_rows") == len(utterances), info)

r = c.post("/api/v1/query/semantic-search", json={"query": "where's my package 1Z999AA10123456784 right now?"})
d = r.json()
check("route to the user's own template", d.get("api_name") == "Track_Shipment", d.get("api_name"))
check("extract its field", d.get("extracted_request_body", {}).get("tracking_number") == "1Z999AA10123456784", d.get("extraction"))

r = c.get("/api/v1/stats")
check("dashboard stats count pgvector rows", r.json()["total_embeddings"] >= 100 + len(utterances), r.json()["total_embeddings"])

r = c.delete(f"/api/v1/datasets/db/{ds_id}")
check("delete dataset", r.status_code in (200, 204), r.status_code)
r = c.post("/api/v1/query/semantic-search", json={"query": "where's my package 1Z999AA10123456784 right now?", "include_slot_extraction": False})
check("deleted dataset no longer routes", r.json().get("api_name") != "Track_Shipment", r.json().get("api_name"))
r = c.delete(f"/api/v1/templates/{t_id}")
check("delete template (leave the demo tenant as it was)", r.status_code in (200, 204), r.status_code)
print("ALL CHECKS PASSED")

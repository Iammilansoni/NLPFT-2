"""Every demo template must pass the Template Builder's own completeness rules."""

import pytest

from app.demo_catalogue import API_TEMPLATES
from app.demo_catalogue_details import DETAILS, build_template_details


def test_every_catalogue_template_has_details():
    assert {t["api_name"] for t in API_TEMPLATES} == set(DETAILS)


@pytest.mark.parametrize("tpl", API_TEMPLATES, ids=lambda t: t["api_name"])
def test_template_meets_template_builder_requirements(tpl):
    d = build_template_details(tpl)

    # Same thresholds as /templates/{id}/validate in api/v1/template_builder.py.
    assert len(d["description"].split()) >= 500
    assert len(d["sample_requests"]) >= 3
    assert len(d["sample_responses"]) >= 3
    assert len(d["parameters"]) >= 1
    assert len(d["domain_tags"]) >= 1
    assert {s["scenario"] for s in d["sample_requests"]} >= {"valid", "edge_case", "error_case"}

    # Parameter rows mirror the request schema and are fully documented.
    schema_props = set(tpl["json_schema"]["properties"])
    assert {p["name"] for p in d["parameters"]} == schema_props
    for p in d["parameters"]:
        assert p["example"] is not None
        assert len(p["description"]) >= 10

    # The valid sample must satisfy the request schema's required fields.
    valid = d["sample_requests"][0]["request"]
    assert set(tpl["json_schema"].get("required", [])) <= set(valid)
    assert d["response_schema"]["type"] == "object"

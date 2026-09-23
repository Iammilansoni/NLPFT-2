"""The dataset-generation prompt must ask for real user phrasing of THIS API only."""

from app.demo_catalogue import TEMPLATES_BY_NAME
from app.demo_catalogue_details import build_template_details
from app.nlp.dataset_generator import EnterpriseDatasetGenerator


def _template(name: str) -> dict:
    tpl = TEMPLATES_BY_NAME[name]
    d = build_template_details(tpl)
    return {"name": name, "description": d["description"], "parameters": d["parameters"],
            "sample_requests": d["sample_requests"]}


def test_prompt_uses_the_templates_own_examples_and_scope():
    prompt = EnterpriseDatasetGenerator()._build_user_prompt(
        "Customers who want to cancel", 10, None, _template("Cancel_Order")
    )
    # Style examples come from Cancel_Order's own samples...
    assert "cancel order 5567" in prompt.lower()
    # ...never from a sibling API (these leaked into Cancel_Order datasets before).
    assert "where's my order" not in prompt.lower()
    # The user's instructions are included, and API jargon is explicitly banned.
    assert "Customers who want to cancel" in prompt
    assert "Do NOT mention the API name" in prompt


def test_prompt_without_samples_uses_an_unrelated_domain_example():
    prompt = EnterpriseDatasetGenerator()._build_user_prompt(
        "", 10, None, {"name": "X", "description": "Does X.", "parameters": [], "sample_requests": []}
    )
    assert "unrelated weather API" in prompt

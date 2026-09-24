"""Pure helpers of live model discovery (no network)."""

import pytest

from app.llm import model_discovery
from app.llm.model_discovery import DiscoveryError, _openrouter_entry


def test_hosted_providers_ignore_custom_base_urls():
    assert model_discovery._check_base_url("openai", "http://169.254.169.254/latest") is None


def test_metadata_address_is_refused():
    with pytest.raises(DiscoveryError):
        model_discovery._check_base_url("custom", "http://169.254.169.254/v1")


def test_name_classification():
    assert model_discovery._classify_by_name("text-embedding-3-small") == "embedding"
    assert model_discovery._classify_by_name("whisper-large-v3") is None
    assert model_discovery._classify_by_name("llama-3.3-70b-versatile") == "llm"


def test_openrouter_far_future_expiry_means_no_shutdown():
    entry = {"id": "m", "expiration_date": "2098-12-31", "pricing": {"prompt": "0", "completion": "0"}}
    model = _openrouter_entry(entry, "llm")
    assert model.shutdown_date is None and model.is_free is True

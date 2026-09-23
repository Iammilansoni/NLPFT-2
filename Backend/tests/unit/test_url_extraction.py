"""Base-URL detection must not mistake e-mail domains or version numbers for hosts."""

import pytest

from app.nlp.url_extraction import extract_url_from_query


@pytest.mark.parametrize(
    "query, expected",
    [
        ("Go to www.Example.com and login", "https://www.example.com"),
        ("Visit https://api.example.com/v1/users", "https://api.example.com/v1/users"),
        ("call api.shop.io/orders, please", "https://api.shop.io/orders"),
    ],
)
def test_detects_urls(query, expected):
    _, normalized = extract_url_from_query(query)
    assert normalized == expected


@pytest.mark.parametrize(
    "query",
    [
        "authenticate with email dana@shop.io and password Passw0rd",
        "cancel order 8820.5 now",
        "log me in",
        "",
    ],
)
def test_ignores_non_urls(query):
    assert extract_url_from_query(query) == (None, None)

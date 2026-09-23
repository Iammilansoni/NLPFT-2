"""
Base-URL detection in a natural-language request.

"Log in to www.shop.io with ..." should route to the template AND tell the caller
which host the user named, so the resolved request can target it instead of the
template's default base_url.

The v1 pattern matched any dotted token, so the domain half of an e-mail address
("dana@shop.io") was reported as a base URL. This version rejects tokens glued to
an '@' or another word character and requires an alphabetic TLD.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

_URL_RE = re.compile(
    r"(?<![\w@.])"                                   # not part of an e-mail or word
    r"(?P<url>"
    r"(?:https?://)?"
    r"(?:www\.)?"
    r"[a-z0-9](?:[-a-z0-9]*[a-z0-9])?"              # first label
    r"(?:\.[a-z0-9](?:[-a-z0-9]*[a-z0-9])?)*"       # middle labels
    r"\.[a-z]{2,24}"                                 # alphabetic TLD
    r"(?::\d{2,5})?"                                 # optional port
    r"(?:/[\w\-._~:/?#\[\]@!$&'()*+,;=%]*)?"         # optional path
    r")"
    r"(?![\w@])",
    re.IGNORECASE,
)

_TRAILING = ".,!?)]'\""


def extract_url_from_query(query: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Return (raw_url, normalized_url) for the first URL in `query`, else (None, None).

        "Go to www.example.com and login" -> ("www.example.com", "https://www.example.com")
        "email dana@shop.io"              -> (None, None)
    """
    if not query:
        return None, None

    match = _URL_RE.search(query)
    if not match:
        return None, None

    raw = match.group("url").rstrip(_TRAILING)
    if raw.lower().startswith(("http://", "https://")):
        normalized = raw
    else:
        normalized = f"https://{raw}"

    # Host names are case-insensitive; paths are not.
    scheme, _, rest = normalized.partition("://")
    host, sep, path = rest.partition("/")
    return raw, f"{scheme.lower()}://{host.lower()}{sep}{path}"

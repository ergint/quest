"""Crossref discovery via the official Crossref REST API (/works).

No HTML scraping. Every network call goes through `_http_get_json`, which is
injectable so tests can run entirely offline against canned JSON.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional

from . import DiscoveryAPIError, DiscoveryWindow, RateLimiter

HttpGetJson = Callable[[str, Dict[str, Any], Dict[str, str], float], Dict[str, Any]]

CROSSREF_SELECT_FIELDS = (
    "DOI,title,container-title,published,published-print,published-online,"
    "author,type,abstract,publisher,URL"
)


def _user_agent() -> str:
    mailto = os.environ.get("CROSSREF_MAILTO")
    base = "ResearchUnpacked-Discovery/1.0 (https://github.com/; mailto:{})"
    return base.format(mailto) if mailto else "ResearchUnpacked-Discovery/1.0"


def _http_get_json(url: str, params: Dict[str, Any], headers: Dict[str, str],
                    timeout: float) -> Dict[str, Any]:
    query = urllib.parse.urlencode(params)
    full_url = f"{url}?{query}"
    req = urllib.request.Request(full_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        raise DiscoveryAPIError(f"Crossref request failed ({full_url}): {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DiscoveryAPIError(f"Could not parse Crossref response ({full_url}): {exc}") from exc


def discover_crossref(
    config: Dict[str, Any],
    window: DiscoveryWindow,
    query_terms: List[str],
    limit: Optional[int] = None,
    http_get_json: HttpGetJson = _http_get_json,
) -> List[Dict[str, Any]]:
    """Queries Crossref once per topic term (query.bibliographic), restricted
    to the discovery window and journal-article type, until the configured
    (or --limit-overridden) budget is reached. Returns raw Crossref work
    items (the dicts under message.items)."""
    budget = config.get("max_results_per_source", 100)
    if limit is not None:
        budget = min(budget, limit)
    if budget <= 0 or not query_terms:
        return []

    limiter = RateLimiter(config.get("rate_limit_requests_per_second_no_key", 3))
    headers = {"User-Agent": _user_agent()}
    timeout = config.get("request_timeout_seconds", 20)

    filter_value = (
        f"type:journal-article,"
        f"from-pub-date:{window.start.isoformat()},"
        f"until-pub-date:{window.end.isoformat()}"
    )

    seen_dois = set()
    items: List[Dict[str, Any]] = []
    per_topic_rows = max(1, budget // max(1, len(query_terms)))

    for topic in query_terms:
        if len(items) >= budget:
            break
        rows = min(per_topic_rows, budget - len(items))
        params = {
            "query.bibliographic": topic,
            "filter": filter_value,
            "rows": rows,
            "select": CROSSREF_SELECT_FIELDS,
        }
        limiter.wait()
        data = http_get_json(config["crossref_api_url"], params, headers, timeout)
        for work in data.get("message", {}).get("items", []):
            doi = (work.get("DOI") or "").lower().strip()
            if doi and doi in seen_dois:
                continue
            if doi:
                seen_dois.add(doi)
            items.append(work)
            if len(items) >= budget:
                break

    return items

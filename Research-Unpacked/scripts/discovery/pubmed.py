"""PubMed discovery via the official NCBI E-utilities (esearch + efetch).

No HTML scraping. Every network call goes through `_http_get`, which is
injectable so tests can run entirely offline against canned XML/JSON.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Callable, Dict, List, Optional

from . import DiscoveryAPIError, DiscoveryWindow, RateLimiter

HttpGet = Callable[[str, Dict[str, Any], float], bytes]


def _http_get(url: str, params: Dict[str, Any], timeout: float) -> bytes:
    query = urllib.parse.urlencode(params)
    full_url = f"{url}?{query}"
    req = urllib.request.Request(
        full_url,
        headers={"User-Agent": "ResearchUnpacked-Discovery/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        raise DiscoveryAPIError(f"PubMed request failed ({full_url}): {exc}") from exc


def _api_key() -> Optional[str]:
    return os.environ.get("NCBI_API_KEY") or None


def search_pubmed_ids(
    config: Dict[str, Any],
    window: DiscoveryWindow,
    query_terms: List[str],
    limiter: RateLimiter,
    http_get: HttpGet = _http_get,
) -> List[str]:
    """Runs one esearch call combining query_terms with OR, restricted to the
    discovery window via mindate/maxdate. Returns a list of PMIDs."""
    if not query_terms:
        return []

    term = "(" + " OR ".join(f'"{t}"[tiab]' for t in query_terms) + ")"
    params = {
        "db": "pubmed",
        "term": term,
        "datetype": "pdat",
        "mindate": window.start.strftime("%Y/%m/%d"),
        "maxdate": window.end.strftime("%Y/%m/%d"),
        "retmax": config.get("max_results_per_source", 100),
        "retmode": "json",
    }
    api_key = _api_key()
    if api_key:
        params["api_key"] = api_key

    limiter.wait()
    raw = http_get(config["ncbi_esearch_url"], params, config.get("request_timeout_seconds", 20))
    try:
        data = json.loads(raw)
        return list(data.get("esearchresult", {}).get("idlist", []))
    except (json.JSONDecodeError, AttributeError, KeyError) as exc:
        raise DiscoveryAPIError(f"Could not parse PubMed esearch response: {exc}") from exc


def _text(el: Optional[ET.Element]) -> Optional[str]:
    if el is None:
        return None
    text = "".join(el.itertext()).strip()
    return text or None


def _parse_pub_date(article_el: ET.Element) -> Optional[str]:
    # Prefer the more precise ArticleDate (often the electronic pub date).
    article_date = article_el.find(".//ArticleDate")
    pub_date = article_date if article_date is not None else article_el.find(".//Journal/JournalIssue/PubDate")
    if pub_date is None:
        return None

    year = _text(pub_date.find("Year"))
    month = _text(pub_date.find("Month"))
    day = _text(pub_date.find("Day"))

    if not year:
        medline_date = _text(pub_date.find("MedlineDate"))
        if medline_date and len(medline_date) >= 4 and medline_date[:4].isdigit():
            year = medline_date[:4]
        else:
            return None

    month_map = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
        "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
    }
    if month and month.isdigit():
        month = month.zfill(2)
    else:
        month = month_map.get((month or "")[:3], "01")
    day = day.zfill(2) if day and day.isdigit() else "01"

    try:
        return f"{int(year):04d}-{month}-{day}"
    except ValueError:
        return None


def parse_pubmed_xml(xml_bytes: bytes) -> List[Dict[str, Any]]:
    """Parses an efetch XML response into a list of raw article dicts."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise DiscoveryAPIError(f"Could not parse PubMed efetch XML: {exc}") from exc

    records: List[Dict[str, Any]] = []
    for article_el in root.findall(".//PubmedArticle"):
        medline = article_el.find("MedlineCitation")
        if medline is None:
            continue
        article = medline.find("Article")
        pmid = _text(medline.find("PMID"))
        title = _text(article.find("ArticleTitle")) if article is not None else None
        journal_title = None
        if article is not None:
            journal_title = _text(article.find("Journal/Title")) or _text(article.find("Journal/ISOAbbreviation"))

        abstract_parts = []
        if article is not None:
            for ab in article.findall("Abstract/AbstractText"):
                text = _text(ab)
                if text:
                    label = ab.get("Label")
                    abstract_parts.append(f"{label}: {text}" if label else text)
        abstract = "\n".join(abstract_parts) if abstract_parts else None

        authors = []
        if article is not None:
            for author_el in article.findall("AuthorList/Author"):
                collective = _text(author_el.find("CollectiveName"))
                if collective:
                    authors.append(collective)
                    continue
                last = _text(author_el.find("LastName"))
                initials = _text(author_el.find("Initials"))
                if last:
                    authors.append(f"{last} {initials}" if initials else last)

        publication_types = []
        if article is not None:
            for pt in article.findall("PublicationTypeList/PublicationType"):
                text = _text(pt)
                if text:
                    publication_types.append(text)

        mesh_terms = []
        for mh in medline.findall("MeshHeadingList/MeshHeading/DescriptorName"):
            text = _text(mh)
            if text:
                mesh_terms.append(text)

        doi = None
        for id_el in article_el.findall(".//ArticleIdList/ArticleId"):
            if id_el.get("IdType") == "doi":
                doi = _text(id_el)
                break
        if doi is None and article is not None:
            for eloc in article.findall("ELocationID"):
                if eloc.get("EIdType") == "doi":
                    doi = _text(eloc)
                    break

        publication_date = _parse_pub_date(article) if article is not None else None

        records.append({
            "pmid": pmid,
            "title": title,
            "journal": journal_title,
            "publication_date": publication_date,
            "authors": authors,
            "publication_types": publication_types,
            "abstract": abstract,
            "doi": doi,
            "mesh_terms": mesh_terms,
            "original_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
        })
    return records


def fetch_pubmed_records(
    pmids: List[str],
    config: Dict[str, Any],
    limiter: RateLimiter,
    http_get: HttpGet = _http_get,
) -> List[Dict[str, Any]]:
    if not pmids:
        return []

    batch_size = config.get("pubmed_batch_size", 200)
    api_key = _api_key()
    records: List[Dict[str, Any]] = []

    for i in range(0, len(pmids), batch_size):
        batch = pmids[i:i + batch_size]
        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "rettype": "abstract",
            "retmode": "xml",
        }
        if api_key:
            params["api_key"] = api_key

        limiter.wait()
        raw = http_get(config["ncbi_efetch_url"], params, config.get("request_timeout_seconds", 20))
        records.extend(parse_pubmed_xml(raw))

    return records


def discover_pubmed(
    config: Dict[str, Any],
    window: DiscoveryWindow,
    query_terms: List[str],
    limit: Optional[int] = None,
    http_get: HttpGet = _http_get,
) -> List[Dict[str, Any]]:
    """Full PubMed discovery: esearch -> efetch -> raw article dicts."""
    api_key = _api_key()
    rate = (
        config.get("rate_limit_requests_per_second_with_key", 10)
        if api_key
        else config.get("rate_limit_requests_per_second_no_key", 3)
    )
    limiter = RateLimiter(rate)

    pmids = search_pubmed_ids(config, window, query_terms, limiter, http_get=http_get)
    if limit is not None:
        pmids = pmids[:limit]
    return fetch_pubmed_records(pmids, config, limiter, http_get=http_get)

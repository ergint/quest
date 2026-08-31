"""Deduplicates normalized candidates found by both PubMed and Crossref.

Matching priority, per spec: (1) normalized DOI, (2) PMID, (3) fallback
normalized-title similarity. Merging never deletes useful metadata — for
each field it prefers whichever record has the more complete (non-null,
non-empty) value, and list-valued fields (authors, discovery_sources, etc.)
are unioned rather than overwritten.
"""
from __future__ import annotations

import difflib
from typing import Any, Dict, List, Optional

from .normalize import make_candidate_id, normalize_title_for_matching

_LIST_FIELDS = ("discovery_sources", "authors", "mesh_terms", "publication_types",
                 "provisional_fields")


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _prefer(a: Any, b: Any) -> Any:
    """Prefer a if non-empty, else b."""
    return a if not _is_empty(a) else b


def merge_candidates(base: Dict[str, Any], other: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key in set(base.keys()) | set(other.keys()):
        if key in _LIST_FIELDS:
            combined = list(base.get(key) or [])
            for item in (other.get(key) or []):
                if item not in combined:
                    combined.append(item)
            merged[key] = combined
        elif key in ("scientific_components", "youtube_components"):
            # Discovery-time components are always all-null; keep base's shape.
            merged[key] = base.get(key) or other.get(key)
        else:
            merged[key] = _prefer(base.get(key), other.get(key))

    doi = merged.get("doi")
    pmid = merged.get("pmid")
    title = merged.get("exact_title")
    merged["id"] = make_candidate_id(doi, pmid, title)
    return merged


def _matches(a: Dict[str, Any], b: Dict[str, Any], title_threshold: float) -> bool:
    a_doi, b_doi = a.get("doi"), b.get("doi")
    if a_doi and b_doi:
        return a_doi == b_doi

    a_pmid, b_pmid = a.get("pmid"), b.get("pmid")
    if a_pmid and b_pmid:
        return a_pmid == b_pmid

    a_title = normalize_title_for_matching(a.get("exact_title"))
    b_title = normalize_title_for_matching(b.get("exact_title"))
    if not a_title or not b_title:
        return False
    ratio = difflib.SequenceMatcher(None, a_title, b_title).ratio()
    return ratio >= title_threshold


def deduplicate(records: List[Dict[str, Any]],
                 title_similarity_threshold: float = 0.92) -> List[Dict[str, Any]]:
    """Merges duplicate candidates. Order of `records` matters as a
    tie-breaker: earlier records act as the merge base, so run PubMed
    records through before Crossref records to prefer PubMed's richer
    abstract/MeSH metadata when both sources agree on a field."""
    clusters: List[Dict[str, Any]] = []

    for record in records:
        merged_into: Optional[int] = None
        for idx, cluster in enumerate(clusters):
            if _matches(cluster, record, title_similarity_threshold):
                merged_into = idx
                break
        if merged_into is None:
            clusters.append(dict(record))
        else:
            clusters[merged_into] = merge_candidates(clusters[merged_into], record)

    return clusters

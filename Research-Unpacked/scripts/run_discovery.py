#!/usr/bin/env python3
"""Stage 2A: PubMed + Crossref discovery ingestion (discovery only).

Fetches recent candidate research metadata from PubMed and Crossref,
normalizes it into one candidate format, deduplicates, applies a
conservative fast filter, and writes candidate JSON files to
research/inbox/. Every candidate is written with verification_status=YELLOW
and ranking_eligible=false — this script never assigns GREEN and never
computes scientific/YouTube scores. Promotion to GREEN happens later,
through the manual verification pipeline (prompts/verification.md).

Usage:
    python3 scripts/run_discovery.py [--dry-run] [--limit N]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.discovery import DiscoveryAPIError, compute_discovery_window  # noqa: E402
from scripts.discovery.crossref import discover_crossref  # noqa: E402
from scripts.discovery.deduplicate import deduplicate  # noqa: E402
from scripts.discovery.normalize import (  # noqa: E402
    apply_fast_filter,
    normalize_crossref_record,
    normalize_pubmed_record,
)
from scripts.discovery.pubmed import discover_pubmed  # noqa: E402

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ROOT_DIR / "config" / "discovery.json"
DEFAULT_INBOX_DIR = ROOT_DIR / "research" / "inbox"
DEFAULT_REPORTS_DIR = ROOT_DIR / "reports"


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@dataclass
class DiscoveryRunResult:
    pubmed_raw: List[Dict[str, Any]] = field(default_factory=list)
    crossref_raw: List[Dict[str, Any]] = field(default_factory=list)
    pubmed_error: Optional[str] = None
    crossref_error: Optional[str] = None
    deduplicated: List[Dict[str, Any]] = field(default_factory=list)
    kept: List[Dict[str, Any]] = field(default_factory=list)
    rejected: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def unique_count(self) -> int:
        return len(self.deduplicated)


def run_discovery(
    config: Dict[str, Any],
    discovered_at: Optional[str] = None,
    limit: Optional[int] = None,
    pubmed_http_get=None,
    crossref_http_get_json=None,
    today: Optional[_dt.date] = None,
) -> DiscoveryRunResult:
    """Runs the full discovery pipeline and returns the result in memory.
    Writing files is the caller's job (see main()) so this function is easy
    to test without touching disk."""
    discovered_at = discovered_at or _dt.datetime.now(_dt.timezone.utc).isoformat()
    window = compute_discovery_window(config.get("lookback_days", 30), today=today)

    pubmed_terms = config.get("pubmed_query_terms") or config.get("priority_topics", [])
    crossref_terms = config.get("crossref_query_terms") or config.get("priority_topics", [])

    result = DiscoveryRunResult()

    try:
        kwargs = {"http_get": pubmed_http_get} if pubmed_http_get is not None else {}
        result.pubmed_raw = discover_pubmed(config, window, pubmed_terms, limit=limit, **kwargs)
    except DiscoveryAPIError as exc:
        result.pubmed_error = str(exc)

    try:
        kwargs = {"http_get_json": crossref_http_get_json} if crossref_http_get_json is not None else {}
        result.crossref_raw = discover_crossref(config, window, crossref_terms, limit=limit, **kwargs)
    except DiscoveryAPIError as exc:
        result.crossref_error = str(exc)

    normalized: List[Dict[str, Any]] = []
    for raw in result.pubmed_raw:
        normalized.append(normalize_pubmed_record(raw, discovered_at))
    for raw in result.crossref_raw:
        normalized.append(normalize_crossref_record(raw, discovered_at))

    threshold = config.get("title_similarity_threshold", 0.92)
    result.deduplicated = deduplicate(normalized, title_similarity_threshold=threshold)

    for candidate in result.deduplicated:
        if not window.contains(candidate.get("publication_date")):
            candidate["discovery_filter_status"] = "rejected"
            candidate["discovery_filter_reason"] = (
                f"publication_date {candidate.get('publication_date')!r} is not "
                f"confirmed inside the discovery window [{window.start.isoformat()}, "
                f"{window.end.isoformat()}]"
            )
        else:
            apply_fast_filter(candidate, config)

        if candidate["discovery_filter_status"] == "rejected":
            result.rejected.append(candidate)
        else:
            result.kept.append(candidate)

    return result


def write_candidates(kept: List[Dict[str, Any]], inbox_dir: Path) -> List[Path]:
    inbox_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for candidate in kept:
        path = inbox_dir / f"{candidate['id']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(candidate, f, indent=2, ensure_ascii=False)
            f.write("\n")
        written.append(path)
    return written


def render_summary(result: DiscoveryRunResult, config: Dict[str, Any],
                    written_paths: Optional[List[Path]], dry_run: bool) -> str:
    today = _dt.date.today().isoformat()
    lines = [f"# Discovery Run — {today}", ""]
    lines.append(f"Mode: {'DRY RUN (no files written)' if dry_run else 'LIVE'}")
    lines.append("")
    lines.append(f"PubMed records fetched: {len(result.pubmed_raw)}")
    if result.pubmed_error:
        lines.append(f"  - PubMed error: {result.pubmed_error}")
    lines.append(f"Crossref records fetched: {len(result.crossref_raw)}")
    if result.crossref_error:
        lines.append(f"  - Crossref error: {result.crossref_error}")
    lines.append(f"Unique records after deduplication: {result.unique_count}")
    lines.append(f"Automatically rejected: {len(result.rejected)}")
    lines.append(f"Candidates written to inbox: {0 if dry_run else len(written_paths or [])}")
    lines.append("")

    journal_counts = Counter(
        c.get("journal") for c in result.deduplicated if c.get("journal")
    )
    if journal_counts:
        lines.append("Top journals represented:")
        for journal, count in journal_counts.most_common(10):
            lines.append(f"  - {journal}: {count}")
        lines.append("")

    type_counts = Counter()
    for c in result.deduplicated:
        for t in (c.get("publication_types") or [c.get("publication_status")]):
            if t:
                type_counts[t] += 1
    if type_counts:
        lines.append("Publication types:")
        for ptype, count in type_counts.most_common(10):
            lines.append(f"  - {ptype}: {count}")
        lines.append("")

    if result.rejected:
        lines.append("Rejected candidates:")
        for c in result.rejected:
            lines.append(f"  - {c.get('id')}: {c.get('discovery_filter_reason')}")
        lines.append("")

    lines.append(
        "No candidate in this report is scientifically verified. All kept "
        "candidates are written with verification_status=YELLOW and "
        "ranking_eligible=false; GREEN promotion requires the manual "
        "verification pipeline (prompts/verification.md)."
    )
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                         help="Run the full pipeline but write nothing to disk.")
    parser.add_argument("--limit", type=int, default=None,
                         help="Cap results per source (development/testing).")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--inbox-dir", type=Path, default=DEFAULT_INBOX_DIR)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    result = run_discovery(config, limit=args.limit)

    written_paths = None
    if not args.dry_run:
        written_paths = write_candidates(result.kept, args.inbox_dir)

    summary = render_summary(result, config, written_paths, dry_run=args.dry_run)
    print(summary)

    if not args.dry_run:
        args.reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = args.reports_dir / f"discovery-{_dt.date.today().isoformat()}.md"
        report_path.write_text(summary, encoding="utf-8")
        print(f"\nWritten to {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

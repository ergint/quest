"""Stage 2A discovery ingestion: PubMed + Crossref, discovery only.

Nothing in this package assigns verification_status GREEN or produces
scientific/YouTube scores. Every record it emits is YELLOW,
ranking_eligible=False, with null scoring fields, per
config/verification_rules.md and config/scoring_rules.md (both locked and
untouched by this stage).
"""
from __future__ import annotations

import datetime as _dt
import time
from dataclasses import dataclass
from typing import Optional


class DiscoveryAPIError(Exception):
    """Raised when a discovery source (PubMed or Crossref) cannot be reached
    or returns an unusable response. Callers should catch this per-source so
    one source failing does not prevent the other from being ingested."""


@dataclass
class DiscoveryWindow:
    start: _dt.date
    end: _dt.date

    def contains(self, date_str: Optional[str]) -> bool:
        if not date_str:
            return False
        try:
            d = _dt.date.fromisoformat(date_str[:10])
        except (ValueError, TypeError):
            return False
        return self.start <= d <= self.end


def compute_discovery_window(lookback_days: int,
                              today: Optional[_dt.date] = None) -> DiscoveryWindow:
    today = today or _dt.date.today()
    start = today - _dt.timedelta(days=lookback_days)
    return DiscoveryWindow(start=start, end=today)


class RateLimiter:
    """Simple sleep-based limiter respecting NCBI/Crossref request-rate
    etiquette. Not thread-safe; discovery runs are sequential in V1."""

    def __init__(self, requests_per_second: float):
        self.min_interval = 1.0 / requests_per_second if requests_per_second > 0 else 0.0
        self._last_call: Optional[float] = None

    def wait(self) -> None:
        if self.min_interval <= 0:
            return
        now = time.monotonic()
        if self._last_call is not None:
            elapsed = now - self._last_call
            remaining = self.min_interval - elapsed
            if remaining > 0:
                time.sleep(remaining)
        self._last_call = time.monotonic()

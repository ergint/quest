"""Ölçek testi (CLAUDE.md §8): 60 personel, 31 gün, 3 vardiya."""

import pytest

from solver.solve import solve


@pytest.mark.slow
def test_scale_60_nurses_31_days(make_request):
    request = make_request(
        nurse_count=60,
        period_days=31,
        default_requirements={"07-15": 8, "15-23": 8, "23-07": 5},
        time_limit_seconds=60.0,
    )
    result = solve(request)

    assert result.status in ("OPTIMAL", "FEASIBLE")
    assert result.violations == []

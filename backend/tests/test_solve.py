"""Uçtan uca çözücü testleri: küçük senaryolarda çözülebilirlik, sıfır ihlal ve adalet."""

from datetime import date

from solver.solve import solve
from solver.types import Nurse, SolveRequest


def test_small_feasible_scenario_has_no_violations(make_request):
    request = make_request(nurse_count=6, period_days=7)
    result = solve(request)

    assert result.status in ("OPTIMAL", "FEASIBLE")
    assert result.violations == []
    assert result.fairness is not None


def test_h5_unavailability_is_respected_end_to_end(example_profile):
    nurses = tuple(Nurse(id=f"H{i + 1}") for i in range(7))
    request = SolveRequest(
        profile=example_profile,
        nurses=nurses,
        period_start=date(2026, 9, 1),
        period_days=3,
        default_requirements={"07-15": 2, "15-23": 2, "23-07": 1},
        unavailable=frozenset({("H1", date(2026, 9, 1))}),
        time_limit_seconds=10.0,
    )
    result = solve(request)

    assert result.status in ("OPTIMAL", "FEASIBLE")
    assert result.violations == []
    assigned_first_day = {a.shift_code for a in result.assignments if a.nurse_id == "H1" and a.day == date(2026, 9, 1)}
    assert assigned_first_day == set()


def test_infeasible_scenario_is_reported_without_crashing(example_profile):
    """Gereken personel sayısı, müsait personel sayısını aştığında INFEASIBLE dönmeli."""
    nurses = tuple(Nurse(id=f"H{i + 1}") for i in range(2))
    request = SolveRequest(
        profile=example_profile,
        nurses=nurses,
        period_start=date(2026, 9, 1),
        period_days=1,
        default_requirements={"07-15": 5, "15-23": 0, "23-07": 0},
        time_limit_seconds=5.0,
    )
    result = solve(request)

    assert result.status == "INFEASIBLE"
    assert result.assignments == []

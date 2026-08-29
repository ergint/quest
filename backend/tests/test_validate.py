"""Bağımsız doğrulayıcının her katı kısıt için doğru ihlali yakaladığını kontrol eder.

Bu testler CP-SAT'a hiç dokunmaz: elle kurulmuş (senaryo, atama listesi) çiftleri
üzerinde validate.py'ı çağırır. Amaç, çözücüye güvenmeden çıktının doğrulanabildiğini
göstermektir (CLAUDE.md §8).
"""

from datetime import date

from solver.profiles import profile_from_dict
from solver.types import Assignment, Nurse, PersonalRestriction, SolveRequest
from solver.validate import validate_hard_constraints

PROFILE = profile_from_dict(
    {
        "name": "test-profili",
        "shift_types": [
            {"code": "07-15", "start_hour": 7, "duration_hours": 8, "is_night": False},
            {"code": "15-23", "start_hour": 15, "duration_hours": 8, "is_night": False},
            {"code": "23-07", "start_hour": 23, "duration_hours": 8, "is_night": True},
        ],
        "min_rest_hours_after_night": 11,
        "max_consecutive_work_days": 3,
        "max_period_hours": 40,
        "min_experienced_per_shift": 1,
    }
)


def _request(**overrides) -> SolveRequest:
    nurses = overrides.pop("nurses", (Nurse(id="H1"), Nurse(id="H2")))
    defaults = dict(
        profile=PROFILE,
        nurses=nurses,
        period_start=date(2026, 9, 1),
        period_days=5,
        default_requirements={"07-15": 1, "15-23": 1, "23-07": 1},
    )
    defaults.update(overrides)
    return SolveRequest(**defaults)


def test_valid_schedule_has_no_violations():
    request = _request(
        nurses=(Nurse(id="H1", is_experienced=True), Nurse(id="H2")),
        default_requirements={"07-15": 1, "15-23": 0, "23-07": 0},
        period_days=1,
    )
    assignments = [Assignment(nurse_id="H1", day=date(2026, 9, 1), shift_code="07-15")]
    assert validate_hard_constraints(assignments, request) == []


def test_h1_understaffed_shift_is_flagged():
    request = _request(default_requirements={"07-15": 2, "15-23": 0, "23-07": 0}, period_days=1)
    assignments = [Assignment(nurse_id="H1", day=date(2026, 9, 1), shift_code="07-15")]
    violations = validate_hard_constraints(assignments, request)
    assert any(v.startswith("H1") for v in violations)


def test_h2_two_shifts_same_day_is_flagged():
    request = _request(default_requirements={"07-15": 1, "15-23": 1, "23-07": 0}, period_days=1)
    assignments = [
        Assignment(nurse_id="H1", day=date(2026, 9, 1), shift_code="07-15"),
        Assignment(nurse_id="H1", day=date(2026, 9, 1), shift_code="15-23"),
    ]
    violations = validate_hard_constraints(assignments, request)
    assert any(v.startswith("H2") for v in violations)


def test_h3_no_rest_after_night_is_flagged():
    request = _request(default_requirements={"07-15": 1, "15-23": 0, "23-07": 1}, period_days=2)
    assignments = [
        Assignment(nurse_id="H1", day=date(2026, 9, 1), shift_code="23-07"),
        Assignment(nurse_id="H1", day=date(2026, 9, 2), shift_code="07-15"),
    ]
    violations = validate_hard_constraints(assignments, request)
    assert any(v.startswith("H3") for v in violations)


def test_h4_too_many_consecutive_days_is_flagged():
    request = _request(default_requirements={"07-15": 1, "15-23": 0, "23-07": 0}, period_days=4)
    assignments = [Assignment(nurse_id="H1", day=date(2026, 9, 1 + i), shift_code="07-15") for i in range(4)]
    violations = validate_hard_constraints(assignments, request)
    assert any(v.startswith("H4") for v in violations)


def test_h5_assignment_while_unavailable_is_flagged():
    request = _request(
        default_requirements={"07-15": 1, "15-23": 0, "23-07": 0},
        period_days=1,
        unavailable=frozenset({("H1", date(2026, 9, 1))}),
    )
    assignments = [Assignment(nurse_id="H1", day=date(2026, 9, 1), shift_code="07-15")]
    violations = validate_hard_constraints(assignments, request)
    assert any(v.startswith("H5") for v in violations)


def test_h6_over_period_hour_limit_is_flagged():
    request = _request(
        nurses=(Nurse(id="H1"),),
        default_requirements={"07-15": 0, "15-23": 0, "23-07": 1},
        period_days=6,
    )
    assignments = [Assignment(nurse_id="H1", day=date(2026, 9, 1 + i), shift_code="23-07") for i in range(6)]
    violations = validate_hard_constraints(assignments, request)
    assert any(v.startswith("H6") for v in violations)


def test_h7_missing_experienced_nurse_is_flagged():
    request = _request(default_requirements={"07-15": 1, "15-23": 0, "23-07": 0}, period_days=1)
    assignments = [Assignment(nurse_id="H2", day=date(2026, 9, 1), shift_code="07-15")]
    violations = validate_hard_constraints(assignments, request)
    assert any(v.startswith("H7") for v in violations)


def test_h8_restricted_assignment_is_flagged():
    restriction = PersonalRestriction(
        nurse_id="H1", start_date=date(2026, 9, 1), end_date=date(2026, 9, 1), shift_code="23-07"
    )
    request = _request(
        default_requirements={"07-15": 0, "15-23": 0, "23-07": 1},
        period_days=1,
        personal_restrictions=(restriction,),
    )
    assignments = [Assignment(nurse_id="H1", day=date(2026, 9, 1), shift_code="23-07")]
    violations = validate_hard_constraints(assignments, request)
    assert any(v.startswith("H8") for v in violations)

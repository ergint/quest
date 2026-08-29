"""Çözücü orkestrasyon: modeli kurar, kısıtları ekler, çözer, bağımsız doğrular."""

from ortools.sat.python import cp_model

from . import fairness, model as model_mod, validate
from .constraints import hard, soft
from .types import Assignment, SolveRequest, SolveResult

HARD_CONSTRAINTS = (
    hard.add_h1_coverage,
    hard.add_h2_one_shift_per_day,
    hard.add_h3_rest_after_night,
    hard.add_h4_max_consecutive_days,
    hard.add_h5_unavailability,
    hard.add_h6_max_period_hours,
    hard.add_h7_skill_mix,
    hard.add_h8_personal_restrictions,
)

# Aşama 1 kapsamı: yalnızca temel adalet (S1, S2). Bkz. constraints/soft.py docstring'i.
SOFT_CONSTRAINTS = (
    soft.add_s1_night_balance,
    soft.add_s2_weekend_balance,
)


def solve(request: SolveRequest) -> SolveResult:
    model, mv = model_mod.build(request)

    for add_constraint in HARD_CONSTRAINTS:
        add_constraint(model, mv, request)

    penalty_terms: list[object] = []
    for add_soft_constraint in SOFT_CONSTRAINTS:
        penalty_terms += add_soft_constraint(model, mv, request)

    if penalty_terms:
        model.Minimize(sum(penalty_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = request.time_limit_seconds

    status = solver.Solve(model)
    status_name = solver.StatusName(status)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return SolveResult(status=status_name, assignments=[], objective_value=None, fairness=None)

    assignments = [
        Assignment(nurse_id=nurse.id, day=day, shift_code=shift.code)
        for nurse in request.nurses
        for day in mv.dates
        for shift in request.profile.shift_types
        if solver.Value(mv.x[(nurse.id, day, shift.code)])
    ]

    objective_value = solver.ObjectiveValue() if penalty_terms else None
    fairness_report = fairness.build_report(assignments, request)
    violations = validate.validate_hard_constraints(assignments, request)

    return SolveResult(
        status=status_name,
        assignments=assignments,
        objective_value=objective_value,
        fairness=fairness_report,
        violations=violations,
    )

"""Esnek kısıtlar (soft). Aşama 1 kapsamı yalnızca S1 ve S2'dir (CLAUDE.md §10:
'katı kısıtlar + temel adalet'). S3-S7, ilgili ürün özellikleri (talep toplama,
eşleştirme vb.) geldikçe ayrı fonksiyonlar olarak eklenir."""

from ortools.sat.python import cp_model

from .. import fairness
from ..model import ModelVars
from ..types import SolveRequest


def add_s1_night_balance(model: cp_model.CpModel, mv: ModelVars, request: SolveRequest) -> list[object]:
    """S1 — gece nöbeti sayısı kişiler arasında dengeli."""
    night_shifts = [shift for shift in request.profile.shift_types if shift.is_night]
    if not night_shifts or request.weight_s1_night_balance <= 0:
        return []

    counts = {
        nurse.id: sum(mv.x[(nurse.id, day, shift.code)] for day in mv.dates for shift in night_shifts)
        for nurse in request.nurses
    }
    target_total = sum(request.required_staff(day, shift.code) for day in mv.dates for shift in night_shifts)

    return fairness.deviation_penalty(
        model, counts, target_total, len(request.nurses), request.weight_s1_night_balance, "night"
    )


def add_s2_weekend_balance(model: cp_model.CpModel, mv: ModelVars, request: SolveRequest) -> list[object]:
    """S2 — hafta sonu nöbeti kişiler arasında dengeli."""
    weekend_dates = [day for day in mv.dates if day.weekday() >= 5]
    if not weekend_dates or request.weight_s2_weekend_balance <= 0:
        return []

    counts = {nurse.id: sum(mv.worked[(nurse.id, day)] for day in weekend_dates) for nurse in request.nurses}
    target_total = sum(
        request.required_staff(day, shift.code) for day in weekend_dates for shift in request.profile.shift_types
    )

    return fairness.deviation_penalty(
        model, counts, target_total, len(request.nurses), request.weight_s2_weekend_balance, "weekend"
    )

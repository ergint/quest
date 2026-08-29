"""Katı kısıtlar (H1-H8). Her kısıt ayrı bir fonksiyondur, tek bir dev fonksiyona yığılmaz."""

from ortools.sat.python import cp_model

from ..model import ModelVars
from ..types import SolveRequest


def add_h1_coverage(model: cp_model.CpModel, mv: ModelVars, request: SolveRequest) -> None:
    """H1 — her gün her vardiyada gereken personel sayısı karşılanır."""
    for day in mv.dates:
        for shift in request.profile.shift_types:
            required = request.required_staff(day, shift.code)
            terms = [mv.x[(nurse.id, day, shift.code)] for nurse in request.nurses]
            model.Add(sum(terms) == required)


def add_h2_one_shift_per_day(model: cp_model.CpModel, mv: ModelVars, request: SolveRequest) -> None:
    """H2 — bir kişi günde en fazla bir vardiya."""
    for nurse in request.nurses:
        for day in mv.dates:
            terms = [mv.x[(nurse.id, day, shift.code)] for shift in request.profile.shift_types]
            model.Add(sum(terms) <= 1)


def add_h3_rest_after_night(model: cp_model.CpModel, mv: ModelVars, request: SolveRequest) -> None:
    """H3 — gece vardiyasından sonra minimum dinlenme süresi."""
    profile = request.profile
    dates = mv.dates
    for shift in profile.shift_types:
        forbidden = profile.forbidden_next_day_shifts(shift)
        if not forbidden:
            continue
        for i in range(len(dates) - 1):
            day, next_day = dates[i], dates[i + 1]
            for nurse in request.nurses:
                for forbidden_shift in forbidden:
                    model.Add(
                        mv.x[(nurse.id, day, shift.code)] + mv.x[(nurse.id, next_day, forbidden_shift.code)] <= 1
                    )


def add_h4_max_consecutive_days(model: cp_model.CpModel, mv: ModelVars, request: SolveRequest) -> None:
    """H4 — ardışık çalışma günü üst sınırı."""
    limit = request.profile.max_consecutive_work_days
    dates = mv.dates
    window = limit + 1
    if len(dates) < window:
        return
    for nurse in request.nurses:
        for start in range(len(dates) - window + 1):
            terms = [mv.worked[(nurse.id, dates[start + k])] for k in range(window)]
            model.Add(sum(terms) <= limit)


def add_h5_unavailability(model: cp_model.CpModel, mv: ModelVars, request: SolveRequest) -> None:
    """H5 — izinli / raporlu / eğitimde olan kişiye atama yapılmaz."""
    for nurse in request.nurses:
        for day in mv.dates:
            if (nurse.id, day) in request.unavailable:
                for shift in request.profile.shift_types:
                    model.Add(mv.x[(nurse.id, day, shift.code)] == 0)


def add_h6_max_period_hours(model: cp_model.CpModel, mv: ModelVars, request: SolveRequest) -> None:
    """H6 — dönemsel toplam çalışma saati üst sınırı."""
    for nurse in request.nurses:
        limit = nurse.max_period_hours_override or request.profile.max_period_hours
        terms = [
            mv.x[(nurse.id, day, shift.code)] * shift.duration_hours
            for day in mv.dates
            for shift in request.profile.shift_types
        ]
        model.Add(sum(terms) <= limit)


def add_h7_skill_mix(model: cp_model.CpModel, mv: ModelVars, request: SolveRequest) -> None:
    """H7 — beceri karışımı: çalışılan her vardiyada en az N deneyimli personel."""
    minimum = request.profile.min_experienced_per_shift
    if minimum <= 0:
        return
    experienced_ids = {nurse.id for nurse in request.nurses if nurse.is_experienced}
    for day in mv.dates:
        for shift in request.profile.shift_types:
            required = request.required_staff(day, shift.code)
            if required <= 0:
                continue  # o gün o vardiya hiç çalışılmıyorsa deneyim şartı da yok
            terms = [mv.x[(nurse_id, day, shift.code)] for nurse_id in experienced_ids]
            model.Add(sum(terms) >= min(minimum, required))


def add_h8_personal_restrictions(model: cp_model.CpModel, mv: ModelVars, request: SolveRequest) -> None:
    """H8 — kişiye özel çalışma kısıtlamaları. Sebep saklanmaz, yalnızca kısıt ve tarih aralığı."""
    for restriction in request.personal_restrictions:
        for day in mv.dates:
            if not (restriction.start_date <= day <= restriction.end_date):
                continue
            shifts = (
                [request.profile.shift_by_code(restriction.shift_code)]
                if restriction.shift_code
                else list(request.profile.shift_types)
            )
            for shift in shifts:
                key = (restriction.nurse_id, day, shift.code)
                if key in mv.x:
                    model.Add(mv.x[key] == 0)

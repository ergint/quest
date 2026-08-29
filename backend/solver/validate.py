"""Bağımsız katı kısıt doğrulayıcı.

CLAUDE.md §8: 'Üretilen her çözüm için tüm katı kısıtlar bağımsız bir doğrulayıcı
fonksiyonla kontrol edilir. Çözücüye güvenilmez, çıktı doğrulanır.'

Bu modül CP-SAT'a hiç dokunmaz; yalnızca üretilen atama listesini düz Python
mantığıyla, constraints/hard.py'dan bağımsız olarak yeniden kontrol eder.
"""

from collections import defaultdict
from datetime import timedelta

from .types import Assignment, SolveRequest


def validate_hard_constraints(assignments: list[Assignment], request: SolveRequest) -> list[str]:
    violations: list[str] = []
    violations += _check_h1_coverage(assignments, request)
    violations += _check_h2_one_shift_per_day(assignments, request)
    violations += _check_h3_rest_after_night(assignments, request)
    violations += _check_h4_max_consecutive_days(assignments, request)
    violations += _check_h5_unavailability(assignments, request)
    violations += _check_h6_max_period_hours(assignments, request)
    violations += _check_h7_skill_mix(assignments, request)
    violations += _check_h8_personal_restrictions(assignments, request)
    return violations


def _by_nurse_day(assignments: list[Assignment]) -> dict[str, dict]:
    schedule: dict[str, dict] = defaultdict(dict)
    for assignment in assignments:
        schedule[assignment.nurse_id][assignment.day] = assignment.shift_code
    return schedule


def _check_h1_coverage(assignments: list[Assignment], request: SolveRequest) -> list[str]:
    violations = []
    counts: dict[tuple, int] = defaultdict(int)
    for assignment in assignments:
        counts[(assignment.day, assignment.shift_code)] += 1
    for day in request.dates():
        for shift in request.profile.shift_types:
            required = request.required_staff(day, shift.code)
            actual = counts.get((day, shift.code), 0)
            if actual != required:
                violations.append(f"H1 ihlali: {day} {shift.code} için {required} gerekli, {actual} atanmış")
    return violations


def _check_h2_one_shift_per_day(assignments: list[Assignment], request: SolveRequest) -> list[str]:
    violations = []
    counts: dict[tuple, int] = defaultdict(int)
    for assignment in assignments:
        counts[(assignment.nurse_id, assignment.day)] += 1
    for (nurse_id, day), count in counts.items():
        if count > 1:
            violations.append(f"H2 ihlali: {nurse_id} {day} tarihinde {count} vardiyaya atanmış")
    return violations


def _check_h3_rest_after_night(assignments: list[Assignment], request: SolveRequest) -> list[str]:
    violations = []
    schedule_by_nurse = _by_nurse_day(assignments)
    dates = request.dates()
    for nurse in request.nurses:
        schedule = schedule_by_nurse.get(nurse.id, {})
        for i in range(len(dates) - 1):
            day, next_day = dates[i], dates[i + 1]
            code, next_code = schedule.get(day), schedule.get(next_day)
            if code is None or next_code is None:
                continue
            shift = request.profile.shift_by_code(code)
            forbidden_codes = {s.code for s in request.profile.forbidden_next_day_shifts(shift)}
            if next_code in forbidden_codes:
                violations.append(
                    f"H3 ihlali: {nurse.id} {day} {code} sonrası {next_day} {next_code} yeterli dinlenme vermiyor"
                )
    return violations


def _check_h4_max_consecutive_days(assignments: list[Assignment], request: SolveRequest) -> list[str]:
    violations = []
    schedule_by_nurse = _by_nurse_day(assignments)
    limit = request.profile.max_consecutive_work_days
    for nurse in request.nurses:
        schedule = schedule_by_nurse.get(nurse.id, {})
        streak = 0
        for day in request.dates():
            if day in schedule:
                streak += 1
                if streak > limit:
                    violations.append(f"H4 ihlali: {nurse.id} {day} itibarıyla {streak} ardışık gün (sınır {limit})")
            else:
                streak = 0
    return violations


def _check_h5_unavailability(assignments: list[Assignment], request: SolveRequest) -> list[str]:
    violations = []
    for assignment in assignments:
        if (assignment.nurse_id, assignment.day) in request.unavailable:
            violations.append(
                f"H5 ihlali: {assignment.nurse_id} müsait değilken {assignment.day} {assignment.shift_code} atanmış"
            )
    return violations


def _check_h6_max_period_hours(assignments: list[Assignment], request: SolveRequest) -> list[str]:
    violations = []
    totals: dict[str, int] = defaultdict(int)
    for assignment in assignments:
        shift = request.profile.shift_by_code(assignment.shift_code)
        totals[assignment.nurse_id] += shift.duration_hours
    for nurse in request.nurses:
        limit = nurse.max_period_hours_override or request.profile.max_period_hours
        if totals[nurse.id] > limit:
            violations.append(f"H6 ihlali: {nurse.id} toplam {totals[nurse.id]} saat, sınır {limit}")
    return violations


def _check_h7_skill_mix(assignments: list[Assignment], request: SolveRequest) -> list[str]:
    violations = []
    minimum = request.profile.min_experienced_per_shift
    if minimum <= 0:
        return violations
    experienced_ids = {nurse.id for nurse in request.nurses if nurse.is_experienced}
    counts: dict[tuple, int] = defaultdict(int)
    for assignment in assignments:
        if assignment.nurse_id in experienced_ids:
            counts[(assignment.day, assignment.shift_code)] += 1
    for day in request.dates():
        for shift in request.profile.shift_types:
            required = request.required_staff(day, shift.code)
            if required <= 0:
                continue  # o gün o vardiya hiç çalışılmıyorsa deneyim şartı da yok
            threshold = min(minimum, required)
            if counts.get((day, shift.code), 0) < threshold:
                violations.append(
                    f"H7 ihlali: {day} {shift.code} vardiyasında en az {threshold} deneyimli personel yok"
                )
    return violations


def _check_h8_personal_restrictions(assignments: list[Assignment], request: SolveRequest) -> list[str]:
    violations = []
    assigned = {(a.nurse_id, a.day, a.shift_code) for a in assignments}
    for restriction in request.personal_restrictions:
        day = restriction.start_date
        while day <= restriction.end_date:
            codes = (
                [restriction.shift_code]
                if restriction.shift_code
                else [s.code for s in request.profile.shift_types]
            )
            for code in codes:
                if (restriction.nurse_id, day, code) in assigned:
                    violations.append(f"H8 ihlali: {restriction.nurse_id} kısıtlı olduğu {day} {code} atanmış")
            day += timedelta(days=1)
    return violations

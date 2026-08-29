"""Adalet hesabı: hedeften sapma cezası ve çözüm sonrası adalet raporu.

Not: dönemler arası devir bakiyesi (CLAUDE.md §3, "Dönemler arası devir") kasıtlı
olarak burada YOK — yol haritasında (§10) Aşama 6 çıktısı olarak ayrılmıştır.
Bu modül yalnızca tek dönem içi adaleti (S1, S2) hesaplar.
"""

from collections import defaultdict

from ortools.sat.python import cp_model

from .types import Assignment, FairnessReport, SolveRequest


def deviation_penalty(
    model: cp_model.CpModel,
    counts: dict[str, object],
    target_total: int,
    n_count: int,
    weight: float,
    label: str,
) -> list[object]:
    """Kişi başına sayının kişi başı ortalamadan sapmasını cezalandırır.

    Yalnızca maksimum-minimum farkı yeterli değildir (CLAUDE.md §3); sapmaların
    toplamı ve maksimum sapma birlikte cezalandırılır. Kesirli ortalamadan
    kaçınmak için sapma `n_count * count - target_total` olarak ölçeklenir.
    """
    if weight <= 0 or n_count == 0:
        return []

    bound = n_count * 366 + abs(target_total) + 1  # bir yıllık dönemi kapsayacak güvenli üst sınır
    abs_devs = []
    for nurse_id, count_expr in counts.items():
        scaled = model.NewIntVar(-bound, bound, f"scaled_dev_{label}_{nurse_id}")
        model.Add(scaled == n_count * count_expr - target_total)
        abs_dev = model.NewIntVar(0, bound, f"abs_dev_{label}_{nurse_id}")
        model.AddAbsEquality(abs_dev, scaled)
        abs_devs.append(abs_dev)

    max_dev = model.NewIntVar(0, bound, f"max_dev_{label}")
    model.AddMaxEquality(max_dev, abs_devs)

    return [weight * sum(abs_devs), weight * max_dev]


def build_report(assignments: list[Assignment], request: SolveRequest) -> FairnessReport:
    """Çözüm sonrası, gerçek atamalardan hesaplanan bağımsız adalet raporu."""
    night_codes = {shift.code for shift in request.profile.shift_types if shift.is_night}
    weekend_dates = {day for day in request.dates() if day.weekday() >= 5}

    night_count: dict[str, int] = defaultdict(int)
    weekend_count: dict[str, int] = defaultdict(int)
    for nurse in request.nurses:
        night_count[nurse.id] = 0
        weekend_count[nurse.id] = 0

    for assignment in assignments:
        if assignment.shift_code in night_codes:
            night_count[assignment.nurse_id] += 1
        if assignment.day in weekend_dates:
            weekend_count[assignment.nurse_id] += 1

    n_count = len(request.nurses) or 1
    night_target = sum(night_count.values()) / n_count
    weekend_target = sum(weekend_count.values()) / n_count

    return FairnessReport(
        night_count=dict(night_count),
        weekend_count=dict(weekend_count),
        night_target=night_target,
        weekend_target=weekend_target,
    )

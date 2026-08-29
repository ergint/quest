"""Nöbet çözücüsünün veri modeli. Bu modül saf Python'dur, CP-SAT'a bağımlı değildir."""

from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass(frozen=True)
class ShiftType:
    code: str
    start_hour: int
    duration_hours: int
    is_night: bool = False

    def __post_init__(self) -> None:
        if int(self.start_hour) != self.start_hour or int(self.duration_hours) != self.duration_hours:
            raise ValueError("ShiftType saat değerleri tam sayı olmalı (dakika hassasiyeti şu an desteklenmiyor)")

    @property
    def end_hour(self) -> int:
        return self.start_hour + self.duration_hours


@dataclass(frozen=True)
class ServiceProfile:
    """Vardiya tipleri, süreleri ve dinlenme kuralları servis profilinden okunur, kodda sabitlenmez."""

    name: str
    shift_types: tuple[ShiftType, ...]
    min_rest_hours_after_night: int
    max_consecutive_work_days: int
    max_period_hours: int
    min_experienced_per_shift: int = 0

    def shift_by_code(self, code: str) -> ShiftType:
        for shift in self.shift_types:
            if shift.code == code:
                return shift
        raise KeyError(f"Bilinmeyen vardiya kodu: {code}")

    def forbidden_next_day_shifts(self, shift: ShiftType) -> tuple[ShiftType, ...]:
        """H3 — bir gece vardiyasından sonra, minimum dinlenmeyi ihlal eden ertesi gün vardiyaları."""
        if not shift.is_night:
            return ()
        forbidden = []
        for other in self.shift_types:
            rest = (other.start_hour + 24) - shift.end_hour
            if rest < self.min_rest_hours_after_night:
                forbidden.append(other)
        return tuple(forbidden)


@dataclass(frozen=True)
class Nurse:
    id: str
    is_experienced: bool = False
    max_period_hours_override: int | None = None


@dataclass(frozen=True)
class PersonalRestriction:
    """H8 — sistem sebebi saklamaz, yalnızca 'bu kişi bu vardiyaya atanamaz' bilgisi tutulur."""

    nurse_id: str
    start_date: date
    end_date: date
    shift_code: str | None = None  # None -> tüm vardiyalar


@dataclass(frozen=True)
class Assignment:
    nurse_id: str
    day: date
    shift_code: str


@dataclass
class FairnessReport:
    night_count: dict[str, int]
    weekend_count: dict[str, int]
    night_target: float
    weekend_target: float


@dataclass
class SolveResult:
    status: str  # "OPTIMAL" | "FEASIBLE" | "INFEASIBLE" | "UNKNOWN"
    assignments: list[Assignment]
    objective_value: float | None
    fairness: FairnessReport | None
    violations: list[str] = field(default_factory=list)


@dataclass
class SolveRequest:
    profile: ServiceProfile
    nurses: tuple[Nurse, ...]
    period_start: date
    period_days: int
    default_requirements: dict[str, int]
    requirement_overrides: dict[date, dict[str, int]] = field(default_factory=dict)
    unavailable: frozenset[tuple[str, date]] = field(default_factory=frozenset)
    personal_restrictions: tuple[PersonalRestriction, ...] = field(default_factory=tuple)
    weight_s1_night_balance: float = 100.0
    weight_s2_weekend_balance: float = 100.0
    time_limit_seconds: float = 60.0

    def dates(self) -> list[date]:
        return [self.period_start + timedelta(days=i) for i in range(self.period_days)]

    def required_staff(self, day: date, shift_code: str) -> int:
        overrides = self.requirement_overrides.get(day)
        if overrides and shift_code in overrides:
            return overrides[shift_code]
        return self.default_requirements.get(shift_code, 0)

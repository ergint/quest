"""Servis profili yükleme.

Gerçek servis profilleri (vardiya saatleri, dinlenme süresi, ardışık gün sınırı vb.)
Aşama 0 keşif sürecinin çıktısı olan `docs/rules/<servis>.md` dosyalarından türetilip
buraya (JSON/dict olarak) girilmelidir. Bu modüldeki EXAMPLE_PROFILE yalnızca test ve
geliştirme amaçlıdır; hiçbir gerçek hastanenin kuralını temsil etmez.
"""

from .types import ServiceProfile, ShiftType


def profile_from_dict(data: dict) -> ServiceProfile:
    shift_types = tuple(
        ShiftType(
            code=s["code"],
            start_hour=s["start_hour"],
            duration_hours=s["duration_hours"],
            is_night=s.get("is_night", False),
        )
        for s in data["shift_types"]
    )
    return ServiceProfile(
        name=data["name"],
        shift_types=shift_types,
        min_rest_hours_after_night=data["min_rest_hours_after_night"],
        max_consecutive_work_days=data["max_consecutive_work_days"],
        max_period_hours=data["max_period_hours"],
        min_experienced_per_shift=data.get("min_experienced_per_shift", 0),
    )


# Yalnızca test/geliştirme içindir — bkz. modül docstring'i.
EXAMPLE_PROFILE_3_SHIFT = profile_from_dict(
    {
        "name": "örnek-3-vardiya (gerçek veri değil)",
        "shift_types": [
            {"code": "07-15", "start_hour": 7, "duration_hours": 8, "is_night": False},
            {"code": "15-23", "start_hour": 15, "duration_hours": 8, "is_night": False},
            {"code": "23-07", "start_hour": 23, "duration_hours": 8, "is_night": True},
        ],
        "min_rest_hours_after_night": 11,
        "max_consecutive_work_days": 5,
        "max_period_hours": 180,
        "min_experienced_per_shift": 0,
    }
)

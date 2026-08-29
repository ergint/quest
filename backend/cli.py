"""Nöbet çözücü CLI (Aşama 1: CLI ile çalışır, UI yok — CLAUDE.md §10).

Girdi: tek bir JSON dosyası (profil, personel, gereksinimler, izinler, kısıtlamalar,
ağırlıklar). Çıktı: atama listesi, adalet raporu ve bağımsız doğrulayıcının bulguları.

Örnek: python cli.py girdi.json -o cikti.json
"""

import argparse
import json
import sys
from datetime import date

from solver import profiles
from solver.solve import solve
from solver.types import Nurse, PersonalRestriction, SolveRequest, SolveResult


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def load_request(data: dict) -> SolveRequest:
    profile = profiles.profile_from_dict(data["profile"])

    nurses = tuple(
        Nurse(
            id=n["id"],
            is_experienced=n.get("is_experienced", False),
            max_period_hours_override=n.get("max_period_hours_override"),
        )
        for n in data["nurses"]
    )

    personal_restrictions = tuple(
        PersonalRestriction(
            nurse_id=r["nurse_id"],
            start_date=_parse_date(r["start_date"]),
            end_date=_parse_date(r["end_date"]),
            shift_code=r.get("shift_code"),
        )
        for r in data.get("personal_restrictions", [])
    )

    unavailable = frozenset((nurse_id, _parse_date(day)) for nurse_id, day in data.get("unavailable", []))

    requirement_overrides = {
        _parse_date(day): reqs for day, reqs in data.get("requirement_overrides", {}).items()
    }

    weights = data.get("weights", {})

    return SolveRequest(
        profile=profile,
        nurses=nurses,
        period_start=_parse_date(data["period_start"]),
        period_days=data["period_days"],
        default_requirements=data["default_requirements"],
        requirement_overrides=requirement_overrides,
        unavailable=unavailable,
        personal_restrictions=personal_restrictions,
        weight_s1_night_balance=weights.get("s1_night_balance", 100.0),
        weight_s2_weekend_balance=weights.get("s2_weekend_balance", 100.0),
        time_limit_seconds=data.get("time_limit_seconds", 60.0),
    )


def result_to_dict(result: SolveResult) -> dict:
    return {
        "status": result.status,
        "objective_value": result.objective_value,
        "assignments": [
            {"nurse_id": a.nurse_id, "day": a.day.isoformat(), "shift_code": a.shift_code}
            for a in result.assignments
        ],
        "fairness": None
        if result.fairness is None
        else {
            "night_count": result.fairness.night_count,
            "weekend_count": result.fairness.weekend_count,
            "night_target": result.fairness.night_target,
            "weekend_target": result.fairness.weekend_target,
        },
        "violations": result.violations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Nöbet çözücü (Aşama 1 — CLI)")
    parser.add_argument("input", help="Girdi JSON dosyası")
    parser.add_argument("-o", "--output", help="Çıktı JSON dosyası (verilmezse stdout)")
    args = parser.parse_args(argv)

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    request = load_request(data)
    result = solve(request)
    output = json.dumps(result_to_dict(result), ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)

    if result.violations:
        print(f"UYARI: bağımsız doğrulayıcı {len(result.violations)} katı kısıt ihlali buldu", file=sys.stderr)
        return 2

    return 0 if result.status in ("OPTIMAL", "FEASIBLE") else 1


if __name__ == "__main__":
    raise SystemExit(main())

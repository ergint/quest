import json
from pathlib import Path

import cli


def test_cli_solves_small_scenario_and_writes_output(tmp_path: Path):
    input_data = {
        "profile": {
            "name": "test-profili",
            "shift_types": [
                {"code": "07-15", "start_hour": 7, "duration_hours": 8, "is_night": False},
                {"code": "15-23", "start_hour": 15, "duration_hours": 8, "is_night": False},
                {"code": "23-07", "start_hour": 23, "duration_hours": 8, "is_night": True},
            ],
            "min_rest_hours_after_night": 11,
            "max_consecutive_work_days": 4,
            "max_period_hours": 60,
            "min_experienced_per_shift": 0,
        },
        "nurses": [{"id": f"H{i + 1}"} for i in range(7)],
        "period_start": "2026-09-01",
        "period_days": 5,
        "default_requirements": {"07-15": 2, "15-23": 2, "23-07": 1},
        "time_limit_seconds": 10,
    }
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    input_path.write_text(json.dumps(input_data), encoding="utf-8")

    exit_code = cli.main([str(input_path), "-o", str(output_path)])

    assert exit_code == 0
    output = json.loads(output_path.read_text(encoding="utf-8"))
    assert output["status"] in ("OPTIMAL", "FEASIBLE")
    assert output["violations"] == []
    assert len(output["assignments"]) > 0

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_index_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "Nöbet Çözücü" in response.text


def test_api_solve_returns_feasible_schedule():
    payload = {
        "profile": {
            "name": "test",
            "shift_types": [
                {"code": "07-15", "start_hour": 7, "duration_hours": 8, "is_night": False},
                {"code": "15-23", "start_hour": 15, "duration_hours": 8, "is_night": False},
                {"code": "23-07", "start_hour": 23, "duration_hours": 8, "is_night": True},
            ],
            "min_rest_hours_after_night": 11,
            "max_consecutive_work_days": 5,
            "max_period_hours": 180,
            "min_experienced_per_shift": 0,
        },
        "nurses": [{"id": f"H{i + 1}"} for i in range(6)],
        "period_start": "2026-09-01",
        "period_days": 7,
        "default_requirements": {"07-15": 2, "15-23": 2, "23-07": 1},
        "time_limit_seconds": 10,
    }

    response = client.post("/api/solve", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("OPTIMAL", "FEASIBLE")
    assert data["violations"] == []
    assert len(data["assignments"]) > 0


def test_api_solve_reports_bad_input():
    response = client.post("/api/solve", json={"profile": {}})
    assert response.status_code == 400
    assert "error" in response.json()

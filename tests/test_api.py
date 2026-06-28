from fastapi.testclient import TestClient
from datetime import datetime, timezone

from backend import main
from backend.main import app
from backend.schemas import RunRecord


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "botjobs-backend"}


def test_search_rejects_arbitrary_command_and_paths():
    response = client.post(
        "/runs/search",
        json={
            "portals": ["indeed"],
            "max_results": 10,
            "command": "Remove-Item -Recurse .",
            "profile": "../../secret.json",
        },
    )

    assert response.status_code == 422


def test_search_rejects_invalid_portal():
    response = client.post(
        "/runs/search",
        json={"portals": ["unknown"], "max_results": 10},
    )

    assert response.status_code == 422


def test_search_starts_a_controlled_run(monkeypatch):
    captured = {}

    def fake_start(run_type, command, params):
        captured.update(run_type=run_type, command=command, params=params)
        return RunRecord(
            run_id="00000000-0000-0000-0000-000000000001",
            type="search",
            status="pending",
            command=command,
            params=params,
            created_at=datetime.now(timezone.utc),
            output_file="output/botjobs_resultados.json",
        )

    monkeypatch.setattr(main.process_runner, "start", fake_start)
    response = client.post(
        "/runs/search",
        json={
            "portals": ["indeed", "linkedin"],
            "max_results": 10,
            "refresh_cache": False,
            "browser": False,
            "research": False,
        },
    )

    assert response.status_code == 202
    assert response.json()["status"] == "pending"
    assert captured["run_type"] == "search"
    assert captured["command"][-4:] == ["--portals", "indeed,linkedin", "--max-results", "10"]


def test_missing_run_returns_404():
    response = client.get("/runs/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404

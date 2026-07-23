from fastapi.testclient import TestClient
from datetime import datetime, timezone
from uuid import uuid4

from backend import main
from backend.main import app
from backend.schemas import RunRecord
from backend import config


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "botjobs-backend"}


def test_cors_allows_private_lan_frontend():
    origin = "http://10.2.34.25:8081"
    response = client.options(
        "/documents/cv",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"


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


def test_prepare_applications_starts_controlled_run(monkeypatch):
    def fake_start(run_type, command, params):
        return RunRecord(
            run_id="00000000-0000-0000-0000-000000000002",
            type=run_type,
            status="pending",
            command=command,
            params=params,
            created_at=datetime.now(timezone.utc),
            output_file="output/botjobs_resultados.json",
        )

    monkeypatch.setattr(main.process_runner, "start", fake_start)
    response = client.post("/runs/apply-approved/prepare")

    assert response.status_code == 202
    assert response.json()["type"] == "prepare_applications"
    assert response.json()["command"][-1] == "--browser"


def test_submit_requires_literal_confirmation(monkeypatch):
    assert client.post("/runs/apply-approved/submit", json={"confirmation": "si"}).status_code == 422

    monkeypatch.setattr(main.process_runner, "start", lambda run_type, command, params: RunRecord(
        run_id="00000000-0000-0000-0000-000000000003",
        type=run_type,
        status="pending",
        command=command,
        params=params,
        created_at=datetime.now(timezone.utc),
        output_file="output/botjobs_resultados.json",
    ))
    response = client.post("/runs/apply-approved/submit", json={"confirmation": "ENVIAR"})

    assert response.status_code == 202
    assert response.json()["type"] == "submit_applications"


def test_letter_endpoint_returns_content_without_accepting_paths():
    config.LETTERS_DIR.mkdir(parents=True, exist_ok=True)
    (config.LETTERS_DIR / "test-letter.md").write_text("Carta de prueba", encoding="utf-8")

    response = client.get("/letters/test-letter")
    invalid = client.get("/letters/test-letter.md")

    assert response.status_code == 200
    assert response.json() == {"letter_id": "test-letter", "content": "Carta de prueba"}
    assert invalid.status_code == 404


def test_job_decision_is_saved(monkeypatch):
    monkeypatch.setattr(config, "DECISIONS_FILE", config.BASE_DIR / "runtime" / "test-decisions" / f"{uuid4()}.json")

    response = client.post("/jobs/decision", json={"url": "https://example.com/job", "decision": "descartada"})

    assert response.status_code == 200
    assert response.json()["decision"] == "descartada"
    assert response.json()["job_key"]


def test_cv_upload_list_and_read(monkeypatch):
    monkeypatch.setattr(config, "CV_DIR", config.BASE_DIR / "runtime" / "test-documents" / str(uuid4()))
    upload = client.post(
        "/documents/cv",
        params={"filename": "Rene_CV.pdf"},
        content=b"%PDF-1.4\nBotJobs test",
        headers={"Content-Type": "application/pdf"},
    )

    assert upload.status_code == 201
    document = upload.json()
    listing = client.get("/documents/cv")
    content = client.get(f"/documents/cv/{document['cv_id']}")

    assert any(item["cv_id"] == document["cv_id"] for item in listing.json())
    assert document["active"] is True
    assert content.status_code == 200
    assert content.headers["content-type"] == "application/pdf"


def test_cv_can_be_marked_active(monkeypatch):
    monkeypatch.setattr(config, "CV_DIR", config.BASE_DIR / "runtime" / "test-documents" / str(uuid4()))
    first = client.post("/documents/cv", params={"filename": "first.pdf"}, content=b"%PDF-1.4\nfirst").json()
    second = client.post("/documents/cv", params={"filename": "second.pdf"}, content=b"%PDF-1.4\nsecond").json()

    response = client.post(f"/documents/cv/{second['cv_id']}/active")
    listing = client.get("/documents/cv").json()

    assert response.status_code == 200
    assert response.json()["cv_id"] == second["cv_id"]
    assert [item["cv_id"] for item in listing if item["active"]] == [second["cv_id"]]


def test_cv_upload_rejects_fake_pdf(monkeypatch):
    monkeypatch.setattr(config, "CV_DIR", config.BASE_DIR / "runtime" / "test-documents" / str(uuid4()))
    response = client.post(
        "/documents/cv",
        params={"filename": "fake.pdf"},
        content=b"not a pdf",
        headers={"Content-Type": "application/pdf"},
    )

    assert response.status_code == 422


def test_job_can_select_uploaded_cv(monkeypatch):
    monkeypatch.setattr(config, "CV_DIR", config.BASE_DIR / "runtime" / "test-documents" / str(uuid4()))
    monkeypatch.setattr(config, "DECISIONS_FILE", config.BASE_DIR / "runtime" / "test-decisions" / f"{uuid4()}.json")
    document = client.post("/documents/cv", params={"filename": "selected.pdf"}, content=b"%PDF-1.4").json()

    response = client.post("/jobs/decision", json={
        "url": "https://www.linkedin.com/jobs/view/1",
        "decision": "aprobada",
        "cv_id": document["cv_id"],
    })

    assert response.status_code == 200
    assert response.json()["cv_id"] == document["cv_id"]

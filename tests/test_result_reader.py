import json
from pathlib import Path
from uuid import uuid4

from backend import config
from backend.schemas import JobDecision
from backend.services.decisions import save_decision
from backend.services.result_reader import read_results, validate_output_path


TEST_RESULTS = Path("output/test_mobile_results.json")


def create_test_results():
    payload = {
        "sheets": {
            "resumen_ejecucion": {
                "name": "resumen_ejecucion",
                "columns": ["metrica", "valor"],
                "rows": [{"metrica": "vacantes_detectadas", "valor": 2}],
            },
            "vacantes_detectadas": {
                "name": "vacantes_detectadas",
                "columns": ["score", "nombre_de_la_vacante", "url"],
                "rows": [{"score": 95, "nombre_de_la_vacante": "Frontend Developer", "url": "https://example.com/job"}],
            },
        }
    }
    TEST_RESULTS.write_text(json.dumps(payload), encoding="utf-8")


def test_read_results_returns_named_tables():
    create_test_results()

    result = read_results(TEST_RESULTS, "00000000-0000-0000-0000-000000000001")

    assert result.run_id == "00000000-0000-0000-0000-000000000001"
    assert result.sheets["resumen_ejecucion"].rows[0]["valor"] == 2
    assert result.sheets["vacantes_detectadas"].rows[0]["nombre_de_la_vacante"] == "Frontend Developer"


def test_read_results_includes_saved_job_decision(monkeypatch):
    monkeypatch.setattr(config, "DECISIONS_FILE", config.BASE_DIR / "runtime" / "test-decisions" / f"{uuid4()}.json")
    create_test_results()
    save_decision(JobDecision(url="https://example.com/job", decision="aprobada"))

    result = read_results(TEST_RESULTS)

    row = result.sheets["vacantes_detectadas"].rows[0]
    assert row["decision_usuario"] == "aprobada"
    assert row["job_key"]


def test_result_reader_rejects_paths_outside_output():
    try:
        validate_output_path(Path("profile.example.json"))
    except ValueError as exc:
        assert "configured results directory" in str(exc)
    else:
        raise AssertionError("unsafe result path was accepted")

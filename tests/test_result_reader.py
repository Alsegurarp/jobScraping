import json
from pathlib import Path

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
                "columns": ["score", "nombre_de_la_vacante"],
                "rows": [{"score": 95, "nombre_de_la_vacante": "Frontend Developer"}],
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


def test_result_reader_rejects_paths_outside_output():
    try:
        validate_output_path(Path("profile.example.json"))
    except ValueError as exc:
        assert "configured results directory" in str(exc)
    else:
        raise AssertionError("unsafe result path was accepted")

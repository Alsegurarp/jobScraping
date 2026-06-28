import json
from pathlib import Path

from botjobs.results import write_results


TEST_OUTPUT = Path("output/test_direct_results.json")


def test_json_output_does_not_expose_document_paths():
    job = {
        "score": 90,
        "nombre_de_la_vacante": "Frontend Developer",
        "documento_que_se_manda": "C:/private/cv.pdf",
        "carta_de_interes_al_rol": "C:/private/letter.md",
    }

    write_results(TEST_OUTPUT, [job], [job], [], [], [], [])
    payload = json.loads(TEST_OUTPUT.read_text(encoding="utf-8"))
    result = payload["sheets"]["vacantes_detectadas"]["rows"][0]

    assert result["nombre_de_la_vacante"] == "Frontend Developer"
    assert "documento_que_se_manda" not in result
    assert "carta_de_interes_al_rol" not in result


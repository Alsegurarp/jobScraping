import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from botjobs.results import write_results


TEST_OUTPUT = Path("output/test_direct_results.json")


def test_json_output_does_not_expose_document_paths():
    job = {
        "score": 90,
        "nombre_de_la_vacante": "Frontend Developer",
        "documento_que_se_manda": "C:/private/cv.pdf",
        "carta_de_interes_al_rol": "C:/private/letter.md",
        "carta_id": "acme-frontend-developer",
    }

    write_results(TEST_OUTPUT, [job], [job], [], [], [], [])
    payload = json.loads(TEST_OUTPUT.read_text(encoding="utf-8"))
    result = payload["sheets"]["vacantes_detectadas"]["rows"][0]

    assert result["nombre_de_la_vacante"] == "Frontend Developer"
    assert "documento_que_se_manda" not in result
    assert "carta_de_interes_al_rol" not in result
    assert result["carta_id"] == "acme-frontend-developer"


def test_new_search_preserves_application_history():
    TEST_OUTPUT.write_text(json.dumps({"sheets": {"aplicaciones": {
        "name": "aplicaciones",
        "columns": ["url", "estado_aplicacion"],
        "rows": [{"url": "https://example.com/old", "estado_aplicacion": "aplicada"}],
    }}}), encoding="utf-8")

    write_results(TEST_OUTPUT, [], [], [], [], [], [])
    payload = json.loads(TEST_OUTPUT.read_text(encoding="utf-8"))

    assert payload["sheets"]["aplicaciones"]["rows"][0]["estado_aplicacion"] == "aplicada"
    assert {"metrica": "aplicaciones_aplicada", "valor": 1} in payload["sheets"]["resumen_ejecucion"]["rows"]


def test_output_declares_schema_version():
    write_results(TEST_OUTPUT, [], [], [], [], [], [])

    payload = json.loads(TEST_OUTPUT.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 1


def test_failed_atomic_replace_preserves_previous_result(monkeypatch):
    root = Path("runtime") / "test-results" / str(uuid4())
    root.mkdir(parents=True)
    try:
        path = root / "results.json"
        path.write_text('{"previous": true}', encoding="utf-8")
        monkeypatch.setattr(os, "replace", lambda *_args: (_ for _ in ()).throw(OSError("replace failed")))

        with pytest.raises(OSError, match="replace failed"):
            write_results(path, [], [], [], [], [], [])

        assert path.read_text(encoding="utf-8") == '{"previous": true}'
        assert list(root.glob("*.tmp")) == []
    finally:
        shutil.rmtree(root)

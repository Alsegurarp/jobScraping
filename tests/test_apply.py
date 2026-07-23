import json
from pathlib import Path
from uuid import uuid4

import pytest

from botjobs.apply import apply_approved


def test_apply_approved_selects_only_explicit_decisions_and_validates_materials():
    root = Path("runtime") / "test-apply" / str(uuid4())
    output = root / "output"
    runtime = root / "runtime"
    (output / "cartas").mkdir(parents=True)
    (runtime / "documents" / "cv").mkdir(parents=True)
    url = "https://www.linkedin.com/jobs/view/1"
    from hashlib import sha256
    (runtime / "decisions.json").write_text(json.dumps({
        sha256(url.encode()).hexdigest(): {"decision": "aprobada"}
    }), encoding="utf-8")
    (runtime / "documents" / "cv" / "cv-1.json").write_text(
        json.dumps({"cv_id": "cv-1", "active": True}), encoding="utf-8"
    )
    (runtime / "documents" / "cv" / "cv-1.pdf").write_bytes(b"%PDF-1.4")
    (output / "cartas" / "letter-1.md").write_text("carta", encoding="utf-8")
    results = output / "botjobs_resultados.json"
    results.write_text(json.dumps({"sheets": {"preseleccionadas": {"rows": [
        {"url": url, "empresa": "Acme", "carta_id": "letter-1"},
        {"url": "https://www.linkedin.com/jobs/view/2", "empresa": "Other", "carta_id": "letter-2"},
    ]}}}), encoding="utf-8")

    attempts = apply_approved(results, runtime, output, dry_run=True)

    assert [(item["empresa"], item["estado_aplicacion"]) for item in attempts] == [("Acme", "autorizada")]
    assert "aplicaciones" not in json.loads(results.read_text())["sheets"]


def test_browser_prepares_authorized_application(monkeypatch):
    root = Path("runtime") / "test-apply" / str(uuid4())
    output, runtime = root / "output", root / "runtime"
    (output / "cartas").mkdir(parents=True)
    (runtime / "documents" / "cv").mkdir(parents=True)
    url = "https://www.linkedin.com/jobs/view/1"
    from hashlib import sha256
    (runtime / "decisions.json").write_text(json.dumps({
        sha256(url.encode()).hexdigest(): {"decision": "aprobada"}
    }), encoding="utf-8")
    (runtime / "documents" / "cv" / "cv-1.json").write_text(json.dumps({"cv_id": "cv-1", "active": True}), encoding="utf-8")
    (runtime / "documents" / "cv" / "cv-1.pdf").write_bytes(b"%PDF-1.4")
    (output / "cartas" / "letter.md").write_text("carta", encoding="utf-8")
    results = output / "botjobs_resultados.json"
    results.write_text(json.dumps({"sheets": {"preseleccionadas": {"rows": [{"url": url, "carta_id": "letter"}]}}}), encoding="utf-8")
    monkeypatch.setattr("botjobs.apply.prepare_application", lambda *args, **kwargs: {
        "estado": "preparada", "resultado": "Formulario preparado", "evidencia": "evidence.png"
    })

    attempts = apply_approved(results, runtime, output, browser=True)

    assert attempts[0]["estado_aplicacion"] == "preparada"
    assert attempts[0]["evidencia_aplicacion"] == "evidence.png"


def test_submit_fails_closed():
    with pytest.raises(ValueError, match="confirm-submit"):
        apply_approved(Path("missing.json"), submit=True)


def test_submit_is_idempotent(monkeypatch):
    root = Path("runtime") / "test-apply" / str(uuid4())
    output, runtime = root / "output", root / "runtime"
    (output / "cartas").mkdir(parents=True)
    (runtime / "documents" / "cv").mkdir(parents=True)
    url = "https://www.linkedin.com/jobs/view/1"
    from hashlib import sha256
    (runtime / "decisions.json").write_text(json.dumps({
        sha256(url.encode()).hexdigest(): {"decision": "aprobada"}
    }), encoding="utf-8")
    (runtime / "documents" / "cv" / "cv-1.json").write_text(json.dumps({"cv_id": "cv-1", "active": True}), encoding="utf-8")
    (runtime / "documents" / "cv" / "cv-1.pdf").write_bytes(b"%PDF-1.4")
    (output / "cartas" / "letter.md").write_text("carta", encoding="utf-8")
    results = output / "botjobs_resultados.json"
    results.write_text(json.dumps({"sheets": {"preseleccionadas": {"rows": [{"url": url, "carta_id": "letter"}]}}}), encoding="utf-8")
    monkeypatch.setattr("botjobs.apply.prepare_application", lambda *args, **kwargs: {
        "estado": "aplicada", "resultado": "Portal confirmó el envío", "evidencia": "proof.png"
    })

    first = apply_approved(results, runtime, output, browser=True, submit=True, confirmation="ENVIAR")
    second = apply_approved(results, runtime, output, browser=True, submit=True, confirmation="ENVIAR")

    assert first[0]["estado_aplicacion"] == "aplicada"
    assert second[0]["estado_aplicacion"] == "omitida"
    assert "envio ya registrado" in second[0]["resultado_aplicacion"]

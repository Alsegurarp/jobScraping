import json
import shutil
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pytest

from botjobs.apply import SEND_ENABLED_PORTALS, apply_approved


@pytest.fixture
def application_case():
    root = Path("runtime") / "test-apply-safety" / str(uuid4())
    output, runtime = root / "output", root / "runtime"
    (output / "cartas").mkdir(parents=True)
    (runtime / "documents" / "cv").mkdir(parents=True)
    cv_id = "a" * 16
    (runtime / "documents" / "cv" / f"{cv_id}.json").write_text(
        json.dumps({"cv_id": cv_id, "active": True}), encoding="utf-8"
    )
    (runtime / "documents" / "cv" / f"{cv_id}.pdf").write_bytes(b"%PDF-1.4")
    try:
        yield root, output, runtime, cv_id
    finally:
        shutil.rmtree(root)


def configure_case(output, runtime, cv_id, jobs, decisions=None, applications=None):
    for job in jobs:
        letter_id = job.get("carta_id")
        if letter_id:
            (output / "cartas" / f"{letter_id}.md").write_text("carta", encoding="utf-8")
    decisions = decisions or {
        job["url"]: {"decision": "aprobada", "cv_id": cv_id}
        for job in jobs
    }
    (runtime / "decisions.json").write_text(json.dumps({
        sha256(url.encode()).hexdigest(): record for url, record in decisions.items()
    }), encoding="utf-8")
    sheets = {"preseleccionadas": {"rows": jobs}}
    if applications is not None:
        sheets["aplicaciones"] = {"rows": applications, "columns": []}
    results = output / "botjobs_resultados.json"
    results.write_text(json.dumps({"sheets": sheets}), encoding="utf-8")
    return results


def test_dry_run_never_opens_browser_or_changes_files(application_case, monkeypatch):
    _root, output, runtime, cv_id = application_case
    url = "https://www.indeed.com/viewjob?jk=1"
    results = configure_case(output, runtime, cv_id, [{"url": url, "carta_id": "letter"}])
    before_results = results.read_bytes()
    before_runtime = sorted(path.relative_to(runtime) for path in runtime.rglob("*"))
    monkeypatch.setattr("botjobs.apply.prepare_application", lambda *_args, **_kwargs: pytest.fail("No debe abrir navegador"))

    attempts = apply_approved(results, runtime, output, dry_run=True, browser=True)

    assert attempts[0]["estado_aplicacion"] == "autorizada"
    assert results.read_bytes() == before_results
    assert sorted(path.relative_to(runtime) for path in runtime.rglob("*")) == before_runtime


def test_missing_material_is_omitted_without_browser(application_case, monkeypatch):
    _root, output, runtime, cv_id = application_case
    url = "https://www.indeed.com/viewjob?jk=2"
    results = configure_case(output, runtime, cv_id, [{"url": url, "carta_id": ""}])
    monkeypatch.setattr("botjobs.apply.prepare_application", lambda *_args, **_kwargs: pytest.fail("No debe abrir navegador"))

    attempt = apply_approved(results, runtime, output, browser=True)[0]

    assert attempt["estado_aplicacion"] == "omitida"
    assert "carta" in attempt["resultado_aplicacion"]


@pytest.mark.parametrize("barrier", ["captcha", "login_requerido"])
def test_browser_barrier_requires_intervention(application_case, monkeypatch, barrier):
    _root, output, runtime, cv_id = application_case
    url = "https://www.indeed.com/viewjob?jk=3"
    results = configure_case(output, runtime, cv_id, [{"url": url, "carta_id": "letter"}])
    monkeypatch.setattr("botjobs.apply.prepare_application", lambda *_args, **_kwargs: {
        "estado": "requiere_intervencion", "resultado": barrier,
        "evidencia": "", "url_final": url,
    })

    attempt = apply_approved(results, runtime, output, browser=True)[0]

    assert attempt["estado_aplicacion"] == "requiere_intervencion"
    assert attempt["resultado_aplicacion"] == barrier


def test_prepare_never_submits_and_persists_evidence_and_final_url(application_case, monkeypatch):
    _root, output, runtime, cv_id = application_case
    url = "https://www.indeed.com/viewjob?jk=4"
    final_url = "https://www.indeed.com/apply/4"
    results = configure_case(output, runtime, cv_id, [{"url": url, "carta_id": "letter"}])

    def prepare(_url, _cv, _letter, evidence_path, _portal, profile_path, submit=False):
        assert submit is False
        assert profile_path == runtime / "browser-profiles" / "indeed"
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_bytes(b"PNG")
        return {
            "estado": "preparada", "resultado": "Formulario preparado",
            "evidencia": str(evidence_path), "url_final": final_url,
        }

    monkeypatch.setattr("botjobs.apply.prepare_application", prepare)
    attempt = apply_approved(results, runtime, output, browser=True)[0]
    saved = json.loads(results.read_text(encoding="utf-8"))["sheets"]["aplicaciones"]["rows"][0]

    assert attempt["estado_aplicacion"] == "preparada"
    assert Path(attempt["evidencia_aplicacion"]).is_file()
    assert saved["url_final"] == final_url
    assert saved["evidencia_aplicacion"] == attempt["evidencia_aplicacion"]


def test_retry_processes_only_previous_interventions(application_case, monkeypatch):
    _root, output, runtime, cv_id = application_case
    retry_url = "https://www.indeed.com/viewjob?jk=5"
    skip_url = "https://www.indeed.com/viewjob?jk=6"
    jobs = [
        {"url": retry_url, "carta_id": "retry"},
        {"url": skip_url, "carta_id": "skip"},
    ]
    previous = [
        {"url": retry_url, "estado_aplicacion": "requiere_intervencion"},
        {"url": skip_url, "estado_aplicacion": "preparada"},
    ]
    results = configure_case(output, runtime, cv_id, jobs, applications=previous)
    called = []
    monkeypatch.setattr("botjobs.apply.prepare_application", lambda url, *_args, **_kwargs: called.append(url) or {
        "estado": "preparada", "resultado": "ok", "evidencia": "", "url_final": url,
    })

    attempts = apply_approved(results, runtime, output, browser=True, retry_intervention=True)

    assert called == [retry_url]
    assert [attempt["url"] for attempt in attempts] == [retry_url]


def test_submit_adapters_are_explicit_and_unknown_domain_is_omitted(application_case, monkeypatch):
    assert SEND_ENABLED_PORTALS == frozenset({"indeed", "linkedin", "occ", "computrabajo", "glassdoor"})
    _root, output, runtime, cv_id = application_case
    url = "https://evil.example/job/1"
    results = configure_case(output, runtime, cv_id, [{"url": url, "carta_id": "letter"}])
    monkeypatch.setattr("botjobs.apply.prepare_application", lambda *_args, **_kwargs: pytest.fail("No debe abrir navegador"))

    attempt = apply_approved(results, runtime, output, browser=True, submit=True, confirmation="ENVIAR")[0]

    assert attempt["estado_aplicacion"] == "omitida"
    assert "portal soportado" in attempt["resultado_aplicacion"]


def test_submit_is_registered_before_browser_and_confirmed_with_evidence(application_case, monkeypatch):
    _root, output, runtime, cv_id = application_case
    url = "https://www.indeed.com/viewjob?jk=submit"
    results = configure_case(output, runtime, cv_id, [{"url": url, "carta_id": "letter"}])
    key = sha256(url.encode()).hexdigest()

    def submit(_url, _cv, _letter, evidence_path, *_args, **kwargs):
        assert kwargs["submit"] is True
        registry = json.loads((runtime / "submitted_applications.json").read_text(encoding="utf-8"))
        assert registry[key]["estado"] == "en_progreso"
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_bytes(b"PNG")
        return {
            "estado": "aplicada", "resultado": "Portal confirmó el envío",
            "evidencia": str(evidence_path), "url_final": "https://www.indeed.com/apply/done",
            "submit_intentado": True,
        }

    monkeypatch.setattr("botjobs.apply.prepare_application", submit)
    attempt = apply_approved(results, runtime, output, browser=True, submit=True, confirmation="ENVIAR")[0]
    registry = json.loads((runtime / "submitted_applications.json").read_text(encoding="utf-8"))

    assert attempt["estado_aplicacion"] == "aplicada"
    assert registry[key]["estado"] == "confirmado"


def test_uncertain_submit_blocks_second_execution(application_case, monkeypatch):
    _root, output, runtime, cv_id = application_case
    url = "https://www.indeed.com/viewjob?jk=uncertain"
    results = configure_case(output, runtime, cv_id, [{"url": url, "carta_id": "letter"}])
    calls = []
    monkeypatch.setattr("botjobs.apply.prepare_application", lambda *_args, **_kwargs: calls.append(1) or {
        "estado": "requiere_intervencion", "resultado": "No se pudo confirmar el envío",
        "evidencia": "proof.png", "url_final": "https://www.indeed.com/apply",
        "submit_intentado": True,
    })

    first = apply_approved(results, runtime, output, browser=True, submit=True, confirmation="ENVIAR")
    second = apply_approved(results, runtime, output, browser=True, submit=True, confirmation="ENVIAR")

    assert first[0]["estado_aplicacion"] == "requiere_intervencion"
    assert second[0]["estado_aplicacion"] == "omitida"
    assert calls == [1]


def test_exception_during_submit_is_uncertain_and_blocks_retry(application_case, monkeypatch):
    _root, output, runtime, cv_id = application_case
    url = "https://www.indeed.com/viewjob?jk=crash"
    results = configure_case(output, runtime, cv_id, [{"url": url, "carta_id": "letter"}])
    calls = []

    def crash(*_args, **_kwargs):
        calls.append(1)
        raise RuntimeError("browser closed")

    monkeypatch.setattr("botjobs.apply.prepare_application", crash)
    with pytest.raises(RuntimeError, match="browser closed"):
        apply_approved(results, runtime, output, browser=True, submit=True, confirmation="ENVIAR")
    second = apply_approved(results, runtime, output, browser=True, submit=True, confirmation="ENVIAR")

    assert second[0]["estado_aplicacion"] == "omitida"
    assert calls == [1]


def test_redirect_to_unknown_domain_fails_closed(application_case, monkeypatch):
    _root, output, runtime, cv_id = application_case
    url = "https://www.indeed.com/viewjob?jk=redirect"
    results = configure_case(output, runtime, cv_id, [{"url": url, "carta_id": "letter"}])
    monkeypatch.setattr("botjobs.apply.prepare_application", lambda *_args, **_kwargs: {
        "estado": "preparada", "resultado": "redirect",
        "evidencia": "", "url_final": "https://evil.example/collect",
        "submit_intentado": False,
    })

    attempt = apply_approved(results, runtime, output, browser=True, submit=True, confirmation="ENVIAR")[0]

    assert attempt["estado_aplicacion"] == "requiere_intervencion"
    assert "dominio" in attempt["resultado_aplicacion"].lower()


def test_failure_before_submit_click_releases_reservation_for_retry(application_case, monkeypatch):
    _root, output, runtime, cv_id = application_case
    url = "https://www.indeed.com/viewjob?jk=before-click"
    results = configure_case(output, runtime, cv_id, [{"url": url, "carta_id": "letter"}])
    responses = [
        {"estado": "fallida", "resultado": "No se encontro boton", "evidencia": "", "url_final": url, "submit_intentado": False},
        {"estado": "requiere_intervencion", "resultado": "No confirmado", "evidencia": "", "url_final": url, "submit_intentado": True},
    ]
    monkeypatch.setattr("botjobs.apply.prepare_application", lambda *_args, **_kwargs: responses.pop(0))

    first = apply_approved(results, runtime, output, browser=True, submit=True, confirmation="ENVIAR")
    second = apply_approved(results, runtime, output, browser=True, submit=True, confirmation="ENVIAR")

    assert first[0]["estado_aplicacion"] == "fallida"
    assert second[0]["estado_aplicacion"] == "requiere_intervencion"
    assert responses == []

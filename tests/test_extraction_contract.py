from pathlib import Path

import pytest

from botjobs.portals.computrabajo import extract_from_markup as computrabajo
from botjobs.portals.glassdoor import extract_from_markup as glassdoor
from botjobs.portals.indeed import extract_from_markup as indeed
from botjobs.portals.linkedin import extract_from_markup as linkedin
from botjobs.portals.occ import extract_from_markup as occ
from botjobs.schema import JOB_CONTRACT_COLUMNS, normalize_job_row, validate_job_row
from botjobs.extractors import extract_links


FIXTURES = Path(__file__).with_name("fixtures") / "portals"
PORTALS = [
    ("indeed", indeed, "https://mx.indeed.com/viewjob?jk=abc"),
    ("linkedin", linkedin, "https://www.linkedin.com/jobs/view/123"),
    ("occ", occ, "https://www.occ.com.mx/empleo/oferta/123"),
    ("computrabajo", computrabajo, "https://mx.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-de-demo"),
    ("glassdoor", glassdoor, "https://www.glassdoor.com.mx/job-listing/demo-123"),
]


@pytest.mark.parametrize("name,extractor,url", PORTALS)
def test_valid_fixture_extracts_the_canonical_contract(name, extractor, url):
    markup = (FIXTURES / f"{name}-valid.html").read_text(encoding="utf-8")

    row = validate_job_row(normalize_job_row({"url": url, **extractor({"url": url}, markup)}))

    assert list(row) == JOB_CONTRACT_COLUMNS
    assert row["titulo"] == "Junior Backend Developer"
    assert row["empresa"] == "Empresa Demo"
    assert row["ubicacion"] == "CDMX, MX"
    assert row["email_contacto"] == "vacantes@example.test"
    assert row["estado_extraccion"] == "ok"
    assert row["requiere_intervencion"] == "no"


@pytest.mark.parametrize("_name,extractor,url", PORTALS)
@pytest.mark.parametrize("expected,text", [
    ("captcha", "Verify you are human with reCAPTCHA"),
    ("login_requerido", "Iniciar sesion para continuar"),
    ("bloqueado", "Access denied: forbidden"),
])
def test_every_portal_maps_access_barriers(_name, extractor, url, expected, text):
    updates = extractor({"url": url}, f"<html><body>{text}</body></html>")

    assert updates["estado_extraccion"] == expected
    assert updates["requiere_intervencion"] == "si"


@pytest.mark.parametrize("_name,extractor,url", PORTALS)
def test_malformed_json_ld_is_not_reported_as_success(_name, extractor, url):
    markup = '<html><head><script type="application/ld+json">{broken</script></head><body>Empleos</body></html>'

    updates = extractor({"url": url}, markup)

    assert updates["estado_extraccion"] == "estructura_no_reconocida"
    assert updates["requiere_intervencion"] == "si"


def test_contract_rejects_unknown_extraction_status():
    with pytest.raises(ValueError, match="estado_extraccion"):
        validate_job_row(normalize_job_row({"estado_extraccion": "inventado"}))


def test_auto_search_error_row_is_not_reopened_or_marked_ignorable(monkeypatch):
    row = normalize_job_row({
        "titulo": "Busqueda Indeed",
        "url": "https://mx.indeed.com/jobs?q=python",
        "fuente_extraccion": "auto_search",
        "estado_extraccion": "error_red",
        "requiere_intervencion": "si",
    }, source="auto_search")
    monkeypatch.setattr("botjobs.extractors.fetch_html", lambda *_args, **_kwargs: pytest.fail("No debe reabrirse"))

    result = extract_links([row])[0]

    assert result["estado_extraccion"] == "error_red"
    assert result["requiere_intervencion"] == "si"

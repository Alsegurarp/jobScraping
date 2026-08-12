import json
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse

from .browser import prepare_application


APPLICATION_COLUMNS = [
    "url", "empresa", "nombre_de_la_vacante", "estado_aplicacion",
    "fecha_aplicacion", "portal_aplicacion", "cv_id", "carta_id",
    "requiere_confirmacion_envio", "resultado_aplicacion",
    "evidencia_aplicacion",
    "url_final",
]

PORTAL_HOSTS = {
    "linkedin": ("linkedin.com",),
    "indeed": ("indeed.com", "indeed.com.mx"),
    "occ": ("occ.com.mx",),
    "computrabajo": ("computrabajo.com.mx",),
    "glassdoor": ("glassdoor.com", "glassdoor.com.mx"),
}

SEND_ENABLED_PORTALS = frozenset({"indeed", "linkedin", "occ", "computrabajo", "glassdoor"})


def apply_approved(
    results_path,
    runtime_dir=Path("runtime"),
    output_dir=Path("output"),
    dry_run=False,
    browser=False,
    submit=False,
    confirmation="",
    retry_intervention=False,
):
    if submit and confirmation != "ENVIAR":
        raise ValueError("--submit requiere --confirm-submit ENVIAR")
    if submit and not browser:
        raise ValueError("--submit requiere --browser")
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    jobs = payload.get("sheets", {}).get("preseleccionadas", {}).get("rows", [])
    decisions = _read_json(runtime_dir / "decisions.json")
    sent = _read_json(runtime_dir / "submitted_applications.json")
    previous = {
        row.get("url"): row
        for row in payload.get("sheets", {}).get("aplicaciones", {}).get("rows", [])
    }
    documents = _cv_documents(runtime_dir)
    active_cv = next((item for item in documents if item.get("active")), None)
    attempts = []

    for job in jobs:
        url = str(job.get("url") or "").strip()
        key = sha256(url.encode("utf-8")).hexdigest()
        decision = decisions.get(sha256(url.encode("utf-8")).hexdigest(), {})
        if decision.get("decision") != "aprobada":
            continue
        if retry_intervention and previous.get(url, {}).get("estado_aplicacion") != "requiere_intervencion":
            continue
        letter_id = str(job.get("carta_id") or "").strip()
        letter = output_dir / "cartas" / f"{letter_id}.md"
        portal = _portal_for(url)
        cv = next((item for item in documents if item.get("cv_id") == decision.get("cv_id")), None) or active_cv
        missing = [
            name for name, value in (
                ("portal soportado", portal),
                ("CV activo", cv),
                ("archivo de CV", cv and (runtime_dir / "documents" / "cv" / f"{cv['cv_id']}.pdf").is_file()),
                ("carta", letter_id and letter.is_file()),
            ) if not value
        ]
        if submit and portal not in SEND_ENABLED_PORTALS:
            missing.append("envio no habilitado")
        if submit and key in sent:
            missing.append("envio ya registrado")
        state = "omitida" if missing else "autorizada"
        result = f"Falta {', '.join(missing)}" if missing else "Lista para preparar"
        evidence = ""
        final_url = ""
        if browser and not dry_run and not missing:
            evidence_path = runtime_dir / "evidence" / f"{sha256(url.encode()).hexdigest()[:16]}.png"
            if submit:
                sent[key] = {
                    "url": url,
                    "estado": "en_progreso",
                    "fecha_aplicacion": datetime.now().isoformat(timespec="seconds"),
                    "evidencia": "",
                }
                _write_json(runtime_dir / "submitted_applications.json", sent)
            try:
                prepared = prepare_application(
                    url,
                    runtime_dir / "documents" / "cv" / f"{cv['cv_id']}.pdf",
                    letter,
                    evidence_path,
                    portal,
                    runtime_dir / "browser-profiles" / portal,
                    submit=submit,
                )
            except Exception as exc:
                if submit:
                    sent[key].update({"estado": "incierto", "error": str(exc)})
                    _write_json(runtime_dir / "submitted_applications.json", sent)
                raise
            state = prepared.get("estado", "fallida")
            result = prepared.get("resultado", "Error desconocido")
            evidence = prepared.get("evidencia", "")
            final_url = prepared.get("url_final", "")
            if submit:
                submitted = bool(prepared.get("submit_intentado"))
                if final_url and not _url_allowed_for_portal(final_url, portal):
                    state = "requiere_intervencion"
                    result = "Redireccion a dominio no soportado; envio bloqueado"
                    if submitted:
                        sent[key].update({"estado": "incierto", "evidencia": evidence, "url_final": final_url})
                    else:
                        sent.pop(key, None)
                elif state == "aplicada" and submitted:
                    sent[key].update({"estado": "confirmado", "evidencia": evidence, "url_final": final_url})
                elif submitted:
                    sent[key].update({"estado": "incierto", "evidencia": evidence, "url_final": final_url})
                else:
                    sent.pop(key, None)
                _write_json(runtime_dir / "submitted_applications.json", sent)
        attempts.append({
            "url": url,
            "empresa": job.get("empresa", ""),
            "nombre_de_la_vacante": job.get("nombre_de_la_vacante", ""),
            "estado_aplicacion": state,
            "fecha_aplicacion": datetime.now().isoformat(timespec="seconds"),
            "portal_aplicacion": portal or job.get("portal", ""),
            "cv_id": cv.get("cv_id", "") if cv else "",
            "carta_id": letter_id,
            "requiere_confirmacion_envio": "si",
            "resultado_aplicacion": result,
            "evidencia_aplicacion": evidence,
            "url_final": final_url,
        })

    combined = {url: row for url, row in previous.items() if url}
    combined.update({row["url"]: row for row in attempts})
    application_rows = list(combined.values())
    payload.setdefault("sheets", {})["aplicaciones"] = {
        "name": "aplicaciones",
        "columns": APPLICATION_COLUMNS,
        "rows": application_rows,
    }
    _update_application_metrics(payload, application_rows)
    if not dry_run:
        _write_json(results_path, payload)
        if sent:
            _write_json(runtime_dir / "submitted_applications.json", sent)
    return attempts


def _read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _cv_documents(runtime_dir):
    return [_read_json(path) for path in (runtime_dir / "documents" / "cv").glob("*.json")]


def _write_json(path, payload):
    from .local_state import _write_json as atomic_write_json

    atomic_write_json(path, payload)


def _portal_for(url):
    host = (urlparse(url).hostname or "").lower()
    return next((
        portal for portal, hosts in PORTAL_HOSTS.items()
        if any(host == item or host.endswith(f".{item}") for item in hosts)
    ), "")


def _url_allowed_for_portal(url, portal):
    host = (urlparse(url).hostname or "").lower()
    return any(
        host == allowed or host.endswith(f".{allowed}")
        for allowed in PORTAL_HOSTS.get(portal, ())
    )


def _update_application_metrics(payload, attempts):
    summary = payload.setdefault("sheets", {}).setdefault("resumen_ejecucion", {
        "name": "resumen_ejecucion", "columns": ["metrica", "valor"], "rows": [],
    })
    rows = [
        row for row in summary.get("rows", [])
        if not str(row.get("metrica", "")).startswith("aplicaciones_")
    ]
    for state in ("autorizada", "preparada", "aplicada", "fallida", "requiere_intervencion", "omitida"):
        rows.append({"metrica": f"aplicaciones_{state}", "valor": sum(1 for item in attempts if item.get("estado_aplicacion") == state)})
    summary["rows"] = rows

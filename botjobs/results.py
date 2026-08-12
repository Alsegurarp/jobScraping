import json
import os
from datetime import datetime
from uuid import uuid4

from .schema import RESEARCH_COLUMNS, RESULT_COLUMNS, SUMMARY_COLUMNS
from .utils import clean_text


def summary_rows(detected, shortlisted, discarded, applied, intervention_rows, research_rows):
    return [
        {"metrica": "fecha_generacion", "valor": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"metrica": "vacantes_detectadas", "valor": len(detected)},
        {"metrica": "preseleccionadas", "valor": len(shortlisted)},
        {"metrica": "descartadas", "valor": len(discarded)},
        {"metrica": "aplicadas", "valor": len(applied)},
        {"metrica": "requieren_intervencion", "valor": len(intervention_rows)},
        {"metrica": "empresas_investigadas", "valor": len(research_rows)},
        {"metrica": "cartas_generadas", "valor": sum(1 for row in shortlisted if clean_text(row.get("carta_id")))},
        {"metrica": "cache_hits", "valor": sum(1 for row in detected if clean_text(row.get("cache_hit")).lower() == "si")},
        {"metrica": "ignoradas_en_futuro", "valor": sum(1 for row in detected if clean_text(row.get("ignorar_en_futuro")).lower() == "si")},
    ]


def write_results(path, detected, shortlisted, discarded, applied, intervention_rows, research_rows):
    previous_applications = _previous_applications(path)
    tables = {
        "resumen_ejecucion": (SUMMARY_COLUMNS, summary_rows(detected, shortlisted, discarded, applied, intervention_rows, research_rows)),
        "vacantes_detectadas": (RESULT_COLUMNS, detected),
        "preseleccionadas": (RESULT_COLUMNS, shortlisted),
        "descartadas": (RESULT_COLUMNS, discarded),
        "aplicadas": (RESULT_COLUMNS, applied),
        "requiere_intervencion": (RESULT_COLUMNS, intervention_rows),
        "empresas_investigadas": (RESEARCH_COLUMNS, research_rows),
    }
    if previous_applications:
        tables["aplicaciones"] = (
            previous_applications.get("columns", []),
            previous_applications.get("rows", []),
        )
        tables["resumen_ejecucion"][1].extend(_application_metrics(previous_applications.get("rows", [])))
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sheets": {
            name: {
                "name": name,
                "columns": columns,
                "rows": [
                    {column: row.get(column, "") for column in columns}
                    for row in rows
                ],
            }
            for name, (columns, rows) in tables.items()
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def _previous_applications(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("sheets", {}).get("aplicaciones")
    except (OSError, ValueError):
        return None


def _application_metrics(rows):
    states = ("autorizada", "preparada", "aplicada", "fallida", "requiere_intervencion", "omitida")
    return [
        {"metrica": f"aplicaciones_{state}", "valor": sum(1 for row in rows if row.get("estado_aplicacion") == state)}
        for state in states
    ]

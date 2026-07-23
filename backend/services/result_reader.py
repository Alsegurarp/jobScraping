import json
from pathlib import Path

from backend import config
from backend.schemas import ResultSheet, ResultsPayload
from backend.services.decisions import job_key, load_decisions


VISIBLE_SHEETS = (
    "resumen_ejecucion",
    "vacantes_detectadas",
    "preseleccionadas",
    "descartadas",
    "aplicadas",
    "aplicaciones",
    "requiere_intervencion",
    "empresas_investigadas",
)


def read_results(path: Path, run_id: str | None = None) -> ResultsPayload:
    safe_path = validate_output_path(path)
    payload = json.loads(safe_path.read_text(encoding="utf-8"))
    raw_sheets = payload.get("sheets", {})
    decisions = load_decisions()
    sheets = {
        name: _with_decisions(ResultSheet.model_validate(raw_sheets[name]), decisions)
        for name in VISIBLE_SHEETS
        if name in raw_sheets
    }
    return ResultsPayload(
        run_id=run_id,
        output_file=safe_path.relative_to(config.BASE_DIR).as_posix(),
        sheets=sheets,
    )


def latest_output_path() -> Path | None:
    candidates = [
        path
        for path in config.OUTPUT_PATH.glob("botjobs_resultados*.json")
        if path.is_file()
    ]
    return max(candidates, key=lambda path: path.stat().st_mtime, default=None)


def validate_output_path(path: Path) -> Path:
    candidate = path if path.is_absolute() else config.BASE_DIR / path
    resolved = candidate.resolve()
    allowed_roots = (config.OUTPUT_PATH.resolve(), config.RESULT_SNAPSHOTS_DIR.resolve())
    if resolved.suffix.lower() != ".json" or not any(resolved.is_relative_to(root) for root in allowed_roots):
        raise ValueError("Result file must be JSON inside a configured results directory")
    return resolved


def _with_decisions(sheet: ResultSheet, decisions) -> ResultSheet:
    if sheet.name not in {"vacantes_detectadas", "preseleccionadas", "descartadas", "aplicadas", "requiere_intervencion"}:
        return sheet
    columns = [*sheet.columns]
    for column in ("job_key", "decision_usuario", "nota_usuario", "decision_actualizada", "cv_id"):
        if column not in columns:
            columns.append(column)
    rows = []
    for row in sheet.rows:
        key = job_key(str(row.get("url") or ""))
        decision = decisions.get(key)
        rows.append({
            **row,
            "job_key": key if row.get("url") else "",
            "decision_usuario": decision.decision if decision else "",
            "nota_usuario": decision.note if decision else "",
            "decision_actualizada": decision.updated_at.isoformat() if decision else "",
            "cv_id": decision.cv_id if decision else "",
        })
    return ResultSheet(name=sheet.name, columns=columns, rows=rows)

import re
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend import config
from backend.schemas import CvDocument, ExtractLinksParams, JobDecision, JobDecisionRecord, LetterContent, ResultsPayload, RunRecord, SearchParams, SubmitApplicationsParams
from backend.services.command_builder import (
    build_apply_dry_run_command,
    build_prepare_applications_command,
    build_retry_applications_command,
    build_submit_applications_command,
    build_extract_links_command,
    build_search_command,
)
from backend.services.process_runner import ProcessRunner
from backend.services.run_store import RunStore
from backend.services.result_reader import latest_output_path, read_results
from backend.services.decisions import save_decision


app = FastAPI(title="BotJobs Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
run_store = RunStore(config.RUNS_DIR)
process_runner = ProcessRunner(run_store)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "botjobs-backend"}


@app.post("/runs/search", response_model=RunRecord, status_code=status.HTTP_202_ACCEPTED)
def start_search(params: SearchParams) -> RunRecord:
    return process_runner.start(
        "search",
        build_search_command(params),
        params.model_dump(mode="json"),
    )


@app.post("/runs/extract-links", response_model=RunRecord, status_code=status.HTTP_202_ACCEPTED)
def start_extract_links(params: ExtractLinksParams) -> RunRecord:
    return process_runner.start(
        "extract_links",
        build_extract_links_command(params),
        params.model_dump(mode="json"),
    )


@app.post(
    "/runs/apply-approved/dry-run",
    response_model=RunRecord,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_apply_dry_run() -> RunRecord:
    return process_runner.start(
        "apply_approved_dry_run",
        build_apply_dry_run_command(),
        {},
    )


@app.post("/runs/apply-approved/prepare", response_model=RunRecord, status_code=status.HTTP_202_ACCEPTED)
def start_prepare_applications() -> RunRecord:
    return process_runner.start(
        "prepare_applications",
        build_prepare_applications_command(),
        {},
    )


@app.post("/runs/apply-approved/retry", response_model=RunRecord, status_code=status.HTTP_202_ACCEPTED)
def start_retry_applications() -> RunRecord:
    return process_runner.start("retry_applications", build_retry_applications_command(), {})


@app.post("/runs/apply-approved/submit", response_model=RunRecord, status_code=status.HTTP_202_ACCEPTED)
def start_submit_applications(params: SubmitApplicationsParams) -> RunRecord:
    return process_runner.start(
        "submit_applications",
        build_submit_applications_command(),
        params.model_dump(mode="json"),
    )


@app.get("/runs/{run_id}", response_model=RunRecord)
def get_run(run_id: str) -> RunRecord:
    try:
        run = run_store.get(run_id)
    except ValueError:
        run = None
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.get("/runs/{run_id}/results", response_model=ResultsPayload)
def get_run_results(run_id: str) -> ResultsPayload:
    run = _find_run(run_id)
    if run.status != "completed":
        raise HTTPException(status_code=409, detail="Run has not completed successfully")
    result_file = run.result_file or run.output_file
    return _read_results_or_http_error(config.BASE_DIR / result_file, run_id)


@app.get("/results/latest", response_model=ResultsPayload)
def get_latest_results() -> ResultsPayload:
    path = latest_output_path()
    if path is None:
        raise HTTPException(status_code=404, detail="No result JSON found")
    return _read_results_or_http_error(path)


@app.get("/letters/{letter_id}", response_model=LetterContent)
def get_letter(letter_id: str) -> LetterContent:
    if not re.fullmatch(r"[a-z0-9-]+", letter_id):
        raise HTTPException(status_code=404, detail="Letter not found")
    path = (config.LETTERS_DIR / f"{letter_id}.md").resolve()
    if not path.is_relative_to(config.LETTERS_DIR.resolve()) or not path.is_file():
        raise HTTPException(status_code=404, detail="Letter not found")
    return LetterContent(letter_id=letter_id, content=path.read_text(encoding="utf-8"))


@app.post("/jobs/decision", response_model=JobDecisionRecord)
def decide_job(decision: JobDecision) -> JobDecisionRecord:
    if decision.cv_id:
        try:
            cv_id = str(UUID(decision.cv_id))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="CV no valido") from exc
        if not (config.CV_DIR / f"{cv_id}.json").is_file():
            raise HTTPException(status_code=422, detail="CV no encontrado")
    return save_decision(decision)


@app.post("/documents/cv", response_model=CvDocument, status_code=status.HTTP_201_CREATED)
async def upload_cv(request: Request, filename: str = Query(min_length=1, max_length=255)) -> CvDocument:
    filename = Path(filename).name
    if Path(filename).suffix.lower() != ".pdf":
        raise HTTPException(status_code=422, detail="El CV debe ser un archivo PDF")
    content = bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content) > config.MAX_CV_BYTES:
            raise HTTPException(status_code=413, detail="El CV supera el limite de 10 MB")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=422, detail="El archivo no contiene un PDF valido")

    cv_id = str(uuid4())
    document = CvDocument(
        cv_id=cv_id,
        filename=filename,
        size_bytes=len(content),
        uploaded_at=datetime.now(timezone.utc),
        active=not any(cv.active for cv in list_cvs()),
    )
    config.CV_DIR.mkdir(parents=True, exist_ok=True)
    (config.CV_DIR / f"{cv_id}.pdf").write_bytes(bytes(content))
    (config.CV_DIR / f"{cv_id}.json").write_text(
        json.dumps(document.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return document


@app.get("/documents/cv", response_model=list[CvDocument])
def list_cvs() -> list[CvDocument]:
    config.CV_DIR.mkdir(parents=True, exist_ok=True)
    documents = []
    for path in config.CV_DIR.glob("*.json"):
        try:
            documents.append(CvDocument.model_validate_json(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return sorted(documents, key=lambda item: item.uploaded_at, reverse=True)


@app.post("/documents/cv/{cv_id}/active", response_model=CvDocument)
def activate_cv(cv_id: str) -> CvDocument:
    try:
        active_id = str(UUID(cv_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="CV no encontrado") from exc

    documents = list_cvs()
    if not any(document.cv_id == active_id for document in documents):
        raise HTTPException(status_code=404, detail="CV no encontrado")

    activated = None
    for document in documents:
        document.active = document.cv_id == active_id
        (config.CV_DIR / f"{document.cv_id}.json").write_text(
            json.dumps(document.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if document.active:
            activated = document
    return activated


@app.get("/documents/cv/{cv_id}")
def get_cv(cv_id: str) -> FileResponse:
    try:
        normalized = str(UUID(cv_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="CV no encontrado") from exc
    path = config.CV_DIR / f"{normalized}.pdf"
    metadata_path = config.CV_DIR / f"{normalized}.json"
    if not path.is_file() or not metadata_path.is_file():
        raise HTTPException(status_code=404, detail="CV no encontrado")
    metadata = CvDocument.model_validate_json(metadata_path.read_text(encoding="utf-8"))
    return FileResponse(path, media_type="application/pdf", filename=metadata.filename, content_disposition_type="inline")


@app.get("/evidence/{evidence_id}")
def get_evidence(evidence_id: str) -> FileResponse:
    if not re.fullmatch(r"[a-f0-9]{16}", evidence_id):
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    path = config.EVIDENCE_DIR / f"{evidence_id}.png"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    return FileResponse(path, media_type="image/png", content_disposition_type="inline")


@app.get("/runs", response_model=list[RunRecord])
def list_runs(limit: int = Query(default=50, ge=1, le=200)) -> list[RunRecord]:
    return run_store.list(limit=limit)


def _find_run(run_id: str) -> RunRecord:
    try:
        run = run_store.get(run_id)
    except ValueError:
        run = None
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


def _read_results_or_http_error(path, run_id=None) -> ResultsPayload:
    try:
        if not path.exists():
            raise FileNotFoundError
        return read_results(path, run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Result JSON not found") from exc
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

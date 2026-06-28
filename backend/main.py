from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from backend import config
from backend.schemas import ExtractLinksParams, ResultsPayload, RunRecord, SearchParams
from backend.services.command_builder import (
    build_apply_dry_run_command,
    build_extract_links_command,
    build_search_command,
)
from backend.services.process_runner import ProcessRunner
from backend.services.run_store import RunStore
from backend.services.result_reader import latest_output_path, read_results


app = FastAPI(title="BotJobs Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
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
        raise HTTPException(status_code=404, detail="No result workbook found")
    return _read_results_or_http_error(path)


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

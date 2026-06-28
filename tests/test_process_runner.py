import subprocess
from datetime import datetime, timezone
from pathlib import Path

from backend.schemas import RunRecord
from backend.services.process_runner import ProcessRunner
from backend.services.run_store import RunStore


TEST_RUNS_DIR = Path("runtime/test-process-runner")


def saved_run(store, run_id):
    run = RunRecord(
        run_id=run_id,
        type="search",
        status="pending",
        command=["python", "bot_jobs.py"],
        params={},
        created_at=datetime.now(timezone.utc),
        output_file="output/botjobs_resultados.json",
    )
    store.save(run)
    return run


def test_runner_marks_success_and_captures_output(monkeypatch):
    store = RunStore(TEST_RUNS_DIR)
    run = saved_run(store, "00000000-0000-0000-0000-000000000010")
    Path(run.output_file).write_text('{"sheets": {}}', encoding="utf-8")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "done", ""),
    )

    ProcessRunner(store)._execute(run.run_id)

    result = store.get(run.run_id)
    assert result.status == "completed"
    assert result.stdout == "done"
    assert result.return_code == 0
    assert result.finished_at is not None
    assert result.result_file == f"runtime/results/{run.run_id}.json"


def test_runner_marks_nonzero_exit_as_failed(monkeypatch):
    store = RunStore(TEST_RUNS_DIR)
    run = saved_run(store, "00000000-0000-0000-0000-000000000011")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 2, "", "bad arguments"),
    )

    ProcessRunner(store)._execute(run.run_id)

    result = store.get(run.run_id)
    assert result.status == "failed"
    assert result.stderr == "bad arguments"
    assert result.error == "BotJobs exited with code 2"

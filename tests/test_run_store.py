from datetime import datetime, timezone
from pathlib import Path
import shutil

from backend.schemas import RunRecord
from backend.services.run_store import RunStore


def make_run(run_id, created_at):
    return RunRecord(
        run_id=run_id,
        type="search",
        status="pending",
        command=["python", "bot_jobs.py"],
        params={},
        created_at=created_at,
        output_file="output/botjobs_resultados.json",
    )


TEST_RUNS_DIR = Path("runtime/test-runs")


def test_store_saves_reads_and_lists_newest_first():
    store = RunStore(TEST_RUNS_DIR)
    older = make_run("00000000-0000-0000-0000-000000000001", datetime(2025, 1, 1, tzinfo=timezone.utc))
    newer = make_run("00000000-0000-0000-0000-000000000002", datetime(2025, 1, 2, tzinfo=timezone.utc))

    store.save(older)
    store.save(newer)

    assert store.get(older.run_id) == older
    assert [run.run_id for run in store.list()] == [newer.run_id, older.run_id]


def test_store_rejects_run_id_that_could_escape_directory():
    store = RunStore(TEST_RUNS_DIR)

    try:
        store.get("../../outside")
    except ValueError as exc:
        assert str(exc) == "invalid run_id"
    else:
        raise AssertionError("invalid run_id was accepted")


def test_store_recreates_directory_removed_by_state_restore():
    runs_dir = Path("runtime/test-runs-restored")
    store = RunStore(runs_dir)
    shutil.rmtree(runs_dir)
    run = make_run("00000000-0000-0000-0000-000000000003", datetime.now(timezone.utc))

    store.save(run)

    assert store.get(run.run_id) == run

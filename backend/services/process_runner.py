import re
import shutil
import subprocess
import threading
from datetime import datetime, timezone
from uuid import uuid4

from backend import config
from backend.schemas import RunRecord
from backend.services.result_reader import validate_output_path
from backend.services.run_store import RunStore


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProcessRunner:
    def __init__(self, store: RunStore):
        self.store = store
        self._execution_lock = threading.Lock()

    def start(self, run_type: str, command: list[str], params: dict) -> RunRecord:
        run = RunRecord(
            run_id=str(uuid4()),
            type=run_type,
            status="pending",
            command=command,
            params=params,
            created_at=_now(),
            output_file=config.OUTPUT_FILE,
        )
        self.store.save(run)
        if config.VERCEL_STATE_ENABLED:
            # ponytail: one synchronous run fits the single-user MVP; use a queue when concurrent users matter.
            self._execute(run.run_id)
            return self.store.get(run.run_id)
        thread = threading.Thread(target=self._execute, args=(run.run_id,), daemon=True)
        thread.start()
        return run

    def _execute(self, run_id: str) -> None:
        with self._execution_lock:
            run = self.store.get(run_id)
            if run is None:
                return
            run.status = "running"
            run.started_at = _now()
            self.store.save(run)

            try:
                result = subprocess.run(
                    run.command,
                    cwd=config.BASE_DIR,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=config.RUN_TIMEOUT_SECONDS,
                    shell=False,
                    check=False,
                )
                run.stdout = result.stdout
                run.stderr = result.stderr
                run.return_code = result.returncode
                if result.returncode == 0:
                    run.status = "completed"
                    self._update_output_file(run)
                    self._snapshot_results(run)
                else:
                    run.status = "failed"
                    run.error = f"BotJobs exited with code {result.returncode}"
            except subprocess.TimeoutExpired as exc:
                run.status = "failed"
                run.stdout = _timeout_text(exc.stdout)
                run.stderr = _timeout_text(exc.stderr)
                run.error = f"Execution exceeded {config.RUN_TIMEOUT_SECONDS} seconds"
            except OSError as exc:
                run.status = "failed"
                run.error = str(exc)
            finally:
                run.finished_at = _now()
                self.store.save(run)

    def _snapshot_results(self, run: RunRecord) -> None:
        source = config.BASE_DIR / run.output_file
        if not source.exists():
            return
        try:
            config.RESULT_SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            destination = config.RESULT_SNAPSHOTS_DIR / f"{run.run_id}.json"
            shutil.copyfile(source, destination)
            run.result_file = destination.relative_to(config.BASE_DIR).as_posix()
        except OSError:
            return

    def _update_output_file(self, run: RunRecord) -> None:
        match = re.search(r"^Listo:\s*(.+\.json)\s*$", run.stdout, re.MULTILINE)
        if not match:
            return
        try:
            actual_path = validate_output_path(config.BASE_DIR / match.group(1).strip())
        except ValueError:
            return
        if actual_path.exists():
            run.output_file = actual_path.relative_to(config.BASE_DIR).as_posix()


def _timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value

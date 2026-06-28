import json
import threading
from pathlib import Path
from uuid import UUID

from backend.schemas import RunRecord


class RunStore:
    def __init__(self, runs_dir: Path):
        self.runs_dir = runs_dir
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def save(self, run: RunRecord) -> None:
        path = self._path(run.run_id)
        temp_path = path.with_suffix(".tmp")
        payload = run.model_dump(mode="json")
        serialized = json.dumps(payload, ensure_ascii=True, indent=2)
        with self._lock:
            temp_path.write_text(serialized, encoding="utf-8")
            try:
                temp_path.replace(path)
            except PermissionError:
                # OneDrive can block atomic renames while synchronizing a folder.
                path.write_text(serialized, encoding="utf-8")

    def get(self, run_id: str) -> RunRecord | None:
        path = self._path(run_id)
        if not path.exists():
            return None
        with self._lock:
            return RunRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def list(self, limit: int = 50) -> list[RunRecord]:
        runs = []
        for path in self.runs_dir.glob("*.json"):
            try:
                runs.append(RunRecord.model_validate_json(path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                continue
        runs.sort(key=lambda run: run.created_at, reverse=True)
        return runs[:limit]

    def _path(self, run_id: str) -> Path:
        try:
            normalized = str(UUID(run_id))
        except ValueError as exc:
            raise ValueError("invalid run_id") from exc
        return self.runs_dir / f"{normalized}.json"

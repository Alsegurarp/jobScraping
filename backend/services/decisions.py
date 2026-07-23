import hashlib
import json
from datetime import datetime, timezone

from backend import config
from backend.schemas import JobDecision, JobDecisionRecord


def job_key(url: str) -> str:
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()


def load_decisions() -> dict[str, JobDecisionRecord]:
    if not config.DECISIONS_FILE.is_file():
        return {}
    try:
        payload = json.loads(config.DECISIONS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {
        key: JobDecisionRecord.model_validate(value)
        for key, value in payload.items()
    }


def save_decision(decision: JobDecision) -> JobDecisionRecord:
    records = load_decisions()
    key = job_key(decision.url)
    current = records.get(key)
    record = JobDecisionRecord(
        job_key=key,
        url=decision.url.strip(),
        decision=decision.decision,
        note=decision.note.strip(),
        updated_at=datetime.now(timezone.utc),
        cv_id=decision.cv_id if decision.cv_id is not None else (current.cv_id if current else ""),
    )
    records[key] = record
    config.DECISIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.DECISIONS_FILE.write_text(
        json.dumps({key: item.model_dump(mode="json") for key, item in records.items()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return record

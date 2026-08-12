import json
import shutil
import subprocess
import sys
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI = PROJECT_ROOT / "bot_jobs.py"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(CLI), *args], cwd=PROJECT_ROOT,
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )


def test_cli_manages_cv_and_decision_end_to_end():
    root = PROJECT_ROOT / "runtime" / "test-state-cli" / str(uuid4())
    root.mkdir(parents=True)
    try:
        source = root / "cv.pdf"
        source.write_bytes(b"%PDF-1.4\nfixture")
        added = run_cli("cv", "add", "--file", str(source), "--runtime", str(root))
        assert added.returncode == 0, added.stderr
        cv_id = json.loads(added.stdout)["cv_id"]

        decided = run_cli(
            "decisions", "set", "--url", "https://example.test/job/1",
            "--decision", "aprobada", "--cv-id", cv_id, "--runtime", str(root),
        )
        assert decided.returncode == 0, decided.stderr
        assert json.loads(decided.stdout)["cv_id"] == cv_id

        listed = run_cli("decisions", "list", "--runtime", str(root))
        assert listed.returncode == 0
        assert len(json.loads(listed.stdout)) == 1
    finally:
        shutil.rmtree(root)

import os
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PYTHON_EXECUTABLE = sys.executable
BOT_SCRIPT = "bot_jobs.py"
PROFILE_FILE = "profile.example.json"
JOBS_TEMPLATE = "vacantes.template.xlsx"
OUTPUT_DIR = "output"
OUTPUT_FILE = "output/botjobs_resultados.json"
OUTPUT_PATH = BASE_DIR / OUTPUT_DIR
LETTERS_DIR = OUTPUT_PATH / "cartas"
RUNS_DIR = BASE_DIR / "runtime" / "runs"
RESULT_SNAPSHOTS_DIR = BASE_DIR / "runtime" / "results"
CV_DIR = BASE_DIR / "runtime" / "documents" / "cv"
DECISIONS_FILE = BASE_DIR / "runtime" / "decisions.json"
EVIDENCE_DIR = BASE_DIR / "runtime" / "evidence"
MAX_CV_BYTES = 10 * 1024 * 1024
RUN_TIMEOUT_SECONDS = int(os.getenv("BOTJOBS_RUN_TIMEOUT_SECONDS", "1800"))

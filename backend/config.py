import os
import sys
import tempfile
from pathlib import Path


SOURCE_DIR = Path(__file__).resolve().parent.parent
IS_VERCEL = bool(os.getenv("VERCEL"))
API_KEY = os.getenv("BOTJOBS_API_KEY", "")
if IS_VERCEL and not os.getenv("BLOB_READ_WRITE_TOKEN"):
    raise RuntimeError("BLOB_READ_WRITE_TOKEN is required on Vercel")
if IS_VERCEL and not API_KEY:
    raise RuntimeError("BOTJOBS_API_KEY is required on Vercel")
VERCEL_STATE_ENABLED = IS_VERCEL
BASE_DIR = Path(tempfile.gettempdir()) / "botjobs" if VERCEL_STATE_ENABLED else SOURCE_DIR
PYTHON_EXECUTABLE = sys.executable
BOT_SCRIPT = str(SOURCE_DIR / "bot_jobs.py") if VERCEL_STATE_ENABLED else "bot_jobs.py"
PROFILE_FILE = str(SOURCE_DIR / "profile.example.json") if VERCEL_STATE_ENABLED else "profile.example.json"
JOBS_TEMPLATE = str(SOURCE_DIR / "vacantes.template.xlsx") if VERCEL_STATE_ENABLED else "vacantes.template.xlsx"
OUTPUT_DIR = "output"
OUTPUT_FILE = "output/botjobs_resultados.json"
OUTPUT_PATH = BASE_DIR / OUTPUT_DIR
LETTERS_DIR = OUTPUT_PATH / "cartas"
RUNS_DIR = BASE_DIR / "runtime" / "runs"
RESULT_SNAPSHOTS_DIR = BASE_DIR / "runtime" / "results"
CV_DIR = BASE_DIR / "runtime" / "documents" / "cv"
DECISIONS_FILE = BASE_DIR / "runtime" / "decisions.json"
EVIDENCE_DIR = BASE_DIR / "runtime" / "evidence"
MAX_CV_BYTES = 4 * 1024 * 1024
RUN_TIMEOUT_SECONDS = int(os.getenv("BOTJOBS_RUN_TIMEOUT_SECONDS", "1800"))

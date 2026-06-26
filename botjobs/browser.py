import json
import os
import shutil
import subprocess
from pathlib import Path

from .schema import normalize_job_row
from .utils import clean_text


NODE_MODULES = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "node_modules"
PNPM_NODE_MODULES = NODE_MODULES / ".pnpm" / "node_modules"
NODE_EXE = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "bin" / "node.exe"
SCRIPT = Path(__file__).with_name("browser_extract.mjs")


def node_command():
    configured = os.environ.get("BOTJOBS_NODE")
    if configured:
        return configured
    if NODE_EXE.exists():
        return str(NODE_EXE)
    return shutil.which("node") or "node"


def node_env():
    env = os.environ.copy()
    configured_path = env.get("BOTJOBS_NODE_PATH")
    if configured_path:
        env["NODE_PATH"] = configured_path
    elif NODE_MODULES.exists():
        paths = [str(NODE_MODULES)]
        if PNPM_NODE_MODULES.exists():
            paths.append(str(PNPM_NODE_MODULES))
        env["NODE_PATH"] = os.pathsep.join(paths)
    return env


def extract_with_browser(row, timeout_ms=30000):
    url = clean_text(row.get("url"))
    if not url:
        return normalize_job_row({**row, "estado_extraccion": "sin_url", "requiere_intervencion": "si"}, source="browser")

    command = [node_command(), str(SCRIPT), url, str(timeout_ms)]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=(timeout_ms / 1000) + 10,
            env=node_env(),
        )
    except Exception as exc:
        return normalize_job_row({
            **row,
            "fuente_extraccion": "browser",
            "estado_extraccion": "navegador_no_disponible",
            "requiere_intervencion": "no",
            "descripcion": clean_text(row.get("descripcion")) or f"No se pudo iniciar navegador: {exc}",
        }, source="browser")

    try:
        payload = json.loads((completed.stdout or "").strip().splitlines()[-1])
    except Exception:
        payload = {
            "ok": False,
            "estado_extraccion": "error_navegador",
            "requiere_intervencion": "no",
            "error": (completed.stderr or completed.stdout or "sin salida del navegador").strip(),
        }

    error_text = clean_text(payload.get("error")).lower()
    if "spawn eperm" in error_text:
        payload["estado_extraccion"] = "navegador_bloqueado"
        payload["requiere_intervencion"] = "si"

    updates = {
        "fuente_extraccion": "browser",
        "estado_extraccion": payload.get("estado_extraccion") or "error_navegador",
        "requiere_intervencion": payload.get("requiere_intervencion") or "no",
    }
    for key in ("titulo", "descripcion", "email_contacto"):
        if clean_text(payload.get(key)) and not clean_text(row.get(key)):
            updates[key] = payload[key]
    if not payload.get("ok") and not clean_text(row.get("descripcion")):
        updates["descripcion"] = f"No se pudo extraer con navegador: {payload.get('error', 'error desconocido')}"

    return normalize_job_row({**row, **updates}, source="browser")


def fetch_html_with_browser(url, timeout_ms=30000):
    command = [node_command(), str(SCRIPT), clean_text(url), str(timeout_ms)]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=(timeout_ms / 1000) + 10,
            env=node_env(),
        )
    except Exception as exc:
        raise RuntimeError(f"No se pudo iniciar navegador: {exc}") from exc

    try:
        payload = json.loads((completed.stdout or "").strip().splitlines()[-1])
    except Exception as exc:
        output = (completed.stderr or completed.stdout or "sin salida del navegador").strip()
        raise RuntimeError(output) from exc

    if not payload.get("ok"):
        raise RuntimeError(payload.get("error") or payload.get("estado_extraccion") or "error_navegador")
    return payload.get("html") or ""

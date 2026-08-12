import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from .browser import node_command


@dataclass(frozen=True)
class Diagnostic:
    name: str
    status: str
    message: str

    @staticmethod
    def exit_code(results):
        return 1 if any(result.status == "ERROR" for result in results) else 0


def find_node():
    command = node_command()
    path = Path(command)
    if path.is_file():
        return str(path)
    return shutil.which(command)


def check_output_directory(path):
    path.mkdir(parents=True, exist_ok=True)
    probe = path / f".botjobs-write-test-{uuid4()}"
    probe.write_text("ok", encoding="utf-8")
    probe.unlink()


def run_diagnostics(
    profile_path,
    jobs_path,
    output_dir,
    browser_required=False,
    node_finder=find_node,
    python_version=None,
):
    version = tuple(python_version or sys.version_info[:3])
    version_text = ".".join(str(part) for part in version)
    if version < (3, 10):
        results = [Diagnostic("python", "ERROR", f"Python 3.10 o superior requerido; detectado {version_text}.")]
    else:
        results = [Diagnostic("python", "OK", version_text)]
    results.append(_check_profile(Path(profile_path)))
    results.append(_check_template(Path(jobs_path) if jobs_path is not None else None))

    try:
        check_output_directory(Path(output_dir))
        results.append(Diagnostic("output", "OK", str(output_dir)))
    except OSError as exc:
        results.append(Diagnostic("output", "ERROR", f"No se puede escribir en {output_dir}: {exc}"))

    node = node_finder()
    if node:
        results.append(Diagnostic("browser", "OK", f"Node disponible: {node}"))
    elif browser_required:
        results.append(Diagnostic("browser", "ERROR", "Node no disponible; es obligatorio con --browser."))
    else:
        results.append(Diagnostic("browser", "ADVERTENCIA", "Node no disponible; los modos sin navegador pueden ejecutarse."))
    return results


def print_diagnostics(results):
    for result in results:
        print(f"[{result.status}] {result.name}: {result.message}")


def _check_profile(path):
    if not path.is_file():
        return Diagnostic("profile", "ERROR", f"El perfil no existe: {path}")
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return Diagnostic("profile", "ERROR", f"JSON invalido en {path}: {exc}")
    return Diagnostic("profile", "OK", str(path))


def _check_template(path):
    if path is None:
        return Diagnostic("template", "OK", "No requerida para busqueda automatica.")
    if not path.is_file():
        return Diagnostic("template", "ERROR", f"La plantilla no existe: {path}")
    return Diagnostic("template", "OK", str(path))

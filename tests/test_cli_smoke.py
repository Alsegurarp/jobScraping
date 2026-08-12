import importlib
import pkgutil
import shutil
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import botjobs


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI = PROJECT_ROOT / "bot_jobs.py"


def run_cli(*arguments, cwd=PROJECT_ROOT):
    return subprocess.run(
        [sys.executable, str(CLI), *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def test_help_exits_successfully():
    result = run_cli("--help")

    assert result.returncode == 0
    assert "Bot local para rankear vacantes tech" in result.stdout
    assert "doctor" in result.stdout
    assert "backup" in result.stdout


def test_doctor_command_has_actionable_output():
    result = run_cli("doctor", "--profile", "profile.example.json", "--jobs", "vacantes.template.xlsx")

    assert result.returncode == 0
    assert "[OK] python:" in result.stdout
    assert "[OK] profile:" in result.stdout
    assert "[OK] template:" in result.stdout
    assert "[OK] output:" in result.stdout
    assert "Traceback" not in result.stderr


def test_missing_profile_fails_without_traceback():
    result = run_cli("--profile", "missing-profile.json")

    assert result.returncode != 0
    assert "Error:" in result.stderr
    assert "missing-profile.json" in result.stderr
    assert "Traceback" not in result.stderr


def test_invalid_profile_fails_without_traceback():
    isolated_dir = PROJECT_ROOT / "runtime" / f"invalid-profile-{uuid4()}"
    isolated_dir.mkdir(parents=True)
    try:
        profile = isolated_dir / "profile.json"
        profile.write_text("not-json", encoding="utf-8")
        result = run_cli("--profile", str(profile))

        assert result.returncode != 0
        assert "Error:" in result.stderr
        assert "profile.json" in result.stderr
        assert "Traceback" not in result.stderr
    finally:
        shutil.rmtree(isolated_dir)


def test_all_botjobs_modules_import():
    modules = [
        module.name
        for module in pkgutil.walk_packages(botjobs.__path__, f"{botjobs.__name__}.")
    ]

    assert modules
    for module in modules:
        importlib.import_module(module)


def test_demo_runs_in_an_isolated_directory():
    isolated_dir = PROJECT_ROOT / ".test-tmp" / f"cli-demo-{uuid4()}"
    isolated_dir.mkdir(parents=True)
    try:
        result = run_cli("--demo", cwd=isolated_dir)

        assert result.returncode == 0, result.stderr
        assert "Listo: output" in result.stdout
        assert (isolated_dir / "vacantes.template.xlsx").is_file()
        assert (isolated_dir / "output" / "botjobs_resultados.json").is_file()
    finally:
        shutil.rmtree(isolated_dir)

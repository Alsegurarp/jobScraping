import json
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from botjobs.doctor import Diagnostic, run_diagnostics


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def local_tmp_path():
    path = PROJECT_ROOT / "runtime" / "test-doctor" / str(uuid4())
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path)


def by_name(results):
    return {result.name: result for result in results}


def test_doctor_reports_valid_local_configuration(local_tmp_path):
    profile = local_tmp_path / "profile.json"
    jobs = local_tmp_path / "jobs.xlsx"
    profile.write_text(json.dumps({"skills": []}), encoding="utf-8")
    jobs.write_bytes(b"placeholder")

    results = by_name(run_diagnostics(profile, jobs, local_tmp_path / "output", node_finder=lambda: None))

    assert results["python"].status == "OK"
    assert results["profile"].status == "OK"
    assert results["template"].status == "OK"
    assert results["output"].status == "OK"
    assert results["browser"].status == "ADVERTENCIA"


def test_doctor_reports_missing_and_invalid_profile(local_tmp_path):
    missing = by_name(run_diagnostics(local_tmp_path / "missing.json", None, local_tmp_path / "out"))
    invalid_profile = local_tmp_path / "invalid.json"
    invalid_profile.write_text("not-json", encoding="utf-8")
    invalid = by_name(run_diagnostics(invalid_profile, None, local_tmp_path / "out"))

    assert missing["profile"].status == "ERROR"
    assert "no existe" in missing["profile"].message
    assert invalid["profile"].status == "ERROR"
    assert "JSON invalido" in invalid["profile"].message


def test_template_is_required_only_for_manual_mode(local_tmp_path):
    profile = local_tmp_path / "profile.json"
    profile.write_text("{}", encoding="utf-8")

    manual = by_name(run_diagnostics(profile, local_tmp_path / "missing.xlsx", local_tmp_path / "out"))
    automatic = by_name(run_diagnostics(profile, None, local_tmp_path / "out"))

    assert manual["template"].status == "ERROR"
    assert automatic["template"].status == "OK"


def test_output_permission_failure_is_actionable(local_tmp_path, monkeypatch):
    profile = local_tmp_path / "profile.json"
    profile.write_text("{}", encoding="utf-8")

    def denied(_path):
        raise PermissionError("denied")

    monkeypatch.setattr("botjobs.doctor.check_output_directory", denied)
    result = by_name(run_diagnostics(profile, None, local_tmp_path / "blocked"))["output"]

    assert result.status == "ERROR"
    assert "No se puede escribir" in result.message


def test_browser_is_warning_when_optional_and_error_when_required(local_tmp_path):
    profile = local_tmp_path / "profile.json"
    profile.write_text("{}", encoding="utf-8")

    optional = by_name(run_diagnostics(profile, None, local_tmp_path / "out", node_finder=lambda: None))
    required = by_name(run_diagnostics(profile, None, local_tmp_path / "out", browser_required=True, node_finder=lambda: None))

    assert optional["browser"].status == "ADVERTENCIA"
    assert required["browser"].status == "ERROR"


def test_diagnostic_exit_code_depends_only_on_errors():
    warning = Diagnostic("browser", "ADVERTENCIA", "opcional")
    error = Diagnostic("profile", "ERROR", "faltante")

    assert Diagnostic.exit_code([warning]) == 0
    assert Diagnostic.exit_code([warning, error]) == 1


def test_unsupported_python_is_an_error(local_tmp_path):
    profile = local_tmp_path / "profile.json"
    profile.write_text("{}", encoding="utf-8")

    results = by_name(
        run_diagnostics(profile, None, local_tmp_path / "out", python_version=(3, 9, 0))
    )

    assert results["python"].status == "ERROR"
    assert "3.10" in results["python"].message

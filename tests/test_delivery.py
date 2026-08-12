from pathlib import Path

from botjobs import __version__


ROOT = Path(__file__).resolve().parents[1]


def test_release_has_fixed_version_and_delivery_scripts():
    assert __version__ == "1.0.0"
    assert (ROOT / "requirements.lock.txt").read_text(encoding="utf-8").splitlines() == [
        "et-xmlfile==2.0.0",
        "openpyxl==3.1.5",
    ]
    assert (ROOT / "scripts" / "install.ps1").is_file()
    assert (ROOT / "scripts" / "verify.ps1").is_file()


def test_delivery_documentation_exists():
    assert (ROOT / "docs" / "MANUAL_OPERATIVO.md").is_file()
    assert (ROOT / "docs" / "CHECKLIST_ENTREGA.md").is_file()


def test_powershell_scripts_fail_on_native_command_errors():
    install = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")
    verify = (ROOT / "scripts" / "verify.ps1").read_text(encoding="utf-8")

    assert install.count("$LASTEXITCODE -ne 0") >= 5
    assert verify.count("$LASTEXITCODE -ne 0") == 3

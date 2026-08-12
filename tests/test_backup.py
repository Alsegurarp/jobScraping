import shutil
import zipfile
from pathlib import Path
from uuid import uuid4

import pytest

from botjobs.backup import create_backup, restore_backup


@pytest.fixture
def workspace():
    root = Path("runtime") / "test-backup" / f"entrega con espacios á-{uuid4()}"
    root.mkdir(parents=True)
    try:
        yield root
    finally:
        shutil.rmtree(root)


def test_backup_and_restore_preserve_local_state_with_unicode_paths(workspace):
    for directory, filename, content in (
        ("runtime", "decisión.json", "estado local"),
        ("cache", "vacante.html", "cache"),
        ("output", "resultado.json", "resultado"),
    ):
        path = workspace / directory / filename
        path.parent.mkdir(parents=True)
        path.write_text(content, encoding="utf-8")
    archive = workspace / "respaldos" / "botjobs respaldo.zip"

    manifest = create_backup(workspace, archive)
    shutil.rmtree(workspace / "runtime")
    shutil.rmtree(workspace / "cache")
    shutil.rmtree(workspace / "output")
    restored = restore_backup(workspace, archive, confirmed=True)

    assert manifest["version"] == 1
    assert restored["files_restored"] == 3
    assert (workspace / "runtime" / "decisión.json").read_text(encoding="utf-8") == "estado local"
    assert (workspace / "cache" / "vacante.html").read_text(encoding="utf-8") == "cache"
    assert (workspace / "output" / "resultado.json").read_text(encoding="utf-8") == "resultado"


def test_restore_requires_confirmation_and_refuses_path_traversal(workspace):
    archive = workspace / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../outside.txt", "unsafe")

    with pytest.raises(ValueError, match="confirmacion"):
        restore_backup(workspace, archive, confirmed=False)
    with pytest.raises(ValueError, match="ruta insegura"):
        restore_backup(workspace, archive, confirmed=True)


def test_interrupted_backup_does_not_replace_previous_archive(workspace, monkeypatch):
    archive = workspace / "backup.zip"
    archive.write_bytes(b"previous")
    (workspace / "runtime").mkdir()
    (workspace / "runtime" / "state.json").write_text("state", encoding="utf-8")

    monkeypatch.setattr(zipfile.ZipFile, "write", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("interrupted")))

    with pytest.raises(OSError, match="interrupted"):
        create_backup(workspace, archive)

    assert archive.read_bytes() == b"previous"
    assert list(workspace.glob("*.tmp")) == []


def test_restore_refuses_archive_outside_workspace(workspace):
    outside = workspace.parent / "outside.zip"
    outside.write_bytes(b"not-a-zip")
    try:
        with pytest.raises(ValueError, match="dentro del proyecto"):
            restore_backup(workspace, outside, confirmed=True)
    finally:
        outside.unlink()

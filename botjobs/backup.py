import json
import os
import zipfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4


BACKUP_DIRECTORIES = ("runtime", "cache", "output")


def _inside(path, root):
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def create_backup(project_root, archive_path):
    root = Path(project_root).resolve()
    archive = Path(archive_path).resolve()
    if not _inside(archive, root):
        raise ValueError("El respaldo debe guardarse dentro del proyecto")
    archive.parent.mkdir(parents=True, exist_ok=True)
    temporary = archive.with_name(f".{archive.name}.{uuid4().hex}.tmp")
    files = []
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for directory in BACKUP_DIRECTORIES:
                source = root / directory
                if not source.exists():
                    continue
                for path in sorted(item for item in source.rglob("*") if item.is_file()):
                    relative = path.relative_to(root).as_posix()
                    bundle.write(path, relative)
                    files.append(relative)
            manifest = {
                "version": 1,
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "files": files,
            }
            bundle.writestr("backup-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        os.replace(temporary, archive)
        return manifest
    finally:
        temporary.unlink(missing_ok=True)


def restore_backup(project_root, archive_path, confirmed=False):
    if not confirmed:
        raise ValueError("La restauracion requiere confirmacion RESTAURAR")
    root = Path(project_root).resolve()
    archive = Path(archive_path).resolve()
    if not _inside(archive, root):
        raise ValueError("El respaldo debe estar dentro del proyecto")
    restored = 0
    with zipfile.ZipFile(archive, "r") as bundle:
        members = bundle.infolist()
        for member in members:
            member_path = Path(member.filename)
            if member.filename == "backup-manifest.json":
                continue
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError(f"El respaldo contiene una ruta insegura: {member.filename}")
            if not member_path.parts or member_path.parts[0] not in BACKUP_DIRECTORIES:
                raise ValueError(f"El respaldo contiene una ruta insegura: {member.filename}")
            destination = (root / member_path).resolve()
            if not _inside(destination, root):
                raise ValueError(f"El respaldo contiene una ruta insegura: {member.filename}")
        for member in members:
            if member.is_dir() or member.filename == "backup-manifest.json":
                continue
            destination = root / Path(member.filename)
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
            try:
                with bundle.open(member) as source, temporary.open("wb") as target:
                    target.write(source.read())
                os.replace(temporary, destination)
                restored += 1
            finally:
                temporary.unlink(missing_ok=True)
    return {"files_restored": restored, "archive": str(archive)}

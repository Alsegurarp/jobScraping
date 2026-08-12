import json
import os
import re
import shutil
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4


DECISIONS = {"aprobada", "descartada", "revision"}
MAX_CV_BYTES = 4 * 1024 * 1024
CV_ID_PATTERN = re.compile(r"[a-f0-9]{16}")


def _inside(path, root):
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class DecisionStore:
    def __init__(self, runtime_dir=Path("runtime")):
        self.runtime_dir = Path(runtime_dir)
        self.path = self.runtime_dir / "decisions.json"

    def list(self):
        return sorted(_read_json(self.path, {}).values(), key=lambda item: item.get("url", ""))

    def set(self, url, decision, note="", cv_id=""):
        url = str(url).strip()
        if decision not in DECISIONS:
            raise ValueError(f"Decision no valida: {decision}")
        if not url.startswith(("http://", "https://")):
            raise ValueError("La URL debe usar http o https")
        if cv_id and not CvStore(self.runtime_dir).get(cv_id):
            raise ValueError(f"CV no encontrado: {cv_id}")
        payload = _read_json(self.path, {})
        record = {
            "url": url,
            "decision": decision,
            "note": str(note).strip(),
            "cv_id": str(cv_id).strip(),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        payload[sha256(url.encode("utf-8")).hexdigest()] = record
        _write_json(self.path, payload)
        return record

    def remove(self, url, confirmed=False):
        if not confirmed:
            raise ValueError("La eliminacion requiere confirmacion BORRAR")
        payload = _read_json(self.path, {})
        removed = payload.pop(sha256(str(url).strip().encode("utf-8")).hexdigest(), None)
        _write_json(self.path, payload)
        return removed is not None


class CvStore:
    def __init__(self, runtime_dir=Path("runtime"), documents_dir=None, max_bytes=MAX_CV_BYTES):
        self.runtime_dir = Path(runtime_dir)
        self.documents_dir = Path(documents_dir) if documents_dir else self.runtime_dir / "documents" / "cv"
        self.max_bytes = max_bytes
        if not _inside(self.documents_dir, self.runtime_dir):
            raise ValueError("El directorio de CV esta fuera de runtime")

    def list(self):
        documents = [
            _read_json(path, {}) for path in self.documents_dir.glob("*.json")
        ] if self.documents_dir.exists() else []
        return sorted((item for item in documents if item.get("cv_id")), key=lambda item: item["cv_id"])

    def get(self, cv_id):
        if not CV_ID_PATTERN.fullmatch(str(cv_id)):
            return None
        path = self.documents_dir / f"{cv_id}.json"
        item = _read_json(path, {})
        return item if item.get("cv_id") == cv_id else None

    def add(self, source):
        source = Path(source)
        if source.suffix.lower() != ".pdf":
            raise ValueError("El CV debe tener extension .pdf")
        try:
            size = source.stat().st_size
            header = source.read_bytes()[:5]
        except OSError as exc:
            raise ValueError(f"No se pudo leer el CV: {exc}") from None
        if header != b"%PDF-":
            raise ValueError("El archivo no contiene un PDF valido")
        if size > self.max_bytes:
            raise ValueError(f"El CV supera el tamano maximo de {self.max_bytes} bytes")
        content = source.read_bytes()
        cv_id = sha256(content).hexdigest()[:16]
        existing = self.get(cv_id)
        if existing:
            return existing
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        active = not self.list()
        destination = self.documents_dir / f"{cv_id}.pdf"
        shutil.copyfile(source, destination)
        record = {
            "cv_id": cv_id, "filename": source.name, "size_bytes": size,
            "active": active, "added_at": datetime.now().isoformat(timespec="seconds"),
        }
        _write_json(self.documents_dir / f"{cv_id}.json", record)
        return record

    def activate(self, cv_id):
        if not self.get(cv_id):
            raise ValueError(f"CV no encontrado: {cv_id}")
        activated = None
        for document in self.list():
            document["active"] = document["cv_id"] == cv_id
            _write_json(self.documents_dir / f"{document['cv_id']}.json", document)
            if document["active"]:
                activated = document
        return activated

    def remove(self, cv_id, confirmed=False):
        if not confirmed:
            raise ValueError("La eliminacion requiere confirmacion BORRAR")
        document = self.get(cv_id)
        if not document:
            raise ValueError(f"CV no encontrado: {cv_id}")
        was_active = document.get("active", False)
        (self.documents_dir / f"{cv_id}.pdf").unlink(missing_ok=True)
        (self.documents_dir / f"{cv_id}.json").unlink(missing_ok=True)
        remaining = self.list()
        if was_active and remaining:
            self.activate(remaining[0]["cv_id"])
        return True

import json
import shutil
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pytest

from botjobs.local_state import CvStore, DecisionStore


@pytest.fixture
def runtime_dir():
    path = Path("runtime") / "test-local-state" / str(uuid4())
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path)


def test_decision_can_be_created_replaced_listed_and_removed(runtime_dir):
    store = DecisionStore(runtime_dir)
    url = "https://example.test/job/1"

    created = store.set(url, "aprobada", note="revisada")
    replaced = store.set(url, "revision")

    assert created["decision"] == "aprobada"
    assert replaced["decision"] == "revision"
    assert store.list() == [replaced]
    assert store.remove(url, confirmed=True) is True
    assert store.list() == []


def test_invalid_decision_and_unconfirmed_remove_fail(runtime_dir):
    store = DecisionStore(runtime_dir)

    with pytest.raises(ValueError, match="Decision no valida"):
        store.set("https://example.test/job", "tal_vez")
    with pytest.raises(ValueError, match="confirmacion"):
        store.remove("https://example.test/job", confirmed=False)


def test_decision_can_reference_an_existing_cv(runtime_dir):
    cv_file = runtime_dir / "source.pdf"
    cv_file.write_bytes(b"%PDF-1.4\nfixture")
    cv = CvStore(runtime_dir).add(cv_file)

    decision = DecisionStore(runtime_dir).set("https://example.test/job", "aprobada", cv_id=cv["cv_id"])

    assert decision["cv_id"] == cv["cv_id"]


def test_decision_rejects_unknown_cv(runtime_dir):
    with pytest.raises(ValueError, match="CV no encontrado"):
        DecisionStore(runtime_dir).set("https://example.test/job", "aprobada", cv_id="missing")


def test_cv_add_validates_pdf_and_uses_stable_identifier(runtime_dir):
    source = runtime_dir / "curriculum.pdf"
    content = b"%PDF-1.4\nfixture"
    source.write_bytes(content)
    store = CvStore(runtime_dir)

    first = store.add(source)
    second = store.add(source)

    assert first["cv_id"] == sha256(content).hexdigest()[:16]
    assert second["cv_id"] == first["cv_id"]
    assert len(store.list()) == 1
    assert store.list()[0]["active"] is True


@pytest.mark.parametrize("filename,content,message", [
    ("fake.txt", b"%PDF-1.4", "extension .pdf"),
    ("fake.pdf", b"not a pdf", "PDF valido"),
])
def test_cv_rejects_invalid_files(runtime_dir, filename, content, message):
    source = runtime_dir / filename
    source.write_bytes(content)

    with pytest.raises(ValueError, match=message):
        CvStore(runtime_dir).add(source)


def test_cv_rejects_oversized_file(runtime_dir):
    source = runtime_dir / "large.pdf"
    source.write_bytes(b"%PDF-" + b"x" * 20)

    with pytest.raises(ValueError, match="tamano maximo"):
        CvStore(runtime_dir, max_bytes=10).add(source)


def test_cv_activation_is_exclusive_and_remove_requires_confirmation(runtime_dir):
    first_path, second_path = runtime_dir / "one.pdf", runtime_dir / "two.pdf"
    first_path.write_bytes(b"%PDF-one")
    second_path.write_bytes(b"%PDF-two")
    store = CvStore(runtime_dir)
    first, second = store.add(first_path), store.add(second_path)

    activated = store.activate(second["cv_id"])

    assert activated["active"] is True
    assert {item["cv_id"]: item["active"] for item in store.list()} == {
        first["cv_id"]: False,
        second["cv_id"]: True,
    }
    with pytest.raises(ValueError, match="confirmacion"):
        store.remove(second["cv_id"], confirmed=False)
    assert store.remove(second["cv_id"], confirmed=True) is True
    assert store.list()[0]["active"] is True


def test_cv_operations_reject_unknown_identifier_and_outside_runtime(runtime_dir):
    store = CvStore(runtime_dir)
    with pytest.raises(ValueError, match="CV no encontrado"):
        store.activate("missing")
    with pytest.raises(ValueError, match="CV no encontrado"):
        store.activate("../outside")
    with pytest.raises(ValueError, match="fuera de runtime"):
        CvStore(runtime_dir, documents_dir=runtime_dir.parent.parent.parent / "outside")

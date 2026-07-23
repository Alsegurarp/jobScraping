import shutil
from pathlib import Path

from backend.services.vercel_state import VercelState


class FakeBlob:
    def __init__(self, path: Path):
        self.path = path

    def put(self, _name, body, **_options):
        self.path.write_bytes(body)

    def download_file(self, _name, destination, **_options):
        Path(destination).write_bytes(self.path.read_bytes())


def test_vercel_state_round_trip():
    root = (Path("runtime") / "test-vercel-state").resolve()
    assert root.is_relative_to(Path.cwd().resolve())
    shutil.rmtree(root, ignore_errors=True)
    try:
        blob = FakeBlob(root / "blob.tar.gz")
        root.mkdir(parents=True)
        state = VercelState(root / "work", blob)
        (state.base_dir / "runtime").mkdir(parents=True)
        (state.base_dir / "output").mkdir()
        (state.base_dir / "cache").mkdir()
        document = state.base_dir / "runtime" / "decisions.json"
        document.write_text('{"saved": true}', encoding="utf-8")
        state.persist()
        document.unlink()
        state.restore()
        assert document.read_text(encoding="utf-8") == '{"saved": true}'
    finally:
        shutil.rmtree(root, ignore_errors=True)

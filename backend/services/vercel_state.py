import shutil
import tarfile
import tempfile
from pathlib import Path

from vercel.blob import BlobClient, BlobNotFoundError


STATE_PATH = "botjobs/state.tar.gz"
STATE_DIRS = ("runtime", "output", "cache")


class VercelState:
    def __init__(self, base_dir: Path, client=None):
        self.base_dir = base_dir
        self.client = client or BlobClient()

    def restore(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for name in STATE_DIRS:
            shutil.rmtree(self.base_dir / name, ignore_errors=True)
            (self.base_dir / name).mkdir()

        archive = Path(tempfile.gettempdir()) / "botjobs-state.tar.gz"
        try:
            self.client.download_file(STATE_PATH, archive, access="private")
        except BlobNotFoundError:
            return
        with tarfile.open(archive, "r:gz") as bundle:
            bundle.extractall(self.base_dir, filter="data")

    def persist(self) -> None:
        archive = Path(tempfile.gettempdir()) / "botjobs-state.tar.gz"
        with tarfile.open(archive, "w:gz") as bundle:
            for name in STATE_DIRS:
                path = self.base_dir / name
                if path.exists():
                    bundle.add(path, arcname=name)
        self.client.put(
            STATE_PATH,
            archive.read_bytes(),
            access="private",
            content_type="application/gzip",
            overwrite=True,
        )

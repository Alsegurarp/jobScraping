import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from botjobs.cache import read_cached_html, write_cached_html
from botjobs import extractor_utils


def test_cache_returns_fresh_content_and_rejects_expired_content():
    cache_dir = Path("runtime") / "test-cache" / str(uuid4())
    url = "https://example.test/job/1"
    try:
        path = write_cached_html(url, "fresh", cache_dir)
        assert read_cached_html(url, cache_dir, ttl_hours=1) == "fresh"

        old = (datetime.now() - timedelta(hours=2)).timestamp()
        os.utime(path, (old, old))
        assert read_cached_html(url, cache_dir, ttl_hours=1) is None
    finally:
        shutil.rmtree(cache_dir)


def test_refresh_cache_bypasses_existing_content(monkeypatch):
    calls = []

    class Response:
        headers = {"content-type": "text/html; charset=utf-8"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit):
            return b"network"

    monkeypatch.setattr(extractor_utils, "read_cached_html", lambda *_args, **_kwargs: "cached")
    monkeypatch.setattr(extractor_utils, "write_cached_html", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(extractor_utils.urllib.request, "urlopen", lambda *_args, **_kwargs: calls.append("network") or Response())

    extractor_utils.configure_cache(refresh=False)
    assert extractor_utils.fetch_html("https://example.test/job") == "cached"
    assert calls == []

    extractor_utils.configure_cache(refresh=True)
    assert extractor_utils.fetch_html("https://example.test/job") == "network"
    assert calls == ["network"]
    extractor_utils.configure_cache(refresh=False)

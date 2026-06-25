import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

from .utils import clean_text


DEFAULT_CACHE_DIR = Path("cache")
DEFAULT_TTL_HOURS = 120


def cache_key(url):
    return hashlib.sha256(clean_text(url).encode("utf-8")).hexdigest()


def portal_name(url):
    host = urlparse(clean_text(url)).netloc.lower().replace("www.", "")
    return host.split(".")[0] or "unknown"


def html_cache_path(url, cache_dir=DEFAULT_CACHE_DIR):
    return Path(cache_dir) / "html" / portal_name(url) / f"{cache_key(url)}.html"


def is_fresh(path, ttl_hours=DEFAULT_TTL_HOURS):
    if not path.exists():
        return False
    modified = datetime.fromtimestamp(path.stat().st_mtime)
    return datetime.now() - modified <= timedelta(hours=ttl_hours)


def read_cached_html(url, cache_dir=DEFAULT_CACHE_DIR, ttl_hours=DEFAULT_TTL_HOURS):
    path = html_cache_path(url, cache_dir)
    if is_fresh(path, ttl_hours):
        return path.read_text(encoding="utf-8", errors="ignore")
    return None


def write_cached_html(url, markup, cache_dir=DEFAULT_CACHE_DIR):
    path = html_cache_path(url, cache_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markup, encoding="utf-8")
    return path


def ignored_urls_path(cache_dir=DEFAULT_CACHE_DIR):
    return Path(cache_dir) / "ignored_urls.json"


def load_ignored_urls(cache_dir=DEFAULT_CACHE_DIR):
    path = ignored_urls_path(cache_dir)
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    if isinstance(payload, list):
        return {clean_text(item) for item in payload if clean_text(item)}
    return set()


def save_ignored_urls(urls, cache_dir=DEFAULT_CACHE_DIR):
    path = ignored_urls_path(cache_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = sorted(clean_text(url) for url in urls if clean_text(url))
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def remember_ignored_urls(rows, cache_dir=DEFAULT_CACHE_DIR):
    ignored = load_ignored_urls(cache_dir)
    for row in rows:
        if clean_text(row.get("ignorar_en_futuro")).lower() == "si":
            url = clean_text(row.get("url"))
            if url:
                ignored.add(url)
    save_ignored_urls(ignored, cache_dir)
    return ignored

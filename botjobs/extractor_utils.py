import html
import json
import re
import urllib.error
import urllib.request
from urllib.parse import urlparse

from .cache import DEFAULT_TTL_HOURS, read_cached_html, write_cached_html
from .utils import clean_text


BLOCK_PATTERNS = {
    "captcha": ("captcha", "recaptcha", "verify you are human", "verifica que eres humano"),
    "login_requerido": ("sign in", "iniciar sesion", "inicia sesion", "login", "log in"),
    "bloqueado": ("access denied", "forbidden", "too many requests", "unusual traffic"),
}

CACHE_ENABLED = True
CACHE_TTL_HOURS = DEFAULT_TTL_HOURS
REFRESH_CACHE = False


def configure_cache(enabled=True, ttl_hours=DEFAULT_TTL_HOURS, refresh=False):
    global CACHE_ENABLED, CACHE_TTL_HOURS, REFRESH_CACHE
    CACHE_ENABLED = enabled
    CACHE_TTL_HOURS = ttl_hours
    REFRESH_CACHE = refresh


def infer_portal(url):
    host = urlparse(url).netloc.lower()
    if "indeed" in host:
        return "Indeed"
    if "linkedin" in host:
        return "LinkedIn"
    if "occ" in host:
        return "OCC"
    if "computrabajo" in host:
        return "Computrabajo"
    if "glassdoor" in host:
        return "Glassdoor"
    return host.replace("www.", "")


def fetch_html(url, timeout=20):
    if CACHE_ENABLED and not REFRESH_CACHE:
        cached = read_cached_html(url, ttl_hours=CACHE_TTL_HOURS)
        if cached is not None:
            return cached

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 BotJobs link extractor",
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("content-type", "")
        raw = response.read(800000)
    encoding = "utf-8"
    match = re.search(r"charset=([\w-]+)", content_type)
    if match:
        encoding = match.group(1)
    markup = raw.decode(encoding, errors="ignore")
    if CACHE_ENABLED:
        write_cached_html(url, markup)
    return markup


def html_to_text(markup):
    text = re.sub(r"<(script|style|noscript).*?</\1>", " ", markup, flags=re.I | re.S)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</(p|div|li|h1|h2|h3)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"[ \t\r\f\v]+", " ", text)).strip()


def meta_content(markup, *names):
    for name in names:
        patterns = [
            rf'<meta[^>]+property=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, markup, flags=re.I)
            if match:
                return html.unescape(match.group(1)).strip()
    return ""


def page_title(markup):
    title = meta_content(markup, "og:title", "twitter:title")
    if title:
        return title
    match = re.search(r"<title[^>]*>(.*?)</title>", markup, flags=re.I | re.S)
    if match:
        return clean_text(html.unescape(re.sub(r"<[^>]+>", " ", match.group(1))))
    return ""


def first_email(text):
    match = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text)
    return match.group(0) if match else ""


def detect_block(text):
    lower = text.lower()
    for status, patterns in BLOCK_PATTERNS.items():
        if any(pattern in lower for pattern in patterns):
            return status
    return ""


def merge_if_empty(row, updates):
    merged = dict(row)
    for key, value in updates.items():
        if clean_text(value) and not clean_text(merged.get(key)):
            merged[key] = value
    return merged


def json_ld_objects(markup):
    objects = []
    scripts = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        markup,
        flags=re.I | re.S,
    )
    for script in scripts:
        try:
            payload = json.loads(html.unescape(script.strip()))
        except Exception:
            continue
        if isinstance(payload, list):
            objects.extend(payload)
        else:
            objects.append(payload)
    return objects


def job_posting(markup):
    for item in json_ld_objects(markup):
        candidates = item if isinstance(item, list) else [item]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            item_type = candidate.get("@type")
            if item_type == "JobPosting" or (isinstance(item_type, list) and "JobPosting" in item_type):
                return candidate
    return {}


def organization_name(value):
    if isinstance(value, dict):
        return clean_text(value.get("name"))
    return clean_text(value)


def location_text(value):
    if isinstance(value, dict):
        address = value.get("address", {})
        if isinstance(address, dict):
            parts = [
                address.get("addressLocality"),
                address.get("addressRegion"),
                address.get("addressCountry"),
            ]
            return clean_text(", ".join(part for part in parts if part))
        return clean_text(address)
    if isinstance(value, list):
        return clean_text("; ".join(location_text(item) for item in value))
    return clean_text(value)


def salary_text(value):
    if not isinstance(value, dict):
        return clean_text(value)
    amount = value.get("value", value)
    currency = value.get("currency", "")
    if isinstance(amount, dict):
        min_value = amount.get("minValue")
        max_value = amount.get("maxValue")
        unit = amount.get("unitText", "")
        if min_value and max_value:
            return clean_text(f"{min_value}-{max_value} {currency} {unit}")
        if min_value or max_value:
            return clean_text(f"{min_value or max_value} {currency} {unit}")
    return clean_text(f"{amount} {currency}")


def employment_type_text(value):
    if isinstance(value, list):
        return clean_text(", ".join(str(item) for item in value))
    return clean_text(value)

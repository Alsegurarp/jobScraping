import html
import re
import urllib.parse
import urllib.request
from datetime import date

from .utils import clean_text


def fetch_url_text(url, timeout=12):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 BotJobs local research"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("content-type", "")
        raw = response.read(300000)
    encoding = "utf-8"
    match = re.search(r"charset=([\w-]+)", content_type)
    if match:
        encoding = match.group(1)
    text = raw.decode(encoding, errors="ignore")
    text = re.sub(r"<(script|style).*?</\1>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def search_company(company):
    query = urllib.parse.quote_plus(f"{company} empresa tecnologia software")
    url = f"https://duckduckgo.com/html/?q={query}"
    return fetch_url_text(url)


def research_company(row, enabled):
    company = clean_text(row.get("empresa"))
    if not company:
        return {"empresa": "", "resumen": "", "fuentes": "", "fecha_investigacion": ""}
    if not enabled:
        return {"empresa": company, "resumen": "Investigacion web no ejecutada.", "fuentes": "", "fecha_investigacion": ""}

    sources = []
    texts = []
    company_url = clean_text(row.get("url_empresa"))
    if company_url:
        try:
            texts.append(fetch_url_text(company_url))
            sources.append(company_url)
        except Exception as exc:
            texts.append(f"No se pudo leer {company_url}: {exc}")
    if not texts:
        try:
            texts.append(search_company(company))
            sources.append("DuckDuckGo HTML search")
        except Exception as exc:
            texts.append(f"No se pudo investigar la empresa: {exc}")

    summary = clean_text(" ".join(texts)[:650])
    return {
        "empresa": company,
        "resumen": summary,
        "fuentes": "; ".join(sources),
        "fecha_investigacion": date.today().isoformat(),
    }

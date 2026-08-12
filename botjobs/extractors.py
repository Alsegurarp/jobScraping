import urllib.error
from urllib.parse import urlparse

from .browser import extract_with_browser
from .extractor_utils import (
    detect_block,
    cache_hit_for,
    fetch_html,
    first_email,
    html_to_text,
    infer_portal,
    merge_if_empty,
    meta_content,
    page_title,
)
from .portals.computrabajo import extract_from_markup as extract_computrabajo_markup
from .portals.glassdoor import extract_from_markup as extract_glassdoor_markup
from .portals.indeed import extract_from_markup as extract_indeed_markup
from .portals.linkedin import extract_from_markup as extract_linkedin_markup
from .portals.occ import extract_from_markup as extract_occ_markup
from .schema import normalize_job_row
from .utils import clean_text


FORCE_UPDATE_FIELDS = {
    "fuente_extraccion",
    "requiere_intervencion",
    "estado_extraccion",
    "cache_hit",
    "motivo_intervencion",
    "accion_recomendada",
}


def merge_extraction(row, updates):
    merged = merge_if_empty(row, updates)
    for key in FORCE_UPDATE_FIELDS:
        if key in updates and clean_text(updates.get(key)):
            merged[key] = updates[key]
    return merged


def portal_updates(row, markup):
    url = clean_text(row.get("url"))
    host = urlparse(url).netloc.lower()
    if "indeed" in host:
        return extract_indeed_markup(row, markup)
    if "computrabajo" in host:
        return extract_computrabajo_markup(row, markup)
    if "occ" in host:
        return extract_occ_markup(row, markup)
    if "glassdoor" in host:
        return extract_glassdoor_markup(row, markup)
    if "linkedin" in host:
        return extract_linkedin_markup(row, markup)
    return generic_updates(row, markup)


def generic_updates(row, markup):
    url = clean_text(row.get("url"))
    text = html_to_text(markup)
    block_status = detect_block(text)
    description = meta_content(markup, "description", "og:description", "twitter:description")
    if not description and text:
        description = clean_text(text[:5000])

    title = page_title(markup)
    updates = {
        "titulo": title,
        "portal": infer_portal(url),
        "descripcion": description,
        "email_contacto": first_email(text),
        "fuente_extraccion": "link",
        "estado_extraccion": block_status or ("ok" if description else "sin_descripcion"),
        "requiere_intervencion": "si" if block_status in {"captcha", "login_requerido", "bloqueado"} else "no",
        "cache_hit": cache_hit_for(url),
    }
    return updates


def extraction_error(row, url, status, description, intervention="no"):
    return normalize_job_row({
        **row,
        "portal": clean_text(row.get("portal")) or infer_portal(url),
        "fuente_extraccion": "link",
        "estado_extraccion": status,
        "requiere_intervencion": intervention,
        "cache_hit": cache_hit_for(url),
        "descripcion": clean_text(row.get("descripcion")) or description,
    }, source="link")


def extract_link(row):
    url = clean_text(row.get("url"))
    if not url:
        return normalize_job_row({**row, "estado_extraccion": "sin_url", "requiere_intervencion": "si"}, source="link")

    try:
        markup = fetch_html(url)
    except urllib.error.HTTPError as exc:
        status = "bloqueado" if exc.code in {401, 403, 429} else "error_red"
        return extraction_error(row, url, status, f"No se pudo abrir el link: HTTP {exc.code}", "si" if status == "bloqueado" else "no")
    except Exception as exc:
        return extraction_error(row, url, "error_red", f"No se pudo abrir el link: {exc}")

    updates = portal_updates(row, markup)
    updates["cache_hit"] = cache_hit_for(url)
    return normalize_job_row(merge_extraction(row, updates), source="link")


def extract_links(rows, use_browser=False):
    extracted = []
    for row in rows:
        is_search_error = (
            clean_text(row.get("fuente_extraccion")) == "auto_search"
            and clean_text(row.get("estado_extraccion")) != "pendiente"
        )
        if is_search_error:
            extracted.append(normalize_job_row(row, source="auto_search"))
        elif use_browser:
            extracted.append(extract_with_browser(row))
        else:
            extracted.append(extract_link(row))
    return extracted

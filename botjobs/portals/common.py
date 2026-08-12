import re

from ..extractor_utils import (
    detect_block,
    employment_type_text,
    first_email,
    html_to_text,
    job_posting,
    location_text,
    meta_content,
    organization_name,
    page_title,
    salary_text,
)
from ..utils import clean_text


def description_from_markup(markup, text, job, selectors=()):
    if clean_text(job.get("description")):
        return html_to_text(job["description"])
    for selector in selectors:
        match = re.search(selector, markup, flags=re.I | re.S)
        if match:
            return html_to_text(match.group(1))
    return meta_content(markup, "description", "og:description", "twitter:description") or clean_text(text[:5000])


def extract_job_posting(row, markup, portal_name, source_name, selectors=()):
    text = html_to_text(markup)
    block_status = detect_block(text)
    job = job_posting(markup)
    employment_type = employment_type_text(job.get("employmentType"))
    recognized = bool(job) or bool(meta_content(markup, "description", "og:description", "twitter:description"))
    if not recognized:
        recognized = any(re.search(selector, markup, flags=re.I | re.S) for selector in selectors)
    description = description_from_markup(markup, text, job, selectors)
    if block_status:
        extraction_status = block_status
    elif not recognized:
        extraction_status = "estructura_no_reconocida"
    elif description:
        extraction_status = "ok"
    else:
        extraction_status = "sin_descripcion"

    updates = {
        "titulo": clean_text(job.get("title")) or page_title(markup),
        "empresa": organization_name(job.get("hiringOrganization")),
        "portal": portal_name,
        "descripcion": description,
        "ubicacion": location_text(job.get("jobLocation")),
        "salario": salary_text(job.get("baseSalary")),
        "fecha_publicacion": clean_text(job.get("datePosted")),
        "email_contacto": first_email(text),
        "fuente_extraccion": source_name,
        "estado_extraccion": extraction_status,
        "requiere_intervencion": "si" if extraction_status in {"captcha", "login_requerido", "bloqueado", "estructura_no_reconocida"} else "no",
    }
    if employment_type and not clean_text(row.get("modalidad")):
        updates["modalidad"] = employment_type
    return updates

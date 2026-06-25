import html
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse

from .extractor_utils import fetch_html, html_to_text
from .schema import normalize_job_row
from .utils import clean_text


@dataclass(frozen=True)
class PortalSearch:
    name: str
    host_patterns: tuple[str, ...]
    url_template: str
    job_path_patterns: tuple[str, ...]


PORTALS = {
    "indeed": PortalSearch(
        name="Indeed",
        host_patterns=("indeed.",),
        url_template="https://mx.indeed.com/jobs?q={query}&l={location}&fromage=14",
        job_path_patterns=("/viewjob", "/rc/clk", "/pagead/clk"),
    ),
    "linkedin": PortalSearch(
        name="LinkedIn",
        host_patterns=("linkedin.com",),
        url_template="https://www.linkedin.com/jobs/search/?keywords={query}&location={location}&f_TPR=r1209600",
        job_path_patterns=("/jobs/view", "/jobs-guest/jobs/api/jobPosting"),
    ),
    "occ": PortalSearch(
        name="OCC",
        host_patterns=("occ.com.mx",),
        url_template="https://www.occ.com.mx/empleos/de-{query}/en-{location}/?tm=14",
        job_path_patterns=("/empleo/oferta/", "/empleos/trabajo-en-"),
    ),
    "computrabajo": PortalSearch(
        name="Computrabajo",
        host_patterns=("computrabajo.",),
        url_template="https://mx.computrabajo.com/trabajo-de-{query}?q={query}",
        job_path_patterns=("/ofertas-de-trabajo/oferta-de-trabajo-de-", "/trabajo-de-"),
    ),
    "glassdoor": PortalSearch(
        name="Glassdoor",
        host_patterns=("glassdoor.",),
        url_template="https://www.glassdoor.com.mx/Empleo/jobs.htm?sc.keyword={query}&locT=C&locId=1152420&fromAge=14",
        job_path_patterns=("/partner/jobListing.htm", "/Job/", "/job-listing/"),
    ),
}


def selected_portals(portal_names):
    if not portal_names:
        return list(PORTALS.values())
    selected = []
    for name in portal_names:
        key = name.strip().lower()
        if key not in PORTALS:
            raise SystemExit(f"Portal no soportado para auto-search: {name}")
        selected.append(PORTALS[key])
    return selected


def search_terms(profile, limit=3):
    roles = profile.get("target_roles", [])[:limit]
    if roles:
        return roles
    return ["Junior Full Stack Developer", "Junior React Developer", "Junior Node.js Developer"]


def search_locations():
    return ["CDMX", "remoto"]


def build_search_urls(profile, portals):
    urls = []
    for portal in portals:
        for term in search_terms(profile):
            for location in search_locations():
                urls.append((
                    portal,
                    term,
                    location,
                    portal.url_template.format(
                        query=quote_plus(term),
                        location=quote_plus(location),
                    ),
                ))
    return urls


def anchor_links(markup, base_url):
    links = []
    for match in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", markup, flags=re.I | re.S):
        href = html.unescape(match.group(1))
        text = clean_text(html_to_text(match.group(2)))
        links.append((urljoin(base_url, href), text))
    return links


def unwrap_redirect(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for key in ("url", "u", "target", "redirectUrl"):
        if key in query and query[key]:
            return unquote(query[key][0])
    return url


def matches_portal(url, portal):
    host = urlparse(url).netloc.lower()
    return any(pattern in host for pattern in portal.host_patterns)


def looks_like_job_url(url, portal):
    parsed = urlparse(url)
    path = parsed.path.lower()
    if any(pattern.lower() in path for pattern in portal.job_path_patterns):
        return True
    return any(token in path for token in ("job", "empleo", "oferta", "vacante"))


def result_rows_from_markup(markup, search_url, portal, term, location):
    rows = []
    for href, text in anchor_links(markup, search_url):
        url = unwrap_redirect(href)
        if not matches_portal(url, portal) or not looks_like_job_url(url, portal):
            continue
        rows.append(normalize_job_row({
            "titulo": text,
            "empresa": "",
            "portal": portal.name,
            "url": url,
            "descripcion": "",
            "ubicacion": location,
            "modalidad": "remoto" if location.lower() == "remoto" else "",
            "fuente_extraccion": "auto_search",
            "estado_extraccion": "pendiente",
            "requiere_intervencion": "no",
        }, source="auto_search"))
    return rows


def dedupe_rows(rows, max_results):
    seen = set()
    unique = []
    for row in rows:
        url = clean_text(row.get("url"))
        if not url or url in seen:
            continue
        seen.add(url)
        unique.append(row)
        if len(unique) >= max_results:
            break
    return unique


def auto_search(profile, max_results=25, portal_names=None):
    portals = selected_portals(portal_names)
    found = []
    for portal, term, location, search_url in build_search_urls(profile, portals):
        if len(found) >= max_results:
            break
        try:
            markup = fetch_html(search_url, timeout=20)
        except Exception:
            continue
        found.extend(result_rows_from_markup(markup, search_url, portal, term, location))
        found = dedupe_rows(found, max_results)
    return found

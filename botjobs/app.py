import argparse
from datetime import date, timedelta
from pathlib import Path

from .cache import load_ignored_urls, remember_ignored_urls
from .extractors import extract_links
from .extractor_utils import configure_cache
from .letters import cover_letter, recruiter_message
from .profile import load_profile
from .ranking import detect_language, enrich_row, parse_date, score_job, short_reason
from .research import research_company
from .search import auto_search
from .utils import clean_text, slug
from .workbook import create_template, read_sheet, write_output


def execution_summary(output_path, detected, shortlisted, discarded, intervention_rows):
    extracted_ok = sum(1 for row in detected if clean_text(row.get("estado_extraccion")) == "ok")
    cache_hits = sum(1 for row in detected if clean_text(row.get("cache_hit")).lower() == "si")
    ignored = sum(1 for row in detected if clean_text(row.get("ignorar_en_futuro")).lower() == "si")
    letters = sum(1 for row in shortlisted if clean_text(row.get("carta_de_interes_al_rol")))
    return {
        "output_path": str(output_path),
        "detectadas": len(detected),
        "extraidas_ok": extracted_ok,
        "preseleccionadas": len(shortlisted),
        "descartadas": len(discarded),
        "intervenciones": len(intervention_rows),
        "cartas_generadas": letters,
        "cache_hits": cache_hits,
        "ignoradas": ignored,
    }


def print_execution_report(summary):
    print(f"Listo: {summary['output_path']}")
    print("Reporte:")
    print(f"- Detectadas: {summary['detectadas']}")
    print(f"- Extraidas correctamente: {summary['extraidas_ok']}")
    print(f"- Preseleccionadas: {summary['preseleccionadas']}")
    print(f"- Descartadas: {summary['descartadas']}")
    print(f"- Requieren intervencion: {summary['intervenciones']}")
    print(f"- Cartas generadas: {summary['cartas_generadas']}")
    print(f"- Cache hits: {summary['cache_hits']}")
    print(f"- Ignoradas en futuro: {summary['ignoradas']}")


def result_row(profile, row, score, status, matched_skills, flags, letter_path="", message=""):
    requires_intervention = clean_text(row.get("requiere_intervencion")).lower() == "si"
    ignore_future = "si" if status == "descartada" and not requires_intervention else clean_text(row.get("ignorar_en_futuro")) or "no"
    if requires_intervention:
        ignore_future = "no"
    motivo, accion = intervention_guidance(row, status, flags)
    return {
        "prioridad": "",
        "score": score,
        "estado": status,
        "nombre_de_la_vacante": clean_text(row.get("titulo")),
        "empresa": clean_text(row.get("empresa")),
        "portal": clean_text(row.get("portal")),
        "industria": clean_text(row.get("industria_detectada")),
        "ubicacion": clean_text(row.get("ubicacion")),
        "modalidad": clean_text(row.get("modalidad")),
        "salario": clean_text(row.get("salario")),
        "horas_semana": clean_text(row.get("horas_semana")),
        "seniority": clean_text(row.get("seniority")),
        "idioma": detect_language(row),
        "url": clean_text(row.get("url")),
        "email_contacto": clean_text(row.get("email_contacto")),
        "fuente_extraccion": clean_text(row.get("fuente_extraccion")),
        "requiere_intervencion": clean_text(row.get("requiere_intervencion")),
        "estado_extraccion": clean_text(row.get("estado_extraccion")),
        "ignorar_en_futuro": ignore_future,
        "cache_hit": clean_text(row.get("cache_hit")),
        "motivo_intervencion": motivo,
        "accion_recomendada": accion,
        "documento_que_se_manda": profile.get("cv_file", "Rene_Alexis_Segura_CV.pdf"),
        "carta_de_interes_al_rol": str(letter_path) if letter_path else "",
        "mensaje_corto_reclutador": message,
        "razon_menos_250": short_reason(status, score, flags, matched_skills),
        "matched_skills": ", ".join(matched_skills),
        "flags": ", ".join(flags),
    }


def intervention_guidance(row, status, flags):
    extraction = clean_text(row.get("estado_extraccion"))
    requires = clean_text(row.get("requiere_intervencion")).lower() == "si"
    ignored = clean_text(row.get("ignorar_en_futuro")).lower() == "si"

    if ignored or extraction == "ignorada_previamente":
        return "Vacante descartada previamente.", "Ignorar, ya fue descartada."
    if extraction == "captcha":
        return "El portal mostro captcha o verificacion humana.", "Abrir manualmente y resolver captcha."
    if extraction == "login_requerido":
        return "El portal requiere inicio de sesion.", "Abrir manualmente e iniciar sesion."
    if extraction == "bloqueado":
        return "El portal bloqueo la extraccion automatica.", "Reintentar con --browser o revisar manualmente."
    if extraction == "navegador_bloqueado":
        return "El entorno no permitio abrir Chrome/Edge.", "Ejecutar desde PowerShell local normal."
    if extraction == "sin_descripcion":
        return "No se pudo extraer descripcion.", "Revisar link o ajustar extractor del portal."
    if extraction == "error_red":
        return "Error de red al abrir la pagina.", "Reintentar luego o usar --refresh-cache."
    if extraction == "estructura_no_reconocida":
        return "La pagina cambio estructura o no coincide con el extractor.", "Ajustar extractor del portal."
    if requires:
        return "La vacante requiere intervencion manual.", "Revisar manualmente."
    if status == "descartada" and flags:
        return "Descartada por filtros del perfil.", "Ignorar salvo que quieras revisar excepcion."
    return "", ""


def run(
    profile_path,
    jobs_path,
    output_dir,
    research_enabled=False,
    extract_links_enabled=False,
    browser_enabled=False,
    auto_search_enabled=False,
    max_results=25,
    portal_names=None,
    refresh_cache=False,
    cache_ttl_hours=120,
):
    configure_cache(enabled=True, ttl_hours=cache_ttl_hours, refresh=refresh_cache)
    profile = load_profile(profile_path)
    ignored_urls = load_ignored_urls()
    if auto_search_enabled:
        rows = auto_search(profile, max_results=max_results, portal_names=portal_names, use_browser=browser_enabled)
        extract_links_enabled = True
    else:
        rows = read_sheet(jobs_path)
    rows = [
        {**row, "ignorar_en_futuro": "si", "estado_extraccion": "ignorada_previamente"}
        if clean_text(row.get("url")) in ignored_urls and clean_text(row.get("fuente_extraccion")) != "auto_search"
        else row
        for row in rows
    ]
    if extract_links_enabled and rows:
        rows_to_extract = [row for row in rows if clean_text(row.get("ignorar_en_futuro")).lower() != "si"]
        ignored_rows = [row for row in rows if clean_text(row.get("ignorar_en_futuro")).lower() == "si"]
        rows = [*extract_links(rows_to_extract, use_browser=browser_enabled), *ignored_rows]
    output_dir.mkdir(parents=True, exist_ok=True)
    letters_dir = output_dir / "cartas"
    letters_dir.mkdir(parents=True, exist_ok=True)

    detected = []
    shortlisted = []
    discarded = []
    intervention_rows = []
    research_by_company = {}
    cutoff = date.today() - timedelta(days=profile.get("max_post_age_days", 14))

    for row in rows:
        row = enrich_row(row)
        posted = parse_date(row.get("fecha_publicacion"))
        if posted and posted < cutoff:
            row = {**row, "descripcion": f"{clean_text(row.get('descripcion'))} vacante_mayor_a_2_semanas"}

        score, status, matched_skills, _matched_interests, flags = score_job(profile, row)
        if clean_text(row.get("ignorar_en_futuro")).lower() == "si":
            status = "descartada"
            flags = [*flags, "ignorada_en_corrida_previa"]
            score = min(score, 1)
        company = clean_text(row.get("empresa"))
        if company not in research_by_company:
            research_by_company[company] = research_company(row, research_enabled)
        research = research_by_company[company]

        letter_path = ""
        message = ""
        if status == "preseleccionada":
            letter_path = letters_dir / f"{slug(company)}-{slug(row.get('titulo'))}.md"
            message = recruiter_message(profile, row, matched_skills)
            letter_path.write_text(cover_letter(profile, row, matched_skills, research), encoding="utf-8")

        result = result_row(profile, row, score, status, matched_skills, flags, letter_path, message)
        detected.append(result)
        if clean_text(result.get("requiere_intervencion")).lower() == "si" or clean_text(result.get("motivo_intervencion")):
            intervention_rows.append(result)
        if status == "preseleccionada":
            shortlisted.append(result)
        else:
            discarded.append(result)

    remember_ignored_urls(detected)

    detected.sort(key=lambda item: item["score"], reverse=True)
    shortlisted.sort(key=lambda item: item["score"], reverse=True)
    discarded.sort(key=lambda item: item["score"], reverse=True)
    for index, item in enumerate(shortlisted, 1):
        item["prioridad"] = index
    for index, item in enumerate(detected, 1):
        item["prioridad"] = item["prioridad"] or index

    output_path = output_dir / "botjobs_resultados.xlsx"
    saved_path = write_output(output_path, detected, shortlisted, discarded, [], intervention_rows, list(research_by_company.values()))
    return saved_path, execution_summary(saved_path, detected, shortlisted, discarded, intervention_rows)


def demo():
    template = Path("vacantes.template.xlsx")
    if not template.exists():
        create_template(template)
    _output_path, summary = run(Path("profile.example.json"), template, Path("output"), research_enabled=False)
    print_execution_report(summary)


def main():
    parser = argparse.ArgumentParser(description="Bot local para rankear vacantes tech y generar cartas.")
    parser.add_argument("--profile", default="profile.example.json")
    parser.add_argument("--jobs", default="vacantes.template.xlsx")
    parser.add_argument("--out", default="output")
    parser.add_argument("--research", action="store_true", help="Investiga empresas por internet.")
    parser.add_argument("--extract-links", action="store_true", help="Abre los links del .xlsx y extrae datos basicos de vacantes.")
    parser.add_argument("--browser", action="store_true", help="Usa navegador automatizado con --extract-links.")
    parser.add_argument("--auto-search", action="store_true", help="Busca vacantes automaticamente en portales soportados.")
    parser.add_argument("--max-results", type=int, default=25, help="Maximo de vacantes candidatas en auto-search.")
    parser.add_argument("--portals", default="", help="Portales para auto-search separados por coma: indeed,linkedin,occ,computrabajo,glassdoor.")
    parser.add_argument("--refresh-cache", action="store_true", help="Ignora cache HTML existente y vuelve a descargar.")
    parser.add_argument("--cache-ttl-hours", type=int, default=120, help="Horas de vida del cache HTML.")
    parser.add_argument("--create-template", action="store_true", help="Crea una plantilla .xlsx de vacantes.")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.create_template:
        create_template(Path(args.jobs))
        print(f"Plantilla creada: {args.jobs}")
        return
    if args.demo:
        demo()
        return

    if args.browser and not (args.extract_links or args.auto_search):
        parser.error("--browser requiere --extract-links o --auto-search")

    portal_names = [item.strip() for item in args.portals.split(",") if item.strip()]
    _output_path, summary = run(
        Path(args.profile),
        Path(args.jobs),
        Path(args.out),
        args.research,
        args.extract_links,
        args.browser,
        args.auto_search,
        args.max_results,
        portal_names,
        args.refresh_cache,
        args.cache_ttl_hours,
    )
    print_execution_report(summary)

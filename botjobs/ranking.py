import re
from datetime import date, datetime
from email.utils import parsedate_to_datetime

from .utils import clean_text, words


def parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = clean_text(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    try:
        return parsedate_to_datetime(text).date()
    except Exception:
        return None


def parse_money_mxn(value):
    text = clean_text(value).lower()
    if not text:
        return None
    amounts = [float(number.replace(",", "")) for number in re.findall(r"\d[\d,]*(?:\.\d+)?", text)]
    if not amounts:
        return None
    amount = max(amounts)
    if "usd" in text or "dolar" in text or "dollar" in text:
        return amount * 18.5
    if amount < 1000 and ("hora" in text or "hour" in text):
        return amount * 40 * 4.33
    return amount


def is_remote(row):
    text = " ".join(clean_text(row.get(key)) for key in ("modalidad", "ubicacion", "descripcion")).lower()
    return any(term in text for term in ("remoto", "remote", "home office", "work from home"))


def is_hybrid(row):
    text = " ".join(clean_text(row.get(key)) for key in ("modalidad", "ubicacion", "descripcion")).lower()
    return "hibrid" in text or "hybrid" in text


def in_cdmx(row):
    text = " ".join(clean_text(row.get(key)) for key in ("ubicacion", "descripcion")).lower()
    return any(term in text for term in ("cdmx", "ciudad de mexico", "ciudad de méxico", "mexico city"))


def mentions_project_work(text):
    terms = [
        "por proyecto", "project based", "project-based", "proyecto temporal",
        "contrato por proyecto", "temporary project",
    ]
    return any(term in text for term in terms)


def quality_flags(profile, row, matched_skills):
    text = " ".join(clean_text(value) for value in row.values()).lower()
    flags = []
    industry = clean_text(row.get("industria_detectada")).lower()

    allowed_industries = [item.lower() for item in profile.get("allowed_industries", [])]
    blocked_industries = [item.lower() for item in profile.get("blocked_industries", [])]
    if allowed_industries and industry and not any(item in industry for item in allowed_industries):
        flags.append("industria_fuera_de_foco")
    if any(item in industry or item in text for item in blocked_industries):
        flags.append("industria_bloqueada")

    if mentions_project_work(text):
        flags.append("trabajo_por_proyecto")
    if any(term in text for term in ("guardia", "nocturno", "night shift", "weekend", "fin de semana", "24/7", "alta disponibilidad")):
        flags.append("horario_descartable")
    if "freelance" in text and any(term in text for term in ("exclusividad", "exclusive", "full dedication")):
        flags.append("freelance_con_exclusividad")

    hour_numbers = [int(number) for number in re.findall(r"\d+", clean_text(row.get("horas_semana")))]
    if hour_numbers and max(hour_numbers) > profile.get("max_hours_per_week", 40):
        flags.append("mas_de_40_horas")

    if not is_remote(row) and not is_hybrid(row) and not in_cdmx(row):
        flags.append("presencial_fuera_cdmx")
    if is_hybrid(row) and not in_cdmx(row):
        flags.append("hibrido_fuera_cdmx")

    seniority = " ".join([clean_text(row.get("seniority")), clean_text(row.get("titulo"))]).lower()
    if any(term in seniority for term in ("senior", "sr.", "lead", "principal", "staff")):
        flags.append("seniority_alto")

    salary = parse_money_mxn(row.get("salario"))
    if salary is not None and salary < profile.get("minimum_salary_mxn", 20000):
        flags.append("salario_bajo")

    if len(matched_skills) < profile.get("minimum_skill_matches", 5):
        flags.append("menos_de_5_skills")

    spam_terms = ("multinivel", "sin experiencia gana", "pago inicial", "curso obligatorio", "deposito", "inversion inicial")
    if any(term in text for term in spam_terms):
        flags.append("posible_spam")

    return flags


def score_job(profile, row):
    text = " ".join(clean_text(value) for value in row.values())
    job_terms = words(text)
    matched_skills = sorted(profile["skill_terms"] & job_terms)
    matched_interests = sorted(profile["interest_terms"] & job_terms)
    flags = quality_flags(profile, row, matched_skills)

    score = 0
    industry = clean_text(row.get("industria_detectada")).lower()
    if any(item in industry for item in [x.lower() for x in profile.get("allowed_industries", [])]):
        score += 22
    salary = parse_money_mxn(row.get("salario"))
    if salary and salary >= profile.get("minimum_salary_mxn", 20000):
        score += 18
    elif not clean_text(row.get("salario")):
        score += 8
    if not any(flag in flags for flag in ("mas_de_40_horas", "horario_descartable")):
        score += 14
    if is_remote(row):
        score += 14
    elif is_hybrid(row) and in_cdmx(row):
        score += 8
    elif in_cdmx(row):
        score += 5
    if any(term in " ".join([clean_text(row.get("seniority")), clean_text(row.get("titulo"))]).lower() for term in ("junior", "jr", "trainee")):
        score += 12
    score += min(len(matched_skills) * 3, 15)
    score += min(len(matched_interests) * 2, 5)

    hard_flags = {
        "industria_bloqueada", "trabajo_por_proyecto", "horario_descartable",
        "mas_de_40_horas", "presencial_fuera_cdmx", "hibrido_fuera_cdmx",
        "seniority_alto", "salario_bajo", "menos_de_5_skills", "posible_spam",
    }
    if any(flag in hard_flags for flag in flags):
        return min(score, 59), "descartada", matched_skills, matched_interests, flags
    return min(score, 100), "preseleccionada", matched_skills, matched_interests, flags


def short_reason(status, score, flags, matched_skills):
    if status == "preseleccionada":
        reason = f"Buena afinidad ({score}/100): coincide con {len(matched_skills)} skills clave y respeta filtros base."
    else:
        reason = f"Descartada ({score}/100): {', '.join(flags[:3]) or 'baja afinidad con el perfil'}."
    return reason[:247] + "..." if len(reason) > 250 else reason


def detect_language(row):
    explicit = clean_text(row.get("idioma")).lower()
    if explicit.startswith("en") or "ingles" in explicit or "english" in explicit:
        return "en"
    text = " ".join(clean_text(row.get(key)) for key in ("titulo", "descripcion")).lower()
    english_hits = sum(term in text for term in ("developer", "engineer", "remote", "requirements", "responsibilities", "english"))
    spanish_hits = sum(term in text for term in ("desarrollador", "remoto", "requisitos", "responsabilidades", "experiencia"))
    return "en" if english_hits > spanish_hits else "es"

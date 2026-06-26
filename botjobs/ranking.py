import re
from datetime import date, datetime
from email.utils import parsedate_to_datetime

from .utils import clean_text, words


INDUSTRY_KEYWORDS = {
    "fintech": ("fintech", "financial technology", "banco", "banking", "pagos", "payments"),
    "SaaS": ("saas", "software as a service", "b2b software", "plataforma cloud"),
    "e-commerce": ("e-commerce", "ecommerce", "marketplace", "retail online", "tienda en linea", "tienda en línea"),
    "logistica": ("logistica", "logística", "supply chain", "paqueteria", "paquetería", "envios", "envíos"),
    "consultoria": ("consultoria", "consultoría", "consulting", "consultora", "staff augmentation"),
    "seguridad": ("seguridad privada", "security guard", "guardia", "vigilancia", "cctv"),
    "viajes": ("viajes", "travel", "turismo", "hotel", "agencia de viajes"),
}

SENIORITY_HIGH_TERMS = (
    "senior", "sr.", "sr ", "lead", "principal", "staff", "architect",
    "arquitecto", "tech lead", "manager", "gerente",
)

SENIORITY_JUNIOR_TERMS = ("junior", "jr", "jr.", "trainee", "entry level", "intern", "becario")


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


def text_blob(row):
    return " ".join(clean_text(value) for value in row.values()).lower()


def infer_industry(row):
    current = clean_text(row.get("industria_detectada"))
    if current:
        return current
    text = text_blob(row)
    for industry, terms in INDUSTRY_KEYWORDS.items():
        if any(term in text for term in terms):
            return industry
    return ""


def infer_modality(row):
    current = clean_text(row.get("modalidad"))
    if current:
        return current
    if is_remote(row):
        return "remoto"
    if is_hybrid(row):
        return "hibrido"
    return ""


def infer_seniority(row):
    current = clean_text(row.get("seniority"))
    if current:
        return current
    text = " ".join([clean_text(row.get("titulo")), clean_text(row.get("descripcion"))]).lower()
    if any(term in text for term in SENIORITY_HIGH_TERMS):
        return "Senior"
    if any(term in text for term in SENIORITY_JUNIOR_TERMS):
        return "Junior"
    return ""


def infer_hours(row):
    current = clean_text(row.get("horas_semana"))
    if current:
        return current
    text = text_blob(row)
    patterns = [
        r"(\d{2})\s*(?:horas|hrs|hours)\s*(?:a la semana|por semana|weekly|week)",
        r"(?:semana|weekly|week)\D{0,12}(\d{2})\s*(?:horas|hrs|hours)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    if "tiempo completo" in text or "full time" in text or "full-time" in text:
        return "40"
    return ""


def infer_salary(row):
    current = clean_text(row.get("salario"))
    if current:
        return current
    text = text_blob(row)
    pattern = r"(?:(?:mxn|mx\$|\$)\s*)?(\d{2,3}[,\d]{3,})(?:\s*[-a]\s*(?:(?:mxn|mx\$|\$)\s*)?(\d{2,3}[,\d]{3,}))?\s*(?:mxn|pesos|mensuales|mes|monthly)?"
    match = re.search(pattern, text)
    if match:
        if match.group(2):
            return f"{match.group(1)}-{match.group(2)} MXN"
        return f"{match.group(1)} MXN"
    usd = re.search(r"(?:usd|\$)\s*(\d{3,5})(?:\s*[-a]\s*(\d{3,5}))?\s*(?:usd|dolares|dólares|monthly|mes)?", text)
    if usd:
        if usd.group(2):
            return f"{usd.group(1)}-{usd.group(2)} USD"
        return f"{usd.group(1)} USD"
    return ""


def enrich_row(row):
    enriched = dict(row)
    enriched["industria_detectada"] = infer_industry(enriched)
    enriched["modalidad"] = infer_modality(enriched)
    enriched["seniority"] = infer_seniority(enriched)
    enriched["horas_semana"] = infer_hours(enriched)
    enriched["salario"] = infer_salary(enriched)
    return enriched


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
    text = text_blob(row)
    flags = []
    industry = infer_industry(row).lower()

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
    if any(term in seniority for term in SENIORITY_HIGH_TERMS):
        flags.append("seniority_alto")

    salary = parse_money_mxn(row.get("salario"))
    if salary is not None and salary < profile.get("minimum_salary_mxn", 20000):
        flags.append("salario_bajo")

    if len(matched_skills) < profile.get("minimum_skill_matches", 5):
        flags.append("menos_de_5_skills")

    spam_terms = (
        "multinivel", "sin experiencia gana", "pago inicial", "curso obligatorio",
        "deposito", "depósito", "inversion inicial", "inversión inicial",
        "gana dinero desde casa", "no necesitas experiencia", "whatsapp para entrevista",
        "capacitacion pagada por el candidato", "capacitación pagada por el candidato",
    )
    if any(term in text for term in spam_terms):
        flags.append("posible_spam")

    return flags


def score_job(profile, row):
    row = enrich_row(row)
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
    if any(term in " ".join([clean_text(row.get("seniority")), clean_text(row.get("titulo"))]).lower() for term in SENIORITY_JUNIOR_TERMS):
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

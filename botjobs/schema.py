from .utils import clean_text


INPUT_SHEET = "vacantes"
INPUT_COLUMNS = [
    "titulo",
    "empresa",
    "portal",
    "url",
    "descripcion",
    "ubicacion",
    "modalidad",
    "salario",
    "fecha_publicacion",
    "email_contacto",
    "industria_detectada",
    "fuente_extraccion",
    "requiere_intervencion",
    "estado_extraccion",
    "ignorar_en_futuro",
    "cache_hit",
    "motivo_intervencion",
    "accion_recomendada",
    "horas_semana",
    "seniority",
    "idioma",
    "url_empresa",
]

JOB_CONTRACT_COLUMNS = INPUT_COLUMNS[:]

EXTRACTION_STATES = {
    "pendiente", "ok", "captcha", "login_requerido", "bloqueado",
    "navegador_bloqueado", "navegador_no_disponible", "error_navegador",
    "error_red", "estructura_no_reconocida", "sin_descripcion", "sin_url",
    "ignorada_previamente",
}

LEGACY_COLUMN_ALIASES = {
    "nombre_de_la_vacante": "titulo",
    "industria": "industria_detectada",
}

RESULT_COLUMNS = [
    "prioridad",
    "score",
    "estado",
    "nombre_de_la_vacante",
    "empresa",
    "portal",
    "industria",
    "ubicacion",
    "modalidad",
    "salario",
    "horas_semana",
    "seniority",
    "idioma",
    "url",
    "email_contacto",
    "fuente_extraccion",
    "requiere_intervencion",
    "estado_extraccion",
    "ignorar_en_futuro",
    "cache_hit",
    "motivo_intervencion",
    "accion_recomendada",
    "carta_id",
    "mensaje_corto_reclutador",
    "razon_menos_250",
    "matched_skills",
    "flags",
]

RESEARCH_COLUMNS = [
    "empresa",
    "resumen",
    "fuentes",
    "fecha_investigacion",
]

SUMMARY_COLUMNS = [
    "metrica",
    "valor",
]


def normalize_job_row(row, source="xlsx"):
    normalized = {column: "" for column in JOB_CONTRACT_COLUMNS}
    for key, value in row.items():
        clean_key = clean_text(key)
        canonical_key = LEGACY_COLUMN_ALIASES.get(clean_key, clean_key)
        if canonical_key in normalized:
            normalized[canonical_key] = value
    normalized["fuente_extraccion"] = clean_text(normalized.get("fuente_extraccion")) or source
    normalized["requiere_intervencion"] = clean_text(normalized.get("requiere_intervencion")) or "no"
    normalized["estado_extraccion"] = clean_text(normalized.get("estado_extraccion")) or "pendiente"
    normalized["ignorar_en_futuro"] = clean_text(normalized.get("ignorar_en_futuro")) or "no"
    normalized["cache_hit"] = clean_text(normalized.get("cache_hit")) or "no"
    normalized["motivo_intervencion"] = clean_text(normalized.get("motivo_intervencion"))
    normalized["accion_recomendada"] = clean_text(normalized.get("accion_recomendada"))
    return normalized


def validate_job_row(row):
    missing = [column for column in JOB_CONTRACT_COLUMNS if column not in row]
    extra = [column for column in row if column not in JOB_CONTRACT_COLUMNS]
    if missing or extra:
        raise ValueError(f"Contrato de vacante invalido; faltantes={missing}, extra={extra}")
    state = clean_text(row.get("estado_extraccion"))
    if state not in EXTRACTION_STATES:
        raise ValueError(f"estado_extraccion no soportado: {state}")
    return row

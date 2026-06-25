from .utils import clean_text


INPUT_SHEET = "vacantes"
OUTPUT_SHEETS = [
    "vacantes_detectadas",
    "preseleccionadas",
    "descartadas",
    "aplicadas",
    "empresas_investigadas",
]

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
    "horas_semana",
    "seniority",
    "idioma",
    "url_empresa",
]

JOB_CONTRACT_COLUMNS = INPUT_COLUMNS[:]

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
    "documento_que_se_manda",
    "carta_de_interes_al_rol",
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
    return normalized

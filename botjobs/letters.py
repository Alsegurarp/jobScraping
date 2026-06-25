from .ranking import detect_language
from .utils import clean_text


def cover_letter(profile, row, matched_skills, research):
    language = detect_language(row)
    name = profile.get("name", "Rene Alexis Segura Perez")
    role = clean_text(row.get("titulo")) or "the role"
    company = clean_text(row.get("empresa")) or "your company"
    skills = ", ".join(matched_skills[:8]) or ", ".join(profile.get("skills", [])[:6])
    github = profile.get("github", "")
    portfolio = profile.get("portfolio", "")
    availability = profile.get("availability", "")
    no_salary = not clean_text(row.get("salario"))
    research_summary = clean_text(research.get("resumen"))[:450]

    if language == "en":
        salary_line = (
            "Since the salary range is not published, I would be interested if the role is above "
            "MXN $22,000 per month or its USD equivalent.\n\n"
            if no_salary else ""
        )
        return f"""# Cover letter - {role} - {company}

Hello {company} team,

My name is {name}. I am a Full Stack Developer focused on React, TypeScript, Node.js, NestJS, CI/CD and Azure DevOps. I am interested in the {role} position because it matches my experience with {skills}.

Based on the role and what I found about {company}, I can contribute by building maintainable web applications, improving delivery workflows, debugging production issues and supporting reliable deployments with Docker, Linux, Nginx and GitHub Actions.

Company context considered:
{research_summary or "No public company research was available in this run."}

{salary_line}My availability is {availability}. You can review my work here:
- GitHub: {github}
- Portfolio: {portfolio}

Best regards,
{name}
"""

    salary_line = (
        "Como la oferta no publica rango salarial, me interesa avanzar si la posicion supera los "
        "$22,000 MXN mensuales o su equivalente en dolares.\n\n"
        if no_salary else ""
    )
    return f"""# Carta de interes - {role} - {company}

Hola equipo de {company},

Mi nombre es {name}. Soy Full Stack Developer con enfoque en React, TypeScript, Node.js, NestJS, CI/CD y Azure DevOps. Me interesa la vacante de {role} porque conecta directamente con mi experiencia en {skills}.

Por el tipo de rol y lo investigado sobre {company}, puedo aportar valor construyendo aplicaciones web mantenibles, mejorando flujos de entrega, resolviendo incidencias en produccion y apoyando despliegues confiables con Docker, Linux, Nginx y GitHub Actions.

Contexto de empresa considerado:
{research_summary or "No se ejecuto investigacion publica de empresa en esta corrida."}

{salary_line}Mi disponibilidad es {availability}. Puedes revisar mi trabajo aqui:
- GitHub: {github}
- Portafolio: {portfolio}

Saludos,
{name}
"""


def recruiter_message(profile, row, matched_skills):
    language = detect_language(row)
    name = profile.get("name", "Rene Alexis Segura Perez")
    role = clean_text(row.get("titulo")) or "the role"
    skills = ", ".join(matched_skills[:5]) or "React, TypeScript, Node.js, NestJS, CI/CD"
    if language == "en":
        return (
            f"Hi, I am {name}, a Junior Full Stack Developer with hands-on experience in {skills}. "
            f"I am interested in {role} and can support product delivery, debugging and reliable deployments."
        )
    return (
        f"Hola, soy {name}, Junior Full Stack Developer con experiencia practica en {skills}. "
        f"Me interesa la vacante de {role} y puedo aportar en desarrollo, debugging y despliegues confiables."
    )

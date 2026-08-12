import json
from pathlib import Path

import pytest

from botjobs.profile import load_profile
from botjobs.ranking import enrich_row, score_job


PROFILE = load_profile(Path(__file__).resolve().parents[1] / "profile.example.json")


def valid_job(**updates):
    row = {
        "titulo": "Junior Full Stack Developer",
        "empresa": "Empresa Demo",
        "descripcion": "React TypeScript Node.js PostgreSQL Docker para plataforma SaaS",
        "industria_detectada": "SaaS",
        "ubicacion": "Remoto Mexico",
        "modalidad": "remoto",
        "salario": "20000 MXN",
        "horas_semana": "40",
        "seniority": "Junior",
    }
    row.update(updates)
    return enrich_row(row)


@pytest.mark.parametrize("updates,expected_flag", [
    ({"salario": "19999 MXN"}, "salario_bajo"),
    ({"horas_semana": "41"}, "mas_de_40_horas"),
    ({"modalidad": "presencial", "ubicacion": "Monterrey"}, "presencial_fuera_cdmx"),
    ({"modalidad": "hibrido", "ubicacion": "Guadalajara"}, "hibrido_fuera_cdmx"),
    ({"titulo": "Senior Full Stack Developer", "seniority": "Senior"}, "seniority_alto"),
    ({"industria_detectada": "viajes"}, "industria_bloqueada"),
    ({"descripcion": "React TypeScript Node.js PostgreSQL Docker por proyecto SaaS"}, "trabajo_por_proyecto"),
])
def test_hard_limits_discard_with_auditable_flag(updates, expected_flag):
    score, status, _skills, _interests, flags = score_job(PROFILE, valid_job(**updates))

    assert status == "descartada"
    assert score <= 59
    assert expected_flag in flags


@pytest.mark.parametrize("updates", [
    {"salario": "20000 MXN"},
    {"horas_semana": "40"},
    {"modalidad": "presencial", "ubicacion": "CDMX"},
    {"modalidad": "hibrido", "ubicacion": "CDMX"},
])
def test_exact_allowed_limits_can_be_shortlisted(updates):
    _score, status, skills, _interests, flags = score_job(PROFILE, valid_job(**updates))

    assert status == "preseleccionada"
    assert len(skills) >= 5
    assert not flags


def test_ranking_decision_is_repeatable():
    first = score_job(PROFILE, valid_job())
    second = score_job(PROFILE, valid_job())

    assert first == second

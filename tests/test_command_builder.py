import sys

import pytest
from pydantic import ValidationError

from backend.schemas import ExtractLinksParams, SearchParams
from backend.services.command_builder import (
    build_apply_dry_run_command,
    build_extract_links_command,
    build_search_command,
)


def test_build_search_command_uses_only_validated_values():
    params = SearchParams(
        portals=["indeed", "linkedin"],
        max_results=10,
        refresh_cache=True,
        browser=True,
        research=True,
    )

    assert build_search_command(params) == [
        sys.executable,
        "bot_jobs.py",
        "--auto-search",
        "--profile",
        "profile.example.json",
        "--out",
        "output",
        "--portals",
        "indeed,linkedin",
        "--max-results",
        "10",
        "--refresh-cache",
        "--browser",
        "--research",
    ]


def test_search_params_reject_unknown_portal_and_free_command():
    with pytest.raises(ValidationError):
        SearchParams(portals=["example"], max_results=10)

    with pytest.raises(ValidationError):
        SearchParams(portals=["indeed"], max_results=10, command="whoami")


@pytest.mark.parametrize("max_results", [0, 51])
def test_search_params_reject_out_of_range_limit(max_results):
    with pytest.raises(ValidationError):
        SearchParams(portals=["indeed"], max_results=max_results)


def test_other_commands_have_fixed_paths():
    assert build_extract_links_command(ExtractLinksParams()) == [
        sys.executable,
        "bot_jobs.py",
        "--profile",
        "profile.example.json",
        "--jobs",
        "vacantes.template.xlsx",
        "--out",
        "output",
        "--extract-links",
    ]
    assert build_apply_dry_run_command() == [
        sys.executable,
        "bot_jobs.py",
        "--apply-approved",
        "--profile",
        "profile.example.json",
        "--jobs",
        "output/botjobs_resultados.json",
        "--dry-run",
    ]

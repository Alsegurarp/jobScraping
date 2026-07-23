from backend import config
from backend.schemas import ExtractLinksParams, SearchParams


def _base_command() -> list[str]:
    return [config.PYTHON_EXECUTABLE, config.BOT_SCRIPT]


def build_search_command(params: SearchParams) -> list[str]:
    command = [
        *_base_command(),
        "--auto-search",
        "--profile",
        config.PROFILE_FILE,
        "--out",
        config.OUTPUT_DIR,
        "--portals",
        ",".join(portal.value for portal in params.portals),
        "--max-results",
        str(params.max_results),
    ]
    if params.refresh_cache:
        command.append("--refresh-cache")
    if params.browser:
        command.append("--browser")
    if params.research:
        command.append("--research")
    return command


def build_extract_links_command(params: ExtractLinksParams) -> list[str]:
    command = [
        *_base_command(),
        "--profile",
        config.PROFILE_FILE,
        "--jobs",
        config.JOBS_TEMPLATE,
        "--out",
        config.OUTPUT_DIR,
        "--extract-links",
    ]
    if params.browser:
        command.append("--browser")
    if params.research:
        command.append("--research")
    return command


def build_apply_dry_run_command() -> list[str]:
    return [
        *_base_command(),
        "--apply-approved",
        "--profile",
        config.PROFILE_FILE,
        "--jobs",
        config.OUTPUT_FILE,
        "--dry-run",
    ]


def build_prepare_applications_command() -> list[str]:
    return [
        *_base_command(),
        "--apply-approved",
        "--profile",
        config.PROFILE_FILE,
        "--jobs",
        config.OUTPUT_FILE,
        "--browser",
    ]


def build_retry_applications_command() -> list[str]:
    return [*build_prepare_applications_command(), "--retry-intervention"]


def build_submit_applications_command() -> list[str]:
    return [*build_prepare_applications_command(), "--submit", "--confirm-submit", "ENVIAR"]

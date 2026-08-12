import json
from pathlib import Path

from .utils import words


def load_profile(path):
    path = Path(path)
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"No se pudo leer el perfil {path}: {exc}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON invalido en el perfil {path}: {exc}") from None
    profile["skill_terms"] = words(" ".join(profile.get("skills", [])))
    profile["interest_terms"] = words(" ".join(profile.get("interest_keywords", [])))
    return profile

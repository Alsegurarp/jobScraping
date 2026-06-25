import json
from pathlib import Path

from .utils import words


def load_profile(path):
    profile = json.loads(Path(path).read_text(encoding="utf-8"))
    profile["skill_terms"] = words(" ".join(profile.get("skills", [])))
    profile["interest_terms"] = words(" ".join(profile.get("interest_keywords", [])))
    return profile

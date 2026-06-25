#!/usr/bin/env python3
import argparse
import csv
import json
import re
from pathlib import Path


STOPWORDS = {
    "a", "al", "and", "con", "de", "del", "el", "en", "for", "la", "las",
    "los", "of", "para", "por", "the", "to", "un", "una", "y",
}


def words(text):
    return {
        word
        for word in re.findall(r"[a-z0-9+#.]+", (text or "").lower())
        if len(word) > 2 and word not in STOPWORDS
    }


def load_profile(path):
    with open(path, encoding="utf-8") as file:
        profile = json.load(file)

    terms = words(" ".join([
        profile.get("headline", ""),
        " ".join(profile.get("skills", [])),
        " ".join(profile.get("target_roles", [])),
        " ".join(profile.get("keywords", [])),
    ]))
    profile["terms"] = terms
    return profile


def load_jobs(path):
    with open(path, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def score_job(profile, job):
    text = " ".join(str(value) for value in job.values())
    job_terms = words(text)
    matched = sorted(profile["terms"] & job_terms)
    score = len(matched) * 10

    title = job.get("title", "").lower()
    for role in profile.get("target_roles", []):
        if role.lower() in title:
            score += 30

    location = " ".join([job.get("location", ""), job.get("remote", "")]).lower()
    preferred_locations = [place.lower() for place in profile.get("preferred_locations", [])]
    if "remote" in location or any(place in location for place in preferred_locations):
        score += 15

    return score, matched


def cover_letter(profile, job, matched):
    name = profile.get("name", "Candidato")
    role = job.get("title", "la vacante")
    company = job.get("company", "su empresa")
    matched = sorted(matched)
    skills = ", ".join(matched[:8]) or ", ".join(profile.get("skills", [])[:5])

    return f"""Hola {company},

Soy {name}. Me interesa {role} porque encaja con mi experiencia en {skills}.

Perfil breve:
{profile.get("summary", "")}

Quedo atento para conversar sobre cómo puedo aportar al equipo.

Saludos,
{name}
"""


def run(profile_path, jobs_path, output_dir, top):
    profile = load_profile(profile_path)
    jobs = load_jobs(jobs_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    ranked = []
    for job in jobs:
        score, matched = score_job(profile, job)
        ranked.append({**job, "score": score, "matched_keywords": ", ".join(matched)})

    ranked.sort(key=lambda item: int(item["score"]), reverse=True)

    ranked_path = output_dir / "ranked_jobs.csv"
    with open(ranked_path, "w", newline="", encoding="utf-8") as file:
        fieldnames = list(ranked[0].keys()) if ranked else []
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ranked)

    for index, job in enumerate(ranked[:top], start=1):
        company = re.sub(r"[^a-z0-9]+", "-", job.get("company", "empresa").lower()).strip("-")
        title = re.sub(r"[^a-z0-9]+", "-", job.get("title", "vacante").lower()).strip("-")
        path = output_dir / f"{index:02d}-{company}-{title}.txt"
        path.write_text(cover_letter(profile, job, words(job["matched_keywords"])), encoding="utf-8")

    return ranked_path


def demo():
    tmp = Path(".demo-output")
    profile = Path("profile.example.json")
    jobs = Path("jobs.example.csv")
    ranked = run(profile, jobs, tmp, 2)
    rows = load_jobs(ranked)
    assert rows[0]["score"] >= rows[-1]["score"]
    assert (tmp / "01-acme-security-analista-de-seguridad.txt").exists()
    print("demo ok")


def main():
    parser = argparse.ArgumentParser(description="Rankea vacantes y genera borradores de aplicación.")
    parser.add_argument("--profile", default="profile.example.json")
    parser.add_argument("--jobs", default="jobs.example.csv")
    parser.add_argument("--out", default="output")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        demo()
        return

    ranked_path = run(Path(args.profile), Path(args.jobs), Path(args.out), args.top)
    print(f"Listo: {ranked_path}")


if __name__ == "__main__":
    main()

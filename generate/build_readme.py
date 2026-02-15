#!/usr/bin/env python3
"""
Generates README.md for the divital-coder profile repo.

Reads static narrative content from data/header.md and data/footer.md,
and dynamically generates a project showcase from data/projects.csv
by fetching live metadata from the GitHub API.

Inspired by https://github.com/oxinabox/oxinabox
"""

import csv
import os
import urllib.request
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
README_PATH = ROOT / "README.md"

GITHUB_API = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github.v3+json"}

# Use token if available (for higher rate limits in CI)
token = os.environ.get("GITHUB_TOKEN")
if token:
    HEADERS["Authorization"] = f"token {token}"


def fetch_repo_info(repo_url: str) -> dict:
    """Fetch repository metadata from GitHub API."""
    # Extract owner/repo from URL
    parts = repo_url.rstrip("/").split("/")
    owner, repo = parts[-2], parts[-1]

    api_url = f"{GITHUB_API}/repos/{owner}/{repo}"
    req = urllib.request.Request(api_url, headers=HEADERS)

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  Warning: Could not fetch {owner}/{repo}: {e}")
        return {
            "full_name": f"{owner}/{repo}",
            "html_url": repo_url,
            "description": "",
            "stargazers_count": 0,
            "language": None,
            "fork": False,
            "owner": {"avatar_url": "", "login": owner},
        }

    return data


def language_badge(lang: str | None) -> str:
    """Return a simple language indicator."""
    if not lang:
        return ""
    return f"`{lang}`"


def star_badge(count: int) -> str:
    """Return star count if non-zero."""
    if count == 0:
        return ""
    word = "star" if count == 1 else "stars"
    return f" ({count} {word})"


def build_project_section(projects_csv: Path) -> str:
    """Read projects CSV, fetch metadata, and build markdown."""
    lines = []

    # Group by category
    categories = defaultdict(list)
    with open(projects_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            categories[row["category"]].append(row["repo"])

    for category, repos in categories.items():
        lines.append(f"### {category}\n")

        for repo_url in repos:
            print(f"  Fetching: {repo_url}")
            info = fetch_repo_info(repo_url)

            name = info["full_name"].split("/")[-1]
            owner = info["owner"]["login"]
            avatar = info["owner"]["avatar_url"]
            desc = info.get("description") or ""
            lang = language_badge(info.get("language"))
            stars = star_badge(info.get("stargazers_count", 0))
            url = info["html_url"]
            fork_indicator = " *(fork — active contributor)*" if info.get("fork") else ""

            lines.append(
                f" - <a href='https://github.com/{owner}'>"
                f"<img src='{avatar}&s=40' height='20' width='20'/></a> "
                f"[**{name}**]({url}){fork_indicator}: "
                f"_{desc}_ {lang}{stars}"
            )

        lines.append("")

    return "\n".join(lines)


def main():
    print("Building README.md...")

    # Read static sections
    header = (DATA_DIR / "header.md").read_text()
    footer = (DATA_DIR / "footer.md").read_text()

    # Build dynamic project section
    print("Fetching project metadata from GitHub API...")
    project_section = build_project_section(DATA_DIR / "projects.csv")

    # Assemble
    readme = f"{header}\n## Project Showcase\n\n{project_section}\n{footer}"

    README_PATH.write_text(readme)
    print(f"Wrote {README_PATH}")


if __name__ == "__main__":
    main()

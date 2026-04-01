#!/usr/bin/env python3
"""Auto-update README with latest repo list and language badges from GitHub API."""

import requests
import re
import urllib.parse
from collections import Counter

GITHUB_USERNAME = "ringmast4r"
README_PATH = "README.md"

# Language -> (shields.io color, logo name, logo color)
# If a language isn't here it gets a default gray badge
LANG_STYLES = {
    "Python":       ("3776AB", "python", "white"),
    "JavaScript":   ("F7DF1E", "javascript", "black"),
    "TypeScript":   ("3178C6", "typescript", "white"),
    "Go":           ("00ADD8", "go", "white"),
    "Rust":         ("000000", "rust", "white"),
    "C":            ("A8B9CC", "c", "black"),
    "C++":          ("00599C", "cplusplus", "white"),
    "C#":           ("239120", "csharp", "white"),
    "Java":         ("ED8B00", "openjdk", "white"),
    "Ruby":         ("CC342D", "ruby", "white"),
    "PHP":          ("777BB4", "php", "white"),
    "Shell":        ("4EAA25", "gnubash", "white"),
    "Bash":         ("4EAA25", "gnubash", "white"),
    "PowerShell":   ("5391FE", "powershell", "white"),
    "HTML":         ("E34F26", "html5", "white"),
    "CSS":          ("1572B6", "css3", "white"),
    "SCSS":         ("CC6699", "sass", "white"),
    "Sass":         ("CC6699", "sass", "white"),
    "Lua":          ("2C2D72", "lua", "white"),
    "Perl":         ("39457E", "perl", "white"),
    "R":            ("276DC3", "r", "white"),
    "Swift":        ("FA7343", "swift", "white"),
    "Kotlin":       ("7F52FF", "kotlin", "white"),
    "Dart":         ("0175C2", "dart", "white"),
    "Dockerfile":   ("2496ED", "docker", "white"),
    "Makefile":     ("427819", "cmake", "white"),
    "HCL":          ("844FBA", "terraform", "white"),
    "Nix":          ("5277C3", "nixos", "white"),
    "Vue":          ("4FC08D", "vuedotjs", "white"),
    "Svelte":       ("FF3E00", "svelte", "white"),
    "Jupyter Notebook": ("F37626", "jupyter", "white"),
    "Elixir":       ("4B275F", "elixir", "white"),
    "Haskell":      ("5D4F85", "haskell", "white"),
    "Zig":          ("F7A41D", "zig", "white"),
    "Nim":          ("FFE953", "nim", "black"),
    "EJS":          ("B4CA65", "ejs", "black"),
    "Handlebars":   ("FF7C00", "handlebarsdotjs", "white"),
    "YAML":         ("CB171E", "yaml", "white"),
    "Arduino":      ("00979D", "arduino", "white"),
}

# Languages to skip (not real programming languages or too noisy)
SKIP_LANGS = {"Procfile", "Batchfile", "Roff", "TeX", "Rich Text Format"}


def fetch_repos():
    """Fetch all public repos from GitHub API."""
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos?per_page=100&page={page}&sort=updated"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching repos: {response.status_code}")
            break
        data = response.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos


def fetch_all_languages(repos):
    """Fetch languages for all repos and aggregate byte counts."""
    lang_bytes = Counter()
    for repo in repos:
        url = repo.get("languages_url", "")
        if not url:
            continue
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                langs = resp.json()
                for lang, bytes_count in langs.items():
                    if lang not in SKIP_LANGS:
                        lang_bytes[lang] += bytes_count
        except Exception:
            continue
    return lang_bytes


def generate_language_badges(lang_bytes):
    """Generate shields.io badge markdown for each language, sorted by usage."""
    sorted_langs = lang_bytes.most_common()
    badges = []

    for lang, _ in sorted_langs:
        # Normalize display name
        display = lang
        if lang == "Shell":
            display = "Bash"
        elif lang == "HTML":
            display = "HTML5"
        elif lang == "CSS":
            display = "CSS3"

        style = LANG_STYLES.get(lang)
        if not style:
            # Default gray badge with no logo
            encoded = urllib.parse.quote(display)
            badges.append(f"![{display}](https://img.shields.io/badge/{encoded}-555555?style=for-the-badge&logoColor=white)")
        else:
            color, logo, logo_color = style
            encoded = urllib.parse.quote(display)
            badges.append(f"![{display}](https://img.shields.io/badge/{encoded}-{color}?style=for-the-badge&logo={logo}&logoColor={logo_color})")

    return "\n".join(badges)


def generate_repo_table(repos):
    """Generate markdown table for repos."""
    repos_sorted = sorted(repos, key=lambda x: x.get('stargazers_count', 0), reverse=True)

    lines = []
    lines.append("| Repository | Description | Stars |")
    lines.append("|:-----------|:------------|:-----:|")

    for repo in repos_sorted:
        name = repo['name']
        desc = repo.get('description') or 'No description'
        desc = desc.replace('|', '-')
        if len(desc) > 60:
            desc = desc[:57] + "..."

        line = f"| [**{name}**](https://github.com/{GITHUB_USERNAME}/{name}) | {desc} | ![](https://img.shields.io/github/stars/{GITHUB_USERNAME}/{name}?style=flat-square&color=CC0000&label=%E2%98%85) |"
        lines.append(line)

    return "\n".join(lines)


def update_readme(repos, lang_bytes):
    """Update README with new repo table and language badges."""
    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    repo_count = len(repos)

    # Update repo count
    content = re.sub(
        r'### All \d+ Public Repositories',
        f'### All {repo_count} Public Repositories',
        content
    )

    # Update repo table
    new_table = generate_repo_table(repos)
    table_start = content.find("| Repository | Description | Stars |")
    if table_start != -1:
        table_end = content.find("</div>", table_start)
        if table_end != -1:
            content = content[:table_start] + new_table + "\n\n" + content[table_end:]
            print(f"Updated repo table with {repo_count} repos")

    # Update language badges
    lang_start = content.find("<!-- LANGUAGES_START -->")
    lang_end = content.find("<!-- LANGUAGES_END -->")
    if lang_start != -1 and lang_end != -1:
        badges = generate_language_badges(lang_bytes)
        lang_section = f"<!-- LANGUAGES_START -->\n### LANGUAGES\n{badges}\n<!-- LANGUAGES_END -->"
        content = content[:lang_start] + lang_section + content[lang_end + len("<!-- LANGUAGES_END -->"):]
        print(f"Updated language badges: {len(lang_bytes)} languages")

    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    print("Fetching repos from GitHub...")
    repos = fetch_repos()
    print(f"Found {len(repos)} repos")

    if not repos:
        print("No repos found, skipping update")
        return

    print("Fetching languages across all repos...")
    lang_bytes = fetch_all_languages(repos)
    print(f"Found {len(lang_bytes)} languages: {', '.join(l for l, _ in lang_bytes.most_common(10))}")

    update_readme(repos, lang_bytes)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Auto-update README with latest repo list from GitHub API."""

import requests
import re

GITHUB_USERNAME = "ringmast4r"
README_PATH = "README.md"

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

def update_readme(repos):
    """Update README with new repo table."""
    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    repo_count = len(repos)

    content = re.sub(
        r'### All \d+ Public Repositories',
        f'### All {repo_count} Public Repositories',
        content
    )

    new_table = generate_repo_table(repos)

    table_start = content.find("| Repository | Description | Stars |")
    if table_start == -1:
        print("Could not find repo table in README")
        return

    table_end = content.find("</div>", table_start)
    if table_end == -1:
        print("Could not find end of repo table")
        return

    new_content = content[:table_start] + new_table + "\n\n" + content[table_end:]

    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Updated README with {repo_count} repos")

def main():
    print("Fetching repos from GitHub...")
    repos = fetch_repos()
    print(f"Found {len(repos)} repos")

    if repos:
        update_readme(repos)
    else:
        print("No repos found, skipping update")

if __name__ == "__main__":
    main()

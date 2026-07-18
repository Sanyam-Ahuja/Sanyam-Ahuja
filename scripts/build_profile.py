#!/usr/bin/env python3
"""
Master build script for Sanyam's GitHub profile.
Runs local scraping, custom heatmap SVG generation, and parses local Next.js portfolio MDX files
to auto-generate latest blog post links.
"""
import os
import re
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)

# Add imports for local scripts
import fetch_contributions
import render_heatmap_svg


def parse_date(date_str):
    try:
        parts = date_str.split()
        month_name = parts[0]
        year = int(parts[1])
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        month = months.index(month_name) + 1
        return (year, month)
    except Exception:
        return (0, 0)


def extract_blog_posts():
    # Local path to portfolio notes relative to the script
    notes_dir = os.path.join(HERE, "..", "..", "..", "src", "content", "notes")
    
    if not os.path.exists(notes_dir):
        print(f"Warning: Local portfolio notes directory not found at {notes_dir}. Falling back to default list.")
        return None

    posts = []
    for filename in os.listdir(notes_dir):
        if filename.endswith(".mdx") or filename.endswith(".md"):
            filepath = os.path.join(notes_dir, filename)
            slug = os.path.splitext(filename)[0]
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
            title_match = re.search(r'title:\s*["\'](.*?)["\']', content)
            updated_match = re.search(r'updated:\s*["\'](.*?)["\']', content)
            
            if title_match and updated_match:
                posts.append({
                    "slug": slug,
                    "title": title_match.group(1),
                    "updated": updated_match.group(1)
                })
                
    # Sort posts descending (newest first)
    posts.sort(key=lambda p: parse_date(p["updated"]), reverse=True)
    return posts


def main():
    print("[1/3] Scraping GitHub contribution data...")
    days = fetch_contributions.fetch_days()
    data = fetch_contributions.build_data(days)
    
    # Save contributions.json
    data_dir = os.path.join(HERE, "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    json_path = os.path.join(data_dir, "contributions.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Saved contribution telemetry to {json_path}")

    print("[2/3] Rendering zinc-blue contribution heatmap SVG...")
    svg_content = render_heatmap_svg.render(data)
    svg_path = os.path.join(HERE, "..", "sanyam-heatmap.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Saved heatmap to {svg_path}")

    print("[3/3] Parsing blog posts and generating README.md...")
    template_path = os.path.join(HERE, "..", "README_template.md")
    readme_path = os.path.join(HERE, "..", "README.md")
    
    if not os.path.exists(template_path):
        print(f"Error: README_template.md not found at {template_path}")
        return 1
        
    with open(template_path, "r", encoding="utf-8") as f:
        readme_content = f.read()

    # Extract existing readme segments for fallbacks
    old_commits_block = ""
    old_repos_block = ""
    old_writing_block = ""
    
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            old_readme = f.read()
        commits_match = re.search(r'<!-- RECENT_COMMITS_START -->([\s\S]*?)<!-- RECENT_COMMITS_END -->', old_readme)
        if commits_match:
            old_commits_block = commits_match.group(1).strip()
        repos_match = re.search(r'<!-- RECENT_REPOS_START -->([\s\S]*?)<!-- RECENT_REPOS_END -->', old_readme)
        if repos_match:
            old_repos_block = repos_match.group(1).strip()
        writing_match = re.search(r'<!-- LATEST_WRITING_START -->([\s\S]*?)<!-- LATEST_WRITING_END -->', old_readme)
        if writing_match:
            old_writing_block = writing_match.group(1).strip()

    # 1. Handle Latest Writing
    posts = extract_blog_posts()
    if posts:
        writing_lines = []
        for post in posts:
            writing_lines.append(f"* [{post['title']}](https://sahuja.in/notes/{post['slug']})")
        writing_block = "\n".join(writing_lines)
    else:
        if old_writing_block:
            writing_block = old_writing_block
        else:
            default_posts = [
                "* [Why I Daily-Drive Fedora Silverblue](https://sahuja.in/notes/fedora-silverblue)",
                "* [My Homelab Was Never About Watching Movies](https://sahuja.in/notes/homelab-movies)",
                "* [Why Tree-Sitter Uses Byte Offsets](https://sahuja.in/notes/tree-sitter-byte-offsets)"
            ]
            writing_block = "\n".join(default_posts)

    # 2. Handle Recent Commits
    commits = data.get("latest_commits", [])
    if commits:
        commit_lines = []
        for c in commits:
            commit_lines.append(f"* **{c['repo']}** [`{c['sha']}`]({c['url']}) — {c['message']}")
        commits_block = "\n".join(commit_lines)
    else:
        commits_block = old_commits_block if old_commits_block else "* No recent commits found."

    # 3. Handle Recently Updated Repos
    repos = data.get("recently_updated_repos", [])
    if repos:
        repo_lines = []
        for r in repos:
            desc = f" — {r['description']}" if r['description'] else ""
            repo_lines.append(f"* **[{r['name']}]({r['url']})**{desc} (*{r['language']}*)")
        repos_block = "\n".join(repo_lines)
    else:
        repos_block = old_repos_block if old_repos_block else "* No recently updated repositories found."

    # Insert blocks into placeholders
    readme_content = re.sub(r'(<!-- LATEST_WRITING_START -->)[\s\S]*?(<!-- LATEST_WRITING_END -->)', f"\\1\n{writing_block}\n\\2", readme_content)
    readme_content = re.sub(r'(<!-- RECENT_COMMITS_START -->)[\s\S]*?(<!-- RECENT_COMMITS_END -->)', f"\\1\n{commits_block}\n\\2", readme_content)
    readme_content = re.sub(r'(<!-- RECENT_REPOS_START -->)[\s\S]*?(<!-- RECENT_REPOS_END -->)', f"\\1\n{repos_block}\n\\2", readme_content)
    
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"Successfully generated profile README at {readme_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

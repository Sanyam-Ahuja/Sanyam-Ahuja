#!/usr/bin/env python3
"""
Master build script for Sanyam's GitHub profile.
Runs local scraping, custom heatmap SVG generation,
and generates the final README.md.
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)

# Add imports for local scripts
import fetch_contributions
import render_heatmap_svg


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

    print("[3/3] Generating README.md...")
    template_path = os.path.join(HERE, "..", "README_template.md")
    readme_path = os.path.join(HERE, "..", "README.md")
    
    if not os.path.exists(template_path):
        print(f"Error: README_template.md not found at {template_path}")
        return 1
        
    with open(template_path, "r", encoding="utf-8") as f:
        readme_content = f.read()

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"Successfully generated profile README at {readme_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

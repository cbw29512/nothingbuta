from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CATALOG_PATH = ROOT / "scripts" / "tool_catalog.json"
BASE_URL = "https://onecleartool.com"
EXCLUDED_DIRS = {"assets", "privacy", "terms"}


def load_catalog() -> list[dict[str, str]]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    required = {"slug", "name", "description", "category"}
    seen: set[str] = set()
    for item in catalog:
        missing = required - item.keys()
        if missing:
            raise ValueError(f"catalog entry missing {sorted(missing)}: {item}")
        slug = item["slug"]
        if slug in seen:
            raise ValueError(f"duplicate catalog slug: {slug}")
        seen.add(slug)
    return sorted(catalog, key=lambda item: item["name"].lower())


def tool_slugs_on_disk() -> set[str]:
    return {
        path.name
        for path in DOCS.iterdir()
        if path.is_dir()
        and path.name not in EXCLUDED_DIRS
        and (path / "index.html").exists()
    }


def render_cards(catalog: list[dict[str, str]]) -> str:
    lines = ['    <section class="tool-grid" aria-label="Available One Clear Tool calculators">']
    for item in catalog:
        slug = html.escape(item["slug"], quote=True)
        name = html.escape(item["name"])
        description = html.escape(item["description"])
        category = html.escape(item["category"])
        lines.append(
            f'      <a class="tool-card" href="{slug}/"><span class="badge">{category}</span>'
            f'<strong>{name}</strong><span>{description}</span></a>'
        )
    lines.append("    </section>")
    return "\n".join(lines)


def render_item_list(catalog: list[dict[str, str]]) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "One Clear Tool calculators",
        "numberOfItems": len(catalog),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index,
                "name": item["name"],
                "url": f'{BASE_URL}/{item["slug"]}/',
            }
            for index, item in enumerate(catalog, 1)
        ],
    }
    return "  <script type=\"application/ld+json\" id=\"oct-catalog-schema\">\n" + json.dumps(data, indent=2) + "\n  </script>"


def sync_home(doc: str, catalog: list[dict[str, str]]) -> str:
    count = len(catalog)
    doc = re.sub(r"Browse \d+ tools", f"Browse {count} tools", doc)
    doc = re.sub(r"\d+ live tools", f"{count} live tools", doc)
    doc = re.sub(r"\d+ tools available\.", f"{count} tools available.", doc)

    cards_pattern = re.compile(
        r'    <section class="tool-grid" aria-label="Available One Clear Tool calculators">.*?    </section>',
        re.DOTALL,
    )
    if not cards_pattern.search(doc):
        raise ValueError("homepage tool grid not found")
    doc = cards_pattern.sub(render_cards(catalog), doc, count=1)

    schema_pattern = re.compile(
        r'\s*<script type="application/ld\+json"(?: id="oct-catalog-schema")?>\s*\{.*?"@type"\s*:\s*"ItemList".*?</script>',
        re.DOTALL,
    )
    match = schema_pattern.search(doc)
    if not match:
        raise ValueError("homepage ItemList schema not found")
    doc = doc[: match.start()] + "\n" + render_item_list(catalog) + doc[match.end() :]
    return doc


def render_sitemap(catalog: list[dict[str, str]]) -> str:
    urls = [(f"{BASE_URL}/", "weekly", "0.9")]
    urls += [(f'{BASE_URL}/{item["slug"]}/', "weekly", "0.8") for item in catalog]
    urls += [(f"{BASE_URL}/privacy/", "monthly", "0.4"), (f"{BASE_URL}/terms/", "monthly", "0.4")]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, freq, priority in urls:
        lines.extend(
            [
                "  <url>",
                f"    <loc>{url}</loc>",
                f"    <changefreq>{freq}</changefreq>",
                f"    <priority>{priority}</priority>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def sync_readme(doc: str, count: int) -> str:
    doc = re.sub(r"\*\*Total: \d+ live calculator pages\.\*\*", f"**Total: {count} live calculator pages.**", doc)
    doc = re.sub(r"requires all \d+ calculator pages", f"requires all {count} calculator pages", doc)
    return doc


def expected_outputs(catalog: list[dict[str, str]]) -> dict[Path, str]:
    return {
        DOCS / "index.html": sync_home((DOCS / "index.html").read_text(encoding="utf-8-sig"), catalog),
        DOCS / "sitemap.xml": render_sitemap(catalog),
        ROOT / "README.md": sync_readme((ROOT / "README.md").read_text(encoding="utf-8-sig"), len(catalog)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    catalog = load_catalog()
    catalog_slugs = {item["slug"] for item in catalog}
    disk_slugs = tool_slugs_on_disk()
    missing = sorted(catalog_slugs - disk_slugs)
    unregistered = sorted(disk_slugs - catalog_slugs)
    if missing or unregistered:
        if missing:
            print("Catalog entries missing pages:", ", ".join(missing))
        if unregistered:
            print("Calculator pages missing catalog entries:", ", ".join(unregistered))
        return 1

    changed: list[Path] = []
    for path, expected in expected_outputs(catalog).items():
        current = path.read_text(encoding="utf-8-sig")
        if current != expected:
            changed.append(path)
            if args.write:
                path.write_text(expected, encoding="utf-8")

    if args.check and changed:
        for path in changed:
            print(f"Catalog-generated file is stale: {path.relative_to(ROOT)}")
        return 1

    print(f"Catalog parity verified for {len(catalog)} tools.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

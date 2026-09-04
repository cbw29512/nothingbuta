from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SUPPORT_URL = "https://www.buymeacoffee.com/divclass016"
BASE_URL = "https://onecleartool.com"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

TOOL_SUPPORT = f'''<aside class="oct-support" id="oct-tool-support" aria-label="Support One Clear Tool">
  <strong>Help keep One Clear Tool free.</strong>
  <p>If this calculator saved you time, optional support helps fund maintenance and new tools. No payment or account is required to use the calculator.</p>
  <a href="{SUPPORT_URL}" target="_blank" rel="noopener noreferrer">☕ Buy me a coffee</a>
</aside>'''

TOOL_FOOTER = f'''<nav class="oct-commercial-footer" id="oct-commercial-footer" aria-label="Site information">
  <a href="../">All tools</a>
  <a href="../privacy/">Privacy</a>
  <a href="../terms/">Terms</a>
  <a href="{SUPPORT_URL}" target="_blank" rel="noopener noreferrer">Support</a>
</nav>'''

HOME_SEARCH = '''<section class="oct-tool-search" id="oct-tool-search" aria-labelledby="oct-tool-search-label">
  <label id="oct-tool-search-label" for="oct-tool-search-input">Find a tool</label>
  <input id="oct-tool-search-input" type="search" autocomplete="off" placeholder="Try debt, mortgage, tip, flooring, pay...">
  <p class="oct-search-status" id="oct-tool-search-status" aria-live="polite">25 tools available.</p>
</section>'''

HOME_FOOTER = f'''<nav class="oct-commercial-footer" id="oct-commercial-footer" aria-label="Site information">
  <a href="privacy/">Privacy</a>
  <a href="terms/">Terms</a>
  <a href="{SUPPORT_URL}" target="_blank" rel="noopener noreferrer">Support</a>
</nav>'''

SCRIPT_RE = re.compile(
    r'<script(?P<attrs>[^>]*)type=["\']application/ld\+json["\'](?P<attrs2>[^>]*)>(?P<body>.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def tool_pages() -> list[Path]:
    excluded = {"assets", "privacy", "terms"}
    return sorted(
        path
        for path in DOCS.glob("*/index.html")
        if path.parent.name not in excluded
    )


def ensure_before(doc: str, marker: str, snippet: str, closing: str) -> str:
    if marker in doc:
        return doc
    if closing not in doc:
        raise ValueError(f"Missing {closing}")
    return doc.replace(closing, snippet + "\n" + closing, 1)


def remove_marker_block(doc: str, element: str, marker_id: str) -> str:
    pattern = rf'\s*<{element}[^>]*id=["\']{re.escape(marker_id)}["\'][^>]*>.*?</{element}>'
    return re.sub(pattern, "", doc, flags=re.IGNORECASE | re.DOTALL)


def canonical_url(doc: str, slug: str) -> str:
    match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', doc, re.IGNORECASE)
    return match.group(1) if match else f"{BASE_URL}/{slug}/"


def page_title(doc: str, slug: str) -> str:
    match = re.search(r'<title>(.*?)</title>', doc, re.IGNORECASE | re.DOTALL)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else slug.replace("-", " ").title()


def normalize_webapp_schema(doc: str, slug: str) -> str:
    kept: list[str] = []
    for match in SCRIPT_RE.finditer(doc):
        body = match.group("body")
        if re.search(r'["\']@type["\']\s*:\s*["\']WebApplication["\']', body, re.IGNORECASE):
            kept.append(match.group(0))

    if kept:
        doc = SCRIPT_RE.sub(
            lambda m: "" if re.search(r'["\']@type["\']\s*:\s*["\']WebApplication["\']', m.group("body"), re.IGNORECASE) else m.group(0),
            doc,
        )

    schema = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": page_title(doc, slug).split("|")[0].strip(),
        "url": canonical_url(doc, slug),
        "applicationCategory": "UtilityApplication",
        "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    }
    tag = f'<script type="application/ld+json" id="oct-tool-schema">{json.dumps(schema, separators=(",", ":"))}</script>'
    return ensure_before(doc, 'id="oct-tool-schema"', "  " + tag, "</head>")


def polish_tool(path: Path) -> str:
    slug = path.parent.name
    doc = path.read_text(encoding="utf-8-sig")

    # Remove prior generated blocks before re-inserting canonical versions.
    doc = remove_marker_block(doc, "aside", "oct-tool-support")
    doc = remove_marker_block(doc, "nav", "oct-commercial-footer")

    doc = ensure_before(doc, 'href="../assets/commercial.css"', '  <link rel="stylesheet" href="../assets/commercial.css">', "</head>")
    doc = ensure_before(doc, 'src="../assets/tool-ux.js"', '  <script src="../assets/tool-ux.js" defer></script>', "</head>")
    doc = normalize_webapp_schema(doc, slug)

    if slug == "paycheck-estimator":
        doc = doc.replace(
            "Enter your gross pay, pay frequency, tax assumptions, and recurring deductions.",
            "Enter your gross pay per check, tax assumptions, and recurring deductions.",
        )

    if "</main>" in doc:
        doc = doc.replace("</main>", TOOL_SUPPORT + "\n" + TOOL_FOOTER + "\n</main>", 1)
    else:
        raise ValueError(f"{slug}: missing </main>")

    return doc


def polish_home(path: Path) -> str:
    doc = path.read_text(encoding="utf-8-sig")
    doc = remove_marker_block(doc, "section", "oct-tool-search")
    doc = remove_marker_block(doc, "nav", "oct-commercial-footer")
    doc = ensure_before(doc, 'href="assets/commercial.css"', '  <link rel="stylesheet" href="assets/commercial.css">', "</head>")
    doc = ensure_before(doc, 'src="assets/home-ux.js"', '  <script src="assets/home-ux.js" defer></script>', "</head>")

    grid = '<section class="tool-grid" aria-label="Available One Clear Tool calculators">'
    if grid not in doc:
        raise ValueError("Homepage tool grid marker missing")
    doc = doc.replace(grid, HOME_SEARCH + "\n\n    " + grid, 1)

    if "</main>" not in doc:
        raise ValueError("Homepage missing </main>")
    doc = doc.replace("</main>", HOME_FOOTER + "\n</main>", 1)
    return doc


def update_sitemap(doc: str) -> str:
    additions = []
    for path in ("privacy", "terms"):
        url = f"{BASE_URL}/{path}/"
        if url not in doc:
            additions.append(
                "  <url>\n"
                f"    <loc>{url}</loc>\n"
                "    <lastmod>2026-09-03</lastmod>\n"
                "    <changefreq>monthly</changefreq>\n"
                "    <priority>0.4</priority>\n"
                "  </url>"
            )
    if additions:
        doc = doc.replace("</urlset>", "\n".join(additions) + "\n</urlset>")
    return doc


def expected_outputs() -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    home = DOCS / "index.html"
    outputs[home] = polish_home(home)
    for path in tool_pages():
        outputs[path] = polish_tool(path)
    sitemap = DOCS / "sitemap.xml"
    outputs[sitemap] = update_sitemap(sitemap.read_text(encoding="utf-8-sig"))
    return outputs


def validate_docs(outputs: dict[Path, str]) -> list[str]:
    errors: list[str] = []
    home = outputs[DOCS / "index.html"]
    for needle in (SUPPORT_URL, "oct-tool-search-input", "privacy/", "terms/"):
        if needle not in home:
            errors.append(f"homepage missing {needle}")

    for path in tool_pages():
        doc = outputs[path]
        rel = path.relative_to(ROOT)
        for needle in (
            "<form",
            'aria-live="polite"',
            SUPPORT_URL,
            'href="../assets/commercial.css"',
            'src="../assets/tool-ux.js"',
            "../privacy/",
            "../terms/",
            f"{BASE_URL}/{path.parent.name}/",
        ):
            if needle not in doc:
                errors.append(f"{rel}: missing {needle}")
        webapps = re.findall(r'["\']@type["\']\s*:\s*["\']WebApplication["\']', doc, re.IGNORECASE)
        if len(webapps) != 1:
            errors.append(f"{rel}: expected one WebApplication schema, found {len(webapps)}")

    paycheck = outputs.get(DOCS / "paycheck-estimator" / "index.html", "")
    if "pay frequency" in paycheck.lower():
        errors.append("paycheck estimator still claims a pay-frequency input that does not exist")

    for path in (DOCS / "privacy" / "index.html", DOCS / "terms" / "index.html"):
        if not path.exists():
            errors.append(f"missing legal page: {path.relative_to(ROOT)}")
            continue
        doc = path.read_text(encoding="utf-8")
        if SUPPORT_URL not in doc:
            errors.append(f"{path.relative_to(ROOT)}: missing support URL")

    sitemap = outputs[DOCS / "sitemap.xml"]
    for url in (f"{BASE_URL}/privacy/", f"{BASE_URL}/terms/"):
        if url not in sitemap:
            errors.append(f"sitemap missing {url}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Write generated changes to disk")
    parser.add_argument("--check", action="store_true", help="Fail if generated changes are not already committed")
    args = parser.parse_args()
    if args.write == args.check:
        parser.error("Choose exactly one of --write or --check")

    try:
        outputs = expected_outputs()
        errors = validate_docs(outputs)
        if errors:
            for error in errors:
                logging.error(error)
            return 1

        changed: list[Path] = []
        for path, expected in outputs.items():
            current = path.read_text(encoding="utf-8-sig")
            if current != expected:
                changed.append(path)
                if args.write:
                    path.write_text(expected, encoding="utf-8")

        if args.check and changed:
            for path in changed:
                logging.error("Generated polish is stale: %s", path.relative_to(ROOT))
            return 1

        logging.info(
            "Commercial polish validated: %d calculator pages, %d generated file(s) %s.",
            len(tool_pages()),
            len(changed),
            "updated" if args.write else "out of date" if changed else "current",
        )
        return 0
    except Exception as exc:
        logging.exception("Commercial polish failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())

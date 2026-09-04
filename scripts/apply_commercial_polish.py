from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CATALOG_PATH = ROOT / "scripts" / "tool_catalog.json"
SUPPORT_URL = "https://www.buymeacoffee.com/divclass016"
BASE_URL = "https://onecleartool.com"
TOOL_COUNT = len(json.loads(CATALOG_PATH.read_text(encoding="utf-8")))

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

HOME_SEARCH = f'''<section class="oct-tool-search" id="oct-tool-search" aria-labelledby="oct-tool-search-label">
  <label id="oct-tool-search-label" for="oct-tool-search-input">Find a tool</label>
  <input id="oct-tool-search-input" type="search" autocomplete="off" placeholder="Try debt, mortgage, tip, flooring, pay...">
  <p class="oct-search-status" id="oct-tool-search-status" aria-live="polite">{TOOL_COUNT} tools available.</p>
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
    return sorted(path for path in DOCS.glob("*/index.html") if path.parent.name not in excluded)


def clean_trailing_whitespace(doc: str) -> str:
    return re.sub(r"[ \t]+(?=\n)", "", doc)


def ensure_before(doc: str, marker: str, snippet: str, closing: str) -> str:
    if marker in doc:
        return doc
    if closing not in doc:
        raise ValueError(f"Missing {closing}")
    return doc.replace(closing, snippet + "\n" + closing, 1)


def upsert_block(doc: str, element: str, marker_id: str, canonical: str, closing: str) -> str:
    pattern = rf'<{element}[^>]*id=["\']{re.escape(marker_id)}["\'][^>]*>.*?</{element}>'
    if re.search(pattern, doc, flags=re.IGNORECASE | re.DOTALL):
        return re.sub(pattern, canonical, doc, count=1, flags=re.IGNORECASE | re.DOTALL)
    if closing not in doc:
        raise ValueError(f"Missing {closing}")
    return doc.replace(closing, canonical + "\n" + closing, 1)


def canonical_url(doc: str, slug: str) -> str:
    match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', doc, re.IGNORECASE)
    return match.group(1) if match else f"{BASE_URL}/{slug}/"


def page_title(doc: str, slug: str) -> str:
    match = re.search(r'<title>(.*?)</title>', doc, re.IGNORECASE | re.DOTALL)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else slug.replace("-", " ").title()


def is_webapp_schema(body: str) -> bool:
    return bool(re.search(r'["\']@type["\']\s*:\s*["\']WebApplication["\']', body, re.IGNORECASE))


def normalize_webapp_schema(doc: str, slug: str) -> str:
    webapps = [match for match in SCRIPT_RE.finditer(doc) if is_webapp_schema(match.group("body"))]
    if len(webapps) == 1 and 'id="oct-tool-schema"' in webapps[0].group(0):
        return doc

    doc = SCRIPT_RE.sub(lambda m: "" if is_webapp_schema(m.group("body")) else m.group(0), doc)
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

    doc = ensure_before(doc, 'href="../assets/commercial.css"', '  <link rel="stylesheet" href="../assets/commercial.css">', "</head>")
    doc = ensure_before(doc, 'src="../assets/tool-ux.js"', '  <script src="../assets/tool-ux.js" defer></script>', "</head>")
    doc = normalize_webapp_schema(doc, slug)

    if slug == "paycheck-estimator":
        doc = doc.replace(
            "Enter your gross pay, pay frequency, tax assumptions, and recurring deductions.",
            "Enter your gross pay per check, tax assumptions, and recurring deductions.",
        )

    doc = upsert_block(doc, "aside", "oct-tool-support", TOOL_SUPPORT, "</main>")
    doc = upsert_block(doc, "nav", "oct-commercial-footer", TOOL_FOOTER, "</main>")
    return clean_trailing_whitespace(doc)


def polish_home(path: Path) -> str:
    doc = path.read_text(encoding="utf-8-sig")
    doc = ensure_before(doc, 'href="assets/commercial.css"', '  <link rel="stylesheet" href="assets/commercial.css">', "</head>")
    doc = ensure_before(doc, 'src="assets/home-ux.js"', '  <script src="assets/home-ux.js" defer></script>', "</head>")

    grid = '<section class="tool-grid" aria-label="Available One Clear Tool calculators">'
    if 'id="oct-tool-search"' in doc:
        doc = upsert_block(doc, "section", "oct-tool-search", HOME_SEARCH, grid)
    elif grid in doc:
        doc = doc.replace(grid, HOME_SEARCH + "\n\n    " + grid, 1)
    else:
        raise ValueError("Homepage tool grid marker missing")

    doc = upsert_block(doc, "nav", "oct-commercial-footer", HOME_FOOTER, "</main>")
    return clean_trailing_whitespace(doc)


def expected_outputs() -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    home = DOCS / "index.html"
    outputs[home] = polish_home(home)
    for path in tool_pages():
        outputs[path] = polish_tool(path)
    return outputs


def validate_docs(outputs: dict[Path, str]) -> list[str]:
    errors: list[str] = []
    home = outputs[DOCS / "index.html"]
    for needle in (SUPPORT_URL, "oct-tool-search-input", "privacy/", "terms/", f"{TOOL_COUNT} tools available."):
        if needle not in home:
            errors.append(f"homepage missing {needle}")

    if len(tool_pages()) != TOOL_COUNT:
        errors.append(f"catalog expects {TOOL_COUNT} calculator pages but found {len(tool_pages())}")

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

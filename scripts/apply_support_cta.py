from pathlib import Path
import logging
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SUPPORT_URL = "https://www.buymeacoffee.com/divclass016"
MARKER = "one-clear-tool-support"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

SUPPORT_STYLE = f'''<style id="{MARKER}-style">
  .oct-support {{
    margin: 1.25rem 0 0;
    padding: 1rem 1.1rem;
    border: 1px solid rgba(37, 99, 235, 0.18);
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(255,255,255,.96), rgba(219,234,254,.70));
    box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
  }}
  .oct-support strong {{ display: block; margin-bottom: .25rem; color: #0f172a; }}
  .oct-support p {{ margin: 0; color: #475569; line-height: 1.55; }}
  .oct-support a {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 44px;
    margin-top: .75rem;
    padding: .7rem .95rem;
    border-radius: 999px;
    background: #ffdd00;
    color: #111827;
    font-weight: 900;
    text-decoration: none;
    box-shadow: 0 10px 24px rgba(15, 23, 42, .12);
  }}
  .oct-support a:hover {{ transform: translateY(-1px); }}
  .oct-support a:focus-visible {{ outline: 4px solid rgba(37,99,235,.22); outline-offset: 2px; }}
</style>'''

SUPPORT_BLOCK = f'''<aside class="oct-support" id="{MARKER}" aria-label="Support One Clear Tool">
  <strong>Help keep One Clear Tool free.</strong>
  <p>If this calculator saved you time, you can support the site with a coffee. No account or payment is required to use any calculator.</p>
  <a href="{SUPPORT_URL}" target="_blank" rel="noopener noreferrer">☕ Buy me a coffee</a>
</aside>'''


def insert_style(doc: str) -> str:
    if f'id="{MARKER}-style"' in doc:
        return doc
    if "</head>" not in doc:
        raise ValueError("HTML page is missing </head>")
    return doc.replace("</head>", SUPPORT_STYLE + "\n</head>", 1)


def insert_support(doc: str) -> str:
    if f'id="{MARKER}"' in doc:
        return doc
    if "</main>" in doc:
        return doc.replace("</main>", SUPPORT_BLOCK + "\n</main>", 1)
    if "</body>" in doc:
        return doc.replace("</body>", SUPPORT_BLOCK + "\n</body>", 1)
    raise ValueError("HTML page is missing </main> and </body>")


def public_pages() -> list[Path]:
    pages = [DOCS / "index.html"]
    pages.extend(sorted(path for path in DOCS.glob("*/index.html") if path.parent.name != "assets"))
    return pages


def update_page(path: Path) -> bool:
    original = path.read_text(encoding="utf-8-sig")
    updated = insert_support(insert_style(original))
    if SUPPORT_URL not in updated:
        raise ValueError(f"Support URL missing after update: {path}")
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def validate(pages: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in pages:
        doc = path.read_text(encoding="utf-8")
        if SUPPORT_URL not in doc:
            errors.append(f"{path.relative_to(ROOT)}: missing Buy Me a Coffee URL")
        if f'id="{MARKER}"' not in doc:
            errors.append(f"{path.relative_to(ROOT)}: missing support block")
        if f'id="{MARKER}-style"' not in doc:
            errors.append(f"{path.relative_to(ROOT)}: missing support styles")
    return errors


def main() -> int:
    pages = public_pages()
    if not pages or not (DOCS / "index.html").exists():
        logging.error("No public pages found under docs/")
        return 1

    changed = 0
    try:
        for path in pages:
            changed += int(update_page(path))
        errors = validate(pages)
    except Exception as exc:
        logging.exception("Support CTA propagation failed: %s", exc)
        return 1

    if errors:
        for error in errors:
            logging.error(error)
        return 1

    logging.info("Buy Me a Coffee coverage verified on %d public pages; %d changed.", len(pages), changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())

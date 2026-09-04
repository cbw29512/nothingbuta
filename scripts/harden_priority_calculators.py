from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

RULES: dict[str, dict[str, dict[str, str | None]]] = {
    "debt-payoff-calculator": {
        "balance": {"min": "0.01", "step": "0.01", "required": None},
        "apr": {"min": "0", "max": "100", "step": "0.01", "required": None},
        "pay": {"min": "0.01", "step": "0.01", "required": None},
        "extra": {"min": "0", "step": "0.01"},
    },
    "mortgage-payment-calculator": {
        "price": {"min": "0", "step": "0.01", "required": None},
        "down": {"min": "0", "step": "0.01"},
        "rate": {"min": "0", "max": "100", "step": "0.01", "required": None},
        "years": {"min": "1", "max": "50", "step": "1", "required": None},
        "escrow": {"min": "0", "step": "0.01"},
    },
    "car-payment-calculator": {
        "price": {"min": "0", "step": "0.01", "required": None},
        "down": {"min": "0", "step": "0.01"},
        "trade": {"min": "0", "step": "0.01"},
        "rate": {"min": "0", "max": "100", "step": "0.01", "required": None},
        "months": {"min": "1", "max": "120", "step": "1", "required": None},
    },
    "paycheck-estimator": {
        "gross": {"min": "0", "step": "0.01", "required": None},
        "federal": {"min": "0", "max": "100", "step": "0.01", "required": None},
        "state": {"min": "0", "max": "100", "step": "0.01", "required": None},
        "deduct": {"min": "0", "step": "0.01"},
    },
    "freelance-rate-calculator": {
        "income": {"min": "0", "step": "0.01", "required": None},
        "expenses": {"min": "0", "step": "0.01"},
        "tax": {"min": "0", "max": "100", "step": "0.01", "required": None},
        "hours": {"min": "0.1", "max": "168", "step": "0.1", "required": None},
        "weeks": {"min": "1", "max": "52", "step": "1", "required": None},
    },
}


def upsert_attribute(tag: str, name: str, value: str | None) -> str:
    pattern = re.compile(rf"\s{name}(?:\s*=\s*(['\"]).*?\1)?", re.IGNORECASE)
    tag = pattern.sub("", tag)
    rendered = name if value is None else f'{name}="{value}"'
    return tag[:-1].rstrip() + " " + rendered + ">"


def harden_input(doc: str, input_id: str, attrs: dict[str, str | None]) -> str:
    pattern = re.compile(rf'<input\b(?=[^>]*\bid=["\']{re.escape(input_id)}["\'])[^>]*>', re.IGNORECASE)
    match = pattern.search(doc)
    if not match:
        raise ValueError(f"missing input #{input_id}")
    tag = match.group(0)
    updated = tag
    for name, value in attrs.items():
        updated = upsert_attribute(updated, name, value)
    return doc[:match.start()] + updated + doc[match.end():]


def associate_debt_labels(doc: str) -> str:
    pairs = {
        "Current balance": "balance",
        "APR %": "apr",
        "Monthly payment": "pay",
        "Extra monthly payment": "extra",
    }
    for text, input_id in pairs.items():
        pattern = re.compile(rf'<label(?![^>]*\bfor=)([^>]*)>{re.escape(text)}\b', re.IGNORECASE)
        doc = pattern.sub(rf'<label for="{input_id}"\1>{text}', doc, count=1)
    return doc


def harden_debt_error_state(doc: str) -> str:
    old = '}catch(err){console.error(err)}}'
    new = '}catch(err){console.error("Debt payoff calculator error",err);const out=document.getElementById("out");if(out)out.innerHTML=\'<div class="warn">Calculation error occurred. Please check the inputs and try again.</div>\';}}'
    if old in doc:
        return doc.replace(old, new, 1)
    if "Debt payoff calculator error" in doc:
        return doc
    raise ValueError("debt payoff catch block did not match expected source")


def expected(path: Path, slug: str) -> str:
    doc = path.read_text(encoding="utf-8")
    for input_id, attrs in RULES[slug].items():
        doc = harden_input(doc, input_id, attrs)
    if slug == "debt-payoff-calculator":
        doc = associate_debt_labels(doc)
        doc = harden_debt_error_state(doc)
    return doc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write == args.check:
        parser.error("Choose exactly one of --write or --check")

    changed = []
    try:
        for slug in RULES:
            path = DOCS / slug / "index.html"
            if not path.exists():
                raise FileNotFoundError(path)
            current = path.read_text(encoding="utf-8")
            target = expected(path, slug)
            if target != current:
                changed.append(path)
                if args.write:
                    path.write_text(target, encoding="utf-8")

        if args.check and changed:
            for path in changed:
                logging.error("Priority hardening is stale: %s", path.relative_to(ROOT))
            return 1

        logging.info("Priority calculator hardening verified for %d pages; %d changed.", len(RULES), len(changed))
        return 0
    except Exception as exc:
        logging.exception("Priority calculator hardening failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())

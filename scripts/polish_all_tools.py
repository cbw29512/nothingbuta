from pathlib import Path
import datetime
import html
import json
import logging
import re
import shutil
import sys

# ---------------------------------------------------------------------
# DATA SCHEMA
# Each tool record controls one calculator page.
# The script does not guess page intent from filenames; it uses this data.
# ---------------------------------------------------------------------

TODAY = "2026-07-03"
BASE_URL = "https://onecleartool.com"

TOOLS = [
    {
        "slug": "break-even-calculator",
        "title": "Break Even Calculator | Find Your Break-Even Point",
        "description": "Calculate how many sales, units, or dollars you need to cover costs and reach break-even.",
        "intro": "Find the point where revenue covers cost.",
        "how": "Enter your fixed cost, variable cost, and price or revenue numbers.",
        "means": "The result estimates when the activity stops losing money and starts covering its own cost.",
        "next": "Try different prices or costs to see which inputs move the break-even point the most.",
        "related": ["roi-calculator", "conversion-rate-calculator", "freelance-rate-calculator"],
    },
    {
        "slug": "car-payment-calculator",
        "title": "Car Payment Calculator | Estimate Monthly Auto Payments",
        "description": "Estimate a monthly car payment using vehicle price, down payment, trade-in value, interest rate, and loan term.",
        "intro": "Estimate your car payment before you commit.",
        "how": "Enter the vehicle price, down payment, trade-in value, rate, and loan term.",
        "means": "The result estimates principal and interest, not taxes, title, registration, insurance, or dealer fees.",
        "next": "Compare several loan terms before choosing a lower payment that may cost more over time.",
        "related": ["loan-early-payoff-calculator", "debt-payoff-calculator", "savings-goal-calculator"],
    },
    {
        "slug": "churn-rate-calculator",
        "title": "Churn Rate Calculator | Measure Customer Loss",
        "description": "Calculate customer churn rate from starting customers, lost customers, and the period you are reviewing.",
        "intro": "Measure how many customers were lost during a period.",
        "how": "Enter the number of customers you started with and the number lost.",
        "means": "The result shows the share of customers lost, which helps compare retention over time.",
        "next": "Compare churn with conversion rate and revenue recovery to understand growth quality.",
        "related": ["conversion-rate-calculator", "roi-calculator", "break-even-calculator"],
    },
    {
        "slug": "concrete-calculator",
        "title": "Concrete Calculator | Estimate Concrete Volume",
        "description": "Estimate concrete needed for slabs, pads, and simple projects using length, width, and depth.",
        "intro": "Estimate concrete volume before buying material.",
        "how": "Enter the project length, width, and depth using the units shown on the page.",
        "means": "The result estimates volume only. Waste, slope, form shape, and ordering rules can change the final amount.",
        "next": "Round up when ordering and check local supplier minimums.",
        "related": ["flooring-calculator", "paint-coverage-calculator", "unit-price-calculator"],
    },
    {
        "slug": "conversion-rate-calculator",
        "title": "Conversion Rate Calculator | Measure Lead or Sales Conversion",
        "description": "Calculate conversion rate from visitors, leads, prospects, or sales outcomes.",
        "intro": "Turn counts into a clear conversion rate.",
        "how": "Enter total attempts or visitors and the number that converted.",
        "means": "The percentage shows how often the desired outcome happened.",
        "next": "Use the result with ROI or break-even calculations to judge whether traffic is valuable.",
        "related": ["roi-calculator", "break-even-calculator", "churn-rate-calculator"],
    },
    {
        "slug": "days-between-dates-calculator",
        "title": "Days Between Dates Calculator | Count Days Between Two Dates",
        "description": "Calculate the number of days between two dates for planning, deadlines, schedules, and timelines.",
        "intro": "Count days between two calendar dates.",
        "how": "Choose the start date and end date.",
        "means": "The result gives a simple day count for planning and comparison.",
        "next": "Use it for deadlines, billing windows, project planning, and schedule checks.",
        "related": ["time-card-calculator", "savings-goal-calculator", "recipe-scale-calculator"],
    },
    {
        "slug": "debt-payoff-calculator",
        "title": "Debt Payoff Calculator | Estimate Time and Interest Saved",
        "description": "Estimate debt payoff time, interest paid, and how extra monthly payments may reduce total cost.",
        "intro": "See your debt payoff path in seconds.",
        "how": "Enter balance, APR, regular monthly payment, and optional extra payment.",
        "means": "The result estimates payoff time and interest using steady monthly payments.",
        "next": "Run the numbers again with different extra payment amounts to compare payoff speed.",
        "related": ["loan-early-payoff-calculator", "emergency-fund-calculator", "savings-goal-calculator"],
    },
    {
        "slug": "discount-calculator",
        "title": "Discount Calculator | Calculate Sale Price and Savings",
        "description": "Calculate the sale price and amount saved from a percentage discount.",
        "intro": "See the real price after a discount.",
        "how": "Enter the original price and discount percentage.",
        "means": "The result shows both the final sale price and the amount saved.",
        "next": "Use sales tax and unit price tools when comparing final checkout cost.",
        "related": ["sales-tax-calculator", "unit-price-calculator", "percentage-change-calculator"],
    },
    {
        "slug": "emergency-fund-calculator",
        "title": "Emergency Fund Calculator | Estimate a Safety Cushion",
        "description": "Estimate how much to save for an emergency fund based on monthly expenses and months of coverage.",
        "intro": "Estimate a practical emergency fund target.",
        "how": "Enter monthly expenses and the number of months you want covered.",
        "means": "The result estimates a target cushion for unexpected costs or income gaps.",
        "next": "Compare the target with your monthly savings goal.",
        "related": ["savings-goal-calculator", "debt-payoff-calculator", "rent-affordability-calculator"],
    },
    {
        "slug": "flooring-calculator",
        "title": "Flooring Calculator | Estimate Flooring Material",
        "description": "Estimate flooring material needs using room size and a waste allowance.",
        "intro": "Estimate flooring before buying materials.",
        "how": "Enter room dimensions and include waste if the calculator supports it.",
        "means": "The result estimates material area, not trim, transitions, tools, or labor.",
        "next": "Compare material cost with the unit price calculator.",
        "related": ["paint-coverage-calculator", "concrete-calculator", "unit-price-calculator"],
    },
    {
        "slug": "freelance-rate-calculator",
        "title": "Freelance Rate Calculator | Estimate Your Hourly Rate",
        "description": "Estimate a freelance hourly rate based on income goals, expenses, taxes, and billable time.",
        "intro": "Turn an income goal into a working freelance rate.",
        "how": "Enter income goals, costs, and realistic billable time.",
        "means": "The result helps estimate what you may need to charge to support the target income.",
        "next": "Compare the rate with hourly salary and ROI calculations.",
        "related": ["hourly-to-salary-calculator", "roi-calculator", "break-even-calculator"],
    },
    {
        "slug": "hourly-to-salary-calculator",
        "title": "Hourly to Salary Calculator | Convert Hourly Pay to Annual Income",
        "description": "Convert hourly pay into weekly, monthly, and yearly gross income using hourly rate, weekly hours, and weeks worked.",
        "intro": "Convert hourly pay into salary numbers.",
        "how": "Enter hourly rate, weekly hours, and weeks worked per year.",
        "means": "The result estimates gross pay before taxes, deductions, benefits, or unpaid time.",
        "next": "Use the paycheck estimator to think about take-home pay.",
        "related": ["paycheck-estimator", "time-card-calculator", "freelance-rate-calculator"],
    },
    {
        "slug": "loan-early-payoff-calculator",
        "title": "Loan Early Payoff Calculator | Estimate Extra Payment Savings",
        "description": "Estimate how extra loan payments may reduce payoff time and interest paid.",
        "intro": "See how extra payments can change a loan.",
        "how": "Enter balance, rate, current payment, and extra monthly payment.",
        "means": "The result estimates payoff time, interest, and savings from paying more.",
        "next": "Compare this with debt payoff and savings goals before changing your plan.",
        "related": ["debt-payoff-calculator", "car-payment-calculator", "mortgage-payment-calculator"],
    },
    {
        "slug": "mortgage-payment-calculator",
        "title": "Mortgage Payment Calculator | Estimate Monthly Home Payments",
        "description": "Estimate a monthly mortgage payment using home price, down payment, interest rate, loan term, taxes, insurance, and escrow costs.",
        "intro": "Estimate your mortgage payment before you shop.",
        "how": "Enter home price, down payment, interest rate, term, and monthly taxes or insurance.",
        "means": "The result estimates principal, interest, and optional escrow, not a lender quote.",
        "next": "Compare the result with rent, utilities, maintenance, other debt, and savings goals.",
        "related": ["rent-affordability-calculator", "savings-goal-calculator", "loan-early-payoff-calculator"],
    },
    {
        "slug": "paint-coverage-calculator",
        "title": "Paint Coverage Calculator | Estimate Paint Needed",
        "description": "Estimate paint coverage for rooms, walls, and repaint projects.",
        "intro": "Estimate how much paint a project may need.",
        "how": "Enter wall area or room dimensions and coverage assumptions.",
        "means": "The result estimates paint quantity, not primer, waste, texture, or extra coats.",
        "next": "Round up for touch-ups and compare can pricing with the unit price calculator.",
        "related": ["flooring-calculator", "concrete-calculator", "unit-price-calculator"],
    },
    {
        "slug": "paycheck-estimator",
        "title": "Paycheck Take-Home Estimator | Estimate Net Pay",
        "description": "Estimate take-home pay after basic taxes and deductions.",
        "intro": "Estimate take-home pay from a gross paycheck.",
        "how": "Enter gross pay and basic deduction or tax estimates.",
        "means": "The result is a planning estimate, not payroll or tax advice.",
        "next": "Compare take-home pay with rent, savings, and debt payoff targets.",
        "related": ["hourly-to-salary-calculator", "rent-affordability-calculator", "savings-goal-calculator"],
    },
    {
        "slug": "percentage-change-calculator",
        "title": "Percentage Change Calculator | Find Increase or Decrease",
        "description": "Calculate percentage increase, percentage decrease, and numeric change between two values.",
        "intro": "Compare two numbers as a percentage change.",
        "how": "Enter the old value and the new value.",
        "means": "The result shows both the numeric change and percentage change.",
        "next": "Use this when comparing prices, revenue, performance, or measurements.",
        "related": ["discount-calculator", "conversion-rate-calculator", "roi-calculator"],
    },
    {
        "slug": "recipe-scale-calculator",
        "title": "Recipe Scale Calculator | Adjust Ingredient Amounts",
        "description": "Scale recipe ingredients up or down when changing servings or batch size.",
        "intro": "Resize a recipe without doing math by hand.",
        "how": "Enter original servings and desired servings.",
        "means": "The result scales ingredient amounts proportionally.",
        "next": "Check taste-sensitive ingredients separately, especially salt, spice, and leavening.",
        "related": ["unit-price-calculator", "days-between-dates-calculator", "tip-calculator"],
    },
    {
        "slug": "rent-affordability-calculator",
        "title": "Rent Affordability Calculator | Estimate a Practical Rent Range",
        "description": "Estimate a practical rent range from income and monthly budget targets.",
        "intro": "Estimate rent affordability before applying.",
        "how": "Enter income and budget assumptions.",
        "means": "The result estimates a rent range for planning, not approval from a landlord.",
        "next": "Compare rent with take-home pay, emergency fund, and savings goals.",
        "related": ["paycheck-estimator", "emergency-fund-calculator", "mortgage-payment-calculator"],
    },
    {
        "slug": "sales-tax-calculator",
        "title": "Sales Tax Calculator | Estimate Final Price",
        "description": "Calculate sales tax and estimated final price before checkout.",
        "intro": "Estimate checkout total with sales tax.",
        "how": "Enter price and sales tax rate.",
        "means": "The result estimates tax and total cost.",
        "next": "Use with discount and unit price tools when comparing purchases.",
        "related": ["discount-calculator", "unit-price-calculator", "percentage-change-calculator"],
    },
    {
        "slug": "savings-goal-calculator",
        "title": "Savings Goal Calculator | Estimate Time to Goal",
        "description": "Estimate how long it may take to reach a savings goal based on current savings and monthly contributions.",
        "intro": "Estimate how long a savings goal may take.",
        "how": "Enter your target, current amount saved, and planned monthly savings.",
        "means": "The result estimates remaining amount and months to goal.",
        "next": "Compare the plan with debt payoff and emergency fund targets.",
        "related": ["emergency-fund-calculator", "debt-payoff-calculator", "rent-affordability-calculator"],
    },
    {
        "slug": "roi-calculator",
        "title": "Simple ROI Calculator | Compare Cost and Return",
        "description": "Calculate profit and return on investment from cost and return values.",
        "intro": "Compare investment cost and return.",
        "how": "Enter the cost and return amount.",
        "means": "The result estimates profit and ROI percentage.",
        "next": "Use break-even and conversion rate tools to understand the inputs behind the return.",
        "related": ["break-even-calculator", "conversion-rate-calculator", "percentage-change-calculator"],
    },
    {
        "slug": "time-card-calculator",
        "title": "Time Card Calculator | Total Hours and Pay",
        "description": "Estimate work hours and pay from regular time, overtime, and hourly rate.",
        "intro": "Estimate hours and gross pay from a time card.",
        "how": "Enter regular hours, overtime hours, hourly rate, and overtime multiplier if available.",
        "means": "The result estimates gross pay before taxes and deductions.",
        "next": "Compare gross pay with paycheck and hourly-to-salary estimates.",
        "related": ["hourly-to-salary-calculator", "paycheck-estimator", "days-between-dates-calculator"],
    },
    {
        "slug": "tip-calculator",
        "title": "Tip Calculator | Split a Bill and Calculate Tip",
        "description": "Calculate tip amount, total bill, and split cost per person.",
        "intro": "Calculate tip and split the bill.",
        "how": "Enter bill amount, tip percentage, and number of people.",
        "means": "The result estimates total tip, final bill, and each person’s share.",
        "next": "Use sales tax or unit price calculators when comparing other everyday costs.",
        "related": ["sales-tax-calculator", "unit-price-calculator", "discount-calculator"],
    },
    {
        "slug": "unit-price-calculator",
        "title": "Unit Price Calculator | Compare Price Per Unit",
        "description": "Compare package prices and quantities to find the better value per unit.",
        "intro": "Compare two package prices quickly.",
        "how": "Enter the price and unit count for each option.",
        "means": "The result estimates price per unit and identifies the lower unit cost.",
        "next": "Use it with discounts and sales tax for a fuller purchase comparison.",
        "related": ["discount-calculator", "sales-tax-calculator", "recipe-scale-calculator"],
    },
]

# ---------------------------------------------------------------------
# STATE LOGIC
# 1. Back up every page before changing it.
# 2. Update metadata and add a standard helpful content panel.
# 3. Regenerate sitemap.
# 4. Validate no page contains noindex and every tool has canonical/index.
# ---------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
ROOT = Path.cwd()
DOCS = ROOT / "docs"
BACKUP_DIR = ROOT / "backups" / f"pre-all-tools-polish-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
REPORT_PATH = ROOT / "reports" / "all-tools-seo-polish-report.txt"

TOOL_MAP = {tool["slug"]: tool for tool in TOOLS}

def esc_attr(value: str) -> str:
    """Escape text before placing it inside an HTML attribute."""
    return html.escape(value, quote=True)

def esc_text(value: str) -> str:
    """Escape text before placing it inside normal HTML content."""
    return html.escape(value, quote=False)

def replace_or_insert(pattern: str, replacement: str, doc: str) -> str:
    """Replace the first matching HTML tag, or insert the replacement before </head>."""
    if re.search(pattern, doc, flags=re.IGNORECASE | re.DOTALL):
        return re.sub(pattern, replacement, doc, count=1, flags=re.IGNORECASE | re.DOTALL)
    return doc.replace("</head>", f"  {replacement}\n</head>", 1)

def upsert_head_tags(doc: str, tool: dict) -> str:
    """Update the SEO head tags while keeping the page calculator body intact."""
    url = f"{BASE_URL}/{tool['slug']}/"
    doc = replace_or_insert(r"<title>.*?</title>", f"<title>{esc_text(tool['title'])}</title>", doc)
    doc = replace_or_insert(r'<meta\s+name=["\']description["\'][^>]*>', f'<meta name="description" content="{esc_attr(tool["description"])}">', doc)
    doc = replace_or_insert(r'<meta\s+name=["\']robots["\'][^>]*>', '<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">', doc)
    doc = replace_or_insert(r'<link\s+rel=["\']canonical["\'][^>]*>', f'<link rel="canonical" href="{url}">', doc)
    doc = replace_or_insert(r'<meta\s+property=["\']og:title["\'][^>]*>', f'<meta property="og:title" content="{esc_attr(tool["title"])}">', doc)
    doc = replace_or_insert(r'<meta\s+property=["\']og:description["\'][^>]*>', f'<meta property="og:description" content="{esc_attr(tool["description"])}">', doc)
    doc = replace_or_insert(r'<meta\s+property=["\']og:url["\'][^>]*>', f'<meta property="og:url" content="{url}">', doc)
    doc = replace_or_insert(r'<meta\s+property=["\']og:type["\'][^>]*>', '<meta property="og:type" content="website">', doc)

    if "../assets/site.css" not in doc:
        doc = doc.replace("</head>", '  <link rel="stylesheet" href="../assets/site.css">\n</head>', 1)

    schema = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": tool["title"].split("|")[0].strip(),
        "url": url,
        "applicationCategory": "UtilityApplication",
        "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    }
    schema_tag = f'<script type="application/ld+json" id="oct-tool-schema">{json.dumps(schema, separators=(",", ":"))}</script>'
    doc = re.sub(r'\s*<script\s+type=["\']application/ld\+json["\']\s+id=["\']oct-tool-schema["\']>.*?</script>', "", doc, flags=re.IGNORECASE | re.DOTALL)
    return doc.replace("</head>", f"  {schema_tag}\n</head>", 1)

def build_related_links(tool: dict) -> str:
    """Build internal links to related calculators."""
    links = []
    for slug in tool["related"]:
        related = TOOL_MAP[slug]
        label = related["title"].split("|")[0].strip()
        links.append(f'<a href="../{slug}/">{esc_text(label)}</a>')
    return "".join(links)

def build_content_panel(tool: dict) -> str:
    """Build a reusable SEO/trust panel for one tool."""
    return f"""
<section class="panel" id="one-clear-tool-seo-panel">
  <h2>{esc_text(tool["intro"])}</h2>
  <div class="content-grid">
    <div>
      <h3>How to use this tool</h3>
      <p>{esc_text(tool["how"])}</p>
    </div>
    <div>
      <h3>What the result means</h3>
      <p>{esc_text(tool["means"])}</p>
    </div>
    <div>
      <h3>Useful next check</h3>
      <p>{esc_text(tool["next"])}</p>
    </div>
  </div>
  <h3>Related tools</h3>
  <div class="related">{build_related_links(tool)}</div>
  <p class="fine">Results are planning estimates for education and comparison only. They are not financial, tax, legal, lending, payroll, construction, or professional advice.</p>
</section>
""".strip()

def upsert_content_panel(doc: str, tool: dict) -> str:
    """Add or replace the standard content panel before the page closes."""
    panel = build_content_panel(tool)
    pattern = r'\s*<section\s+class=["\']panel["\']\s+id=["\']one-clear-tool-seo-panel["\']>.*?</section>'
    if re.search(pattern, doc, flags=re.IGNORECASE | re.DOTALL):
        return re.sub(pattern, "\n" + panel, doc, count=1, flags=re.IGNORECASE | re.DOTALL)
    if "</main>" in doc:
        return doc.replace("</main>", panel + "\n</main>", 1)
    return doc.replace("</body>", panel + "\n</body>", 1)

def polish_tool_page(tool: dict) -> str:
    """Back up and polish one calculator page."""
    path = DOCS / tool["slug"] / "index.html"
    if not path.exists():
        raise FileNotFoundError(f"Missing page: {path}")

    backup_path = BACKUP_DIR / tool["slug"] / "index.html"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_path)

    original = path.read_text(encoding="utf-8")
    updated = upsert_head_tags(original, tool)
    updated = upsert_content_panel(updated, tool)

    path.write_text(updated, encoding="utf-8")
    return str(path)

def update_sitemap() -> None:
    """Regenerate the sitemap using the canonical production domain."""
    urls = [("/", "0.9")] + [(f"/{tool['slug']}/", "0.8") for tool in TOOLS]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, priority in urls:
        lines.extend([
            "  <url>",
            f"    <loc>{BASE_URL}{path}</loc>",
            f"    <lastmod>{TODAY}</lastmod>",
            "    <changefreq>weekly</changefreq>",
            f"    <priority>{priority}</priority>",
            "  </url>",
        ])
    lines.append("</urlset>")
    (DOCS / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")

def validate_site() -> list[str]:
    """Validate the minimum SEO requirements after the polish pass."""
    errors = []

    for tool in TOOLS:
        path = DOCS / tool["slug"] / "index.html"
        doc = path.read_text(encoding="utf-8")
        lower = doc.lower()
        expected_url = f"{BASE_URL}/{tool['slug']}/"

        if "noindex" in lower:
            errors.append(f"{tool['slug']}: contains noindex")
        if 'name="robots" content="index, follow' not in lower:
            errors.append(f"{tool['slug']}: missing index/follow robots tag")
        if expected_url not in doc:
            errors.append(f"{tool['slug']}: missing canonical production URL")
        if "../assets/site.css" not in doc:
            errors.append(f"{tool['slug']}: missing shared stylesheet")
        if "one-clear-tool-seo-panel" not in doc:
            errors.append(f"{tool['slug']}: missing standard SEO panel")

    sitemap = (DOCS / "sitemap.xml").read_text(encoding="utf-8")
    for tool in TOOLS:
        expected = f"{BASE_URL}/{tool['slug']}/"
        if expected not in sitemap:
            errors.append(f"sitemap missing {expected}")

    return errors

def main() -> int:
    """Run the full polish workflow with meaningful logging."""
    try:
        if not DOCS.exists():
            raise RuntimeError("Run this script from the repo root where the docs folder exists.")

        logging.info("Starting all-tools SEO polish.")
        logging.info("Backup folder: %s", BACKUP_DIR)

        changed = []
        for tool in TOOLS:
            changed.append(polish_tool_page(tool))
            logging.info("Polished %s", tool["slug"])

        update_sitemap()
        logging.info("Updated sitemap.xml")

        errors = validate_site()
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

        if errors:
            REPORT_PATH.write_text("SEO polish validation failed:\n" + "\n".join(errors) + "\n", encoding="utf-8")
            for error in errors:
                logging.error(error)
            return 1

        REPORT_PATH.write_text(
            "SEO polish validation passed.\n"
            f"Updated tool pages: {len(changed)}\n"
            f"Date: {TODAY}\n",
            encoding="utf-8",
        )

        logging.info("Validation passed.")
        logging.info("Report written to %s", REPORT_PATH)
        return 0

    except Exception as exc:
        logging.exception("Polish failed: %s", exc)
        return 1

if __name__ == "__main__":
    sys.exit(main())

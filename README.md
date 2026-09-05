# One Clear Tool

Free, simple calculators for everyday decisions.

## Live Site

https://onecleartool.com/

## Purpose

One Clear Tool is a static calculator hub built around focused, single-purpose micro-apps. Every calculator has its own direct URL, but the homepage also serves as the shared discovery layer. Pages are designed to give one useful estimate quickly without an account wall, clutter, or long setup.

## Current Tools

### Money, work, and business

- Break Even Calculator
- Car Payment Calculator
- Churn Rate Calculator
- Compound Interest Calculator
- Conversion Rate Calculator
- Debt Payoff Calculator
- Discount Calculator
- Emergency Fund Calculator
- Freelance Rate Calculator
- Hourly to Salary Calculator
- Loan Early Payoff Calculator
- Mortgage Payment Calculator
- Overtime Pay Calculator
- Paycheck Take-Home Estimator
- Percentage Change Calculator
- Rent Affordability Calculator
- Sales Tax Calculator
- Savings Goal Calculator
- Simple ROI Calculator
- Time Card Calculator
- Tip Calculator
- Unit Price Calculator

### Home and project planning

- Concrete Calculator
- Drywall Calculator
- Flooring Calculator
- Grass Seed Calculator
- Gravel Calculator
- Mulch Calculator
- Paint Coverage Calculator
- Tile Calculator
- Topsoil Calculator

### Kitchen and everyday planning

- Days Between Dates Calculator
- Meat Per Person Calculator
- Recipe Scale Calculator
- Rice Water Calculator

**Total: 70 live calculator pages.**

## Publishing

This repository publishes from the `/docs` folder using GitHub Pages.

Custom domain:

```text
onecleartool.com
```

Important SEO files:

```text
docs/CNAME
docs/robots.txt
docs/sitemap.xml
docs/index.html
```

## Product Standard

Every public tool page should have:

- A clear title and meta description
- A canonical URL using `https://onecleartool.com/`
- A single focused calculation with understandable inputs and outputs
- Helpful on-page explanation text and related-tool links
- Accessible form labels and an `aria-live` result region
- Shared One Clear Tool styling and mobile behavior
- Client-side-only calculator inputs with no analytics or submission API
- Privacy, terms, and support links
- A short estimate-only disclaimer when the tool touches money, pay, taxes, loans, construction, or planning

## Quality Gate

The permanent GitHub Actions quality workflow verifies generated commercial state, JavaScript syntax, runtime calculator behavior, client-side privacy boundaries, credential hygiene, and clean diffs. The runtime smoke gate requires all 70 calculator pages to execute and produce a result.

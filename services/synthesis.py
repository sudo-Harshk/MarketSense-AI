from __future__ import annotations

import json

from services.groq_client import call_llm


def _build_prompt(companies: list[dict], idea: str, insight_count: int) -> str:
    rows = "\n".join(
        f"- {c['name']}: summary={c['summary']!r}, target={c['target_audience']!r}, "
        f"features={c['features']!r}, pricing={c['pricing']!r}"
        for c in companies
    )
    return f"""You are a market analyst. A founder has this idea: "{idea}"

You have data on {len(companies)} competitors. Use ONLY this data — no external knowledge.

COMPANIES:
{rows}

Return a single JSON object with exactly two keys:

{{
  "table": "<markdown table string>",
  "insights": ["insight 1", ..., "insight {insight_count}"]
}}

TABLE RULES:
- Columns must be exactly: Company | Summary | Target | Features | Pricing
- One row per company
- Every cell must be under 15 words
- No bullet points inside cells

INSIGHT RULES:
- Generate exactly {insight_count} insights
- Each insight must be under 25 words
- Each insight must end with: (based on: [company name(s)] or "all listed companies" if the pattern applies to all)
- Never write "(based on: None)" — if a pattern applies to all, write "(based on: all listed companies)"
- Do not use any knowledge outside the COMPANIES data above
- At least one insight must directly compare two companies (e.g., "X does Y while Z does W → different strategies")
- Every insight must state a "so what" — not just what is true, but what it means for the market
- Never assume a gap is automatically an opportunity — one insight must assess whether the gap is valuable or risky

Answer these {insight_count} questions strictly using only the data above:
1. What pattern appears in most or all companies, and what does that mean for the market? (cite which ones, explain implication)
2. What is the clearest strategic difference between any two specific companies, and what does it reveal? (name both)
3. What capability is completely absent from all companies listed? (state that none mention it — do not invent absences)
4. Is that absence an opportunity or a risk? Take a clear stance — either "this is an underserved segment because X" or "this gap likely exists because demand is too small, given Y." Do NOT say "may be" or "could be." Commit to one interpretation based on the data.
{"5. REQUIRED FORMAT — Last insight must be: 'Existing tools focus on [what they do], not [what the idea does] → building for [specific audience] could differentiate on [concrete angle].' (based on: [company name(s)])" if insight_count >= 5 else "Last insight REQUIRED FORMAT: 'Existing tools focus on [what they do], not [what the idea does] → building for [specific audience] could differentiate on [concrete angle].' (based on: [company name(s)])"}

Output ONLY the JSON object."""


def _validate_insights(insights: list[str], company_names: list[str]) -> list[str]:
    names_lower = [n.lower() for n in company_names]
    valid = []
    for insight in insights:
        words = insight.split()
        if len(words) < 10:
            continue
        text = insight.lower()
        grounded = any(n in text for n in names_lower) or "(based on:" in text
        if not grounded:
            continue
        valid.append(insight)
    return valid


def synthesize(analyses: list[dict], idea: str) -> dict:
    # Scale insight count to input quality: 2 companies → 3, 3 → 4, 4+ → 5
    insight_count = min(len(analyses) + 1, 5)

    normalized = [
        {
            "name": a["name"],
            "summary": a["summary"],
            "target_audience": a["target_audience"],
            "features": ", ".join(a["features"][:3]),
            "pricing": a["pricing"],
        }
        for a in analyses
    ]
    company_names = [c["name"] for c in normalized]

    prompt = _build_prompt(normalized, idea, insight_count)
    response = call_llm([{"role": "user", "content": prompt}], json_mode=True)
    raw = json.loads(response)

    insights = raw.get("insights", [])[:5]
    validated = _validate_insights(insights, company_names)
    # Fall back to unvalidated if post-processing removed everything
    raw["insights"] = validated if validated else insights

    return raw

from __future__ import annotations


def build_analysis_prompt(content: str, url: str) -> str:
    return f"""You are a strict market analyst. Analyze ONLY the data below.

DATA:
{content[:4000]}

Return a single JSON object matching this schema exactly:

{{
  "name": "Company Name",
  "summary": "One sentence, max 20 words",
  "target_audience": "Who this is for",
  "features": ["Feature one", "Feature two", "Feature three"],
  "pricing": "Pricing info or Not available",
  "confidence": 80,
  "sources": ["{url}"]
}}

STRICT RULES:
- features MUST have between 3 and 5 items — no more, no fewer
- features MUST be a JSON array of plain strings — no numbering, no dict keys
- confidence MUST be an integer between 0 and 100 (e.g. 80, not 0.8)
- pricing = "Not available" if missing
- reduce confidence if source is a LinkedIn page or generic blog
- output ONLY the JSON object, nothing else"""




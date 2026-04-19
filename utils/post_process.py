from __future__ import annotations

import re

_MARKETING_PATTERNS = (
    "up to", "increase", "improve", "better", "faster",
    "boost", "proven", "guaranteed", "x more", "more than",
    "reduce cost", "save time", "save money",
)
_WEAK_URL_SIGNALS = (
    "linkedin.com", "medium.com", "twitter.com",
    "substack.com", "blog.", "/blog/",
)
_PRICING_SIGNALS = ("pricing", "$", "€", "per month", "free plan", "paid", "/mo", "usd", "subscribe")
_FEATURE_SIGNALS = ("feature", "how it works", "capabilities", "solution", "tool", "dashboard")


def _is_real_feature(text: str) -> bool:
    t = text.lower()
    if re.search(r"\d+\s*%", t):
        return False
    return not any(p in t for p in _MARKETING_PATTERNS)


def _compute_confidence(content: str, url: str) -> int:
    score = 50  # baseline: we know nothing yet

    # Content depth
    if len(content) > 3000:
        score += 15
    elif len(content) > 1000:
        score += 10
    elif len(content) > 300:
        score += 5

    # Pricing found = company has a real product
    if any(s in content.lower() for s in _PRICING_SIGNALS):
        score += 10

    # Feature language = structured product description
    if any(s in content.lower() for s in _FEATURE_SIGNALS):
        score += 5

    # Weak source = less reliable
    if any(w in url.lower() for w in _WEAK_URL_SIGNALS):
        score -= 20

    return max(20, min(90, score))


def _deduplicate_features(features: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for f in features:
        key = re.sub(r"\W+", "", f.lower())
        if key not in seen:
            seen.add(key)
            result.append(f)
    return result


def post_process(data: dict, url: str, content: str) -> dict:
    # Sources: always deterministic — we scraped this URL, we own it
    data["sources"] = [url]

    # Confidence: computed from signals, never from LLM
    data["confidence"] = _compute_confidence(content, url)

    # Features: filter marketing claims → deduplicate → cap at 5
    raw = data.get("features", [])
    clean = [f for f in raw if _is_real_feature(f)]
    deduped = _deduplicate_features(clean if clean else raw)
    data["features"] = deduped[:5]

    return data

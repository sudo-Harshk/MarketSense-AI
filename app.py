import random
import streamlit as st
from services.exa_client import search_companies, get_contents
from services.groq_client import filter_companies, analyze_company
from services.synthesis import synthesize

_NOISE_DOMAINS = (
    "capterra.com", "g2.com", "trustpilot.com", "getapp.com",
    "softwareadvice.com", "producthunt.com", "crunchbase.com",
    "linkedin.com", "twitter.com", "facebook.com",
)
_NOISE_PATHS = ("/contact", "/about", "/privacy", "/terms", "/login", "/signup")

def is_quality_url(url: str) -> bool:
    u = url.lower()
    return not any(d in u for d in _NOISE_DOMAINS) and not any(u.endswith(p) or f"{p}/" in u for p in _NOISE_PATHS)

def _confidence_label(score: int) -> str:
    if score >= 75:
        return "High"
    if score >= 55:
        return "Medium"
    return "Low"


# ── Input ────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
.example-buttons div[data-testid="stHorizontalBlock"] {
    gap: 14px;
    margin: 8px 0 14px 0;
}

.example-buttons div[data-testid="column"] button {
    min-height: 92px;
    width: 100%;
    text-align: left;
    white-space: normal;
    line-height: 1.35;
    padding: 16px 16px;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.10);
    background: rgba(255, 255, 255, 0.04);
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.04) inset, 0 10px 24px rgba(0, 0, 0, 0.22);
    transition: transform 120ms ease, background-color 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
}

.example-buttons div[data-testid="column"] button:hover {
    border-color: rgba(255, 255, 255, 0.18);
    background: rgba(255, 255, 255, 0.07);
    transform: translateY(-1px);
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.05) inset, 0 14px 30px rgba(0, 0, 0, 0.28);
}

.example-buttons div[data-testid="column"] button:active {
    transform: translateY(0px);
    background: rgba(255, 255, 255, 0.05);
}

.example-buttons div[data-testid="column"] button p {
    margin: 0;
    font-weight: 550;
    font-size: 0.95rem;
    letter-spacing: -0.01em;
}
</style>
""", unsafe_allow_html=True)

st.title("MarketSense AI")
st.caption("Understand your competition in seconds.")

_ALL_EXAMPLES = [
    "AI tool for detecting crop diseases from photos",
    "Scheduling app that adjusts plans based on weather",
    "AI copilot for solo lawyers",
    "Mental health journaling app powered by AI",
    "Hiring tool that scores candidates using public GitHub activity",
    "AI tutor for dyslexic children",
    "Fleet management tool for small delivery businesses",
    "Personalized meal planner for people with food allergies",
    "AI tool that generates legal contracts for freelancers",
    "Sleep tracking app with actionable habit coaching",
    "Inventory forecasting tool for independent retailers",
    "Interview prep coach for non-native English speakers",
    "AI-powered code reviewer for junior developers",
    "Real estate deal analyzer for first-time investors",
    "Customer churn predictor for SaaS startups",
]

if "examples" not in st.session_state:
    st.session_state["examples"] = random.sample(_ALL_EXAMPLES, 3)

st.markdown('<div class="example-buttons">', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
for col, example in zip([col1, col2, col3], st.session_state["examples"]):
    if col.button(f'"{example}"', use_container_width=True):
        st.session_state["idea_input"] = example
st.markdown("</div>", unsafe_allow_html=True)

idea = st.text_input(
    "Describe your startup idea",
    placeholder="e.g. AI tool for detecting crop diseases from photos",
    key="idea_input",
)
st.caption("Be specific — better input produces better market intelligence.")

run = st.button("Analyze Market", type="primary", disabled=not idea)

if run and idea:

    # ── Pipeline ─────────────────────────────────────────────────────────────

    try:
        with st.status("Researching competitors…", expanded=True) as status:
            st.write("Searching for companies…")
            results = search_companies(f"companies or startups that: {idea}")

            st.write("Filtering real companies…")
            filtered = filter_companies(results)

            urls = [r["url"] for r in filtered if is_quality_url(r["url"])]

            st.write("Extracting website content…")
            contents = get_contents(urls)

            st.write("Analyzing each company…")
            analyses = []
            for c in contents:
                result = analyze_company(c["text"], c["url"])
                if result:
                    analyses.append(result)

            synthesis = None
            if len(analyses) >= 2:
                st.write("Synthesizing market overview…")
                try:
                    synthesis = synthesize(analyses, idea)
                except Exception as e:
                    st.warning(f"Could not generate market overview: {e}")

            competition_label = "Limited competition found" if len(analyses) <= 2 else f"Found {len(analyses)} competitors"
            status.update(label=competition_label, state="complete", expanded=False)

    except Exception as e:
        st.error(f"Something went wrong while researching: {e}")
        st.stop()

    if not analyses:
        st.warning("No competitors found. Try a more specific idea.")
        st.stop()

    # ── Key Insights (destination — shown first) ──────────────────────────────

    if synthesis:
        st.divider()
        st.subheader("Key Insights")
        for insight in synthesis["insights"]:
            st.info(insight)

    # ── Competitor Overview (supporting) ──────────────────────────────────────

    if synthesis:
        st.divider()
        st.subheader("Competitor Overview")
        st.markdown(synthesis["table"])

    # ── Competitor Cards (exploration detail, collapsed by default) ───────────

    st.divider()
    with st.expander(f"Explore {len(analyses)} competitors", expanded=False):
        for a in analyses:
            with st.container(border=True):
                st.markdown(f"**{a['name']}**")
                st.caption(a["summary"])

                for f in a["features"][:3]:
                    st.write(f"• {f}")

                meta_col1, meta_col2 = st.columns(2)
                meta_col1.caption(f"💰 {a['pricing']}")
                meta_col2.caption(f"Confidence: {_confidence_label(a['confidence'])}")

                st.caption(a["sources"][0])
            st.write("")

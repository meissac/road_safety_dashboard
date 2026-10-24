"""Visual identity ("night road"): colours, fonts and reusable HTML blocks."""
import streamlit as st

# Palette - amber = road markings / volume, red = deaths, grey = reference values
BG = "#0F1115"
SURFACE = "#181B22"
BORDER = "#2A2F3A"
TEXT = "#ECEAE6"
MUTED = "#A3A9B3"
AMBER = "#F5B700"
RED = "#FF5A5F"
GREY = "#7C8491"
GREEN = "#3DD68C"

VERDICT_CLASS = {"CONFIRMED": "confirmed", "DEBUNKED": "debunked", "NUANCED": "nuanced"}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Roboto:wght@400;500;700&display=swap');

html, body, [class*="css"], .stMarkdown, p, li {{ font-family: 'Roboto', sans-serif; }}
h1, h2, h3, .display {{ font-family: 'Plus Jakarta Sans', sans-serif !important; letter-spacing: .01em; }}
.block-container {{ padding-top: 3.5rem; max-width: 1250px; }}

.kicker {{ color: {AMBER}; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 600;
          letter-spacing: .14em; text-transform: uppercase; font-size: .85rem; }}
.hero-title {{ font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: clamp(2.2rem, 5vw, 3.8rem);
              line-height: 1; margin: .3rem 0 .8rem 0; color: {TEXT}; }}
.hero-title .red {{ color: {RED}; }}
.lede {{ font-size: 1.15rem; color: {MUTED}; max-width: 760px; line-height: 1.55; }}
.lede b {{ color: {TEXT}; }}


.kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: .8rem; margin: 1rem 0; }}
.kpi {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; padding: 1rem 1.1rem; }}
.kpi .label {{ color: {MUTED}; font-size: .8rem; text-transform: uppercase; letter-spacing: .08em; }}
.kpi .value {{ font-family: 'Plus Jakarta Sans', sans-serif; font-size: 2.15rem; font-weight: 700; line-height: 1.15; }}
.kpi .sub {{ color: {MUTED}; font-size: .85rem; }}

.chapter-num {{ font-family: 'Plus Jakarta Sans', sans-serif; color: {AMBER}; font-size: 1rem;
               letter-spacing: .12em; text-transform: uppercase; font-weight: 700; }}
.claim {{ font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.65rem; font-weight: 700; line-height: 1.15;
         margin: .2rem 0 .6rem 0; }}
.badge {{ display: inline-block; padding: .25rem .7rem; border-radius: 4px; font-weight: 700; font-size: .85rem;
         letter-spacing: .12em; font-family: 'Plus Jakarta Sans', sans-serif; margin-right: .6rem; }}
.badge.confirmed {{ background: {GREEN}; color: #08130D; }}
.badge.debunked {{ background: {RED}; color: #1A0607; }}
.badge.nuanced {{ background: {AMBER}; color: #1A1400; }}
.evidence {{ color: {TEXT}; font-size: 1.02rem; line-height: 1.55; margin: .8rem 0 1rem 0; max-width: 900px; }}
.evidence b {{ color: {AMBER}; }}

.card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-left: 4px solid {AMBER}; border-radius: 8px;
        padding: 1rem 1.2rem; height: 100%; }}
.card.red {{ border-left-color: {RED}; }}
.card .card-title {{ font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.12rem; margin: 0 0 .5rem 0; font-weight: 700; }}
.card p {{ color: {MUTED}; margin: 0; line-height: 1.5; }}
.card p b {{ color: {TEXT}; }}
.note {{ color: {MUTED}; font-size: .85rem; }}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def section_divider() -> None:
    st.divider()


def kpi_cards(items: list[dict]) -> None:
    """items: [{'label', 'value', 'sub'}]"""
    html = "".join(
        f'<div class="kpi"><div class="label">{i["label"]}</div>'
        f'<div class="value">{i["value"]}</div><div class="sub">{i.get("sub", "")}</div></div>'
        for i in items)
    st.markdown(f'<div class="kpi-grid">{html}</div>', unsafe_allow_html=True)


def chapter(subject: str, claim: str, verdict: str, evidence: str) -> None:
    """Hypothesis header: subject, claim, verdict badge and one evidence sentence."""
    st.markdown(
        f'<div class="chapter-num">{subject}</div>'
        f'<div class="claim">« {claim} »</div>'
        f'<span class="badge {VERDICT_CLASS[verdict]}">{verdict}</span>'
        f'<div class="evidence">{evidence}</div>',
        unsafe_allow_html=True)


def card(title: str, body: str, tone: str = "") -> None:
    st.markdown(f'<div class="card {tone}"><div class="card-title">{title}</div><p>{body}</p></div>',
                unsafe_allow_html=True)


def fmt_int(x) -> str:
    return f"{int(x):,}".replace(",", "\u00a0")  # non-breaking space so numbers never split


def fmt_pct(x, digits: int = 1) -> str:
    return "n/a" if x is None or x != x else f"{x:.{digits}f}"

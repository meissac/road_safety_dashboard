"""Hook and KPI header (responds to the sidebar filters)."""
import streamlit as st

from utils.style import fmt_int, kpi_cards, section_divider


def render(k: dict, story: dict, filters) -> None:
    one_in = round(100 / story["lethality"])
    st.markdown(
        '<div class="kicker">Study of road injury accidents in France between 2019 and 2024</div>'
        '<div class="hero-title">When a crash turns <span class="red">deadly</span></div>'
        f'<div class="lede">Between 2019 and 2024, French police recorded <b>{fmt_int(story["accidents"])} injury '
        f'accidents</b>. Most victims survive, but <b>{fmt_int(story["killed"])} people died</b>, about '
        f'<b>1 victim in {one_in}</b>. This dashboard tests six popular beliefs about <i>where, when and for whom</i> '
        'a crash becomes fatal, and lets you check each verdict yourself with the filters on the left.</div>',
        unsafe_allow_html=True)

    years = filters.years[1] - filters.years[0] + 1
    kpi_cards([
        {"label": "Injury accidents", "value": fmt_int(k["accidents"]),
         "sub": f"≈ {fmt_int(k['accidents'] / years)} per year"},
        {"label": "Victims", "value": fmt_int(k["victims"]),
         "sub": "(killed, hospitalised or slightly injured)"},
        {"label": "People killed", "value": fmt_int(k["killed"]),
         "sub": f"≈ {fmt_int(k['killed'] / years)} per year"},
        {"label": "Lethality", "value": f"{k['lethality']:.2f}", "sub": "killed per 100 victims"},
    ])
    st.caption("Lethality measures how often a crash victim dies. Unlike raw counts, it does not simply grow "
               "with population or traffic, so places, hours and groups can be compared fairly.")
    section_divider()

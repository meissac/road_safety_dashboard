"""When a crash turns deadly: road accident lethality in France, 2019-2024.

Run:  streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="When a crash turns deadly", page_icon="🚗", layout="wide")

from sections import conclusions, data_quality, deep_dives, intro, overview  # noqa: E402
from utils import io, prep, style  # noqa: E402

style.inject_css()
accidents_all, users_all = io.load_data()
MODES = sorted(m for m in users_all["mode"].astype(str).unique() if m != "Other or unknown") + ["Other or unknown"]

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown('<div class="kicker">Explore</div>', unsafe_allow_html=True)
    st.markdown("### Filters")
    years = st.slider("Years", 2019, 2024, (2019, 2024),
                      help="Include 2019 and 2020 to see the COVID comparison.")
    territory = st.radio("Territory", ["All France", "Metropolitan", "Overseas"],
                         help="Metropolitan = mainland France and Corsica. The map shows mainland only.")
    area = st.radio("Area", ["All areas", "Built-up area", "Outside built-up area"],
                    help="As recorded by the police: inside or outside a town's limits.")
    modes = st.multiselect("Mode of travel", MODES, placeholder="All modes",
                           help="Keeps only these road users, and the accidents they were involved in.")
    st.divider()
    st.markdown("**Lethality** = people killed per 100 victims\n\n"
                "We consider victims persons that were killed, hospitalised or slightly injured.")
    st.caption(f"Data: ONISR / data.gouv.fr, {io.LICENCE}")

filters = prep.Filters(years=tuple(years), territory=territory, area=area, modes=tuple(modes))
acc, users = prep.filter_data(filters)
victims = prep.victims_only(users)
story = prep.story_numbers()

# ---------------------------------------------------------------- story
k = prep.kpis(acc, users)
intro.render(k, story, filters)

if k["victims"] == 0:
    st.warning("No victims match these filters. Widen the year range or remove a filter.")
    st.stop()
if k["victims"] < 500:
    st.info(f"Only {k['victims']:,} victims match these filters, so percentages below may be unstable.")

overview.render(acc, victims, story)
deep_dives.render(acc, victims, story, filters)
conclusions.render(story)
data_quality.render()

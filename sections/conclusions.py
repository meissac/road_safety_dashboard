"""Key insights (full-data numbers) and implications."""
import streamlit as st

from utils.style import card, section_divider


def render(story: dict) -> None:
    st.markdown('<div class="chapter-num">What we learned</div>'
                '<div class="claim">Four findings, 2019 to 2024, all of France</div>', unsafe_allow_html=True)
    covid = story["covid"]
    c1, c2 = st.columns(2)
    with c1:
        card("1. It's not the motorway, it's the country road",
             f"Departmental roads carry <b>{story['dep_road_pct_acc']:.0f}% of crashes but "
             f"{story['dep_road_pct_killed']:.0f}% of deaths</b>, and their lethality "
             f"({story['dep_road_lethality']:.1f}) is double that of motorways ({story['motorway_lethality']:.1f}). "
             f"Outside built-up areas: {story['outside_pct_acc']:.0f}% of crashes, "
             f"<b>{story['outside_pct_killed']:.0f}% of deaths</b>.", "red")
        st.write("")
        card("3. Young people get hurt, older people die",
             f"18 to 24-year-olds are <b>{story['young_pct_victims']:.0f}% of victims</b>. The 75+ are "
             f"{story['old_pct_victims']:.0f}% of victims but <b>{story['old_pct_killed']:.0f}% of deaths</b> "
             f"(lethality {story['old_lethality']:.1f} vs {story['adult_lethality']:.1f} for 25 to 34-year-olds).")
    with c2:
        card("2. Night doesn't cause most deaths, it multiplies the risk",
             f"Only <b>{story['night_pct_killed']:.0f}% of deaths</b> happen at night, but a night crash is "
             f"<b>{story['night_lethality'] / story['day_lethality']:.1f}× deadlier</b> than a daytime one. "
             "The gap is largest on unlit roads and in the small hours.")
        st.write("")
        covid_txt = (f"Lethality on lockdown days was <b>{covid['lock_lethality']:.2f}</b> vs "
                     f"{covid['ref_lethality']:.2f} on the same days of 2019." if covid else "")
        card("4. Emptier roads were not safer roads",
             f"April 2020 saw <b>{abs(story['april_drop']):.0f}% fewer crashes</b> than April 2019. {covid_txt}",
             "red")

    st.write("")
    st.markdown('<div class="chapter-num">So what?</div>'
                '<div class="claim">Where prevention could pay off most</div>', unsafe_allow_html=True)
    st.markdown("""
- **Prioritise country roads.** Safety audits, barriers, safer bends and overtaking lanes on departmental
  roads would target the majority of deaths, not motorways, which are already comparatively safe.
- **Use the hotspot map to choose road sections to inspect.** Clusters of fatal crashes flag stretches worth a
  site visit. The data records surface *conditions* (wet, icy), not road *damage*, so repairs need on-site checks.
- **Make night driving visible.** Lighting, reflective markings and campaigns aimed at late-night weekend trips
  address the hours when a crash is most likely to kill.
- **Protect older road users.** Safer crossings, longer pedestrian signal times and fitness-to-drive awareness
  address the group most likely to die once hurt.
- **Check emergency coverage in high-lethality rural départements.** Response times and hospital distances are
  not in this dataset.
""")
    section_divider()

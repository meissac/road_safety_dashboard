"""Context: monthly trend 2019-2024 and the COVID test (H5)."""
import streamlit as st

from utils import prep, viz
from utils.style import chapter, section_divider


def render(acc, victims, story: dict) -> None:
    covid = prep.covid_comparison(victims)
    drop = prep.april_drop(acc)
    if covid and drop is not None:
        evidence = (f"In April 2020, crashes fell by <b>{abs(drop):.0f}%</b> compared with April 2019. "
                    f"Yet on lockdown days, lethality was <b>{covid['lock_lethality']:.2f}</b> against "
                    f"<b>{covid['ref_lethality']:.2f}</b> on the same calendar days of 2019: fewer crashes, "
                    "but each one deadlier. Emptier roads may have encouraged faster driving. This is a "
                    "plausible explanation that this data cannot prove.")
    else:
        evidence = ("Include 2019 and 2020 in the year filter to compare lockdown days with the same days "
                    "of 2019.")
    chapter("COVID", "COVID cut the number of crashes, not the danger", "CONFIRMED", evidence)

    m = prep.monthly(acc, victims)
    st.plotly_chart(viz.trend_chart(m, story["lethality"]), width="stretch")
    st.caption("Chart description: grey bars show the number of injury accidents each month, and the red line shows "
               "lethality (killed per 100 victims). Shaded bands mark the three national lockdowns.")
    section_divider()

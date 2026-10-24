"""Hypotheses on road type, territories, time of day, age and holidays.

Each one shows: subject, claim, verdict, one evidence sentence and its chart(s).
"""
import pandas as pd
import streamlit as st

from utils import io, prep, viz
from utils.style import chapter, section_divider


def _row(df: pd.DataFrame, col: str, key):
    hit = df[df[col] == key]
    return hit.iloc[0] if len(hit) else None


# ---------------------------------------------------------------- time of day
def night(acc, victims, story) -> None:
    s = prep.summary(victims, "is_night", acc)
    n, d = _row(s, "is_night", True), _row(s, "is_night", False)
    lights = prep.summary(victims, "light", acc)
    unlit, lit = _row(lights, "light", "Night, no street lighting"), _row(lights, "light", "Night, street lighting on")
    if n is not None and d is not None:
        evidence = (f"Most deaths happen in daylight: night accounts for <b>{n['pct_accidents']:.0f}% of crashes</b> "
                    f"and <b>{n['pct_killed']:.0f}% of deaths</b>. But a night crash is "
                    f"<b>{n['lethality'] / d['lethality']:.1f}× deadlier</b> (lethality {n['lethality']:.2f} vs "
                    f"{d['lethality']:.2f}).")
        if unlit is not None and lit is not None:
            evidence += (f" The real divide is light: <b>{unlit['lethality']:.1f}</b> on unlit roads vs "
                         f"<b>{lit['lethality']:.1f}</b> under street lights, partly because unlit roads are rural.")
    else:
        evidence = "Not enough data in the current selection."
    chapter("Time of day", "Deadly crashes mostly happen at night", "NUANCED", evidence)

    c1, c2 = st.columns([3, 2])
    with c1:
        st.plotly_chart(viz.heatmap(prep.hour_weekday(victims)), width="stretch")
        st.caption("Chart description: lethality for each hour and weekday. Darker means safer, red means deadlier. "
                   "Cells with fewer than 30 victims are left blank.")
    with c2:
        st.plotly_chart(viz.light_bars(lights, story["lethality"]), width="stretch")
        st.caption("Chart description: lethality by lighting conditions, with night categories in red.")
    section_divider()


# ---------------------------------------------------------------- holidays
def holidays(acc, victims, filters) -> None:
    d = prep.per_day(acc, victims, filters.years)
    ordinary = _row(d, "day_type", "Ordinary day")
    if ordinary is not None and len(d) > 1:
        above = d[(d["day_type"] != "Ordinary day") & (d["killed_per_day"] > ordinary["killed_per_day"])]
        names = ", ".join(above["day_type"].str.replace(r" \(.*\)", "", regex=True)) or "none"
        evidence = (f"An ordinary day costs <b>{ordinary['killed_per_day']:.1f} lives</b> on average. Most "
                    "festive days are <i>below</i> that: fewer people commute, so there are fewer crashes. "
                    f"Days above the ordinary level in this selection: <b>{names}</b>. With one such day per "
                    "year, these are signals, not proof.")
    else:
        evidence = "Not enough data in the current selection."
    chapter("Holidays", "Holidays and celebrations are deadlier", "DEBUNKED", evidence)
    st.plotly_chart(viz.day_type_bars(d), width="stretch")
    st.caption("Chart description: average number of people killed per day for each type of day. The dotted line "
               "is an ordinary day, and red bars are above it. n is the number of such days in the selected years.")
    section_divider()


# ---------------------------------------------------------------- road type
def roads(acc, victims) -> None:
    r = prep.roads(acc, victims)
    dep, mot = _row(r, "road", "Departmental road"), _row(r, "road", "Motorway")
    area = prep.summary(victims, "area", acc)
    out = _row(area, "area", "Outside built-up area")
    if dep is not None and mot is not None:
        evidence = (f"Motorways carry <b>{mot['pct_accidents']:.0f}% of crashes</b> and have one of the lowest "
                    f"lethalities (<b>{mot['lethality']:.1f}</b>). Departmental roads, France's two-way country "
                    f"roads, carry <b>{dep['pct_accidents']:.0f}% of crashes but {dep['pct_killed']:.0f}% of "
                    f"deaths</b>, with a lethality of <b>{dep['lethality']:.1f}</b>.")
        if out is not None and len(area) > 1:
            evidence += (f" Overall, crashes outside built-up areas are {out['pct_accidents']:.0f}% of the total "
                         f"but {out['pct_killed']:.0f}% of deaths.")
    else:
        evidence = "Select both built-up and rural areas to compare road types."
    chapter("Road type", "Motorways are the most dangerous roads", "DEBUNKED", evidence)
    st.plotly_chart(viz.road_share(r), width="stretch")
    st.caption("Chart description: for each road type, the grey bar is its share of all accidents and the red bar "
               "its share of all deaths. A red bar longer than the grey one means crashes there are deadlier "
               "than average.")
    section_divider()


# ---------------------------------------------------------------- age
def ages(victims, story) -> None:
    a = prep.summary(victims[victims["age_group"].notna()], "age_group")
    old, young, adult = _row(a, "age_group", "75+"), _row(a, "age_group", "18-24"), _row(a, "age_group", "25-34")
    if old is not None and young is not None and adult is not None:
        evidence = (f"Two different problems. <b>Young people get hurt most often</b>: 18 to 24-year-olds are "
                    f"<b>{young['pct_victims']:.0f}% of victims</b>. <b>Older people die most often</b>: the 75+ "
                    f"are {old['pct_victims']:.0f}% of victims but <b>{old['pct_killed']:.0f}% of deaths</b>, "
                    f"a lethality <b>{old['lethality'] / adult['lethality']:.1f}× higher</b> than for 25 to "
                    "34-year-olds, most likely because the body is more fragile. Licence age is not in the data, "
                    "so new drivers are approximated by the 18 to 24 group.")
    else:
        evidence = "Not enough data in the current selection."
    chapter("Age", "Young and elderly road users are over-represented", "CONFIRMED", evidence)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(viz.age_shares(a), width="stretch")
        st.caption("Chart description: share of all victims (grey) and of all deaths (red) by age group.")
    with c2:
        st.plotly_chart(viz.age_lethality(a, story["lethality"]), width="stretch")
        st.caption("Chart description: lethality by age group. The dotted line is the national average.")
    st.markdown('<span class="note">Tip: use the "Mode of travel" filter to see the same picture for pedestrians, '
                "cyclists or motorcyclists.</span>", unsafe_allow_html=True)
    section_divider()


# ---------------------------------------------------------------- territories
def territories(acc, victims, filters) -> None:
    names = io.department_names()
    d = prep.departments(acc, victims, names)
    reliable = d[d["reliable"]].sort_values("lethality")
    metro = reliable[~reliable["dep"].str.startswith(("97", "98"))]
    if len(metro) >= 2:
        lo, hi = metro.iloc[0], metro.iloc[-1]
        top_killed = d.sort_values("killed", ascending=False).iloc[0]
        evidence = (f"Counting deaths and measuring lethality draw <b>opposite maps</b>. "
                    f"{top_killed['name']} records the most deaths ({int(top_killed['killed']):,}), but in mainland "
                    f"France a victim is <b>{hi['lethality'] / lo['lethality']:.0f}× more likely to die</b> in "
                    f"{hi['name']} ({hi['lethality']:.1f}) than in {lo['name']} ({lo['lethality']:.1f}). Rural "
                    "départements combine faster roads with longer distances to emergency care. This is a lead "
                    "worth investigating, not something this data can prove.")
    else:
        evidence = "Not enough départements with 300+ victims in the current selection."
    chapter("Territories", "Severe crashes cluster in some territories", "CONFIRMED", evidence)

    view = st.radio("Map view", ["Lethality by département", "People killed by département", "Fatal crash locations"],
                    horizontal=True, label_visibility="collapsed")
    c1, c2 = st.columns([3, 2])
    with c1:
        if view == "Fatal crash locations":
            p = acc[acc["is_fatal"] & acc["coords_valid"]].copy()
            p["date_str"] = p["date"].dt.strftime("%d %b %Y")
            st.plotly_chart(viz.fatal_points(p, io.load_geojson()), width="stretch")
            st.caption("Chart description: each red dot is a fatal crash in mainland France, and larger dots mean "
                       "more deaths. Zoom in to find hotspots along specific roads.")
        else:
            metric = "lethality" if view.startswith("Lethality") else "killed"
            st.plotly_chart(viz.choropleth(d, io.load_geojson(), metric), width="stretch")
            st.caption("Chart description: mainland départements coloured by the selected measure. Départements "
                       f"with fewer than {prep.MIN_VICTIMS_DEPT} victims in the selection are left blank for "
                       "lethality. Overseas territories appear in the ranking only.")
    with c2:
        if len(reliable) >= 2:
            st.plotly_chart(viz.ranking(d), width="stretch")
            st.caption("Chart description: the 10 lowest and 10 highest lethalities among départements with "
                       f"at least {prep.MIN_VICTIMS_DEPT} victims (overseas included).")
    if filters.territory == "Overseas":
        st.info("The map shows mainland France only. Overseas results are in the ranking.")
    section_divider()


def render(acc, victims, story, filters) -> None:
    roads(acc, victims)
    territories(acc, victims, filters)
    night(acc, victims, story)
    ages(victims, story)
    holidays(acc, victims, filters)

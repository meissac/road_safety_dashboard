"""Data quality, methodology, limitations and sources."""
import pandas as pd
import streamlit as st

from utils import io, viz


def _checks(report: dict) -> pd.DataFrame:
    rows = [
        ("Duplicate accident IDs", report["duplicate_accident_ids"], "Must be 0", "pass"),
        ("Accidents with no victim", report["accidents_with_zero_victims"],
         "Must be 0 (an injury accident has at least one victim)", "pass"),
        ("People not linked to an accident", report["users_without_matching_accident"], "Must be 0", "pass"),
        ("People not linked to a vehicle", report["users_without_matching_vehicle"], "Must be 0", "pass"),
        ("Exact duplicate person rows", report["exact_duplicate_user_rows"],
         "Kept: the 2019 and 2020 files have no person ID, so true duplicates can't be told apart from identical "
         "passengers", "info"),
        ("Extra road rows removed (2023 and 2024)", sum(report["lieux_extra_rows_dropped_by_year"].values()),
         "Several roads per accident since 2023. The first listed road is kept so each crash counts once", "info"),
        ("Mainland coordinates outside France", report["metro_accidents_with_invalid_coords"],
         "Excluded from the map only, kept in all totals", "info"),
        ("Unknown severity", report["users_with_unknown_severity"], "Not counted as victims", "info"),
        ("Missing or impossible age", report["users_with_invalid_or_missing_age"],
         "Age set to unknown (outside 0 to 105)", "info"),
    ]
    df = pd.DataFrame(rows, columns=["Check", "Count", "Rule / treatment", "type"])
    df["Status"] = [("Passed" if c == 0 else "Failed") if t == "pass" else "Documented"
                    for c, t in zip(df["Count"], df["type"])]
    return df[["Status", "Check", "Count", "Rule / treatment"]]


def render() -> None:
    report, missing = io.load_quality()
    st.markdown('<div class="chapter-num">Behind the numbers</div>'
                '<div class="claim">Data quality, method and limits</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Validation checks", "Missing values", "Method", "Limitations & sources"])
    with tab1:
        raw = report["raw_rows"]
        st.markdown(f"Raw files (2019 to 2024): **{raw['caract']:,}** accidents, **{raw['lieux']:,}** road rows, "
                    f"**{raw['vehicules']:,}** vehicles and **{raw['usagers']:,}** people involved.")
        st.dataframe(_checks(report), hide_index=True, width="stretch")
        totals = pd.DataFrame(report["totals_by_year"]).T.rename_axis("Year").reset_index()
        totals["Lethality"] = (100 * totals["killed"] / totals["victims"]).round(2)
        st.markdown("**Totals per year after cleaning**")
        st.dataframe(totals[["Year", "accidents", "victims", "killed", "Lethality"]], hide_index=True,
                     width="stretch")
    with tab2:
        st.plotly_chart(viz.missingness_bars(missing), width="stretch")
        st.caption("Chart description: percentage of rows where each raw column is empty or coded -1 "
                   "('not recorded'). Missing values are kept as 'Unknown', never treated as zero.")
        st.markdown("Fields used in this dashboard (lighting, area, road type, severity, mode of travel, age) are "
                    "all **below 2% unknown**. Columns with high missingness (e.g. secondary safety equipment, "
                    "pedestrian location) are not used.")
    with tab3:
        st.markdown("""
- **Source tables joined** on the accident ID: characteristics (time, place, light), locations (road type),
  vehicles (vehicle category) and road users (severity, age, role). Every join is validated (one-to-one or
  many-to-one), and the 2022 rename `Accident_Id → Num_Acc` is harmonised.
- **Victims** are people killed (within 30 days), hospitalised or slightly injured. Unharmed people involved are
  kept but not counted as victims.
- **Lethality** = killed ÷ victims × 100. Used instead of raw counts to compare groups of very different sizes.
- **Engineered features:** hour, weekday, night flag (lighting codes 3 to 5), age and age group, mode of travel
  (pedestrians are classed as pedestrians, not by the vehicle that hit them), French public holidays
  (computed, incl. Easter-based ones), festive dates, COVID lockdown periods (17 Mar to 10 May 2020,
  30 Oct to 14 Dec 2020, 3 Apr to 2 May 2021).
- **Small numbers:** heatmap cells with fewer than 30 victims are hidden, and départements with fewer than
  300 victims are not ranked.
- **Reproduce:** `scripts/download_data.py` → `scripts/prepare_data.py` → `streamlit run app.py`.
""")
    with tab4:
        st.markdown(f"""
- **Under-reporting.** The file only contains crashes recorded by police or gendarmerie. All deaths are
  recorded, but many non-fatal crashes (especially single cyclists or motorcyclists) are missing. This
  inflates lethality for those groups.
- **No exposure data.** Without traffic volumes or kilometres driven, we compare *shares* and *lethality*,
  not true risk per trip. A road with many crashes may simply carry more traffic.
- **Correlation, not causation.** Night, rural roads and speed limits overlap (unlit roads are mostly rural).
  The dashboard shows associations and checks one obvious confounder (night × area), not causes.
- **'Hospitalised'** is no longer a certified indicator since 2019, so we do not use it in headline figures.
- **Holiday results** rest on one day per year (6 days per festive date). Treat them as signals.
- **Privacy.** Data is published anonymised by ONISR. This dashboard only shows aggregates and crash locations,
  never individuals.

**Sources**
- Dataset: [{io.SOURCE_TITLE}]({io.SOURCE_URL}), {io.PRODUCER}, {io.LICENCE}.
- Variable definitions: ONISR, *Description des bases de données annuelles* (documentation on the dataset page).
- Département boundaries: [france-geojson]({io.GEO_SOURCE_URL}) (simplified, derived from IGN data).
""")

# When a crash turns deadly: road accident lethality in France, 2019 to 2024

An interactive Streamlit data story built on the official French road-accident database (BAAC).
It tests six popular beliefs about **where, when and for whom a road crash becomes fatal**, and lets the
user check every verdict with filters.

*EFREI Paris, Data Visualisation individual project, #EFREIDataStories2026*
*Author: Meïssa CHINI (20230315, BIA)*

**Live app:** (https://roadsafetydashboard-7yggqcxdhwenrgkn3rpyxg.streamlit.app/?embed_options=dark_theme,show_toolbar)
**Demo video:** https://drive.google.com/file/d/13WmaNMLiN1FCbhkq1ZpLqUozRmOSmvT-/view?usp=sharing

---

## 1. Problem, audience and question

Most injury crashes are not fatal. The ones that kill cluster in particular conditions, and knowing *which*
conditions tells authorities where prevention pays off most.

- **Audience:** local road-safety decision-makers (prefecture road-safety teams, départements, road-safety
  observatories), and secondarily the informed public.
- **Main question:** *Where, when and for whom does a road crash in France turn deadly (2019 to 2024)?*
- **Core metric, lethality:** people killed per 100 victims. Victims are people killed, hospitalised or
  slightly injured. Unlike raw counts, lethality does not simply grow with population or traffic, so places,
  hours and groups can be compared fairly.

## 2. Narrative: six hypotheses, tested

Each hypothesis was written **before** looking at the data, then confirmed, debunked or nuanced.
Figures below are for all of France, 2019 to 2024: 327,628 accidents, 431,066 victims, 19,877 killed,
lethality 4.61.

| Subject | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| Road type | Motorways are the most dangerous roads | **Debunked** | Motorways: 9.4% of crashes, 7.9% of deaths, lethality 3.43. Departmental roads: 37.5% of crashes but **58.1% of deaths**, lethality 6.85. Outside built-up areas: 36.4% of crashes, 67.3% of deaths. |
| Territories | Severe crashes cluster in some territories | **Confirmed** | Counts and lethality draw opposite maps. Bouches-du-Rhône has the most deaths (607) but low lethality (2.86). Lethality is 0.67 in Paris vs 12.3 in Creuse (about 18×). |
| Time of day | Deadly crashes mostly happen at night | **Nuanced** | Night = 26.8% of crashes and 35.8% of deaths, so most deaths happen by day. But a night crash is 1.4× deadlier (5.84 vs 4.13). Unlit roads at night: 9.65 vs 2.90 under street lights. Holds both in and outside towns. |
| Age | Young and elderly road users are over-represented | **Confirmed** | 18 to 24: 20.1% of victims. 75+: 5.3% of victims but 15.4% of deaths, lethality 13.31, which is 3.7× that of 25 to 34 (3.56). |
| COVID | COVID cut the number of crashes, not the danger | **Confirmed** | April 2020: 1,208 crashes vs 4,616 in April 2019 (−74%). Lockdown days: lethality 5.30 vs 4.41 on the same days of 2019. |
| Holidays | Holidays and celebrations are deadlier | **Mostly debunked** | Ordinary day: 9.1 deaths per day. New Year's Eve 6.2, Christmas Eve 8.2, other public holidays 8.5. Exceptions: French National Day, 14 July (11.3) and 1 January (11.2), with only 6 days each, so a signal, not proof. |

**Key takeaways**
1. It's not the motorway, it's the country road.
2. Night doesn't cause most deaths, it multiplies the risk.
3. Young people get hurt, older people die.
4. Emptier roads were not safer roads.

**Implications (leads, not proven causes)**
- Prioritise safety work on departmental roads.
- Use the hotspot map to select road sections for on-site inspection.
- Improve night visibility.
- Protect older road users.
- Check emergency-care coverage in high-lethality rural départements.

## 3. Data

| | |
|---|---|
| Dataset | *Bases de données annuelles des accidents corporels de la circulation routière, Années de 2005 à 2024* |
| Link | https://www.data.gouv.fr/datasets/53698f4ca3a729239d2036df/ |
| Producer | ONISR (Observatoire national interministériel de la sécurité routière), Ministère de l'Intérieur |
| Portal | data.gouv.fr (approved portal) |
| Licence | Licence Ouverte / Open Licence (Etalab), reuse allowed with attribution |
| Scope used | 2019 to 2024, all of France (mainland and overseas), 4 tables per year (24 CSV files, about 190 MB) |
| Map boundaries | Simplified département contours from https://github.com/gregoiredavid/france-geojson (derived from IGN data) |

**Included in this submission:** the cleaned files in `data/processed/` (about 17 MB, Parquet), so the app
runs immediately. The raw files are **not** included because of their size. `scripts/download_data.py`
re-downloads them from the portal.

## 4. Data preparation and methods

Pipeline: `scripts/download_data.py` → `scripts/prepare_data.py` → `app.py`.

1. **Load and harmonise** the four tables (characteristics, locations, vehicles, road users) for 6 years,
   and rename the 2022 `Accident_Id` column to `Num_Acc`.
2. **Join** on the accident ID, each join validated (`one_to_one` or `many_to_one`). Every person matches an
   accident and a vehicle, and no accident is left without a victim.
3. **Deduplicate locations:** since 2023 an accident can list several roads (31,884 extra rows). The first
   listed road is kept so each crash is counted once.
4. **Missing values:** code `-1` (not recorded) becomes a true missing value shown as "Unknown". It is never
   dropped and never treated as zero. All fields used are below 2% unknown.
5. **Feature engineering:** hour, weekday, night flag (lighting codes 3 to 5), age and age group, mode of
   travel (pedestrians classed as pedestrians, not by the vehicle that hit them), French public holidays
   (including Easter-based ones, computed), festive dates, COVID lockdown periods, coordinate validity.
6. **Analysis:** group-bys, shares and lethality, a confounder check (night × built-up area), comparison of
   lockdown days with the same calendar days of 2019, and small-number safeguards (heatmap cells with fewer
   than 30 victims hidden, départements with fewer than 300 victims not ranked). No machine learning, only
   simple and transparent methods.

Validation results are shown in the app (section "Data quality, method and limits") and can be re-run with
`python scripts/validate.py` (13 automated checks, all passing).

## 5. Assumptions and limitations

- **Under-reporting:** only police-recorded crashes are included. All deaths are recorded, but many
  non-fatal crashes (especially single cyclists or motorcyclists) are missing, which inflates lethality for
  those groups.
- **No exposure data** (traffic volumes, km driven, population by age): we compare shares and lethality,
  not true risk per trip.
- **Correlation, not causation:** night, rural roads and speed limits overlap.
- **"Hospitalised"** is no longer a certified indicator since 2019 and is not used in headline figures.
- **Licence age** is not in the data, so new drivers are approximated by the 18 to 24 age group.
- **Holiday results** rest on 6 days per festive date.
- 164 exact duplicate person rows (2019 and 2020 files, which have no person ID) are kept because they
  cannot be told apart from identical passengers (0.02% of rows).

## 6. Application features

- **Sidebar filters:** year range, territory (all, mainland, overseas), area (built-up or outside), mode of
  travel. All KPIs and charts respond.
- **KPI header:** accidents, victims, people killed, lethality.
- **Interactive charts with tooltips:** monthly trend with lockdown bands, hour × weekday heatmap, lighting
  bars, holiday bars with reference line, road-type shares, age charts, département ranking.
- **Maps:** département choropleth (lethality or deaths) and every fatal crash location (hotspots).
- **Data-quality section:** validation checks, missingness chart, method, limitations and sources.
- **Accessibility:** verdicts always written in text (not colour only), a text description under every
  chart, labelled axes and units, high-contrast dark theme.
- **Performance:** `st.cache_data` for loading and filtered tables, Parquet files, pre-computed features.

## 7. Installation and execution

Requirements: Python 3.11 and internet access (map base layer and fonts).

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate            # Windows (macOS/Linux: source .venv/bin/activate)

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app (processed data is included)
streamlit run app.py
```

Optional, to rebuild the data from the source portal:

```bash
python scripts/download_data.py   # downloads 24 CSV files into data/raw/
python scripts/prepare_data.py    # cleans, joins and writes data/processed/
python scripts/validate.py        # 13 automated checks
python scripts/explore.py         # prints the hypothesis tests used in the story
```

## 8. Project structure

```
app.py                  page setup, sidebar filters, sections in story order
sections/               intro (hook and KPIs), overview (trend, COVID), deep_dives (road type,
                        territories, time of day, age, holidays), conclusions, data_quality
utils/                  io (cached loading, sources), prep (filters, aggregations),
                        viz (charts), style (theme)
scripts/                download_data, prepare_data, validate, explore
data/processed/         cleaned Parquet files and quality report
assets/                 département boundaries (GeoJSON)
.streamlit/config.toml  theme
STORYBOARD.md           narrative structure
VIDEO_SCRIPT.md         demo video script
```

## 9. Dependencies

`streamlit`, `pandas`, `plotly`, `pyarrow`, `requests`, with versions pinned in `requirements.txt`.

## 10. Credits

- Data: ONISR, Ministère de l'Intérieur, via data.gouv.fr, Licence Ouverte.
- Variable definitions: ONISR, *Description des bases de données annuelles 2005 à 2024*.
- Département boundaries: Grégoire David, france-geojson (from IGN data).
- Built with Streamlit and Plotly. Fonts from Google Fonts.

"""Filtering and aggregations used by the dashboard sections.

Lethality = killed per 100 victims (victims = killed + hospitalised + slightly injured).
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st

from utils.io import load_data

LOCKDOWNS = [("2020-03-17", "2020-05-10"), ("2020-10-30", "2020-12-14"), ("2021-04-03", "2021-05-02")]
AGE_ORDER = ["0-13", "14-17", "18-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75+"]
MAIN_ROADS = ["Motorway", "National road", "Departmental road", "Municipal road", "Metropolitan urban road"]
DAY_TYPE_ORDER = ["Ordinary day", "Other public holiday", "French National Day (14 Jul)", "Christmas Eve (24 Dec)",
                  "Christmas Day (25 Dec)", "New Year's Eve (31 Dec)", "New Year's Day (1 Jan)"]
MIN_VICTIMS_DEPT = 300  # below this, a departement's lethality is too unstable to rank


@dataclass(frozen=True)
class Filters:
    years: tuple[int, int] = (2019, 2024)
    territory: str = "All France"          # "All France" | "Metropolitan" | "Overseas"
    area: str = "All areas"                # "All areas" | "Built-up area" | "Outside built-up area"
    modes: tuple[str, ...] = ()            # empty = all modes of travel


def lethality(killed, victims) -> float:
    return float(100 * killed / victims) if victims else float("nan")


# ---------------------------------------------------------------- filtering
@st.cache_data(max_entries=16, show_spinner=False)
def filter_data(filters: Filters) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (accidents, users) matching the sidebar filters."""
    acc, users = load_data()
    a_mask = acc["year"].between(*filters.years)
    u_mask = users["year"].between(*filters.years)
    if filters.territory != "All France":
        a_mask &= acc["territory"] == filters.territory
        u_mask &= users["territory"] == filters.territory
    if filters.area != "All areas":
        a_mask &= acc["area"] == filters.area
        u_mask &= users["area"] == filters.area
    acc_f, users_f = acc[a_mask], users[u_mask]
    if filters.modes:
        # Keep the selected road users, and the accidents in which at least one of them was involved
        users_f = users_f[users_f["mode"].isin(filters.modes)]
        acc_f = acc_f[acc_f["Num_Acc"].isin(users_f["Num_Acc"].unique())]
    return acc_f, users_f


def victims_only(users: pd.DataFrame) -> pd.DataFrame:
    return users[users["is_victim"]]


def kpis(acc: pd.DataFrame, users: pd.DataFrame) -> dict:
    v = victims_only(users)
    killed, n_victims = int(v["is_killed"].sum()), len(v)
    return {"accidents": len(acc), "victims": n_victims, "killed": killed,
            "lethality": lethality(killed, n_victims)}


def summary(victims: pd.DataFrame, by, acc: pd.DataFrame | None = None) -> pd.DataFrame:
    """Victims, killed, shares and lethality per group (optionally accident counts)."""
    g = victims.groupby(by, observed=True).agg(victims=("is_victim", "size"), killed=("is_killed", "sum"))
    if acc is not None:
        g.insert(0, "accidents", acc.groupby(by, observed=True).size())
        g["accidents"] = g["accidents"].fillna(0)
        g["pct_accidents"] = 100 * g["accidents"] / g["accidents"].sum()
    g["pct_victims"] = 100 * g["victims"] / g["victims"].sum()
    g["pct_killed"] = 100 * g["killed"] / max(g["killed"].sum(), 1)
    g["lethality"] = 100 * g["killed"] / g["victims"]
    return g.reset_index()


# ---------------------------------------------------------------- overview / H5
def monthly(acc: pd.DataFrame, victims: pd.DataFrame) -> pd.DataFrame:
    a = acc.groupby(acc["date"].dt.to_period("M")).size().rename("accidents")
    v = victims.groupby(victims["date"].dt.to_period("M")).agg(victims=("is_victim", "size"),
                                                               killed=("is_killed", "sum"))
    m = pd.concat([a, v], axis=1).fillna(0)
    m["lethality"] = np.where(m["victims"] > 0, 100 * m["killed"] / m["victims"].replace(0, np.nan), np.nan)
    m.index = m.index.to_timestamp()
    return m.rename_axis("month").reset_index()


def covid_comparison(victims: pd.DataFrame) -> dict | None:
    """Lockdown days vs the same calendar days in 2019 (needs 2019 and lockdown years in the filter)."""
    lock = victims[victims["covid_lockdown"]]
    if lock.empty or not (victims["year"] == 2019).any():
        return None
    days = lock["date"].dt.strftime("%m-%d").unique()
    ref = victims[(victims["year"] == 2019) & victims["date"].dt.strftime("%m-%d").isin(days)]
    if ref.empty:
        return None
    return {"lock_lethality": lethality(lock["is_killed"].sum(), len(lock)),
            "ref_lethality": lethality(ref["is_killed"].sum(), len(ref))}


def april_drop(acc: pd.DataFrame) -> float | None:
    apr19 = ((acc["year"] == 2019) & (acc["month"] == 4)).sum()
    apr20 = ((acc["year"] == 2020) & (acc["month"] == 4)).sum()
    return float(100 * (apr20 - apr19) / apr19) if apr19 else None


# ---------------------------------------------------------------- H1
def hour_weekday(victims: pd.DataFrame, min_victims: int = 30) -> pd.DataFrame:
    g = victims.groupby(["weekday", "hour"], observed=True).agg(victims=("is_victim", "size"),
                                                                killed=("is_killed", "sum")).reset_index()
    g["lethality"] = 100 * g["killed"] / g["victims"]
    g.loc[g["victims"] < min_victims, "lethality"] = np.nan  # too few victims to be meaningful
    return g


# ---------------------------------------------------------------- H2
@st.cache_data(show_spinner=False)
def calendar_days(years: tuple[int, int]) -> pd.Series:
    """Number of calendar days of each type in the selected years."""
    acc, _ = load_data()
    lookup = acc[["date", "day_type"]].drop_duplicates("date").set_index("date")["day_type"].astype("string")
    days = pd.Series(pd.date_range(f"{years[0]}-01-01", f"{years[1]}-12-31"))
    return days.map(lookup).fillna("Ordinary day").value_counts()


def per_day(acc: pd.DataFrame, victims: pd.DataFrame, years: tuple[int, int]) -> pd.DataFrame:
    s = summary(victims, "day_type", acc).set_index("day_type")
    s["days"] = calendar_days(years)
    s["accidents_per_day"] = s["accidents"] / s["days"]
    s["killed_per_day"] = s["killed"] / s["days"]
    order = [d for d in DAY_TYPE_ORDER if d in s.index]
    return s.loc[order].reset_index()


# ---------------------------------------------------------------- H3
def roads(acc: pd.DataFrame, victims: pd.DataFrame) -> pd.DataFrame:
    a = acc.assign(road=acc["road_type"].astype("string").where(acc["road_type"].isin(MAIN_ROADS), "Other"))
    v = victims.assign(road=victims["road_type"].astype("string").where(victims["road_type"].isin(MAIN_ROADS),
                                                                        "Other"))
    s = summary(v, "road", a)
    order = MAIN_ROADS + ["Other"]
    s["road"] = pd.Categorical(s["road"], categories=order, ordered=True)
    return s.sort_values("road")


# ---------------------------------------------------------------- H6
def departments(acc: pd.DataFrame, victims: pd.DataFrame, names: dict) -> pd.DataFrame:
    s = summary(victims, "dep", acc)
    s["name"] = s["dep"].map(names).fillna(s["dep"])
    s["reliable"] = s["victims"] >= MIN_VICTIMS_DEPT
    return s


# ---------------------------------------------------------------- story numbers (full data)
@st.cache_data(show_spinner=False)
def story_numbers() -> dict:
    """Headline numbers on the full, unfiltered dataset (used in the hook and conclusions)."""
    acc, users = load_data()
    v = victims_only(users)
    out = kpis(acc, users)
    night = summary(v, "is_night").set_index("is_night")
    out["night_lethality"] = night.loc[True, "lethality"]
    out["day_lethality"] = night.loc[False, "lethality"]
    out["night_pct_killed"] = night.loc[True, "pct_killed"]
    area = summary(v, "area", acc).set_index("area")
    out["outside_pct_acc"] = area.loc["Outside built-up area", "pct_accidents"]
    out["outside_pct_killed"] = area.loc["Outside built-up area", "pct_killed"]
    r = roads(acc, v).set_index("road")
    out["dep_road_pct_acc"] = r.loc["Departmental road", "pct_accidents"]
    out["dep_road_pct_killed"] = r.loc["Departmental road", "pct_killed"]
    out["motorway_lethality"] = r.loc["Motorway", "lethality"]
    out["dep_road_lethality"] = r.loc["Departmental road", "lethality"]
    age = summary(v, "age_group").set_index("age_group")
    out["old_pct_victims"] = age.loc["75+", "pct_victims"]
    out["old_pct_killed"] = age.loc["75+", "pct_killed"]
    out["old_lethality"] = age.loc["75+", "lethality"]
    out["young_pct_victims"] = age.loc["18-24", "pct_victims"]
    out["adult_lethality"] = age.loc["25-34", "lethality"]
    out["covid"] = covid_comparison(v)
    out["april_drop"] = april_drop(acc)
    return out

"""Automated checks on the processed data and the dashboard's calculations.

Run from the project folder:  python scripts/validate.py
Exits with code 1 if any check fails.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DATA = ROOT / "data" / "processed"

acc = pd.read_parquet(DATA / "accidents.parquet")
users = pd.read_parquet(DATA / "users.parquet")
victims = users[users["is_victim"]]
results = []


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append(condition)
    print(f"[{'PASS' if condition else 'FAIL'}] {name}{'  (' + detail + ')' if detail else ''}")


# Integrity of the cleaned tables
check("Accident IDs are unique", acc["Num_Acc"].is_unique)
check("Every person belongs to an accident", users["Num_Acc"].isin(acc["Num_Acc"]).all())
check("Every accident has at least one victim", (acc["n_victims"] > 0).all())
check("Years are 2019-2024 only", acc["year"].between(2019, 2024).all() and users["year"].between(2019, 2024).all())
check("Hours are within 0-23", acc["hour"].dropna().between(0, 23).all())
check("Ages are within 0-105", users["age"].dropna().between(0, 105).all())
check("Killed people are counted as victims", (~users["is_killed"] | users["is_victim"]).all())
check("Map coordinates are inside mainland France",
      acc.loc[acc["coords_valid"], "lat"].between(41, 51.6).all()
      and acc.loc[acc["coords_valid"], "lon"].between(-5.6, 9.8).all())

# Consistency between the two tables (the dashboard uses both)
check("Killed: accident totals = person totals", int(acc["n_killed"].sum()) == int(users["is_killed"].sum()),
      f"{int(acc['n_killed'].sum()):,} vs {int(users['is_killed'].sum()):,}")
check("Victims: accident totals = person totals", int(acc["n_victims"].sum()) == len(victims))

# Dashboard calculations reproduce an independent computation
import streamlit.logger  # noqa: E402

streamlit.logger.set_log_level("error")  # silence "no runtime" cache warnings outside the app
from utils.prep import kpis, summary  # noqa: E402

k = kpis(acc, users)
check("KPI lethality = killed / victims x 100",
      abs(k["lethality"] - 100 * users["is_killed"].sum() / users["is_victim"].sum()) < 1e-9,
      f"{k['lethality']:.2f}")
s = summary(victims, "area", acc)
check("Group shares sum to 100%", abs(s["pct_killed"].sum() - 100) < 1e-6 and abs(s["pct_victims"].sum() - 100) < 1e-6)
check("Group totals add up to the overall total", int(s["killed"].sum()) == k["killed"])

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)

"""Exploratory analysis: test each hypothesis H1-H6 against the cleaned data.

Run from the project folder:  python scripts/explore.py
Lethality = killed per 100 victims (victims = killed + hospitalised + slightly injured).
"""
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data" / "processed"
pd.set_option("display.width", 200)
pd.set_option("display.max_rows", 60)

acc = pd.read_parquet(DATA / "accidents.parquet")
users = pd.read_parquet(DATA / "users.parquet")
victims = users[users["is_victim"]]


def summary(df_victims: pd.DataFrame, by, df_acc: pd.DataFrame | None = None) -> pd.DataFrame:
    """Victims, killed, their shares of the total, and lethality for each group."""
    g = df_victims.groupby(by, observed=True).agg(victims=("is_victim", "size"),
                                                  killed=("is_killed", "sum"))
    if df_acc is not None:
        g.insert(0, "accidents", df_acc.groupby(by, observed=True).size())
        g["%accidents"] = (100 * g["accidents"] / g["accidents"].sum()).round(1)
    g["%victims"] = (100 * g["victims"] / g["victims"].sum()).round(1)
    g["%killed"] = (100 * g["killed"] / g["killed"].sum()).round(1)
    g["lethality"] = (100 * g["killed"] / g["victims"]).round(2)
    return g


def title(text: str) -> None:
    print(f"\n{'=' * 8} {text} {'=' * 8}")


title("BASELINE")
print(f"Accidents {len(acc):,} | victims {len(victims):,} | killed {int(victims['is_killed'].sum()):,} "
      f"| lethality {100 * victims['is_killed'].mean():.2f}")

# ---------------------------------------------------------------- H1
title("H1  Deadly crashes happen mostly at night")
print(summary(victims, "is_night", acc).to_string())
print("\nBy light condition:")
print(summary(victims, "light", acc).to_string())
print("\nLethality by hour (accidents, killed, lethality):")
h = summary(victims, "hour", acc)[["accidents", "killed", "lethality"]]
print(h.T.to_string())
print("\nConfounder check - night x area (is night deadlier everywhere, or only outside towns?):")
print(summary(victims, ["area", "is_night"])[["victims", "killed", "lethality"]].to_string())
print("\nBy weekday:")
print(summary(victims, "weekday", acc)[["accidents", "killed", "%killed", "lethality"]].to_string())

# ---------------------------------------------------------------- H2
title("H2  Holidays and celebrations are deadlier")
all_days = pd.DataFrame({"date": pd.date_range("2019-01-01", "2024-12-31")})
all_days = all_days.merge(acc[["date", "day_type"]].drop_duplicates(), on="date", how="left")
all_days["day_type"] = all_days["day_type"].astype("string").fillna("Ordinary day")
n_days = all_days.groupby("day_type").size().rename("days")
d = summary(victims, "day_type", acc).join(n_days)
d["accidents/day"] = (d["accidents"] / d["days"]).round(1)
d["killed/day"] = (d["killed"] / d["days"]).round(2)
print(d[["days", "accidents/day", "killed/day", "lethality"]].sort_values("killed/day").to_string())
print("Note: festive days occur only 6 times each (one per year) - small samples, read with care.")

# ---------------------------------------------------------------- H3
title("H3  Motorways are the most dangerous roads")
print(summary(victims, "road_type", acc).sort_values("lethality", ascending=False).to_string())
print("\nBuilt-up vs outside built-up areas:")
print(summary(victims, "area", acc).to_string())
print("\nBy speed limit (km/h):")
print(summary(victims.merge(acc[["Num_Acc", "speed_limit"]], on="Num_Acc"), "speed_limit",
              acc).query("victims >= 500")[["accidents", "%killed", "lethality"]].to_string())

# ---------------------------------------------------------------- H4
title("H4  Young and elderly road users are over-represented")
print(summary(victims, "age_group").to_string())
print("\nDrivers only (involvement in accidents, incl. unharmed drivers):")
drivers = users[users["user_role"] == "Driver"]
print((drivers["age_group"].value_counts(normalize=True).sort_index() * 100).round(1).to_string())
print("\nBy mode of travel:")
print(summary(victims, "mode").sort_values("lethality", ascending=False).to_string())

# ---------------------------------------------------------------- H5
title("H5  COVID cut crash numbers, not lethality")
print(summary(victims, "year", acc).to_string())
lock = victims[victims["covid_lockdown"]]
lock_days = lock["date"].dt.strftime("%m-%d").unique()
ref = victims[(victims["year"] == 2019) & victims["date"].dt.strftime("%m-%d").isin(lock_days)]
for name, df in [("Same calendar days in 2019", ref), ("Lockdown days 2020-21", lock)]:
    print(f"{name:28s} victims {len(df):>6,}  killed {int(df['is_killed'].sum()):>5,}  "
          f"lethality {100 * df['is_killed'].mean():.2f}")
print("\nMonthly accidents, 2019 vs 2020:")
m = acc[acc["year"].isin([2019, 2020])].groupby(["month", "year"]).size().unstack()
print(m.T.to_string())

# ---------------------------------------------------------------- H6
title("H6  Severe crashes cluster in some territories")
dep = summary(victims, "dep", acc)
dep = dep[dep["victims"] >= 300]
print("Top 10 departements by number killed:")
print(dep.sort_values("killed", ascending=False).head(10)[["accidents", "killed", "lethality"]].to_string())
print("\nTop 10 by lethality (min 300 victims):")
print(dep.sort_values("lethality", ascending=False).head(10)[["victims", "killed", "lethality"]].to_string())
print("\nBottom 5 by lethality:")
print(dep.sort_values("lethality").head(5)[["victims", "killed", "lethality"]].to_string())
print(f"\nFatal accidents with valid map coordinates (metropolitan): "
      f"{int((acc['is_fatal'] & acc['coords_valid']).sum()):,}")

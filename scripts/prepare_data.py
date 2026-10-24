"""Clean and join the raw BAAC files (2019-2024) into analysis-ready tables.

Outputs in data/processed/:
  accidents.parquet       one row per accident (time, place, road, victim counts)
  users.parquet           one row per person involved (driver, passenger, pedestrian)
  quality_report.json     validation checks shown in the dashboard
  missingness.csv         share of unknown values per raw column

Run from the project folder:  python scripts/prepare_data.py
"""
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"
YEARS = range(2019, 2025)

# Bounding box of metropolitan France incl. Corsica (used to validate coordinates)
LAT_RANGE = (41.0, 51.6)
LON_RANGE = (-5.6, 9.8)

# Lockdown periods in France (used to label COVID months)
LOCKDOWNS = [("2020-03-17", "2020-05-10"), ("2020-10-30", "2020-12-14"), ("2021-04-03", "2021-05-02")]

# Code labels from the official BAAC description (2019 onwards). -1 = not recorded.
LABELS = {
    "grav": {1: "Unharmed", 2: "Killed", 3: "Hospitalised", 4: "Slightly injured"},
    "lum": {1: "Daylight", 2: "Dusk or dawn", 3: "Night, no street lighting",
            4: "Night, street lighting off", 5: "Night, street lighting on"},
    "agg": {1: "Outside built-up area", 2: "Built-up area"},
    "catr": {1: "Motorway", 2: "National road", 3: "Departmental road", 4: "Municipal road",
             5: "Off public network", 6: "Car park", 7: "Metropolitan urban road", 9: "Other"},
    "atm": {1: "Normal", 2: "Light rain", 3: "Heavy rain", 4: "Snow or hail", 5: "Fog or smoke",
            6: "Strong wind or storm", 7: "Dazzling weather", 8: "Overcast", 9: "Other"},
    "surf": {1: "Normal", 2: "Wet", 3: "Puddles", 4: "Flooded", 5: "Snow", 6: "Mud",
             7: "Icy", 8: "Grease or oil", 9: "Other"},
    "catu": {1: "Driver", 2: "Passenger", 3: "Pedestrian"},
    "sexe": {1: "Male", 2: "Female"},
}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
AGE_BINS = [-1, 13, 17, 24, 34, 44, 54, 64, 74, 120]
AGE_LABELS = ["0-13", "14-17", "18-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75+"]


# ---------------------------------------------------------------- loading
def read_table(table: str) -> pd.DataFrame:
    """Read one table for all years, harmonising column names."""
    frames = []
    for year in YEARS:
        df = pd.read_csv(RAW_DIR / f"{table}-{year}.csv", sep=";", dtype=str, encoding="utf-8")
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"Accident_Id": "Num_Acc"})  # renamed in 2022 only
        df = df.apply(lambda col: col.str.strip())
        df["file_year"] = year
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def missingness(df: pd.DataFrame, table: str) -> pd.DataFrame:
    """Share of empty or '-1' (not recorded) values per column."""
    cols = [c for c in df.columns if c not in ("Num_Acc", "file_year")]
    unknown = df[cols].isna() | df[cols].isin(["-1", ""])
    return pd.DataFrame({"table": table, "column": cols,
                         "unknown_pct": (unknown.mean() * 100).round(2).values})


def to_code(series: pd.Series) -> pd.Series:
    """Numeric code with -1 (not recorded) turned into a real missing value."""
    codes = pd.to_numeric(series, errors="coerce")
    return codes.where(codes != -1).astype("Int64")


def label(series: pd.Series, field: str) -> pd.Series:
    return series.map(LABELS[field]).fillna("Unknown").astype("category")


# ---------------------------------------------------------------- calendar
def easter_sunday(year: int) -> date:
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return date(year, month, day)


def day_type_lookup() -> dict:
    """Map each special date to a label (French public holidays + festive dates)."""
    lookup = {}
    for year in YEARS:
        easter = easter_sunday(year)
        for d in [date(year, 5, 1), date(year, 5, 8), date(year, 8, 15), date(year, 11, 1),
                  date(year, 11, 11), easter + timedelta(days=1), easter + timedelta(days=39),
                  easter + timedelta(days=50)]:
            lookup[d] = "Other public holiday"
        lookup[date(year, 7, 14)] = "French National Day (14 Jul)"
        lookup[date(year, 12, 24)] = "Christmas Eve (24 Dec)"
        lookup[date(year, 12, 25)] = "Christmas Day (25 Dec)"
        lookup[date(year, 12, 31)] = "New Year's Eve (31 Dec)"
        lookup[date(year, 1, 1)] = "New Year's Day (1 Jan)"
    return lookup


# ---------------------------------------------------------------- accidents
def build_accidents(car: pd.DataFrame, lieux: pd.DataFrame, report: dict) -> pd.DataFrame:
    acc = pd.DataFrame({"Num_Acc": car["Num_Acc"], "year": car["file_year"]})

    acc["date"] = pd.to_datetime(
        dict(year=pd.to_numeric(car["an"], errors="coerce"),
             month=pd.to_numeric(car["mois"], errors="coerce"),
             day=pd.to_numeric(car["jour"], errors="coerce")), errors="coerce")
    acc["month"] = acc["date"].dt.month.astype("Int64")
    acc["weekday"] = pd.Categorical(acc["date"].dt.dayofweek.map(dict(enumerate(WEEKDAYS))),
                                    categories=WEEKDAYS, ordered=True)
    hhmm = car["hrmn"].str.replace(":", "", regex=False).str.zfill(4)
    hour = pd.to_numeric(hhmm.str[:2], errors="coerce")
    acc["hour"] = hour.where(hour.between(0, 23)).astype("Int64")

    lookup = day_type_lookup()
    acc["day_type"] = acc["date"].dt.date.map(lookup).fillna("Ordinary day").astype("category")
    acc["covid_lockdown"] = False
    for start, end in LOCKDOWNS:
        acc.loc[acc["date"].between(start, end), "covid_lockdown"] = True

    acc["dep"] = car["dep"].str.upper()
    acc["territory"] = np.where(acc["dep"].str.startswith(("97", "98")), "Overseas", "Metropolitan")
    acc["light"] = label(to_code(car["lum"]), "lum")
    acc["is_night"] = to_code(car["lum"]).isin([3, 4, 5]).fillna(False).astype(bool)
    acc["area"] = label(to_code(car["agg"]), "agg")
    acc["weather"] = label(to_code(car["atm"]), "atm")

    lat = pd.to_numeric(car["lat"].str.replace(",", ".", regex=False), errors="coerce")
    lon = pd.to_numeric(car["long"].str.replace(",", ".", regex=False), errors="coerce")
    in_box = lat.between(*LAT_RANGE) & lon.between(*LON_RANGE)
    metro = acc["territory"] == "Metropolitan"
    acc["lat"], acc["lon"] = lat, lon
    acc["coords_valid"] = metro & in_box
    report["metro_accidents_with_invalid_coords"] = int((metro & ~in_box).sum())

    # Since 2023, an accident can have several road rows (e.g. at junctions).
    # Keep the first listed road so each accident is counted once.
    extra_rows = lieux.duplicated("Num_Acc", keep="first")
    report["lieux_extra_rows_dropped_by_year"] = (
        lieux.loc[extra_rows, "file_year"].value_counts().sort_index().astype(int)
        .rename(index=str).to_dict())
    road = lieux.loc[~extra_rows, ["Num_Acc", "catr", "vma", "surf"]].copy()
    road["road_type"] = label(to_code(road["catr"]), "catr")
    road["surface"] = label(to_code(road["surf"]), "surf")
    vma = to_code(road["vma"])
    road["speed_limit"] = vma.where(vma.between(10, 130))
    acc = acc.merge(road[["Num_Acc", "road_type", "surface", "speed_limit"]],
                    on="Num_Acc", how="left", validate="one_to_one")
    report["accidents_without_road_info"] = int(acc["road_type"].isna().sum())
    for col in ["road_type", "surface"]:
        acc[col] = acc[col].astype("string").fillna("Unknown").astype("category")
    return acc


# ---------------------------------------------------------------- users
def mode_of_travel(catu: pd.Series, catv: pd.Series) -> pd.Series:
    """Group users by how they travelled. Pedestrians first: their 'vehicle' is the one that hit them."""
    conditions = [
        catu == 3,
        catv.isin([1, 80]),                                   # bicycle, e-bike
        catv.isin([50, 60]),                                  # e-scooters / personal mobility devices
        catv.isin([2, 30, 31, 32, 33, 34, 35, 36, 41, 42, 43]),  # mopeds, motorbikes, 3-wheelers, quads
        catv == 7,                                            # car
        catv == 10,                                           # light utility vehicle
        catv.isin([13, 14, 15, 16, 17]),                      # heavy goods vehicles
        catv.isin([37, 38, 39, 40]),                          # bus, coach, train, tram
    ]
    # Missing codes make comparisons return <NA>, so treat them as "condition not met".
    conditions = [c.fillna(False).to_numpy(dtype=bool) for c in conditions]
    choices = ["Pedestrian", "Cyclist", "E-scooter", "Motorised two-wheeler", "Car",
               "Light utility vehicle", "Heavy goods vehicle", "Bus, coach or tram"]
    return pd.Series(np.select(conditions, choices, default="Other or unknown"),
                     index=catu.index, dtype="category")


def build_users(usagers: pd.DataFrame, veh: pd.DataFrame, report: dict) -> pd.DataFrame:
    report["vehicle_duplicate_keys"] = int(veh.duplicated(["Num_Acc", "id_vehicule"]).sum())
    veh = veh.drop_duplicates(["Num_Acc", "id_vehicule"])[["Num_Acc", "id_vehicule", "catv"]]
    users = usagers.merge(veh, on=["Num_Acc", "id_vehicule"], how="left", validate="many_to_one")
    report["users_without_matching_vehicle"] = int(users["catv"].isna().sum())

    grav = to_code(users["grav"])
    report["users_with_unknown_severity"] = int(grav.isna().sum())
    catu = to_code(users["catu"])
    out = pd.DataFrame({"Num_Acc": users["Num_Acc"], "year": users["file_year"]})
    out["severity"] = label(grav, "grav")
    out["is_killed"] = (grav == 2).fillna(False).astype(bool)
    out["is_hospitalised"] = (grav == 3).fillna(False).astype(bool)
    out["is_victim"] = grav.isin([2, 3, 4]).fillna(False).astype(bool)  # killed + hospitalised + slightly injured
    out["user_role"] = label(catu, "catu")
    out["mode"] = mode_of_travel(catu, to_code(users["catv"]))
    out["sex"] = label(to_code(users["sexe"]), "sexe")

    age = out["year"] - pd.to_numeric(users["an_nais"], errors="coerce")
    report["users_with_invalid_or_missing_age"] = int((~age.between(0, 105)).sum())
    out["age"] = age.where(age.between(0, 105)).astype("Int64")
    out["age_group"] = pd.cut(out["age"].astype("float"), bins=AGE_BINS, labels=AGE_LABELS)
    return out


# ---------------------------------------------------------------- main
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {}

    car, lieux = read_table("caract"), read_table("lieux")
    veh, usagers = read_table("vehicules"), read_table("usagers")

    pd.concat([missingness(car, "caract"), missingness(lieux, "lieux"),
               missingness(veh, "vehicules"), missingness(usagers, "usagers")]
              ).to_csv(OUT_DIR / "missingness.csv", index=False)

    report["raw_rows"] = {name: int(len(df)) for name, df in
                          [("caract", car), ("lieux", lieux), ("vehicules", veh), ("usagers", usagers)]}
    report["duplicate_accident_ids"] = int(car["Num_Acc"].duplicated().sum())
    report["exact_duplicate_user_rows"] = int(usagers.duplicated().sum())

    accidents = build_accidents(car, lieux, report)
    users = build_users(usagers, veh, report)
    report["users_without_matching_accident"] = int((~users["Num_Acc"].isin(accidents["Num_Acc"])).sum())

    # Victim counts per accident
    counts = users.groupby("Num_Acc").agg(
        n_users=("is_victim", "size"), n_victims=("is_victim", "sum"),
        n_killed=("is_killed", "sum"), n_hospitalised=("is_hospitalised", "sum")).reset_index()
    accidents = accidents.merge(counts, on="Num_Acc", how="left", validate="one_to_one")
    for col in ["n_users", "n_victims", "n_killed", "n_hospitalised"]:
        accidents[col] = accidents[col].fillna(0).astype("int32")
    accidents["is_fatal"] = accidents["n_killed"] > 0
    report["accidents_with_zero_victims"] = int((accidents["n_victims"] == 0).sum())

    # Add accident context to each user (for filters and 'who' analyses)
    context = ["Num_Acc", "date", "month", "weekday", "hour", "day_type", "covid_lockdown", "dep",
               "territory", "light", "is_night", "area", "road_type"]
    users = users.merge(accidents[context], on="Num_Acc", how="left", validate="many_to_one")

    # Sanity table: totals per year
    per_year = users.groupby("year").agg(victims=("is_victim", "sum"), killed=("is_killed", "sum"))
    per_year["accidents"] = accidents.groupby("year").size()
    report["totals_by_year"] = {str(y): {k: int(v) for k, v in row.items()}
                                for y, row in per_year.iterrows()}

    accidents.to_parquet(OUT_DIR / "accidents.parquet", index=False)
    users.to_parquet(OUT_DIR / "users.parquet", index=False)
    with open(OUT_DIR / "quality_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=== VALIDATION REPORT ===")
    print(json.dumps({k: v for k, v in report.items() if k != "totals_by_year"}, indent=2))
    print("\n=== TOTALS BY YEAR ===")
    print(per_year[["accidents", "victims", "killed"]].to_string())
    print(f"\nLethality (killed per 100 victims), all years: "
          f"{100 * users['is_killed'].sum() / users['is_victim'].sum():.2f}")
    print("\n=== UNKNOWN SHARE IN KEY FIELDS (%) ===")
    for col in ["light", "area", "road_type", "weather", "surface"]:
        print(f"accidents.{col:10s} {100 * (accidents[col] == 'Unknown').mean():5.2f}")
    for col in ["severity", "mode", "sex", "user_role"]:
        unknown = users[col].isin(["Unknown", "Other or unknown"]).mean()
        print(f"users.{col:14s} {100 * unknown:5.2f}")
    print(f"users.age (missing) {100 * users['age'].isna().mean():5.2f}")
    print(f"\nSaved: accidents {accidents.shape}, users {users.shape} -> {OUT_DIR}")
    for f in sorted(OUT_DIR.iterdir()):
        print(f"  {f.name:22s} {f.stat().st_size / 1e6:6.2f} MB")


if __name__ == "__main__":
    main()

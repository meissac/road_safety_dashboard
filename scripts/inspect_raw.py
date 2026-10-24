"""First look at the raw BAAC files: size, columns, schema changes, sample rows."""
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
YEARS = range(2019, 2025)
TABLES = ["caract", "lieux", "vehicules", "usagers"]

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 40)


def read_raw(path: Path) -> tuple[pd.DataFrame, str]:
    for encoding in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(path, sep=";", dtype=str, encoding=encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {path}")


frames = {}
print("=== ROWS / COLUMNS / ENCODING ===")
for table in TABLES:
    for year in YEARS:
        df, enc = read_raw(RAW_DIR / f"{table}-{year}.csv")
        frames[(table, year)] = df
        flag = "  <-- only 1 column: separator problem!" if df.shape[1] == 1 else ""
        print(f"{table:9s} {year}: {df.shape[0]:>7,} rows  {df.shape[1]:>2} cols  {enc}{flag}")

print("\n=== COLUMN NAMES (2019) AND CHANGES IN LATER YEARS ===")
for table in TABLES:
    base = list(frames[(table, 2019)].columns)
    print(f"\n{table} 2019: {base}")
    for year in YEARS:
        cols = set(frames[(table, year)].columns)
        added, removed = cols - set(base), set(base) - cols
        if added or removed:
            print(f"  {year}: added {sorted(added)}  removed {sorted(removed)}")

print("\n=== SAMPLE ROWS (2024) ===")
for table in TABLES:
    print(f"\n--- {table} 2024 ---")
    print(frames[(table, 2024)].head(3).to_string())

c24 = frames[("caract", 2024)]
print("\n=== LAT/LONG FORMAT (caract 2024) ===")
print(c24[["lat", "long"]].head(5).to_string())
print("lat values containing a comma:", c24["lat"].str.contains(",", na=False).sum())
print("lat missing:", c24["lat"].isna().sum())

print("\n=== GRAVITY CODES (usagers 2024, column 'grav') ===")
print(frames[("usagers", 2024)]["grav"].value_counts(dropna=False).to_string())
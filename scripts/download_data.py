"""Download the BAAC road-accident files (2019-2024) from data.gouv.fr into data/raw/.

Source: https://www.data.gouv.fr/datasets/53698f4ca3a729239d2036df/
Licence: Licence Ouverte / Open Licence (Etalab)
"""
import re
import sys
from pathlib import Path

import requests

DATASET_ID = "53698f4ca3a729239d2036df"
API_URL = f"https://www.data.gouv.fr/api/1/datasets/{DATASET_ID}/"
YEARS = range(2019, 2025)
TABLES = ["caract", "lieux", "vehicules", "usagers"]
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# File titles are inconsistent across years, e.g. "caract-2023.csv",
# "carcteristiques-2022.csv" (sic), "Caract_2024.csv".
TITLE_PATTERN = re.compile(r"^(caract\w*|carct\w*|lieux|vehicules|usagers)[-_](\d{4})\.csv$")


def normalise_table(prefix: str) -> str:
    return "caract" if prefix.startswith("car") else prefix


def find_resources() -> dict:
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    selected = {}
    for res in response.json()["resources"]:
        title = (res.get("title") or "").strip().lower()
        match = TITLE_PATTERN.match(title)
        if not match:
            continue
        table, year = normalise_table(match.group(1)), int(match.group(2))
        if year not in YEARS:
            continue
        key = (table, year)
        # If a file appears twice, keep the most recently modified version.
        if key not in selected or res.get("last_modified", "") > selected[key].get("last_modified", ""):
            selected[key] = res
    return selected


def download(url: str, dest: Path) -> None:
    with requests.get(url, timeout=180, stream=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    selected = find_resources()

    for year in YEARS:
        for table in TABLES:
            res = selected.get((table, year))
            if res is None:
                continue
            dest = RAW_DIR / f"{table}-{year}.csv"
            if dest.exists() and dest.stat().st_size > 0:
                print(f"[skip] {dest.name} already downloaded")
                continue
            print(f"[get ] {dest.name}  <-  {res['title']}")
            download(res["url"], dest)
            print(f"       {dest.stat().st_size / 1e6:.1f} MB")

    missing = [f"{t}-{y}" for y in YEARS for t in TABLES if (t, y) not in selected]
    if missing:
        print("\nMISSING (not found on the portal):", ", ".join(missing))
        sys.exit(1)
    print(f"\nOK: all {len(YEARS) * len(TABLES)} files are in {RAW_DIR}")


if __name__ == "__main__":
    main()

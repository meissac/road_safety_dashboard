"""Data loading (cached) and source/licence metadata."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"
ASSETS_DIR = ROOT / "assets"

SOURCE_TITLE = ("Bases de données annuelles des accidents corporels de la circulation routière "
                "– Années de 2005 à 2024")
SOURCE_URL = "https://www.data.gouv.fr/datasets/53698f4ca3a729239d2036df/"
PRODUCER = "ONISR – Ministère de l'Intérieur, via data.gouv.fr"
LICENCE = "Licence Ouverte / Open Licence (Etalab)"
GEO_SOURCE_URL = "https://github.com/gregoiredavid/france-geojson"

OVERSEAS_NAMES = {
    "971": "Guadeloupe", "972": "Martinique", "973": "Guyane", "974": "La Réunion", "975": "Saint-Pierre-et-Miquelon",
    "976": "Mayotte", "977": "Saint-Barthélemy", "978": "Saint-Martin", "986": "Wallis-et-Futuna",
    "987": "Polynésie française", "988": "Nouvelle-Calédonie",
}


def _require(path: Path) -> None:
    if not path.exists():
        st.error(f"Missing file `{path.relative_to(ROOT)}`. Run `python scripts/download_data.py` "
                 "then `python scripts/prepare_data.py` from the project folder.")
        st.stop()


@st.cache_data(show_spinner="Loading 327,000 accidents…")
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    for name in ("accidents.parquet", "users.parquet"):
        _require(DATA_DIR / name)
    accidents = pd.read_parquet(DATA_DIR / "accidents.parquet")
    users = pd.read_parquet(DATA_DIR / "users.parquet")
    for df in (accidents, users):  # label used by older processed files
        df["day_type"] = (df["day_type"].astype("string")
                          .replace("Bastille Day (14 Jul)", "French National Day (14 Jul)").astype("category"))
    return accidents, users


@st.cache_data
def load_quality() -> tuple[dict, pd.DataFrame]:
    _require(DATA_DIR / "quality_report.json")
    with open(DATA_DIR / "quality_report.json", encoding="utf-8") as f:
        report = json.load(f)
    missing = pd.read_csv(DATA_DIR / "missingness.csv")
    return report, missing


@st.cache_data
def load_geojson() -> dict:
    _require(ASSETS_DIR / "departements.geojson")
    with open(ASSETS_DIR / "departements.geojson", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def department_names() -> dict:
    names = {f["properties"]["code"]: f["properties"]["nom"] for f in load_geojson()["features"]}
    return {**names, **OVERSEAS_NAMES}

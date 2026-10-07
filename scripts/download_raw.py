"""Download the raw source files into raw/ (gitignored).

Run from the repo root:  python scripts/download_raw.py

The Olympedia historical dataset (Joseph Cheng, Kaggle, CC0) needs a Kaggle
login, so it is downloaded by hand and unzipped into archive/ (also gitignored).
Everything else is fetched here. See README.md for licences.
"""
import json
import urllib.request
import zipfile
from pathlib import Path

RAW = Path("raw")

SOURCES = {
    # Keith Galli, Olympics-Dataset (MIT), scraped from olympedia.org: birthplaces.
    "galli_bios_locs.csv": "https://raw.githubusercontent.com/KeithGalli/Olympics-Dataset/master/clean-data/bios_locs.csv",
    # Paris 2024 Olympic Summer Games, Petro Ivaniuk (Kaggle, CC BY-NC-SA 4.0).
    # Original: https://www.kaggle.com/datasets/piterfm/paris-2024-olympic-summer-games
    # Fetched from an unmodified public GitHub copy because Kaggle needs a login.
    "paris_medals.csv": "https://raw.githubusercontent.com/simjoshi/Olympic_Data_Analysis/master/medals.csv",
    "paris_medallists.csv": "https://raw.githubusercontent.com/simjoshi/Olympic_Data_Analysis/master/medallists.csv",
    "paris_medals_total.csv": "https://raw.githubusercontent.com/simjoshi/Olympic_Data_Analysis/master/medals_total.csv",
    "paris_athletes.csv": "https://raw.githubusercontent.com/simjoshi/Olympic_Data_Analysis/master/athletes.csv",
    # GeoNames gazetteer for Australia (CC BY 4.0): birthplace coordinates.
    "geonames_AU.zip": "https://download.geonames.org/export/dump/AU.zip",
    # World Bank, Population, total (SP.POP.TOTL), CC BY 4.0.
    "worldbank_population_2024.json": "https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?date=2024&format=json&per_page=400",
    # datasets/country-codes (PDDL): IOC code <-> ISO 3166 crosswalk.
    "country_codes.csv": "https://raw.githubusercontent.com/datasets/country-codes/main/data/country-codes.csv",
    # world-atlas 2.0.2 (ISC), Natural Earth 1:110m countries as TopoJSON.
    "world_countries_110m.json": "https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json",
    # Natural Earth (public domain).
    "ne_10m_admin_1_states_provinces.geojson": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson",
    "ne_110m_admin_0_countries.geojson": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson",
    "ne_50m_admin_0_countries.geojson": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson",
    "ne_10m_populated_places.geojson": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_populated_places.geojson",
}


def main():
    RAW.mkdir(exist_ok=True)
    for name, url in SOURCES.items():
        target = RAW / name
        if target.exists():
            print(f"skip   {name}")
            continue
        print(f"fetch  {name}")
        req = urllib.request.Request(url, headers={"User-Agent": "fit3179-dv2-olympics"})
        with urllib.request.urlopen(req) as resp:
            target.write_bytes(resp.read())

    with zipfile.ZipFile(RAW / "geonames_AU.zip") as z:
        z.extract("AU.txt", RAW)

    (RAW / "SOURCES.json").write_text(json.dumps(SOURCES, indent=2))
    print("done")


if __name__ == "__main__":
    main()

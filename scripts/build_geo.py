"""Build the TopoJSON map files in data/geo/ from Natural Earth.

Run from the repo root after scripts/download_raw.py:

    python scripts/build_geo.py

Needs Node.js; mapshaper is fetched on demand with npx.
"""
import json
import shutil
import subprocess
from pathlib import Path

RAW = Path("raw")
GEO = Path("data/geo")
STATES = [
    "New South Wales", "Victoria", "Queensland", "Western Australia",
    "South Australia", "Tasmania", "Australian Capital Territory", "Northern Territory",
]


def build_world():
    """world-atlas countries-110m, with an id added to Kosovo (XKX), which has none."""
    world = json.loads((RAW / "world_countries_110m.json").read_text())
    for g in world["objects"]["countries"]["geometries"]:
        if g["properties"]["name"] == "Kosovo" and "id" not in g:
            g["id"] = "XKX"
    (GEO / "world-110m.json").write_text(json.dumps(world, separators=(",", ":")))


def build_states():
    """The eight Australian states and territories from Natural Earth 1:10m admin-1."""
    admin1 = json.loads((RAW / "ne_10m_admin_1_states_provinces.geojson").read_text(encoding="utf8"))
    feats = [
        {"type": "Feature", "properties": {"state": f["properties"]["name"]}, "geometry": f["geometry"]}
        for f in admin1["features"]
        if f["properties"]["adm0_a3"] == "AUS" and f["properties"]["name"] in STATES
    ]
    assert len(feats) == len(STATES), [f["properties"]["state"] for f in feats]
    tmp = RAW / "aus_states.geojson"
    tmp.write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    subprocess.run(
        [npx, "--yes", "mapshaper@0.6", str(tmp),
         "-simplify", "10%", "keep-shapes",
         "-filter-islands", "min-area=50km2",
         "-rename-layers", "states",
         "-o", str(GEO / "aus-states.json"), "format=topojson", "quantization=1e5"],
        check=True,
    )


def main():
    GEO.mkdir(parents=True, exist_ok=True)
    build_world()
    build_states()
    for f in sorted(GEO.iterdir()):
        print(f"{f}  {f.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()

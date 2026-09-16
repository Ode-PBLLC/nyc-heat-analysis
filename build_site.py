#!/usr/bin/env python3
"""Bundle each visualization's data files into site/bundle.js so index.html loads them without fetch().

    python3 build_site.py

Browsers block fetch() for pages opened from disk; a plain <script> tag is not blocked. The JSON and GeoJSON
files in each */data/ directory remain the source of truth; edit those (or rerun the build scripts), then rerun this.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = [
    "01_heat_vulnerability_map/data/layers.json",
    "01_heat_vulnerability_map/data/boroughs.geojson",
    "01_heat_vulnerability_map/data/neighborhoods.geojson",
    "01_heat_vulnerability_map/data/council_districts.geojson",
    "02_no_working_ac/data/ac_status.json",
    "03_days_at_or_above_90f/data/days_at_or_above_90f.json",
    "04_heat_vulnerability_overlap/data/modzcta_bivariate.geojson",
    "04_heat_vulnerability_overlap/data/legend.json",
    "04_heat_vulnerability_overlap/data/citywide_context.json",
]

if __name__ == "__main__":
    payload = {name: json.loads((ROOT / name).read_text(encoding="utf-8")) for name in FILES}
    text = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")).replace("</", "<\\/")
    out = ROOT / "site" / "bundle.js"
    out.write_text("window.NYC_HEAT_DATA=" + text + ";\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1048576:.2f} MiB, {len(payload)} files)")

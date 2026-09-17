#!/usr/bin/env python3
"""Consistency checks: bundle matches the data directories, published counts hold, page copy is intact. Exit 1 on failure."""
import json
import re
import sys
from pathlib import Path

from build_site import FILES

ROOT = Path(__file__).resolve().parent
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


bundle_text = (ROOT / "site" / "bundle.js").read_text(encoding="utf-8")
check(bundle_text.startswith("window.NYC_HEAT_DATA="), "bundle.js must assign window.NYC_HEAT_DATA")
check("</" not in bundle_text, "bundle.js must not contain a closing-tag sequence")
bundle = json.loads(bundle_text[len("window.NYC_HEAT_DATA="):].rstrip().rstrip(";"))
check(sorted(bundle) == sorted(FILES), "bundle keys differ from build_site.FILES")
for name in FILES:
    disk = json.loads((ROOT / name).read_text(encoding="utf-8"))
    check(bundle.get(name) == disk, f"bundle entry differs from {name}")
    check(disk.get("sources"), f"{name} lacks sources")
    check(disk.get("description"), f"{name} lacks description")

d01 = "01_heat_vulnerability_map/data/"
neighborhoods = bundle[d01 + "neighborhoods.geojson"]["features"]
check(len(bundle[d01 + "boroughs.geojson"]["features"]) == 5, "expected 5 boroughs")
check(len(neighborhoods) == 262, "expected 262 neighborhoods")
check(sum(f["properties"]["HVI_RANK"] is not None for f in neighborhoods) == 197, "expected 197 scored neighborhoods")
check(len(bundle[d01 + "council_districts.geojson"]["features"]) == 51, "expected 51 council districts")
layers = bundle[d01 + "layers.json"]
check([l["id"] for l in layers["layers"]] == ["hvi", "no_ac", "black", "hispanic"], "layer ids changed")
for layer in layers["layers"]:
    allowed = set(layer["colors"]) | {layer["no_data_color"]}
    used = {f["properties"][layer["color_field"]] for f in neighborhoods}
    check(used <= allowed, f"{layer['id']} uses colors outside its ramp: {used - allowed}")
    for f in neighborhoods:
        v = f["properties"][layer["value_field"]]
        expected = layer["no_data_color"] if v is None else layer["colors"][sum(v > cut for cut in layer["breakpoints"])]
        check(f["properties"][layer["color_field"]] == expected, f"{layer['id']} color mismatch in {f['properties']['nta2020']}")

ac = bundle["02_no_working_ac/data/ac_status.json"]
check(ac["denominator"] == 25 and ac["working_and_used"] == 0, "AC headline changed")
check([c["count"] for c in ac["categories"]] == [13, 12, 0], "AC category counts changed")

days = bundle["03_days_at_or_above_90f/data/days_at_or_above_90f.json"]["series"]
check(days[0]["observed"] and days[0]["p25"] == 17 and days[-1]["p90"] == 108, "90°F series anchors changed")
for row in days:
    check(row["p10"] <= row["p25"] <= row["p75"] <= row["p90"], f"percentiles out of order in {row['period']}")

d04 = "04_heat_vulnerability_overlap/data/"
zones = bundle[d04 + "modzcta_bivariate.geojson"]["features"]
legend = bundle[d04 + "legend.json"]
check(len(zones) == 178 and len({f["properties"]["modzcta"] for f in zones}) == 178, "expected 178 unique ZIP areas")
palette = {c for row in legend["palette"] for c in row}
for comp in legend["comparisons"]:
    classed = 0
    for f in zones:
        p = f["properties"]
        h, v = p["hvi_tercile"], p[comp["class_column"]]
        expected = legend["no_data_color"] if h is None or v is None else legend["palette"][int(h)][int(v)]
        check(p[comp["color_column"]] == expected, f"{comp['id']} color mismatch in {p['modzcta']}")
        classed += h is not None and v is not None
    check(classed == comp["classed"], f"{comp['id']} classed count {classed} != {comp['classed']}")
    check(set(f["properties"][comp["color_column"]] for f in zones) <= palette | {legend["no_data_color"]}, f"{comp['id']} palette drift")
check([c["classed"] for c in legend["comparisons"]] == [173, 177, 177], "classed totals changed")
check([c["top_right_count"] for c in legend["comparisons"]] == [3, 49, 29], "top-right counts changed")
city = bundle[d04 + "citywide_context.json"]
check(city["applications_2025"] == 26606 and city["application_areas_included"] == 173, "application benchmark changed")
check(city["population_2020"] == 8804190 and city["hvi_scored_neighborhoods"] == 197, "citywide Census inputs changed")
apps_in = sum(int(line.split(",")[1]) for line in (ROOT / "inputs" / "dss_applications_2025_by_modzcta.csv").read_text().splitlines()[1:])
check(apps_in == 26606, f"aggregated application input sums to {apps_in}, expected 26606")

html = (ROOT / "index.html").read_text(encoding="utf-8")
check(re.findall(r'data-step="([a-z_]+)"', html) == ["boroughs", "no_ac", "hvi", "black", "hispanic", "council"], "scroll steps changed")
for text in ["No working air conditioning in use", "Number of Days At or Above 90°F", "Where Heat Vulnerability Overlaps", "Data + Resources",
             'src="site/bundle.js"', 'src="site/main.js"', 'href="site/style.css"']:
    check(text in html, f"index.html missing: {text}")
check("<table" not in html, "no static tables belong in index.html")

# Provenance and scope: the DSS workbook and derived denial tables are not part of this repository.
check(all("dcp_decennial" in p.name for p in ROOT.rglob("*.xlsx")), "unexpected workbook in repository")
DIRS = ["01_heat_vulnerability_map", "02_no_working_ac", "03_days_at_or_above_90f", "04_heat_vulnerability_overlap"]
for name in ["README.md", "inputs/README.md", "geometry/README.md", "common.py", "build_site.py", "figures.py", "run_notebooks.py",
             "04_heat_vulnerability_overlap/aggregate_dss.ipynb"] + [f"{d}/README.md" for d in DIRS] + [f"{d}/analysis.ipynb" for d in DIRS]:
    check((ROOT / name).exists(), f"missing {name}")
# Notebooks are the analysis code: they must be saved with executed, error-free outputs.
for path in sorted(ROOT.glob("*/*.ipynb")):
    notebook = json.loads(path.read_text(encoding="utf-8"))
    code_cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]
    check(all(c.get("execution_count") for c in code_cells), f"{path.relative_to(ROOT)} has unexecuted code cells")
    check(not any(o.get("output_type") == "error" for c in code_cells for o in c.get("outputs", [])), f"{path.relative_to(ROOT)} has error outputs")
for fig in ["01_heat_vulnerability_map/figures/hvi.png", "02_no_working_ac/figures/ac_status.png",
            "03_days_at_or_above_90f/figures/days_at_or_above_90f.png", "04_heat_vulnerability_overlap/figures/black.png"]:
    check((ROOT / fig).exists(), f"missing figure {fig}")

if failures:
    print("\n".join("FAIL " + f for f in failures))
    sys.exit(1)
print(f"OK: {len(FILES)} bundled files match their data directories; counts, colors and page copy verified")

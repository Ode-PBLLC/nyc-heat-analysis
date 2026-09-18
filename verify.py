#!/usr/bin/env python3
"""Independent checks on the committed data, the page and the notebooks. Exit 1 on any failure.

    python3 verify.py            # recompute classes, rates and totals from the data files and inputs; check the page
    python3 verify.py --execute  # also re-run the four analysis notebooks and require the data files to be unchanged

The default mode does not trust stored classes or colors: it re-derives them from values and legend edges, rebuilds
rates from counts, reconciles application counts by area against inputs/, and compares published values against the
pinned source files. It does not prove the notebooks are fresh; --execute does (it needs the notebook dependencies).
"""
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

from build_site import FILES

ROOT = Path(__file__).resolve().parent
DIRS = ["01_heat_vulnerability_map", "02_no_working_ac", "03_days_at_or_above_90f", "04_heat_vulnerability_overlap"]
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def read_csv(relative, **kwargs):
    with (ROOT / relative).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, **kwargs))


def bin_index(value, cuts):
    """Upper-inclusive bins: a value greater than a breakpoint enters the next bin."""
    return sum(value > cut for cut in cuts)


def tercile_index(value, edges):
    """Right-inclusive terciles with the minimum included, matching pandas.cut(..., include_lowest=True)."""
    if value <= edges[1]:
        return 0
    return 1 if value <= edges[2] else 2


# ---- bundle packaging ------------------------------------------------------------------------------------------------
bundle_text = (ROOT / "site" / "bundle.js").read_text(encoding="utf-8")
check(bundle_text.startswith("window.NYC_HEAT_DATA="), "bundle.js must assign window.NYC_HEAT_DATA")
check("</" not in bundle_text, "bundle.js must not contain a closing-tag sequence")
bundle = json.loads(bundle_text[len("window.NYC_HEAT_DATA="):].rstrip().rstrip(";"))
check(sorted(bundle) == sorted(FILES), "bundle keys differ from build_site.FILES")
for name in FILES:
    disk = read_json(name)
    check(bundle.get(name) == disk, f"bundle entry differs from {name}")
    check(disk.get("sources") and disk.get("description"), f"{name} lacks sources or description")

# ---- 01: neighborhoods against the pinned HVI and Census inputs -------------------------------------------------
d01 = "01_heat_vulnerability_map/data/"
neighborhoods = read_json(d01 + "neighborhoods.geojson")["features"]
layers = read_json(d01 + "layers.json")
check(len(read_json(d01 + "boroughs.geojson")["features"]) == 5, "expected 5 boroughs")
check(len(read_json(d01 + "council_districts.geojson")["features"]) == 51, "expected 51 council districts")
check(len(neighborhoods) == 262 and len({f["properties"]["nta2020"] for f in neighborhoods}) == 262, "expected 262 unique neighborhoods")
hvi_rows = {}
for row in read_csv("inputs/hvi_nta2020.csv"):
    rank = float(row["HVI_RANK"]) if row["HVI_RANK"] else None
    ac = float(row["PCT_HOUSEHOLDS_AC"]) if row["PCT_HOUSEHOLDS_AC"] else None
    if row["NTACode"] in hvi_rows:
        check(hvi_rows[row["NTACode"]] == (rank, ac), f"duplicate HVI rows disagree for {row['NTACode']}")
    hvi_rows[row["NTACode"]] = (rank, ac)
scored = 0
for f in neighborhoods:
    p = f["properties"]
    rank, ac = hvi_rows.get(p["nta2020"], (None, None))
    check(p["HVI_RANK"] == rank, f"HVI rank differs from input for {p['nta2020']}")
    if ac is not None:
        check(abs(p["pct_households_no_ac"] - (100 - ac)) < 1e-9, f"No-AC share not 100 - input for {p['nta2020']}")
    scored += p["HVI_RANK"] is not None
    pop = p["population_2020"]
    for share, count in [("pct_black_nh", "black_non_hispanic_count"), ("pct_hispanic", "hispanic_count")]:
        expected = None if not pop else round(p[count] / pop * 100, 1)
        check(p[share] == expected or (expected is not None and abs(p[share] - expected) < 0.051), f"{share} not count/population for {p['nta2020']}")
check(scored == 197, f"expected 197 scored neighborhoods, found {scored}")
check(sum(f["properties"]["population_2020"] for f in neighborhoods) == 8804190, "NTA populations must sum to the 2020 NYC total")
check([l["id"] for l in layers["layers"]] == ["hvi", "no_ac", "black", "hispanic"], "layer ids changed")
for layer in layers["layers"]:
    for f in neighborhoods:
        v = f["properties"][layer["value_field"]]
        expected = layer["no_data_color"] if v is None else layer["colors"][bin_index(v, layer["breakpoints"])]
        check(f["properties"][layer["color_field"]] == expected, f"{layer['id']} color mismatch in {f['properties']['nta2020']}")

# ---- 02: AC status against the pinned table ------------------------------------------------------------------------
ac = read_json("02_no_working_ac/data/ac_status.json")
table2 = read_csv("inputs/dohmh_heat_report_table2_ac_status.tsv", delimiter="\t")
check([(c["label"], c["count"]) for c in ac["categories"]] == [(r["AC status"], int(r["Number"])) for r in table2], "AC categories differ from the pinned table")
check(sum(c["count"] for c in ac["categories"]) == ac["denominator"] == 25 and ac["working_and_used"] == 0, "AC headline changed")

# ---- 03: 90°F series against the pinned NPCC file ------------------------------------------------------------------
days = read_json("03_days_at_or_above_90f/data/days_at_or_above_90f.json")["series"]
column = "Number of days/year with maximum temperature at or above 90°F"
npcc = {r["Period"]: float(r[column]) for r in read_csv("inputs/npcc_extreme_events_projections.csv") if r[column] not in ("", "n/a")}
check(days[0]["observed"] and days[0]["p25"] == npcc["Baseline (1981-2010)"] == 17, "baseline differs from the pinned file")
for row in days[1:]:
    for q in (10, 25, 75, 90):
        check(row[f"p{q}"] == npcc[f"{row['period']} ({q}th Percentile)"], f"{row['period']} p{q} differs from the pinned file")
    check(row["p10"] <= row["p25"] <= row["p75"] <= row["p90"], f"percentiles out of order in {row['period']}")

# ---- 04: recompute rates, classes, colors and totals from values -------------------------------------------------
d04 = "04_heat_vulnerability_overlap/data/"
zones = read_json(d04 + "modzcta_bivariate.geojson")["features"]
legend = read_json(d04 + "legend.json")
city = read_json(d04 + "citywide_context.json")
check(len(zones) == 178 and len({f["properties"]["modzcta"] for f in zones}) == 178, "expected 178 unique ZIP areas")
apps_input = {r["modzcta"]: int(r["applications_2025"]) for r in read_csv("inputs/dss_applications_2025_by_modzcta.csv")}
check(set(apps_input) <= {f["properties"]["modzcta"] for f in zones}, "application rows must match map areas")
for f in zones:
    p = f["properties"]
    check(p["applications_2025"] == apps_input.get(p["modzcta"]), f"applications differ from input for {p['modzcta']}")
    if p["applications_2025"] is not None and p["pop_est"]:
        check(abs(p["apps_1k"] - p["applications_2025"] / p["pop_est"] * 1000) < 1e-9, f"apps_1k not applications/pop_est for {p['modzcta']}")
    expected_h = None if p["hvi_popwtd"] is None else tercile_index(p["hvi_popwtd"], legend["hvi_edges"])
    check(p["hvi_tercile"] == expected_h, f"HVI tercile not derived from value for {p['modzcta']}")
    for comp in legend["comparisons"]:
        v = p[comp["field"]]
        expected_c = None if v is None else tercile_index(v, comp["edges"])
        if expected_c is not None and comp["inverted"]:
            expected_c = 2 - expected_c
        check(p[comp["class_column"]] == expected_c, f"{comp['id']} class not derived from value for {p['modzcta']}")
        expected_color = legend["no_data_color"] if expected_h is None or expected_c is None else legend["palette"][expected_h][expected_c]
        check(p[comp["color_column"]] == expected_color, f"{comp['id']} color mismatch in {p['modzcta']}")
for comp in legend["comparisons"]:
    classed = sum(f["properties"]["hvi_tercile"] is not None and f["properties"][comp["class_column"]] is not None for f in zones)
    top_right = sum(f["properties"]["hvi_tercile"] == 2 and f["properties"][comp["class_column"]] == 2 for f in zones)
    check(classed == comp["classed"] and classed + comp["no_data"] == 178, f"{comp['id']} classed/no-data counts wrong")
    check(top_right == comp["top_right_count"], f"{comp['id']} top-right count wrong")
check([c["classed"] for c in legend["comparisons"]] == [173, 177, 177], "classed totals changed")
check([c["top_right_count"] for c in legend["comparisons"]] == [3, 50, 31], "top-right counts changed")
valid = [f["properties"] for f in zones if f["properties"]["applications_2025"] is not None and f["properties"]["pop_est"]]
apps_total, pop_total = sum(p["applications_2025"] for p in valid), sum(p["pop_est"] for p in valid)
check(city["applications_2025"] == apps_total == 26606 and city["application_areas_included"] == len(valid) == 173, "application benchmark not the sum over areas with records")
check(abs(city["apps_per_1000"] - apps_total / pop_total * 1000) < 1e-9 and city["application_population_denominator"] == pop_total, "apps_per_1000 not recomputable")
check(abs(city["pct_black_nh"] - city["black_non_hispanic_count"] / city["population_2020"] * 100) < 1e-9, "citywide Black share not count/population")
check(abs(city["pct_hispanic"] - city["hispanic_count"] / city["population_2020"] * 100) < 1e-9, "citywide Hispanic share not count/population")
check(city["population_2020"] == 8804190 and city["hvi_scored_neighborhoods"] == 197, "citywide Census inputs changed")
tc = city["tract_crosswalk"]
check(tc["tracts_total"] == tc["tracts_scored"] + tc["tracts_without_hvi"] + tc["tracts_outside_every_modzcta_with_hvi"] + tc["tracts_with_hvi_but_zero_population"], "tract accounting does not close")
hvi_rows = read_csv(d04 + "hvi_by_modzcta.csv")
check(abs(sum(float(r["pop_2020"]) for r in hvi_rows) + tc["population_outside_every_modzcta"] - 8804190) < 1, "interpolated population not conserved")
check(len(hvi_rows) == 177 and tc["population_outside_every_modzcta"] == 173, "crosswalk coverage changed")

# ---- DSS reconciliation -----------------------------------------------------------------------------------------------
totals = read_json("inputs/dss_applications_2025_totals.json")
unmatched = sum(int(r["applications_2025"]) for r in read_csv("inputs/dss_applications_2025_unmatched_zips.csv"))
check(sum(apps_input.values()) == totals["matched_to_modzcta"] == 26606, "matched applications differ from totals.json")
check(unmatched == totals["unmatched_applications"], "unmatched ZIP file disagrees with totals.json")
check(totals["with_five_digit_zip"] == totals["matched_to_modzcta"] + totals["unmatched_applications"], "matched + unmatched must equal applications with a ZIP label")
check(totals["with_five_digit_zip"] + totals["rows_without_usable_zip_label"] == totals["workbook_grand_total"], "DSS reconciliation does not close")
check(len(apps_input) == totals["modzcta_areas_with_applications"] == 173, "area count differs from totals.json")

# ---- page -----------------------------------------------------------------------------------------------------------
html = (ROOT / "index.html").read_text(encoding="utf-8")
check(re.findall(r'data-step="([a-z_]+)"', html) == ["boroughs", "no_ac", "hvi", "black", "hispanic", "council"], "scroll steps changed")
for text in ["No working air conditioning in use", "Number of Days At or Above 90°F", "Where Heat Vulnerability Overlaps", "Data + Resources",
             'src="site/bundle.js"', 'src="site/main.js"', 'href="site/style.css"', 'id="stage-table"', 'id="chart-table"', 'id="biv-table"']:
    check(text in html, f"index.html missing: {text}")
check("<table" not in html, "no static tables belong in index.html")
check("not an HVI input" not in html and "not HVI inputs" not in html, "index.html carries the retracted HVI-input claim")

# ---- repository shape -------------------------------------------------------------------------------------------------
for name in ["README.md", "inputs/README.md", "geometry/README.md", "common.py", "build_site.py", "figures.py", "run_notebooks.py",
             "04_heat_vulnerability_overlap/aggregate_dss.ipynb"] + [f"{d}/README.md" for d in DIRS] + [f"{d}/analysis.ipynb" for d in DIRS]:
    check((ROOT / name).exists(), f"missing {name}")
for fig in ["01_heat_vulnerability_map/figures/hvi.png", "02_no_working_ac/figures/ac_status.png",
            "03_days_at_or_above_90f/figures/days_at_or_above_90f.png", "04_heat_vulnerability_overlap/figures/black.png"]:
    check((ROOT / fig).exists(), f"missing figure {fig}")
for path in sorted(ROOT.glob("*/*.ipynb")):
    notebook = json.loads(path.read_text(encoding="utf-8"))
    code_cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]
    check(all(c.get("execution_count") for c in code_cells), f"{path.relative_to(ROOT)} has unexecuted code cells")
    check(not any(o.get("output_type") == "error" for c in code_cells for o in c.get("outputs", [])), f"{path.relative_to(ROOT)} has error outputs")
check(all("dcp_decennial" in p.name for p in ROOT.rglob("*.xlsx")), "unexpected workbook in repository")

# ---- optional: prove the notebooks regenerate the committed data ---------------------------------------------------
if "--execute" in sys.argv[1:] and not failures:
    data_dirs = [f"{d}/data" for d in DIRS]
    before = {p: p.read_bytes() for d in data_dirs for p in (ROOT / d).iterdir() if p.is_file()}
    subprocess.run([sys.executable, str(ROOT / "run_notebooks.py")], check=True)
    after = {p: p.read_bytes() for d in data_dirs for p in (ROOT / d).iterdir() if p.is_file()}
    changed = sorted(str(p.relative_to(ROOT)) for p in set(before) | set(after) if before.get(p) != after.get(p))
    check(not changed, "re-running the notebooks changed data files: " + ", ".join(changed))
    tracked = subprocess.run(["git", "ls-files", "--", *data_dirs], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    untracked = sorted(str(p.relative_to(ROOT)) for p in after if str(p.relative_to(ROOT)) not in tracked)
    check(not untracked, "data files not tracked by git: " + ", ".join(untracked))

if failures:
    print("\n".join("FAIL " + f for f in failures))
    sys.exit(1)
print("OK: data re-derived from values and pinned inputs; page and notebooks checked" + (" ; notebooks re-executed with unchanged outputs" if "--execute" in sys.argv[1:] else ""))

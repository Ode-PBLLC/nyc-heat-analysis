#!/usr/bin/env python3
"""Air-conditioning status among heat-stress decedents exposed to heat at home, NYC residents, 2016–2025.

Reads inputs/dohmh_heat_report_table2_ac_status.tsv (DOHMH 2026 Heat-Related Mortality Report, Table 2)
and writes data/ac_status.json and data/ac_status.csv.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import INPUTS, SOURCES, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
DENOMINATOR = 25  # Source: DOHMH 2026 Heat-Related Mortality Report, Table 2: home-exposed decedents with known AC status

rows = list(csv.DictReader((INPUTS / "dohmh_heat_report_table2_ac_status.tsv").open(encoding="utf-8"), delimiter="\t"))
categories = [{"label": r["AC status"], "count": int(r["Number"]), "percent": int(r["Percent"].rstrip("%"))} for r in rows]
assert sum(c["count"] for c in categories) == DENOMINATOR, categories
for c in categories:
    assert c["percent"] == round(c["count"] / DENOMINATOR * 100), c
working = next(c for c in categories if c["label"] == "AC working and used")

write_json(HERE / "data" / "ac_status.json", {
    "description": "Air-conditioning status among heat-stress decedents who were exposed to heat at home and whose AC status was known, New York City residents, 2016–2025. Heat-stress deaths are deaths caused directly by heat. Exposure at home does not imply death occurred at home.",
    "sources": [SOURCES["heat_report"]],
    "period": "2016–2025",
    "denominator": DENOMINATOR,
    "working_and_used": working["count"],
    "categories": categories,
    "note": "The denominator is the 25 home-exposed heat-stress decedents with known AC status, not all at-home exposures. 'AC not working or not in use' includes units present but not running; it does not mean every unit was broken.",
})
with (HERE / "data" / "ac_status.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["label", "count", "percent"])
    writer.writeheader()
    writer.writerows(categories)
print("wrote data/ac_status.csv")

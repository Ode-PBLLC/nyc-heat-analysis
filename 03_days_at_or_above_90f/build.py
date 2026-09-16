#!/usr/bin/env python3
"""Annual days with maximum temperature at or above 90°F: observed 1981–2010 baseline and NPCC model percentiles.

Reads inputs/npcc_extreme_events_projections.csv (NYC Open Data 38ps-fnsg) and writes
data/days_at_or_above_90f.json and data/days_at_or_above_90f.csv.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import INPUTS, SOURCES, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
COLUMN = "Number of days/year with maximum temperature at or above 90°F"
PERCENTILES = [10, 25, 75, 90]  # the four percentiles the source publishes; no median is published
# Horizontal positions for plotting: baseline midpoint and decade midpoints. Display only.
PERIODS = [("2030s", 2035), ("2050s", 2055), ("2080s", 2085)]

raw = pd.read_csv(INPUTS / "npcc_extreme_events_projections.csv")
baseline = float(raw.loc[raw.Period.str.startswith("Baseline"), COLUMN].iloc[0])
assert baseline == 17, baseline
series = [{"period": "Baseline (1981–2010)", "year": 1995, "observed": True, **{f"p{q}": baseline for q in PERCENTILES}}]
for decade, year in PERIODS:
    row = {"period": decade, "year": year, "observed": False}
    for q in PERCENTILES:
        row[f"p{q}"] = float(raw.loc[raw.Period == f"{decade} ({q}th Percentile)", COLUMN].iloc[0])
    assert row["p10"] <= row["p25"] <= row["p75"] <= row["p90"], row
    series.append(row)

write_json(HERE / "data" / "days_at_or_above_90f.json", {
    "description": "Days per year with maximum air temperature at or above 90°F in New York City: observed 1981–2010 baseline and model percentiles (10th, 25th, 75th, 90th) for the 2030s, 2050s and 2080s. Projections are CMIP6 models under the SSP framework as published by the NPCC. The baseline row repeats the observed value in every percentile field so a plotted range can start from it; the baseline has no model spread.",
    "sources": [SOURCES["npcc"]],
    "threshold_f": 90,
    "units": "days per year",
    "percentiles": PERCENTILES,
    "series": series,
    "plotting_note": "year values are display positions (baseline midpoint 1995; decade midpoints 2035, 2055, 2085). Percentile ranges describe model spread, not confidence intervals.",
})
pd.DataFrame(series).to_csv(HERE / "data" / "days_at_or_above_90f.csv", index=False)
print("wrote data/days_at_or_above_90f.csv")

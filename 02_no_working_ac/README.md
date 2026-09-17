# 02 · No working air conditioning in use

## Objective

Report the air-conditioning status of New York City residents who died of heat stress after being exposed
to heat at home, as published by the city's health department.

## Data

NYC Department of Health and Mental Hygiene, 2026 Heat-Related Mortality Report, Table 2, "Air conditioning
presence among heat-stress decedents exposed to heat in homes," covering 2016–2025. The pinned copy is the
report's underlying Datawrapper table, [`../inputs/dohmh_heat_report_table2_ac_status.tsv`](../inputs/README.md).

## Method

[`analysis.ipynb`](analysis.ipynb) reads the three published categories and their counts, checks that they
total the published denominator of 25 and that the published percentages equal count ÷ 25, and writes
`data/ac_status.json` and `data/ac_status.csv`. No values are derived beyond that check.

## Results

![AC status among home-exposed heat-stress decedents](figures/ac_status.png)

| AC status | Decedents | Share |
|---|---:|---:|
| No AC in home | 13 | 52% |
| AC not working or not in use | 12 | 48% |
| AC working and used | 0 | 0% |
| Total with known AC status | 25 | 100% |

## Scope

Heat-stress deaths are deaths caused directly by heat, distinct from the report's modeled estimates of
heat-exacerbated mortality. The 25 decedents are those exposed at home whose AC status was known. The
report's text, not the pinned table, supplies the wider denominator: "People who died from heat stress were
most often exposed to dangerous heat in homes (48%, n=31 of 64 records with detailed information available
about onset place)." Exposure at home does not mean death occurred at home. The category "not working or
not in use" includes units that were present but not running, so it cannot be read as "broken." The report
states that "data for 2024 and 2025 are considered provisional because death data are still being compiled
by the NYC Health Department Bureau of Vital Statistics," so the 2016–2025 counts may change.

## Files

| File | Content |
|---|---|
| `analysis.ipynb` | Executed notebook: reads the table, checks totals, writes the data files |
| `data/ac_status.json`, `data/ac_status.csv` | The three categories with counts and percentages |
| `figures/ac_status.png` | Rendering |

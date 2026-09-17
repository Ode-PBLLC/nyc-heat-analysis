# Inputs

Pinned copies of every source file used by the build scripts, as retrieved on the dates below. They are
kept here so the analysis reproduces exactly; the publishers' live datasets may change.

| File | Publisher and dataset | Link | Retrieved |
|---|---|---|---|
| `hvi_nta2020.csv` | NYC Department of Health and Mental Hygiene, Heat Vulnerability Index by 2020 Neighborhood Tabulation Area (rank 1–5 and component indicators, including percentage of households with air conditioning) | https://a816-dohbesp.nyc.gov/IndicatorPublic/data-features/hvi/ | 2026-08-21 |
| `nta2020.geojson` | NYC Open Data, 2020 Neighborhood Tabulation Areas, dataset 9nt8-h7nd | https://data.cityofnewyork.us/d/9nt8-h7nd | 2026-08-21 |
| `boroughs_dcp_26b.geojson` | NYC Department of City Planning, Borough Boundaries (water areas excluded), release 26b, dataset gthc-hcne | https://data.cityofnewyork.us/d/gthc-hcne | 2026-09-09 |
| `council_districts.geojson` | NYC Open Data, City Council Districts, dataset 872g-cjhh | https://data.cityofnewyork.us/d/872g-cjhh | 2026-08-21 |
| `dcp_decennial_census_2020.xlsx` | NYC Department of City Planning, Decennial Census data: 2020 Census Data download, workbook `nyc_decennialcensusdata_2010_2020_change-core-geographies` (sheet `2020`; columns `GeoType`, `GeoID`, `Pop1` total population, `BNH` Black non-Hispanic, `Hsp1` Hispanic of any race). The current release (`_v2`, dated June 2024 on the page) has identical values in every numeric column. | https://www.nyc.gov/content/planning/pages/resources/datasets/decennial-census · https://s-media.nyc.gov/agencies/dcp/assets/files/zip/data-tools/population/census-2020/2020-census-data.zip | 2026-08-21 |
| `modzcta.geojson` | NYC Open Data, Modified Zip Code Tabulation Areas with population estimates (`pop_est`), dataset pri4-ifjk | https://data.cityofnewyork.us/d/pri4-ifjk | 2026-08-21 |
| `tracts2020.geojson` | NYC Open Data, 2020 Census Tracts (carries the `nta2020` code of each tract), dataset 63ge-mke6 | https://data.cityofnewyork.us/d/63ge-mke6 | 2026-08-21 |
| `zcta_to_modzcta.csv` | NYC Department of Health and Mental Hygiene, ZCTA to MODZCTA crosswalk (Geography-resources) | https://github.com/nychealth/coronavirus-data | 2026-08-21 |
| `dohmh_heat_report_table2_ac_status.tsv` | NYC Department of Health and Mental Hygiene, 2026 Heat-Related Mortality Report, Table 2: air conditioning presence among heat-stress decedents exposed to heat in homes, 2016–2025 (underlying Datawrapper table) | https://a816-dohbesp.nyc.gov/IndicatorPublic/data-features/heat-report/ · https://datawrapper.dwcdn.net/GOFed/2/dataset.csv | 2026-08-21 |
| `npcc_extreme_events_projections.csv` | Mayor's Office of Climate and Environmental Justice, New York City Panel on Climate Change, New York City Climate Projections: Extreme Events and Sea Level Rise, dataset 38ps-fnsg | https://data.cityofnewyork.us/d/38ps-fnsg | 2026-08-21 |
| `dss_applications_2025_by_modzcta.csv` | NYC Department of Social Services, Cooling Assistance applications (approved plus denied) for the 2025 cooling season by ZIP code, obtained by The Margin; aggregated to modified ZIP code areas by `04_heat_vulnerability_overlap/aggregate_dss.ipynb` | not publicly posted | 2025 season |
| `dss_applications_2025_unmatched_zips.csv` | Same source: the 15 applications from 13 ZIP codes that have no modified ZIP code area (outside New York City or PO-box ZIPs), listed so nothing is dropped silently | not publicly posted | 2025 season |

The DSS workbook itself is not redistributed. It also contains approval and denial counts and denial
reasons, none of which are used here; only 2025 application totals per ZIP code enter the analysis.

"""Shared paths, source citations, palettes and writers for the per-visualization analysis notebooks."""
import json
from pathlib import Path

import shapely
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parent
INPUTS = ROOT / "inputs"
GEOMETRY = ROOT / "geometry"

# One citation string per input dataset. Retrieval dates are the dates the pinned copies in inputs/ were downloaded.
SOURCES = {
    "hvi": "NYC Department of Health and Mental Hygiene, Heat Vulnerability Index by 2020 Neighborhood Tabulation Area, Environment & Health Data Portal, https://a816-dohbesp.nyc.gov/IndicatorPublic/data-features/hvi/ (retrieved 2026-08-21)",
    "nta": "NYC Open Data, 2020 Neighborhood Tabulation Areas, dataset 9nt8-h7nd, https://data.cityofnewyork.us/d/9nt8-h7nd (retrieved 2026-08-21)",
    "boroughs": "NYC Department of City Planning, Borough Boundaries (water areas excluded), release 26b, dataset gthc-hcne, https://data.cityofnewyork.us/d/gthc-hcne (retrieved 2026-09-09)",
    "council": "NYC Open Data, City Council Districts, dataset 872g-cjhh, https://data.cityofnewyork.us/d/872g-cjhh (retrieved 2026-08-21)",
    "census": "NYC Department of City Planning, Decennial Census data, 2020 Census Data download (nyc_decennialcensusdata_2010_2020_change-core-geographies workbook; columns Pop1, BNH, Hsp1), https://www.nyc.gov/content/planning/pages/resources/datasets/decennial-census ; file https://s-media.nyc.gov/agencies/dcp/assets/files/zip/data-tools/population/census-2020/2020-census-data.zip (retrieved 2026-08-21)",
    "heat_report": "NYC Department of Health and Mental Hygiene, 2026 Heat-Related Mortality Report, Table 2 (air conditioning presence among heat-stress decedents exposed to heat in homes, 2016–2025), https://a816-dohbesp.nyc.gov/IndicatorPublic/data-features/heat-report/ ; underlying table https://datawrapper.dwcdn.net/GOFed/2/dataset.csv (retrieved 2026-08-21)",
    "npcc": "Mayor's Office of Climate and Environmental Justice, New York City Panel on Climate Change, New York City Climate Projections: Extreme Events and Sea Level Rise, NYC Open Data dataset 38ps-fnsg, https://data.cityofnewyork.us/d/38ps-fnsg (retrieved 2026-08-21)",
    "dss": "NYC Department of Social Services, Cooling Assistance application approvals and denials by ZIP code, 2025 cooling season, obtained by The Margin. The workbook is not redistributed; application counts aggregated to modified ZIP code areas are in inputs/dss_applications_2025_by_modzcta.csv",
    "modzcta": "NYC Open Data, Modified Zip Code Tabulation Areas (MODZCTA) with population estimates, dataset pri4-ifjk, https://data.cityofnewyork.us/d/pri4-ifjk (retrieved 2026-08-21)",
    "tracts": "NYC Open Data, 2020 Census Tracts, dataset 63ge-mke6, https://data.cityofnewyork.us/d/63ge-mke6 (retrieved 2026-08-21)",
    "crosswalk": "NYC Department of Health and Mental Hygiene, ZCTA to MODZCTA crosswalk, https://github.com/nychealth/coronavirus-data (Geography-resources; retrieved 2026-08-21)",
}

NO_DATA = "#bdbdbd"
# Sequential ramps: pale to Margin Red (#c60101) for HVI and No AC; pale to blue (#53b1e3) for Census shares.
RED_RAMP = ["#f5ded8", "#eeafa3", "#e47c6c", "#d84536", "#c60101"]
BLUE_RAMP = ["#e5f3fb", "#bedff4", "#94ccee", "#73bfe9", "#53b1e3"]
# Bivariate 3x3 grid, rows = HVI tercile low to high, columns = comparison tercile left to right.
BIVARIATE_PALETTE = [["#F2E5FD", "#94CCEE", "#53B1E3"], ["#E97A83", "#997EB0", "#446BAF"], ["#E93323", "#A02842", "#56287C"]]


def dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n"


def write_json(path: Path, obj) -> None:
    path.write_text(dump(obj), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def write_geojson(path: Path, frame, key: str, simplified: str, description: str, sources: list) -> None:
    """Write `frame` as GeoJSON, replacing each feature's geometry with the simplified display polygon of the same ID.

    Attribute values stay as computed from the unsimplified sources; only the coordinates change.
    """
    obj = json.loads(frame.to_json(drop_id=True, na="null"))
    display = json.loads((GEOMETRY / f"{simplified}_7pct.geojson").read_text(encoding="utf-8"))
    by_id = {f["properties"][key]: f["geometry"] for f in display["features"]}
    ids = [str(f["properties"][key]) for f in obj["features"]]
    assert len(ids) == len(set(ids)), f"duplicate {key} values in {path.name}"
    assert set(ids) == set(by_id), f"{path.name}: feature IDs differ from geometry/{simplified}_7pct.geojson"
    for feature in obj["features"]:
        feature["geometry"] = by_id[str(feature["properties"][key])]
        geom = shape(feature["geometry"])
        assert geom.is_valid and not geom.is_empty, (path.name, feature["properties"][key])
    out = {"type": "FeatureCollection", "description": description, "sources": sources,
           "crs_note": "WGS84 longitude/latitude", "simplification": display["simplification"], "features": obj["features"]}
    path.write_text(dump(out), encoding="utf-8")
    vertices = int(shapely.get_num_coordinates([shape(f["geometry"]) for f in obj["features"]]).sum())
    print(f"wrote {path.relative_to(ROOT)} ({len(obj['features'])} features, {vertices:,} vertices)")

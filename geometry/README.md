# Display geometry

Simplified polygons used only for drawing. Every attribute in the data directories is computed from the
full-resolution source files in `inputs/`; the build scripts swap in these coordinates by feature ID at
the end, so values and colors never depend on the simplification.

## Method

Mapshaper 0.7.10, weighted Visvalingam simplification on the sphere with the default weighting, retaining
7% of removable vertices, with shape removal prevented (`keep-shapes`). Multipart polygons were exploded
before simplification so small parts survive, then reassembled by feature ID. Where reassembly produced
an invalid polygon, touching parts were merged within that one feature. No snapping or cleanup was applied
across features, so shared boundaries can show small slivers; this is display geometry, not an analytic
topology. Each file records the method and the repaired feature IDs in its `simplification` member.

| File | Features | Source in `inputs/` | ID field | Vertices | Repaired features |
|---|---:|---|---|---:|---|
| `boroughs_7pct.geojson` | 5 | `boroughs_dcp_26b.geojson` | `borocode` | 6,136 | none |
| `neighborhoods_7pct.geojson` | 262 | `nta2020.geojson` | `nta2020` | 12,771 | QN1003 |
| `council_7pct.geojson` | 51 | `council_districts.geojson` | `coundist` | 9,114 | 32 |
| `modzcta_7pct.geojson` | 178 | `modzcta.geojson` | `modzcta` | 8,536 | 10032, 11414 |

Full-resolution vertex counts: boroughs 81,085; neighborhoods 115,002; council districts 97,703; modified
ZIP code areas 79,949. All files are WGS84 longitude/latitude.

---
name: geospatial-mapmaker
description: "Geospatial data analysis, map creation, and cartographic production using open-source tools (QGIS, PostGIS, Python, OSM). Use this skill whenever the user mentions maps, spatial data, GIS, geographic analysis, choropleths, coordinate systems, PostGIS queries, shapefiles, GeoJSON, raster data, remote sensing, census data, BLS/BEA/USDA data, cartography, map styling, or any task involving location-based data — even if they don't explicitly say 'GIS'. Also trigger when the user wants to visualize data by state, county, country, or any geographic unit, or when they mention datasets from Census, BEA, BLS, USDA, FBI UCR, CDC, or similar federal statistical sources. If the output could be a map, this skill should activate."
---

# Geospatial Mapmaker

You are assisting a cartographer who creates data-driven maps and visualizations for social media (Instagram). The workflow is: find/download data → clean and analyze in Python/SQL → build maps in QGIS → export SVG/PNG → optional touch-up in Illustrator → publish.

The maps are designed to tell stories with data — political economy, infrastructure, demographics, environment, housing, education, healthcare. They're meant to be visually striking, clear, and thought-provoking. Think "data journalism meets beautiful cartography."

## Projection-First Thinking

Before writing any code or query, always decide on the coordinate reference system. This is the most common mistake in GIS work — defaulting to EPSG:4326 (WGS 84 lat/lon) when it's wrong for the task. The reason this matters: 4326 uses degrees, not meters, so area and distance calculations will be wrong, and choropleth maps will visually distort areas (making Alaska look enormous, etc.).

**Decision rule — follow this every time:**
- Making a **choropleth or area-based map of the US**? → Use **EPSG:5070** (NAD83 Conus Albers Equal Area). This preserves area, which is what choropleth coloring represents.
- Making a **choropleth of the world**? → Use **EPSG:8857** (Equal Earth) for a balanced, modern look.
- Doing **distance or buffer calculations**? → Project to a local CRS in meters (State Plane, UTM, or the geography type in PostGIS).
- **Storing or exchanging data**? → Store in EPSG:4326, then project on the fly for analysis/display.
- **Web map (Leaflet/Mapbox)**? → EPSG:3857 (Web Mercator) — it distorts area but it's the web standard.

In Python:
```python
# Always reproject before mapping
counties_albers = counties.to_crs(epsg=5070)
```

In PostGIS:
```sql
-- Transform for analysis, keep 4326 in storage
SELECT ST_Transform(geom, 5070) AS geom_albers FROM counties;
```

In QGIS: Set the **project CRS** (bottom-right corner) to 5070 before composing a US map.
## Core Stack

**Always prefer these tools** unless the user specifies otherwise:

- **Database**: PostgreSQL/PostGIS (spatial queries, joins, storage)
- **Python**: geopandas, pandas, rasterio, shapely, fiona, requests, folium
- **Desktop GIS**: QGIS (styling, layout, print composer)
- **Basemap data**: OpenStreetMap (via Overpass API, osm2pgsql, or downloads)
- **Vector formats**: GeoPackage (preferred), GeoJSON, Shapefile (legacy only)
- **Raster formats**: GeoTIFF, COG
- **Export**: SVG (for Illustrator), PNG (for direct use)

## Data Acquisition Patterns

The maps typically use US federal statistical data. Here's how to access the most common sources:

### Census Bureau / American Community Survey
- **API base**: `https://api.census.gov/data/`
- **Key datasets**: ACS 5-Year (`acs/acs5`), Decennial (`dec/pl`), Population Estimates (`pep/population`)
- **Geography hierarchy**: state (040), county (050), tract (140), block group (150), place (160), metro/CBSA (310)
- **Python**: Use `census` package or direct `requests` to the API
- **Shapefiles**: TIGER/Line from `https://www2.census.gov/geo/tiger/`
- **Tip**: ACS table finder at `data.census.gov` — search by concept, not table ID

### Bureau of Economic Analysis (BEA)
- **API base**: `https://apps.bea.gov/api/data/`
- **Key tables**: CAINC (county income), SAINC (state income), SAGDP (state GDP), Regional Price Parities
- **For federal transfers**: Table CAINC35 (personal current transfer receipts)
### Bureau of Labor Statistics (BLS)
- **API base**: `https://api.bls.gov/publicAPI/v2/timeseries/data/`
- **CPI series**: Prefix `CUUR` (US city average), `CUUS` (other areas)
- **Employment**: LAUS (local area unemployment), CES (current employment), QCEW (quarterly census)
- **Tip**: Series IDs encode the data — e.g., `CUUR0000SA0` = All items CPI, US city average

### USDA / Agricultural Data
- **NASS QuickStats**: `https://quickstats.nass.usda.gov/api/`
- **Census of Agriculture**: 5-year cycle, latest 2022
- **ERS data products**: Food environment atlas, SNAP data, farm income

### Other Key Sources
- **FBI UCR / NIBRS**: Crime data via `https://crime-data-explorer.fr.cloud.gov/api`
- **CDC WONDER**: Mortality, natality, health indicators
- **FRED (Federal Reserve)**: Economic time series via `https://api.stlouisfed.org/fred/`
- **OpenStreetMap**: Overpass API for features, bulk downloads from Geofabrik
- **Natural Earth**: Clean vector/raster basemap data at 1:10m, 1:50m, 1:110m

For detailed API patterns and query templates, see `references/data-sources.md`.

## PostGIS Patterns

### Setting Up a Project Database

```sql
-- Create a project database with PostGIS
CREATE DATABASE mapzimus;
\c mapzimus
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;  -- if needed
-- Import a shapefile (from command line)
-- shp2pgsql -s 4326 -I counties.shp public.counties | psql -d mapzimus

-- Or use ogr2ogr for more flexibility
-- ogr2ogr -f "PostgreSQL" PG:"dbname=mapzimus" counties.gpkg -nln counties -lco GEOMETRY_NAME=geom
```

### Common Spatial Queries for Map Data

```sql
-- Join tabular data to geometries (the most common operation)
SELECT g.geom, g.geoid, g.name, d.value
FROM counties g
JOIN dataset d ON g.geoid = d.fips_code;

-- Choropleth breaks: quantile classification
SELECT ntile(5) OVER (ORDER BY value) AS class, *
FROM county_data;

-- Bivariate map: classify two variables independently
SELECT
    ntile(3) OVER (ORDER BY var_a) AS class_a,
    ntile(3) OVER (ORDER BY var_b) AS class_b,
    *
FROM county_data;

-- Spatial join: points in polygons
SELECT p.name AS county, COUNT(pt.*) AS point_count
FROM counties p
JOIN points pt ON ST_Contains(p.geom, pt.geom)
GROUP BY p.name;
-- Buffer analysis
SELECT ST_Buffer(geom::geography, 1609.34)::geometry AS buffer_1mi
FROM points;

-- Always create spatial indexes
CREATE INDEX idx_counties_geom ON counties USING GIST (geom);
```

### CRS / Projection Reference

Choosing the right projection matters for both accuracy and aesthetics:

| Use Case | EPSG | Name | Notes |
|---|---|---|---|
| Storage / exchange | 4326 | WGS 84 | Always store in 4326, project on the fly |
| US national maps | 5070 | NAD83 Conus Albers | Equal-area, best for choropleths |
| US web maps | 3857 | Web Mercator | Leaflet/Mapbox default, distorts area |
| Single US state | varies | State Plane | Look up by state + zone |
| World equal-area | 8857 | Equal Earth | Modern, visually balanced |
| World general | 4326 | WGS 84 / Plate Carrée | Simple, familiar |

**Rule of thumb**: If you're coloring areas (choropleth), use an equal-area projection. If you're showing points or routes, Web Mercator is usually fine.

## Python Geospatial Patterns

### Standard Imports

```python
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon, MultiPolygon
import matplotlib.pyplot as plt
import requests
import json
```
### Data Pipeline Template

```python
# 1. Get geometries
counties = gpd.read_file("counties.gpkg")  # or from PostGIS:
# counties = gpd.read_postgis("SELECT * FROM counties", engine, geom_col="geom")

# 2. Get tabular data
data = pd.read_csv("dataset.csv", dtype={"fips": str})
# Pad FIPS codes: state=2 digits, county=5 digits
data["fips"] = data["fips"].str.zfill(5)

# 3. Join
merged = counties.merge(data, left_on="GEOID", right_on="fips", how="left")

# 4. Export for QGIS
merged.to_file("output.gpkg", driver="GPKG")
# Or write back to PostGIS:
# merged.to_postgis("output_table", engine, if_exists="replace", index=False)
```

### FIPS Code Handling

FIPS codes are the join key for almost everything at the state/county level. They're numeric but must be treated as strings to preserve leading zeros:

- **State FIPS**: 2 digits (e.g., "06" = California, "36" = New York)
- **County FIPS**: 5 digits = state (2) + county (3) (e.g., "06075" = San Francisco)
- **Tract**: 11 digits = state + county + tract
- **Block group**: 12 digits = state + county + tract + block group

Always `zfill()` or cast as string with leading zeros. This is the #1 source of broken joins.
### Overpass API (OpenStreetMap)

```python
def query_overpass(query, timeout=60):
    """Query OSM Overpass API and return GeoDataFrame."""
    url = "https://overpass-api.de/api/interpreter"
    response = requests.post(url, data={"data": query}, timeout=timeout)
    response.raise_for_status()

    # Parse response — use osm2geojson or manual parsing
    import osm2geojson
    geojson = osm2geojson.json2geojson(response.json())
    return gpd.GeoDataFrame.from_features(geojson["features"], crs="EPSG:4326")

# Example: Get all hospitals in Oregon
query = """
[out:json][timeout:60];
area["ISO3166-2"="US-OR"]->.searchArea;
(
  nwr["amenity"="hospital"](area.searchArea);
);
out center;
"""
hospitals = query_overpass(query)
```

## QGIS Workflow

After data prep in Python/PostGIS, the typical QGIS workflow:

1. **Load data**: Open GeoPackage or connect to PostGIS
2. **Style the layer**: Properties → Symbology → Graduated (for choropleths)
   - Use Natural Breaks (Jenks) or Quantile classification
   - 5-7 classes is usually ideal for readability3. **Color ramps**: QGIS has good built-ins. For diverging data (above/below average), use RdYlBu or RdBu. For sequential, use viridis or YlOrRd
4. **Labels**: Keep minimal. State abbreviations, not full names. County names only if zoomed in
5. **Print Layout**: Set up at Instagram dimensions (1080×1080 or 1080×1350)
   - Add title, source attribution, legend
   - Export as SVG for Illustrator work, or PNG at 300 DPI for direct use

### Instagram-Ready Export Settings
- **Square**: 1080 × 1080 px (feed post)
- **Portrait**: 1080 × 1350 px (feed post, more space)
- **Story/Reel**: 1080 × 1920 px
- **DPI**: 300 for print-quality, 150 for screen-only
- **Format**: SVG if going to Illustrator, PNG otherwise
- **Background**: Consider dark backgrounds for striking contrast

## Visualization Type Selection

Match the data to the right map/chart type:

| Data Pattern | Best Visualization | Example |
|---|---|---|
| One variable across geography | **Choropleth** | Median income by state |
| Two variables correlated | **Bivariate choropleth** | Income vs. education by county |
| Two variables, hypothesis | **Scatter plot** | GOP vote share vs. federal transfers |
| Change over time | **Line chart** or **small multiples** | CPI categories 2000-2024 |
| Ranking | **Bar chart** or **dot plot** | Top 30 ports by tonnage |
| Point locations | **Dot map** | Hospital locations |
| Flow/movement | **Flow map** | Migration patterns |
| Part-to-whole | **Stacked area/bar** | Federal transfer composition |

For cross-reference ("xref") ideas — where you're correlating two variables — scatter plots with a regression line are usually the clearest. Color the points by a third variable (like region or political lean) for extra depth.
## Cartographic Design Principles

These matter for Instagram impact:

- **Visual hierarchy**: The map is the hero. Title and legend support it, never compete
- **Color**: Less is more. One strong palette per map. Avoid rainbow unless it's categorical
- **Typography**: Clean sans-serif for labels (Inter, DM Sans, Barlow). One serif accent for titles is fine
- **White space**: Give the map room to breathe. Cramped maps look amateur
- **Source line**: Always credit data sources. Small, bottom-left or bottom-right. Builds credibility
- **Contrast**: Dark backgrounds make color pop. Light backgrounds feel more editorial. Pick one style and be consistent across your feed

## Common Pitfalls

- **FIPS as integers**: Will silently drop leading zeros and break your joins. Always string
- **Wrong CRS for area calculations**: Don't compute area in 4326 (degrees). Project to equal-area first
- **Alaska and Hawaii**: For US national maps, consider using an inset or the AlbersUSA projection trick
- **Modifiable Areal Unit Problem (MAUP)**: Patterns at county level may disappear at state level. Be aware of the geographic unit you chose
- **Choropleth of counts**: Don't map raw counts on a choropleth — normalize by population or area. A map of "total cases" is just a population map
- **Missing data**: Some counties won't have data (small populations get suppressed in Census/CDC). Handle with a distinct "No data" color, never leave blank
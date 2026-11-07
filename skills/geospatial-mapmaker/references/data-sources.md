# Data Sources Reference

Detailed API patterns and download links for the most commonly used federal data sources in the Mapzimus workflow.

## Table of Contents
1. [Census Bureau & ACS](#census)
2. [BEA — Bureau of Economic Analysis](#bea)
3. [BLS — Bureau of Labor Statistics](#bls)
4. [FRED — Federal Reserve Economic Data](#fred)
5. [USDA](#usda)
6. [FBI Crime Data](#fbi)
7. [CDC WONDER](#cdc)
8. [Election Data](#elections)
9. [OpenStreetMap](#osm)
10. [Geometry Downloads](#geometries)

---

## Census Bureau & ACS {#census}

### API Pattern
```python
import requests

CENSUS_API_KEY = "YOUR_KEY"  # Get free at api.census.gov/data/key_signup.html
BASE = "https://api.census.gov/data"

def get_acs(year, variables, geo, key=CENSUS_API_KEY):
    """Fetch ACS 5-year data.

    Args:
        year: e.g., 2022
        variables: list of variable codes, e.g., ["B19013_001E"] (median income)
        geo: dict like {"for": "county:*", "in": "state:*"}
        key: API key
    """    url = f"{BASE}/{year}/acs/acs5"
    params = {
        "get": ",".join(["NAME"] + variables),
        "key": key,
        **geo
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    return pd.DataFrame(data[1:], columns=data[0])

# Example: Median household income by county
income = get_acs(2022, ["B19013_001E"], {"for": "county:*", "in": "state:*"})
```

### Common ACS Variables

| Variable | Description |
|---|---|
| B19013_001E | Median household income |
| B01003_001E | Total population |
| B25077_001E | Median home value |
| B15003_022E | Population with bachelor's degree |
| B15003_001E | Population 25+ (education denominator) |
| B23025_005E | Unemployed population |
| B23025_002E | Labor force (unemployment denominator) |
| B25064_001E | Median gross rent |
| B27001_001E | Health insurance coverage universe |
| DP05_0001E | Total pop (data profile, simpler) |
### TIGER/Line Shapefiles
```
# Download county boundaries
wget https://www2.census.gov/geo/tiger/TIGER2023/COUNTY/tl_2023_us_county.zip
# State boundaries
wget https://www2.census.gov/geo/tiger/TIGER2023/STATE/tl_2023_us_state.zip
# Congressional districts
wget https://www2.census.gov/geo/tiger/TIGER2023/CD/tl_2023_us_cd118.zip
```

---

## BEA — Bureau of Economic Analysis {#bea}

### API Pattern
```python
BEA_KEY = "YOUR_KEY"  # Register at apps.bea.gov/API/signup/

def get_bea(dataset, table, geo="STATE", year="ALL"):
    url = "https://apps.bea.gov/api/data/"
    params = {
        "UserID": BEA_KEY,
        "method": "GetData",
        "DataSetName": dataset,
        "TableName": table,
        "GeoFips": geo,
        "Year": year,
        "ResultFormat": "JSON"
    }
    r = requests.get(url, params=params)
    return r.json()["BEAAPI"]["Results"]["Data"]

# Personal current transfer receipts by county
transfers = get_bea("Regional", "CAINC35", geo="COUNTY", year="2022")
# Per capita personal income by state
income = get_bea("Regional", "SAINC1", geo="STATE", year="2022")
### Key BEA Tables
| Table | Content |
|---|---|
| CAINC1 | County personal income summary |
| CAINC35 | Personal current transfer receipts (federal transfers) |
| SAINC1 | State personal income summary |
| SAGDP2N | State GDP by industry |
| SARPP | State regional price parities |

---

## BLS — Bureau of Labor Statistics {#bls}

### API Pattern
```python
BLS_KEY = "YOUR_KEY"  # Register at bls.gov/developers/

def get_bls(series_ids, start_year, end_year, key=BLS_KEY):
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    payload = {
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year),
        "registrationkey": key
    }
    r = requests.post(url, json=payload)
    return r.json()["Results"]["series"]

# CPI All Items, US City Average
cpi = get_bls(["CUUR0000SA0"], 2000, 2024)
```

### CPI Series ID Structure
`CU UR 0000 SA0`
- CU = CPI
- U = not seasonally adjusted (S = seasonally adjusted)
- R = current (S = revised)
- 0000 = US city average (regional codes vary)
- SA0 = All items (SA0E = Energy, SAF = Food, SAH = Housing, etc.)
### Common CPI Series
| Series ID | Item |
|---|---|
| CUUR0000SA0 | All items |
| CUUR0000SAF1 | Food at home |
| CUUR0000SEFV | Food away from home |
| CUUR0000SAH1 | Shelter |
| CUUR0000SETA01 | New vehicles |
| CUUR0000SETA02 | Used vehicles |
| CUUR0000SETB01 | Gasoline |
| CUUR0000SAM1 | Medical care |
| CUUR0000SEMC01 | Hospital services |
| CUUR0000SEMF01 | Prescription drugs |
| CUUR0000SS4501 | Car insurance |

---

## FRED — Federal Reserve Economic Data {#fred}

### API Pattern
```python
FRED_KEY = "YOUR_KEY"  # Register at fred.stlouisfed.org/docs/api/api_key.html

def get_fred(series_id, start="2000-01-01", key=FRED_KEY):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": key,
        "observation_start": start,
        "file_type": "json"
    }
    r = requests.get(url, params=params)
    return pd.DataFrame(r.json()["observations"])

# Federal funds rate
fed_rate = get_fred("FEDFUNDS")
# Household debt to GDP
debt = get_fred("HDTGPDUSQ163N")
### Useful FRED Series
| Series | Description |
|---|---|
| FEDFUNDS | Federal funds rate |
| CPIAUCSL | CPI for all urban consumers |
| UNRATE | Unemployment rate |
| MORTGAGE30US | 30-year fixed mortgage rate |
| DRCCLACBS | Credit card delinquency rate |
| TOTALSL | Total student loans outstanding |
| MSPUS | Median sales price of houses |

---

## USDA {#usda}

### NASS QuickStats API
```python
NASS_KEY = "YOUR_KEY"  # Request at quickstats.nass.usda.gov/api

def get_nass(**kwargs):
    url = "https://quickstats.nass.usda.gov/api/api_GET/"
    params = {"key": NASS_KEY, **kwargs}
    r = requests.get(url, params=params)
    return pd.DataFrame(r.json()["data"])

# Corn production by state, 2023
corn = get_nass(commodity_desc="CORN", statisticcat_desc="PRODUCTION",
                agg_level_desc="STATE", year=2023)
```

### SNAP Data
- Monthly state-level: `https://www.fns.usda.gov/pd/supplemental-nutrition-assistance-program-snap`
- County-level: SAIPE (Census Small Area Income and Poverty Estimates)

---

## FBI Crime Data {#fbi}

### Crime Data Explorer API
```python
def get_fbi_crime(state_abbrev, offense, start_year, end_year):
    url = f"https://api.usa.gov/crime/fbi/cde/estimate/state/{state_abbrev}/{offense}"
    params = {"from": start_year, "to": end_year, "API_KEY": "YOUR_KEY"}
    r = requests.get(url, params=params)
    return r.json()

# Also available as bulk CSV downloads:
# https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/downloads
```

---

## CDC WONDER {#cdc}

CDC WONDER doesn't have a clean REST API — it uses form-based queries. Best approach:
1. Use the web interface at `https://wonder.cdc.gov/`
2. Export as tab-delimited text
3. Parse with pandas: `pd.read_csv("file.txt", sep="\t", skiprows=...)`

Key datasets: mortality (by cause, county), natality (births), bridged-race estimates.
---

## Election Data {#elections}

### MIT Election Data + Science Lab
- **URL**: `https://electionlab.mit.edu/data`
- **County-level presidential**: CSV with FIPS, candidate, votes, total
- **Best for**: Vote margin maps, correlation analysis

### Dave Leip's Atlas / Harvard Dataverse
- More granular precinct-level data for some elections

### Joining to geometries
Election data uses FIPS codes. Join to Census TIGER county boundaries:
```python
election = pd.read_csv("county_president.csv", dtype={"county_fips": str})
counties = gpd.read_file("tl_2023_us_county.zip")
merged = counties.merge(election, left_on="GEOID", right_on="county_fips")
```

---

## OpenStreetMap {#osm}

### Overpass API Query Templates

**All of a feature type in a state:**
```
[out:json][timeout:120];
area["ISO3166-2"="US-{STATE_CODE}"]->.searchArea;
(
  nwr["{key}"="{value}"](area.searchArea);
);
out center;
```

**Within a bounding box:**
```
[out:json][timeout:60];
(
  nwr["{key}"="{value}"](south,west,north,east);
);
out geom;
```

### Bulk Downloads
- **Geofabrik**: `https://download.geofabrik.de/north-america/us.html` (state-level .osm.pbf)
- **Import to PostGIS**: `osm2pgsql -d mapzimus -C 2048 -S default.style state.osm.pbf`

---

## Geometry Downloads {#geometries}

### Quick Reference

| Geography | Best Source | Format |
|---|---|---|
| US states/counties | Census TIGER | Shapefile/GeoPackage |
| World countries | Natural Earth 1:10m | Shapefile/GeoJSON |
| US congressional districts | Census TIGER | Shapefile |
| Metro areas (CBSA) | Census TIGER | Shapefile |
| ZIP code areas (ZCTA) | Census TIGER | Shapefile |
| US counties (simplified) | Census Cartographic Boundaries | Shapefile (smaller file) |

### Cartographic vs. TIGER Boundaries
- **TIGER**: Full resolution, includes coastline/water. Larger files. Use for analysis
- **Cartographic Boundaries**: Simplified, clipped to shoreline. Smaller files. Better for choropleths — use the `cb_*_500k` files

```
# Cartographic boundary files (better for maps)
wget https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_county_500k.zip
wget https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_500k.zip
```
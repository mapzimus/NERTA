import pandas as pd, geopandas as gpd
from shapely.geometry import Point
tr=gpd.read_file("zip://dl/tracts.zip").to_crs(26919)
p=pd.read_csv("dl/tr_pop.txt",dtype=str,encoding="utf-8-sig"); p["GEOID"]="25"+p.COUNTYFP+p.TRACTCE; p["POP"]=p.POPULATION.astype(int)
w=pd.read_csv("dl/wac.csv.gz",dtype={"w_geocode":str},usecols=["w_geocode","C000"]); w["GEOID"]=w.w_geocode.str[:11]; j=w.groupby("GEOID").C000.sum()
tr=tr.merge(p[["GEOID","POP"]],on="GEOID",how="left"); tr["JOBS"]=tr.GEOID.map(j).fillna(0); tr["A"]=tr.area
def walk(g,r):
    c=g.buffer(r*1609.34); t=tr[tr.intersects(c)]; a=t.intersection(c).area/t.A
    return int((t.POP*a).sum()),int((t.JOBS*a).sum())
for n,(la,lo) in {"Burlington Mall":(42.4840,-71.2140),"Northwest Park, Burlington":(42.4910,-71.1960),"Woburn Mall/Anderson":(42.5040,-71.1370),"Woburn Center":(42.4793,-71.1523),"Seaver St at Blue Hill Ave":(42.3077,-71.0853),"Wyoma Sq":(42.4770,-70.9580),"Thompson Sq":(42.3760,-71.0610)}.items():
    g=gpd.GeoSeries([Point(lo,la)],crs=4326).to_crs(26919).iloc[0]
    print(n,"half mile",walk(g,.5),"one mile",walk(g,1),"two miles",walk(g,2))

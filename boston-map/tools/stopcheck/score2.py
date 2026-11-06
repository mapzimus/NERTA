import json, pandas as pd, geopandas as gpd, numpy as np
from shapely.geometry import Point
st=gpd.read_file(r"D:/REPOS/30dmc-day08/days/08-utopia/data/mbta_stops.gpkg").to_crs(26919).drop_duplicates("name").set_index("name")
tr=gpd.read_file("zip://dl/tracts.zip").to_crs(26919)
p=pd.read_csv("dl/tr_pop.txt",dtype=str,encoding="utf-8-sig"); p["GEOID"]="25"+p.COUNTYFP+p.TRACTCE; p["POP"]=p.POPULATION.astype(int)
w=pd.read_csv("dl/wac.csv.gz",dtype={"w_geocode":str},usecols=["w_geocode","C000"]); w["GEOID"]=w.w_geocode.str[:11]; j=w.groupby("GEOID").C000.sum()
tr=tr.merge(p[["GEOID","POP"]],on="GEOID",how="left"); tr["JOBS"]=tr.GEOID.map(j).fillna(0); tr["A"]=tr.area
def walk(g):
    c=g.buffer(804.7); t=tr[tr.intersects(c)]; a=t.intersection(c).area/t.A
    return int((t.POP*a).sum()),int((t.JOBS*a).sum())
print("MBTA stops file names sample:",[n for n in st.index if any(k in n for k in ("Reading","Wakefield","Belmont","Waltham","Salem","Hersey","Concord"))])
sub=st[st.routes.astype(str).str.contains("Red|Orange|Blue|Green|Mattapan")].geometry
base=np.array([sum(walk(g)) for g in sub])
pc=lambda v:int((base<v).mean()*100)
print("--- existing commuter stops used for new subway stops")
for n in ("Reading","Wakefield","Greenwood","Melrose Highlands","Wyoming Hill","Waverley","Belmont","Waltham","West Medford","Roslindale Village","Bellevue","Highland","West Roxbury","Hersey","Needham Junction","Needham Heights","Needham Center","Hyde Park","Lynn Interim","Readville","Concord","Salem","Framingham","Wellesley Square","Beverly"):
    if n in st.index:
        a,b=walk(st.geometry[n]); print(f"{n}: {a}+{b}={a+b} p{pc(a+b)}")
    else: print(n,"not in file")
H={"South Weymouth":(42.1554,-70.9530),"Weymouth Landing":(42.2210,-70.9680)}
print("--- hand-located centers and candidates")
g=gpd.GeoSeries([Point(v[1],v[0]) for v in H.values()],index=list(H),crs=4326).to_crs(26919)
for n,x in g.items():
    a,b=walk(x); print(f"{n}: {a}+{b}={a+b} p{pc(a+b)}")

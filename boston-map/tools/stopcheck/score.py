import json, gzip, zipfile, numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import Point
D=r"D:/REPOS/30dmc-day08/days/08-utopia/data/mbta_stops.gpkg"
geo=json.load(open("geo.json"))
hand={"Linden Sq":(42.4265,-71.0255),"Cliftondale":(42.4545,-71.0115),"West Station":(42.3575,-71.1160),"Logan Terminals":(42.3656,-71.0096),"Stadium":(42.3920,-71.0620),"Convention Center":(42.3455,-71.0450)}
pts={k:(v[1],v[0]) for k,v in geo.items() if v}
pts.update({k:(v[1],v[0]) for k,v in hand.items()})
new=gpd.GeoSeries([Point(v) for v in pts.values()],index=list(pts),crs=4326).to_crs(26919)
st=gpd.read_file(D).to_crs(26919).drop_duplicates("name").set_index("name")
print(st.columns.tolist(), st.routes.iloc[0] if "routes" in st else "")
sub=st[st.routes.astype(str).str.contains("Red|Orange|Blue|Green|Mattapan")].geometry
print("existing rapid transit stops",len(sub))
tr=gpd.read_file("zip://dl/tracts.zip").to_crs(26919)
p=pd.read_csv("dl/tr_pop.txt",dtype=str,encoding="utf-8-sig"); p.columns=[c.strip() for c in p.columns]
p["GEOID"]="25"+p.COUNTYFP+p.TRACTCE; p["POP"]=p.POPULATION.astype(int)
w=pd.read_csv("dl/wac.csv.gz",dtype={"w_geocode":str},usecols=["w_geocode","C000"]); w["GEOID"]=w.w_geocode.str[:11]; j=w.groupby("GEOID").C000.sum()
tr=tr.merge(p[["GEOID","POP"]],on="GEOID",how="left"); tr["JOBS"]=tr.GEOID.map(j).fillna(0); tr["A"]=tr.area
def walk(g):
    c=g.buffer(804.7); t=tr[tr.intersects(c)]
    a=t.intersection(c).area/t.A
    return (t.POP*a).sum(),(t.JOBS*a).sum()
base=pd.DataFrame([walk(g) for g in sub],index=sub.index,columns=["pop","jobs"]); base["all"]=base["pop"]+base["jobs"]
print("existing stops residents+jobs within 1/2 mile: p25 %d  median %d  p75 %d"%tuple(base["all"].quantile([.25,.5,.75])))
print("existing min-spacing median mi %.2f"%(np.median([sub.drop(k).distance(g).min() for k,g in sub.items()])/1609.34))
rows=[]
for n,g in new.items():
    if n=="Fort Independence": continue
    a,b=walk(g); d=sub.distance(g); near=d.idxmin()
    rows.append((n,int(a),int(b),int(a+b),int((base["all"]<a+b).mean()*100),near,round(d.min()/1609.34,2)))
df=pd.DataFrame(rows,columns=["stop","residents","jobs","total","pctile","nearest_T","mi"]).sort_values("total")
pd.set_option("display.width",140,"display.max_rows",100)
print(df.to_string(index=False))
df.to_csv("scores.csv",index=False)
# Spacing along planned order, real miles
seq={"Red Arlington":["Alewife","East Arlington","Arlington Ctr","Arlington Heights","Lexington Ctr","Lexington Route 128","Trapelo Rd","Waltham","Waverley Sq","Belmont Ctr","Alewife"],
"OL Reading":["Oak Grove","Wyoming Hill","Melrose Highlands","Greenwood","Wakefield","Reading"],
"OL Saugus":["Malden Center","Linden Sq","Cliftondale","Saugus Center","East Saugus","Wonderland"],
"OL Wash":["Tufts Medical Center","Dover","Northampton","Nubian","Four Corners","Grove Hall","Franklin Park","Wellington Hill","Mattapan"],
"OL Hyde":["Forest Hills","Hyde Park","Readville"],"OL WRox":["Forest Hills","Roslindale Village","Bellevue","Highland","West Roxbury","VFW Parkway"],
"GL Medford":["Medford/Tufts","Medford Hillside","West Medford"],"GL Watertown":["West Station","Allston","Brighton Center","Oak Sq","Newton Corner","Watertown"],
"GL Needham":["Eliot","Needham Heights","Needham Junction","Hersey","VFW Parkway"],"GL Inman":["Union Square","Inman Sq","Harvard"],
"YL":["Logan Terminals","Airport","Bellingham Sq","Chelsea","Everett Sq","Stadium","Sullivan Square","Inner Belt","Lechmere","Binney","Kendall/MIT","Mass Ave (MIT)","BU Bridge","West Station","Kenmore","Fenway","Landmark Center","Longwood Medical Area","Ruggles","Mass & Cass","Nubian","Newmarket","Boston Medical","JFK/UMass","Convention Center","Seaport","Logan Terminals"],
"CL":["Assembly","Encore","Stadium","Charlestown","Navy Yard","City Square","North Station","North End","Aquarium","Fort Point","Courthouse","Seaport","City Point","L Street","Convention Center","West Broadway","Broadway"],
"BL":["Wonderland","Lynn Harbor","Lynn"]}
def P(n):
    if n in new.index: return new[n]
    for k in (n,n.replace(" Sq"," Square"),n+" Center"):
        if k in st.index: return st.geometry[k]
    m=[i for i in st.index if i.startswith(n)]
    return st.geometry[m[0]] if m else None
for k,s in seq.items():
    print(k,[(a,round(P(a).distance(P(b))/1609.34,2)) if P(a) is not None and P(b) is not None else (a,None) for a,b in zip(s,s[1:])])

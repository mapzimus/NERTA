"""Which subway stops are accessible, from the MBTA V3 API (one keyless call). Writes data/wheelchair.csv."""
import csv
import json
import urllib.request
from pathlib import Path

URL = "https://api-v3.mbta.com/stops?filter%5Broute_type%5D=0,1&fields%5Bstop%5D=name,wheelchair_boarding"
req = urllib.request.Request(URL, headers={"User-Agent": "30dmc-day08-map", "Accept": "application/vnd.api+json"})
data = json.load(urllib.request.urlopen(req, timeout=60))["data"]
out = Path(__file__).resolve().parents[1] / "data/wheelchair.csv"
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["name", "wheelchair_boarding"])
    for d in data:
        w.writerow([d["attributes"]["name"], d["attributes"]["wheelchair_boarding"]])
print(len(data), "stops")

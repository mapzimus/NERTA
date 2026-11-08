"""Export the NERTA tram network for nerta.fun and anything else that reads it.

python export_tram_network.py   -> data/tram/tram_network.json

One entry per tram line: id (route number), name, color, terminals, branches (ordered stops), and per stop the name as
printed on the maps, lat, lon, and transfer pills (RL OL BL GL YL CL IL SL CR HSR F). Built from data/tram/tram_draft.json
(32 routes, Max, November 7 and 8). Transfer pills follow make_tmap's lines() and CR_STOPS, so commuter rail shows at
mixed stations too.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import make_tmap as M  # noqa: E402  (read only)

DAY = Path(__file__).resolve().parents[1]
TD = DAY / "data" / "tram"
CODE = {M.RED: "RL", M.ORANGE: "OL", M.BLUE: "BL", M.GREEN: "GL", M.YELLOW: "YL", M.CYAN: "CL", M.INDIGO: "IL", M.SILVER: "SL"}
ORDER = ["RL", "OL", "BL", "GL", "YL", "CL", "IL", "SL", "CR", "HSR", "F"]
HSR_STOPS = {"North Station", "Boston Central", "South Station", "Back Bay", "West Station", "Route 128"}


def station_pills():
    pills = {}
    for color, _style, _path, stops in M.lines():
        for n in stops:
            pills.setdefault(n.rstrip("+"), set()).add(CODE.get(color, "?"))
    for n, _xy, _side, _st in M.CR_STOPS:
        pills.setdefault(n.replace("\n", " ").replace(" ", ""), set()).add("CR")
    for n in HSR_STOPS:
        pills.setdefault(n, set()).add("HSR")
    return pills


def main():
    d = json.loads((TD / "tram_draft.json").read_text(encoding="utf-8"))
    sp = station_pills()
    lines = []
    for r in d["routes"]:
        stops = []
        for s in r["stops"]:
            p = set(s.get("pills", []))
            if s.get("nerta"):
                p |= sp.get(s["name"], set())
            stops.append({"name": s.get("label") or s["name"], "key": s["name"], "lat": round(s["lonlat"][1], 6), "lon": round(s["lonlat"][0], 6),
                          "station": bool(s.get("nerta")), "pills": sorted(p, key=ORDER.index) if p else [],
                          "trams": sorted(set(s.get("shared_with", [])) - {r["id"]})})
        lines.append({"id": r["id"], "name": r["name"], "via": r["via"], "color": d.get("color", "#e0457b"),
                      "terminals": [stops[0]["name"], stops[-1]["name"]], "branches": [{"name": "main", "stops": stops}],
                      "path": [[round(lat, 6), round(lon, 6)] for lon, lat in r["path"]]})
    out = {"name": "NERTA Trams", "color": d.get("color", "#e0457b"), "symbol": "white circle, pink edge, pink cross along the track",
           "service": "Driverless maglev trams, 24 hours a day, 7 days a week. Extra trams for special events. Pods on demand at every stop.",
           "lines": lines}
    (TD / "tram_network.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    n_stops = len({s["key"] for ln in lines for s in ln["branches"][0]["stops"]})
    print(f"wrote {TD / 'tram_network.json'}: {len(lines)} lines, {n_stops} distinct stops")


if __name__ == "__main__":
    main()

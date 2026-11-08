"""One update cycle for nerta.fun: re-render web maps if any map source changed, rebuild, say what changed, deploy.

    python site/tools/refresh.py            # render only if map code or renders changed since the last cycle
    python site/tools/refresh.py --render   # always render
    python site/tools/refresh.py --no-deploy

Remembers the last cycle in site/tools/.refresh_state.json (file times and the deployed network.json), so it only does the
slow render when something it depends on moved. Never writes outside site/ and boston-map/output/copies/web_vN/.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SITE = REPO / "site"
STATE = SITE / "tools" / ".refresh_state.json"
LIVE = SITE / "tools" / ".network_live.json"
PY = sys.executable
SOURCES = ["make_tmap.py", "make_line_poster.py", "make_ferry_network.py", "make_rail_poster.py", "nerta_mark.py",
           "station_kit.py", "release_tag.py"]


def mtimes():
    src = REPO / "boston-map" / "src"
    return {n: (src / n).stat().st_mtime for n in SOURCES if (src / n).exists()}


def run(args, **kw):
    print(">", " ".join(str(a) for a in args), flush=True)
    r = subprocess.run(args, cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    keep = [ln for ln in (r.stdout + r.stderr).splitlines()
            if any(w in ln for w in ("rendering", "flags", "overlaps", "stops,", "Error", "Traceback", "WARNING", "Version ID", "line "))]
    print("\n".join(keep[-12:]))
    if r.returncode:
        print((r.stdout + r.stderr)[-3000:])
        raise SystemExit(f"step failed: {args[1] if len(args) > 1 else args}")
    return r


def main():
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    now = mtimes()
    must_render = "--render" in sys.argv or now != state.get("mtimes")
    if must_render:
        run([PY, "site/tools/render_web_maps.py"])
    run([PY, "site/tools/build_assets.py"] + ([] if must_render else ["--data-only"]))
    if LIVE.exists():
        r = subprocess.run([PY, "site/tools/diff_network.py", str(LIVE), str(SITE / "data" / "network.json")], cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
        print("NETWORK CHANGES:\n" + r.stdout.strip())
    if "--no-deploy" not in sys.argv:
        npx = "npx.cmd" if sys.platform == "win32" else "npx"
        r = subprocess.run([npx, "--yes", "wrangler@latest", "deploy"], cwd=SITE, capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(next((ln for ln in r.stdout.splitlines() if "Version ID" in ln), r.stdout[-800:] + r.stderr[-800:]))
        if r.returncode:
            raise SystemExit("deploy failed")
        shutil.copyfile(SITE / "data" / "network.json", LIVE)
    STATE.write_text(json.dumps({"mtimes": now}))
    print("rendered" if must_render else "data only", "- done")


if __name__ == "__main__":
    main()

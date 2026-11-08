"""Say in plain words what changed between two builds of site/data/network.json.

    python site/tools/diff_network.py OLD.json NEW.json
"""
import json
import sys


def load(p):
    d = json.load(open(p, encoding="utf-8"))
    names = {s["id"]: s["name"] for s in d["stops"]}
    return d, names


def main(a, b):
    A, an = load(a)
    B, bn = load(b)
    out = []
    added = sorted(set(bn) - set(an), key=lambda i: bn[i])
    gone = sorted(set(an) - set(bn), key=lambda i: an[i])
    if added:
        out.append("New stops: " + ", ".join(bn[i] for i in added))
    if gone:
        out.append("Removed stops: " + ", ".join(an[i] for i in gone))
    for k in sorted(set(A["lines"]) | set(B["lines"])):
        la, lb = A["lines"].get(k), B["lines"].get(k)
        if not la:
            out.append(f"New line: {lb['name']}")
            continue
        if not lb:
            out.append(f"Removed line: {la['name']}")
            continue
        if la["legs"] != lb["legs"]:
            out.append(f"{lb['name']}: stops or order changed")
            for leg in lb["legs"]:
                if leg not in la["legs"]:
                    out.append("    now: " + " > ".join(bn[i] for i in leg))
        if la["terminals"] != lb["terminals"] or la.get("beyond") != lb.get("beyond"):
            out.append(f"{lb['name']}: ends now " + ", ".join(bn[i] for i in lb["terminals"]) +
                       (f", running on to {lb['beyond']['to']}" if lb.get("beyond") else ""))
        if la["name"] != lb["name"]:
            out.append(f"Renamed line: {la['name']} -> {lb['name']}")
    print("\n".join(out) if out else "No network changes.")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

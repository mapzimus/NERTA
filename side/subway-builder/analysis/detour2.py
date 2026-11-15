import compare as C
from detour import detour
base = C.N_SEGS
tests = {
 "66 corridor (Harvard-Allston-Coolidge-Brookline Village-Roxbury Crossing-Nubian)":
    ["Harvard", "Allston", "Coolidge Corner", "Brookline Village", "Roxbury Crossing", "Nubian"],
 "middle arc (Wellington-Medford-Alewife-Watertown-BC-Forest Hills-Fields Corner)":
    ["Wellington", "Medford/Tufts", "West Medford", "Alewife", "Watertown", "Brighton Center",
     "Boston College", "Reservoir", "Forest Hills", "Morton St", "Fields Corner"],
}
print("base", detour(base, C.NM))
for k, st in tests.items():
    print(k, detour(base + [("X", "dash", st)], C.NM))
both = base + [("X", "dash", v) for v in tests.values()]
print("both", detour(both, C.NM))

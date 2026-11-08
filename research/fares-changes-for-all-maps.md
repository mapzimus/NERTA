# Fares: Charlie Points and free rides (all maps)

Max, November 8, 2026. Applies to every map, poster and nerta.fun. Research and sources: `research/free-rides.md`.

**Code for every map:** `boston-map/src/charlie_points.py`: `draw_cp(ax, x, y, r)` draws the Charlie Points coin (a rim of every NERTA color, an ink face, and CP lettered like the T: three layers, with diagonal stripes of every color; Max, November 8); `draw_free_tag(ax, x, y, h)` draws the FREE tag (always level); `KEY_TEXT` and `FREE_TEXT` hold the Key wording. Use it rather than redrawing, so every map matches.

**Spelling:** "Charlie Points", capital P, matching nerta.fun.

## The lore

- Riders pay with **Charlie Points**, which replace the CharlieCard. They work for single trips, and there are **monthly passes** (subscriptions).
- Paying with points is the normal case, so the Key says it once. It is not marked line by line.
- Some lines and short shuttles are **free**, and they carry the FREE tag.
- As with pods, mention points casually and never explain how they work. (Note: "A Charlie line" is on the Rejected list. That was a line *named* Charlie; Charlie Points are a way to pay, so they don't conflict.)

## Key line, every map

Add one row near the service rows (e.g. under "Driverless maglev, 24 hours a day"):

> [CP coin] Pay with Charlie Points. Monthly passes available.

If a map shows any free ride, add the tag row too:

> [FREE] Free ride, no Charlie Points needed

## The FREE tag (Max picked option A)

| Part | Drawing |
|---|---|
| Shape | A small white pill with full round ends, sitting on the line (centered on it), at about mid-length of the free stretch |
| Edge | Ink `#16161a`, 1 pt |
| Text | The CP coin in the pill's left round end, then "FREE", Arial Bold, ink; cap height about 45% of the pill's height (Max: "it should say free and have the CP symbol alongside it") |
| Size | Pill about 11 pt tall so FREE reads at normal viewing size (or 1.4 times the line width if that is bigger); width to fit the text plus a half-height margin each side |
| How many | One tag per free line or stretch; a second only if the stretch is long enough that one would be lost |
| Never | On a station dot, a pill or a label. Move it along the line instead |

Mockup: `free_symbol_tall.png` in the tram session's scratchpad.

## What's free

| Free ride | Why | Maps |
|---|---|---|
| **Silver Line, the Logan shuttle**, the whole line | The real SL1 is free boarding at Logan, and Massport's airport shuttles are free (two sources each, `free-rides.md`) | Main map, Silver poster, nerta.fun |
| **Tram 23**, Washington St, Dorchester, Ashmont to Nubian | Boston's real fare-free Route 23 (City of Boston and Boston.com; free through December 31, 2026) | Tram posters, tram map, nerta.fun |
| **Fast Ferry shuttle**, Navy Yard, Langone Ferryport, Long Wharf | Short shuttle linking docks (Max's short-shuttle rule) | Main map, ferry posters, nerta.fun. Tag the shuttle only, not the North or South Shore Fast Ferry |
| **River zigzag boats** on the Charles, Mystic and Chelsea Creek | Short bank-to-bank crossings (short-shuttle rule; tram session's call) | Ferry posters, nerta.fun |

Not free: every other line, including the Orange branch on the old Route 28 corridor and the Winthrop spur. Those are tram session calls for Max to overrule. The open questions are in `free-rides.md`.

## Status by map

| Maps | Charlie Points row | FREE tags | By |
|---|---|---|---|
| Rail poster, rail station display, rail regional, 15 rail line posters | Done (re-render if made before the coin lettering change, about 12:07 Nov 8) | None needed | Rail session |
| Tram map, Tram Network poster, tram station display | In progress | Tram 23 | Tram session |
| nerta.fun | Done | Silver Line, Tram 23, Fast Ferry shuttle, zigzag boats | Website session |
| Main map, 8 line posters, ferry posters | Main session | Silver Logan shuttle (main map, Silver poster), Fast Ferry shuttle, zigzag boats | Main session |

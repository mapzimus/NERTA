---
name: mbta-style
description: Draw fantasy or real transit maps and single-line posters in the MBTA wall-poster style, using Python and matplotlib, with Illustrator as the finish. Use this whenever the user wants a subway, T, metro, rapid transit, rail network or transit line map or poster, a fantasy transit system, a transit system for a New England city, or a line diagram with transfer pills, even if they never say "MBTA style". Also use it for changes to the NERTA maps.
---

# MBTA-style transit maps

This is a house style built over dozens of revision passes on a fantasy Boston T map. It should read like a station wall poster, reward zooming in, and stay crisp with nothing overlapping.

These are fan works. The real map is a reference to compare against, never a source to copy. Any map using the T roundel says it isn't affiliated with the MBTA. Credit reads "Map: Maxwell Howe", with no handle. Keep it non-commercial unless the user has legal advice.

## Start with the network, not the drawing

1. **Research first.** Real proposals, real development plans and real stations come before fantasy. Assembled facts need 2 named sources, or get labeled unverified.
2. **For a city with no system, place stations first** by need: housing, jobs, hospitals, schools, entertainment, travel hubs, existing track. Draw lines through the stations afterward.
3. **Keep one source of truth.** A single `lines()` function holds every line as color, style, path and stops. Maps and posters both read from it, so they can't disagree.
4. **Log every new stop** with its basis and source count in an audit file, and label invented ones as invented.

## Line styles

| Style | Meaning | Drawing |
|---|---|---|
| Solid | Running today | Heaviest line |
| Striped | Real proposal | Line with a white center |
| Dashed | Imagined | Square dashes |

Commuter rail is thin and faded so subway lines lead. Its text stays dark enough to read. High-speed rail is a gold line inside the commuter line, and ferries are dotted teal. Don't change these meanings between maps. The Key must explain every symbol on the map, and the Key is worth rechecking after any new symbol appears.

## Colors

| Use | Hex |
|---|---|
| Red | `#da291c` |
| Orange | `#ed8b00` |
| Blue | `#003da5` |
| Green | `#00843d` |
| Yellow | `#f5c400` |
| Cyan | `#00a9c9` |
| Indigo | `#3f3fb5` |
| Silver | `#7c878e` |
| Commuter line | `#a98aa8` |
| Commuter text | `#80276c` |
| High-speed gold | `#ffd23f` |
| Ferry | `#2b7a9b` |
| Paper | `#fcfcfa` |
| Water | `#c9e3ee` |
| Coast | `#7fb2c6` |
| Ink | `#16161a` |

## Geometry

- Lines run on a 45-degree grid with rounded corners. Remove wobble: a line should bend only for a reason.
- Use a matplotlib figure about 18 inches wide, Arial, and data units of about 4.8 points each.
- Black edge on every dot, including ferry stops.
- Each station is drawn once. No dot sits under a pill or under text.
- The real coast comes from Census towns bent to the diagram with a thin-plate spline through hand-matched shoreline points. Hand-drawn coast was rejected. If a place falls off the frame, add anchor points to bring it in rather than cutting it.
- Route ferries over a water grid and snap stops to the shore, so tracks stay on water. Keep tracks out from behind boxes like the Key.

## Transfers

- Where two lines really cross, use a ring on the crossing. This beats a pill.
- Pills span one line gap where possible. If a pill looks long, the fix is usually to move a line or use a real crossing.
- On line posters, each transfer is a colored pill beside the station, with further pills tucked behind the first.

## Labels

- Station names use Center, St, Sq, Ave, Rd. Keep real spellings such as Newton Centre.
- Line labels at the map edge: "X LINE" first, then high-speed rows, with "TO" inline where it fits. Slash-joined names copy the MBTA, as in `FRAMINGHAM / WORCESTER LINE`.
- Terminals are bold capitals.
- A label must sit next to its own dot and never closer to another stop's dot. Check this by eye, because overlap scripts can't.
- Accessible icons sit between the stop and its name.
- No italics, except a disclaimer the user wrote.
- Only the Green Line has branch letters. Other branches are named by end station.

## Layout

Furniture sits in the corners: title top left, Key and any feature box bottom right, sources in small type at bottom right. The title block holds the roundel, title, credit, hashtag line and disclaimer.

## Checks before calling anything done

1. Run an overlap check for text against text, and for dots against dots, pills and text.
2. Check that stops aren't in the water and ferries aren't on land.
3. **Look at a zoomed crop of everything changed.** Most real bugs were found this way: labels near the wrong dot, labels clipped at the frame edge, and tracks hidden behind boxes.
4. Compare the Key against what's on the map.

## Illustrator

Open the PDF, save as `.ai`, export PNG at 200 dpi and 600 dpi. Station labels become outlines, while headings and the Key stay live text. Move any hand edits back into the code, or the next rebuild loses them.

## Code

`scripts/station_kit.py` has the drawing helpers: `rounded`, `stroke`, `transfer`, `bullet` and `label`. In the NERTA repo, `boston-map/src/make_tmap.py` is the full worked example, and `boston-map/src/make_line_poster.py` is the poster.

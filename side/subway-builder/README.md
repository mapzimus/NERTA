# Spencer's Subway Builder network

A side project, separate from NERTA. Spencer F. built a Boston network in the
game Subway Builder and asked Max to draw it in the MBTA poster style. His
files and every output stay in `private/` (gitignored) until he says they can
be shared.

## Build

```bash
cd side/subway-builder/src
python make_core.py       # subway map
python make_regional.py   # regional rail map
python make_tstyle.py     # T-style map built with the NERTA station kit
python make_posters.py    # one poster per line, plus a combined PDF
python make_hub.py        # Government Center hub diagram
```

Outputs go to `private/output/`. `analysis/` compares the network with NERTA:
`python compare.py <census folder>` with LODES and TIGER tract files.

## Where the data came from

- `network.py`: stop order for 21 subway routes, read off page 9 of his PDF
  (the game's own diagram). Transfers were checked against the game's
  ridership screen (page 7) and map pills (page 2). One source: his game.
- `layout.py`: stop positions on the schematic, also from page 9.
- Regional rail: **rebuilt, not read from a stop list.** Outer stops are the
  export points that sit on each purple line in his page 5 map. Downtown stops
  come from the numbered pills. Line numbers were matched to names by shared
  stops.

## Name changes (check with Spencer)

Spelling: Lechemere → Lechmere, Sommerville → Somerville, Ohlmsted → Olmsted,
Millenium → Millennium, Lynn Interrim → Lynn Interim, Glouchester →
Gloucester, Worchester → Worcester, Shrewsberry → Shrewsbury.
House style: Square → Sq, Street → St, MIT shortened.
Patriot Stadium → Foxborough Stadium (the NERTA rule against naming the team).
The export calls Cambridge Sq "Central Square"; the game now calls it Cambridge Square.

## Questions for Spencer

1. Route Details screenshots (like his Orange Line A page) for the 5 regional
   lines, so the regional map uses his real stop lists.
2. Brown Line North has three ends (Southside Waltham, Point Shirley,
   Marblehead). How does it actually run?
3. Line 1 seems to go West Station → Back Bay → Cambridge Sq. Is that right?
4. About 40 stops in the export have no line through them (Gallivan, Saugus,
   Swampscott, Winthrop and others). Buses, or unused?

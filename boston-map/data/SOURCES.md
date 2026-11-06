# Day 08 — Utopia: data sources

## On the map

- Today's stops and lines: MBTA V3 API, checked against OpenStreetMap (99.6% of commuter rail and 98.3% of subway within 25 m). Script: `src/fetch_mbta.py`.
- Accessibility: MBTA V3 API. One source; new stops are assumed accessible. Script: `src/fetch_access.py`.
- Coast and islands: Census TIGER/Line towns (`data/shared/ne_towns.gpkg`), bent to the diagram through matched shoreline points in `src/make_tmap.py`. Rivers are drawn by hand.
- Layout: set by hand on a 45-degree grid, so distances are not to scale.

## Behind the network

- Evidence for each new line and stop: `line_audit.md`.
- Plan history: `../research/`. `06-historic-track-map.md` paraphrases vanshnookenraggen's Boston Historic "T" Expansion Track Map (v1.0.4, 2023), which is unofficial and not for alteration or distribution without consent. Its art is not reused.
- Siting brief supplied by Max: cites the MassDOT North South Rail Link reassessment and other studies. Those underlying documents were not read directly.
- 1631 ferry note: MBTA history page (mbta.com/history) and Wikipedia, "Winnisimmet Ferry".

## Dropped versions

`src/make_map.py`, `src/make_regional.py` and their outputs also used Natural Earth 10m land and Day 2 flowlines. The final map uses neither.

## Cost figures in the Dig box

- $21.5B tunnel: MassDOT four-track Central Artery estimate, in 2028 dollars, including vehicles and upstream work. Final report Table 23 ($21.53B, `research/01-massachusetts.md`) and press reports of about $21.5B agree. Other estimates run far lower, such as Harvard's.
- $15B original Big Dig: reports give $14.6B to $14.8B; rounded. Higher figures that count interest exist and are not used.
- ~$125B whole map: our rough sum, not a sourced figure. Tunnel $21.5B, plus regional rail $40.7B (Rail Vision, 2030 dollars), plus about 110 new miles at the Green Line Extension rate of about $0.53B a mile ($2.28B over 4.3 miles). The mileage is estimated by hand. Dollar years are mixed, and high-speed trains are not counted.

## Commuter rail proposals and development (added in the final passes)

- Stoughton to Taunton stops: South Coast Rail Phase 2. Town of Bridgewater corridor map and Wikipedia agree on North Easton, Easton Village, Raynham Place and Taunton.
- Northern Tier (Fitchburg to Greenfield and North Adams): CBS Boston and Wikipedia agree this was studied. No service date.
- South Acton to Marlborough: listed in the Boston MPO long-range plan appendix. One source, unverified.
- Cape Cod via Middleborough: Buzzards Bay National Estuary Program describes the extension option. One source, unverified.
- Foxborough to Mansfield: the track is real (Framingham Secondary, Wikipedia). Regular service on it is our idea.
- Suffolk Downs drawn as a larger station: HYM says 10,000 homes; a 2020 Boston Planning release says about 7,000. The sources differ.
- Everett stadium: the City of Everett says 25,000 seats; ENR says 24,000. The sources differ.
- The ~$125B total does not include the commuter branches added in these passes.

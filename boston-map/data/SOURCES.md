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
- ~$125B whole map, 2026 dollars: our rough sum, not a sourced figure. See Cost estimate below.

## Commuter rail proposals and development (added in the final passes)

- Stoughton to Taunton stops: South Coast Rail Phase 2. Town of Bridgewater corridor map and Wikipedia agree on North Easton, Easton Village, Raynham Place and Taunton.
- Northern Tier (Fitchburg to Greenfield and North Adams): CBS Boston and Wikipedia agree this was studied. No service date.
- South Acton to Marlborough: listed in the Boston MPO long-range plan appendix. One source, unverified.
- Cape Cod via Middleborough: Buzzards Bay National Estuary Program describes the extension option. One source, unverified.
- Foxborough to Mansfield: the track is real (Framingham Secondary, Wikipedia). Regular service on it is our idea.
- Suffolk Downs drawn as a larger station: HYM says 10,000 homes; a 2020 Boston Planning release says about 7,000. The sources differ.
- Everett stadium: the City of Everett says 25,000 seats; ENR says 24,000. The sources differ.

## Cost estimate, 2026 dollars

Rough and ours. High-speed trains, ferries and buses aren't counted.

| Part | Starting figure | To 2026 dollars | Result |
|---|---|---|---|
| Tunnel | $21.5B, top of MassDOT's 2018 range, in 2028 dollars (Boston Magazine, Wikipedia) | Back two years at 3% | $20B |
| Regional rail | $29B Rail Vision, 2020 dollars | CPI, about 1.29 | $37B |
| New commuter branches | About 30 miles, hand estimated | Allowance | $1B |
| New subway lines | About 110 miles, hand estimated, at the Green Line Extension rate: $2.3B over 4.3 miles (FTA), or $0.53B a mile | CPI, about 1.14, gives $0.61B a mile | $67B |
| **Total** | | | **About $125B** |

- Original Big Dig: $14.8B final cost, 2007 (NBC News and others), times 1.61 on CPI gives about $24B. The separate $24B figure with interest is a coincidence and isn't what's shown.
- The map total is about 5 times the Big Dig: $125B divided by $24B.
- CPI: 207.3 for 2007 is confirmed. The 2026 value of 333.9 is a July reading from one third-party calculator. The 2020 and 2022 values are from memory. All of these should be rechecked against BLS.
- The panel's New miles figure, about 140, is 110 subway miles plus 30 commuter miles, both hand estimated.
- The T stops figure, 215, is 205 from `tools/audit.py` plus the 10 stops only the Logan Silver Line uses: Logan Dock, Office Center, Parking, Rental Cars and Terminals A to F. The audit reads `lines()`, and those 10 are drawn separately.

# Ferry network poster: stop audit

For `boston-map/src/make_ferry_network.py` (renders in `boston-map/output/copies/ferry_network_v*.png`).
Written November 7, 2026. Rebuilt the same night around Max's stop list (`ferry_stops.pdf`, 12 inner routes). The long-distance routes come from Max's notes 12 to 21 and the later notes (Salisbury, Carson Beach, Quincy and Quincy Point, river loops and zigzags, the Long Wharf to Navy Yard spine).

How to read the Basis column:

- **Real service**: a boat calls there today, or did recently.
- **Max's idea, real place**: from Max's list or notes. The place was found in one quick search on November 7 (source named). No ferry plan was checked.
- **Max's idea**: from Max's list or notes, place not checked.
- **Unverified**: one source or none. Every row with one source is unverified under the two-source rule.

Sources: where `boston-map/data/line_audit.md` already names two sources, they are repeated here. The November 7 quick checks used one web search per place or group of places; those rows have one source and stay **Unverified**.

## Flags for Max (November 7 rebuild)

| Item | What | Suggested |
|---|---|---|
| Gronk | Charles, Boston bank stop 3. A football player's nickname, which the house rules keep off the map. Drawn as "Gronk (rename)". | Max picks a name. |
| Route names | Max's inner route "South Shore" clashed with the high-speed "South Shore" boat. The coast boats are now "North Shore Express" and "South Shore Express". | Confirm. |
| Three things called Express | Max's Navy Yard to Long Wharf "Express", the two coast "Express" routes, and express trips that stop only at major ports. | Confirm, or rename one. |
| Columbia Point and UMass Boston | The South Shore Express stop "Columbia Point" (Fallon Pier) is the same dock as Max's "UMass Boston". Merged under Max's name. | Confirm. |
| Hingham Shipyard and Hingham | The South Shore Express stop "Hingham Shipyard" and Max's Fore River "Hingham" are drawn as one dock named Hingham. | Confirm. |
| Finigan | Probably Senator Joseph Finnegan Park at Port Norfolk, Dorchester (dotnews.com). Spelling kept as Max wrote it. | Finnegan? |
| Poormans | Not found in a search. Max lists it on the Cambridge bank between Broad Canal and Charlesgate. | Max to say where. |
| Charlesgate | A real place, but on the Boston bank where the Muddy River meets the Charles (Wikipedia, Muddy River). Max lists it on the Cambridge bank. Kept where Max put it. | Move to the Boston bank? |
| Boston Bay, Quigley, Pearl St, Addison St | Not found as waterfront places on Chelsea Creek or the Mystic. Quigley Park turned up inland at 25 Essex St, Chelsea (one map listing). | Max to say where. |
| Martins Park | The real park is "Martin's Park". Max's spelling kept. | Add the apostrophe? |
| Suffolk Downs | On Max's Chelsea Creek list. `docs/DECISIONS.md` rejects a Suffolk Downs ferry ("reopen only if one turns up"). Drawn because it is on Max's list. | Max confirms the reopening. |
| Admirals Hill | On Max's Mystic list. `line_audit.md` notes the one Chelsea site studied (Admirals Hill) was rejected by that study. Drawn because it is on Max's list. | Confirm. |
| Harbor Islands, Winthrop and Revere, Chelsea Creek | These routes share no dock with any other route on Max's list, so they float free on the poster. Harbor Islands no longer starts at Long Wharf. | Add a link dock, or leave free. |
| Dropped from the poster | Lewis Mall, Kendall, Cambridgeport, Watertown Sq, and Claude's Mystic and Chelsea Creek drafts (Draw Seven Park, Wellington, Medford Sq, Mary O'Malley Park, PORT Park, Mill Creek). Max's list replaced them. Rows kept below for the record. | None. |

## Colors (six families)

Checked with CIEDE2000 (scratchpad `ferry_build/fam.py`). Every route color is 15.7 or more from each T line, commuter purple, high-speed gold, the bus pink `#f7b8cf`, water and paper. Families are 16 or more apart; shades inside a family are 10.8 or more apart.

| Family | Routes and colors |
|---|---|
| River loops | Charles `#9e00ff`, Mystic `#cf8bff`, Chelsea Creek `#c74ae6` |
| Harbor | Harbor West `#00796d`, Express `#003d36`, East Boston `#26a69a`, Harbor Islands `#005f73` |
| South Boston, Dorchester and Quincy | Seaport `#8a4b1c`, South Shore `#b5652a`, Quincy Bay `#4a2a14`, Fore River `#a07a52` |
| North Shore | North Shore Express `#9eb000`, Winthrop and Revere `#6f7c00` |
| South Shore and the Cape | South Shore Express `#611824` |
| The Islands | Nantucket and Martha's Vineyard `#0277bd` |

Major ports (express trips stop only here): Long Wharf, Navy Yard, Lovejoy Wharf, Logan Dock, Seaport, Quincy, Hull, Salem Wharf, Gloucester, Plymouth Rock, Provincetown, Hyannis, Woods Hole, New Bedford, Vineyard Haven, Nantucket Downtown. Claude's pick from the coordinator's list plus Plymouth Rock. Event docks named in the passenger notice: Hatch Shell, Agganis, Lovejoy Wharf, Stadium, Encore, Pavilion.

## Charles River (loop)

Boston bank, upstream, then Cambridge bank, inbound, in Max's order.

| Stop | Bank | Basis | Sources |
|---|---|---|---|
| Lovejoy Wharf | Boston, 1 | Real service | line_audit.md: MBTA lists Lovejoy Wharf (North Station); Wikipedia agrees. Two |
| Nashua St | Boston, 2 | Max's idea, real place (Nashua Street Park, across from North Point Park) | Landscape Notes, "New Charles River Basin parks", 2012. Unverified |
| Gronk | Boston, 3 | Max's idea. A nickname, not a place. See Flags | Unverified |
| Hatch Shell | Boston, 4 | Max's idea, real place (Hatch Memorial Shell, Esplanade) | Wikipedia, Charles River Esplanade. Unverified |
| Esplanade | Boston, 5 | Real proposal (Wada Hoppah boat) | line_audit.md: MassLive and CBS Boston. Two |
| Gloucester St | Boston, 6 | Max's idea. Back Bay street, not checked | Unverified |
| BU Docks | Boston, 7 | Max's idea, not checked | Unverified |
| BU Bridge | Boston, 8 | Max's idea, real place | Wikipedia, Magazine Beach (the park runs to the BU Bridge). Unverified |
| Agganis | Boston, 9 | Max's idea. Agganis Arena, not checked | Unverified |
| Western Ave | Boston, 10 | Max's idea. Western Ave bridge, not checked | Unverified |
| John W. Weeks | Boston, 11 | Max's idea, real place (Weeks Footbridge) | Wikipedia, Weld Boathouse (downstream crossing). Unverified |
| Newell | Boston, 12 | Max's idea, real place (Newell Boathouse, 65 Soldiers Field Rd, Allston) | Wikipedia, List of Charles River boathouses. Unverified |
| Cumnock | Boston, 13 | Max's idea, real place ("Cumnock Fields", Harvard, Allston) | Harvard University Police campus map (Clery geography). Unverified |
| Herter | Boston, 14 | Max's idea, real place (Christian Herter Park, Brighton) | Northeast Explorer, "New public boat dock for Charles River". Unverified |
| Northeastern | Boston, 15 | Max's idea. Northeastern's boathouse, not found in the search | Unverified |
| Arsenal St | Boston, 16 | Max's idea, not checked | Unverified |
| Belmont Hill | Cambridge, 1 | Max's idea, real place (Belmont Hill and Winsor shared boathouse, 5 Greenough Blvd, by the Eliot Bridge) | Wikipedia, List of Charles River boathouses. Unverified |
| Winsor | Cambridge, 2 | Max's idea, real place (same boathouse) | Wikipedia, List of Charles River boathouses. Unverified |
| Eliot | Cambridge, 3 | Max's idea, real place (Eliot Bridge) | Wikipedia, List of Charles River boathouses. Unverified |
| Weld | Cambridge, 4 | Max's idea, real place (Weld Boathouse, 971 Memorial Dr) | Wikipedia, Weld Boathouse. Unverified |
| Riverside | Cambridge, 5 | Max's idea, real place (Riverside Boat Club, 796 Memorial Dr, at Magazine Beach) | Wikipedia, Magazine Beach. Unverified |
| Magazine Beach | Cambridge, 6 | Max's idea, real place | Wikipedia, Magazine Beach. Unverified |
| DeWolfe | Cambridge, 7 | Max's idea. BU's DeWolfe Boathouse, not confirmed in the search | Unverified |
| Resch | Cambridge, 8 | Max's idea, real place (MIT's Richard J. Resch Boathouse on Memorial Dr, the old Pierce Boathouse). Spelling is right | Bruner/Cott, MIT Boathouse preservation award. Unverified |
| Ames St | Cambridge, 9 | Max's idea, not checked | Unverified |
| Broad Canal | Cambridge, 10 | Max's idea. Real canal at Kendall; only a wiki mirror turned up | Unverified |
| Poormans | Cambridge, 11 | Max's idea. Not found. See Flags | Unverified |
| Charlesgate | Cambridge, 12 | Max's idea, real place, but on the Boston bank. See Flags | Wikipedia, Muddy River (Massachusetts). Unverified |
| Museum of Science | Cambridge, 13 | Max's idea, real place (1 Science Park, on the Charles River Dam) | BU Today, "Boston Duck Tours", 2024. Unverified |
| North Point | Cambridge, 14 | Max's idea, real place (North Point Park) | Landscape Notes, 2012. Unverified |
| Duck Tours | Cambridge, 15 | Max's idea, real place (the duck boats enter the river by the Museum of Science) | BU Today, 2024. Unverified |
| Paul Revere Park | Cambridge, 16 | Max's idea, real place (Charlestown, on the Charles) | Wikipedia, Paul Revere Park. Unverified |
| Navy Yard | Cambridge, 17 | Real service (MBTA F4) | line_audit.md: Boston Harbor Now 2019 plan names Navy Yard Pier 4. F4 route itself: Unverified |

## Mystic River (loop)

| Stop | Bank | Basis | Sources |
|---|---|---|---|
| Menino | West, 1 | Max's idea, real place (Thomas M. Menino Park, west end of the Charlestown Navy Yard) | charlestownbridge.com, "Menino Park in Navy Yard transferred to Parks Department". Unverified |
| Navy Yard | West, 2 | Real service | See Charles |
| Little Mystic | West, 3 | Max's idea, real place (Little Mystic Channel, Charlestown) | charlestownbridge.com, Little Mystic mitigation, July 2021. Unverified |
| Medford St | West, 4 | Max's idea, real place (Medford St, Charlestown; a Medford Street Path is planned) | charlestownbridge.com, July 2021. Unverified |
| Alford St | West, 5 | Max's idea, real place (Alford Street Bridge, Charlestown to Everett) | charlestownbridge.com, September 2018. Unverified |
| Assembly | West, 6 | Max's idea (was Claude's draft). Assembly Row riverfront, not checked | Unverified |
| Encore | East, 1 | Real service (Encore shuttle boat) | line_audit.md: Encore Boston Harbor and MassLive. Two |
| Stadium | East, 2 | Max's idea. Named for the NERTA Stadium station; no dock checked | Unverified |
| Admirals Hill | East, 3 | Max's idea, real place (Chelsea, between the Mystic and Island End rivers). See Flags | Boston Basin Hills, "Hills of Chelsea". Unverified |
| Pearl St | East, 4 | Max's idea. Not found on the Chelsea or Everett waterfront. See Flags | Unverified |

## Chelsea Creek (loop)

| Stop | Bank | Basis | Sources |
|---|---|---|---|
| Quigley | North, 1 | Max's idea. Only an inland Quigley Park found. See Flags | Unverified |
| Chelsea St | North, 2 | Max's idea, real place (Chelsea Street Bridge) | Northeastern University Library, East Boston archive item. Unverified |
| Eastern Ave | North, 3 | Max's idea, not checked | Unverified |
| Suffolk Downs | South, 1 | Max's idea. On the Rejected list as a ferry stop. See Flags | Unverified |
| Addison St | South, 2 | Max's idea. Not found. See Flags | Unverified |
| Condor St | South, 3 | Max's idea, real place (Condor Street Urban Wild on Chelsea Creek) | boston.gov, Urban Wilds: East Boston. Unverified |
| Boston Bay | South, 4 | Max's idea. Not found. See Flags | Unverified |

## Harbor routes: Express, Harbor West, East Boston, Seaport

| Stop | Route | Basis | Sources |
|---|---|---|---|
| Navy Yard, Long Wharf | Express | Real service (MBTA F4) | line_audit.md. See Charles and Long Wharf |
| Langone | Harbor West | Max's idea, real place (Langone Park, North End). No dock found | Wikipedia, Langone Park. Unverified |
| Battery Wharf | Harbor West | Max's idea, real place (North End) | Battery Wharf Hotel, history page. Unverified |
| Sargent's Wharf | Harbor West | Max's idea. Not found in the search | Unverified |
| Long Wharf | Harbor West, Express, both coast routes | Real service (main hub) | line_audit.md: MBTA ferry pages and Wikipedia. Two |
| Central Wharf | Harbor West | Max's idea, not checked | Unverified |
| Rowes Wharf | Harbor West | Max's idea, not checked (a water taxi landing today, by Claude's knowledge) | Unverified |
| Dorchester Ave | Harbor West | Max's idea, not checked | Unverified |
| White St | East Boston | Max's idea, not checked | Unverified |
| Bennington St | East Boston | Max's idea, not checked | Unverified |
| Piers Park | East Boston | Max's idea, real place | Wikipedia, Piers Park. Unverified |
| Porzio | East Boston | Max's idea, real place (Joseph Porzio Memorial Park, Jeffries Point, with a harbor walk). Spelling is right | boston.gov, Improvements to Porzio Park. Unverified |
| Logan Dock | East Boston | Real service | line_audit.md: MBTA ferry pages and Wikipedia. Two |
| Martins Park | Seaport | Max's idea, real place (Martin's Park, 64 Sleeper St, on Fort Point Channel). See Flags | WBUR, June 2019. Unverified |
| Fan Pier | Seaport | Real service | line_audit.md: MBTA ferry pages and Wikipedia. Two |
| Seaport | Seaport | Max's idea, not checked | Unverified |
| Pavilion | Seaport | Max's idea, real place (Leader Bank Pavilion, 290 Northern Ave) | Wikipedia, Leader Bank Pavilion. Unverified |

## South Boston, Dorchester and Quincy: South Shore, Quincy Bay, Fore River

| Stop | Route | Basis | Sources |
|---|---|---|---|
| First St | South Shore | Max's idea, not checked | Unverified |
| Castle Island | South Shore | Max's idea, real place | Mass.gov, Castle Island, Pleasure Bay, M Street Beach and Carson Beach. Unverified |
| M St | South Shore | Max's idea, real place (M Street Beach) | Mass.gov, same page. Unverified |
| Carson Beach | South Shore, South Shore Express | Max's idea, real place | Mass.gov, same page; line_audit.md calls the dock invented. Unverified |
| Dorchester Shores | South Shore | Max's idea, real place (Dorchester Shores Reservation: Savin Hill, Malibu and Tenean beaches) | Wikipedia, Dorchester Shores Reservation. Unverified |
| Old Harbor | South Shore | Max's idea, real place (Carson Beach/Old Harbor Reservation) | Guidesly, South Boston fishing guide. Unverified |
| UMass Boston | South Shore, South Shore Express | Max's idea. Same dock as the old "Columbia Point" stop. See Flags | Columbia Point: Boston Harbor Now only (line_audit.md). Unverified |
| Fox Point | South Shore | Max's idea, real place (UMass Boston Marine Operations dock in Savin Hill Cove) | UMass Boston, Marine Operations facilities. Unverified |
| Finigan | South Shore | Max's idea. Probably Finnegan Park, Port Norfolk. See Flags | Dorchester Reporter, "Finnegan Park". Unverified |
| Squantum Point | Quincy Bay, South Shore Express | Real service (Marina Bay) | line_audit.md: MBTA Quincy ferry page, Boston Harbor Now, Patriot Ledger. Two |
| Nickerson | Quincy Bay | Max's idea, real place (Nickerson Beach, Squantum) | Wikipedia, Squantum. Unverified |
| Thompson Island | Quincy Bay | Max's idea, real place (served today by the Thompson Island Outward Bound ferry) | Wikipedia, Quincy Bay. Unverified |
| Moon Island | Quincy Bay | Max's idea, real place (causeway from Squantum, access controlled) | Wikipedia, Quincy Bay. Unverified |
| Squantum | Quincy Bay | Max's idea, real place | Wikipedia, Squantum. Unverified |
| Wollaston Beach | Quincy Bay | Max's idea, real place | Wikipedia, Wollaston Beach. Unverified |
| Hough's Neck | Quincy Bay | Max's idea, real place | Wikipedia, Quincy Bay. Unverified |
| Nut Island | Quincy Bay | Max's idea, real place (tip of Hough's Neck) | Wikipedia, Quincy Bay. Unverified |
| Bay Pointe | Fore River | Max's idea, real place (Bay Pointe Marina on the Town River, Quincy, now run as MarineMax Boston) | Boating Industry, September 2018. Unverified |
| King's Cove | Fore River | Max's idea, real place (King's Cove Park, North Weymouth, at the Fore River Bridge) | Neponset River Watershed Association listing. Unverified |
| Wessagusset | Fore River | Max's idea, real place (Wessagusset Beach on the Fore River, North Weymouth). Spelling is right | Neponset River Watershed Association listing. Unverified |
| Hingham | Fore River, South Shore Express | Real service (Hingham Shipyard terminal). See Flags | line_audit.md: one source for the terminal name. Unverified |
| Nantasket | Fore River | Max's idea, not checked | Unverified |
| Hull | Fore River, South Shore Express | Real service (Pemberton Point) | line_audit.md: two sources |

## Harbor Islands; Winthrop and Revere

| Stop | Route | Basis | Sources |
|---|---|---|---|
| Long Island | Harbor Islands | Real plan (recovery campus); the ferry stop is ours | line_audit.md: two for the plan. Stop Unverified |
| Georges Island | Harbor Islands | Real service | line_audit.md: Harbor Islands ferry schedule and NPS. Two |
| Spectacle Island | Harbor Islands | Real service | line_audit.md: Harbor Islands ferry schedule and NPS. Two |
| Deer Island | Harbor Islands | Max's idea, not checked | Unverified |
| Winthrop Beach | Winthrop and Revere | Max's idea, real place | Winthrop town memorials photo archive (c. 1890 photo of Winthrop Beach). Unverified |
| Highlands Beach | Winthrop and Revere | Max's idea, real place (Winthrop Highlands) | Homes.com, Winthrop Highlands guide. Unverified |
| Revere Beach | Winthrop and Revere | Max's idea, not checked | Unverified |
| Beachmont | Winthrop and Revere | Max's idea, not checked | Unverified |

## Dropped on November 7 (kept for the record)

| Stop | Was on | Basis then | Sources |
|---|---|---|---|
| Lewis Mall | Inner Harbor | Real service (East Boston ferry, seasonal) | line_audit.md: MBTA notice, CBS, NBC. Two |
| Kendall | Charles | Real proposal | line_audit.md: one source. Unverified |
| Cambridgeport | Charles | Real proposal | line_audit.md: MassLive and CBS Boston. Two |
| Watertown Sq | Charles | Real proposal | line_audit.md: MassLive and CBS Boston. Two |
| Draw Seven Park, Wellington, Medford Sq | Mystic | Claude draft | Unverified |
| Mary O'Malley Park, PORT Park, Mill Creek | Chelsea Creek | Claude draft | Unverified |

## North Shore Express (high-speed, unchanged stops)

| Stop | Route | Basis | Sources |
|---|---|---|---|
| Winthrop Landing | North Shore | Real service | line_audit.md: MBTA ferry guide and Town of Winthrop. Two |
| Lynn Harbor | North Shore | Real service (Blossom St Pier) | line_audit.md: MBTA and Streetsblog. Two |
| Nahant Harbor | North Shore | Max's idea | Unverified |
| Swampscott | North Shore | Max's idea | Unverified |
| Marblehead | North Shore | Max's idea | Unverified |
| Salem Wharf | North Shore | Real service (Blaney St) | line_audit.md: City of Salem, Port of Salem, City Cruises. Two |
| Beverly | North Shore | Max's idea (Glover Wharf) | Unverified |
| Prides Crossing | North Shore | Max's idea. Real place with a commuter rail stop | Unverified |
| Beverly Farms | North Shore | Max's idea. Real place with a commuter rail stop | Unverified |
| Manchester-by-the-Sea | North Shore | Max's idea. Real harbor with a commuter rail stop | Unverified |
| Magnolia | North Shore | Max's idea. Real place, no proposal | Unverified |
| Gloucester | North Shore | Max's idea. Ferry to Gloucester was named in the MassDOT and MBTA Water Transportation Study | line_audit.md: Mass.gov, MBTA, Streetsblog. Two for the study |
| Brier Neck | North Shore | Max's idea. Real place, no proposal | Unverified |
| Rockport | North Shore | Max's idea. Real harbor with a commuter rail stop | Unverified |
| Annisquam | North Shore | Max's idea. Real place, no proposal | Unverified |
| Crane Beach | North Shore | Max's idea. Real place, no proposal | Unverified |
| Ipswich | North Shore | Max's idea. Real place, no proposal | Unverified |
| Plum Island South | North Shore | Max's idea. Real place, no proposal | Unverified |
| Plum Island Central | North Shore | Max's idea. Real place, no proposal | Unverified |
| Plum Island North | North Shore | Max's idea. Real place, no proposal | Unverified |
| Newburyport | North Shore | Max's idea. Real waterfront, no proposal | Unverified |
| Salisbury | North Shore (end) | Max's idea. Real place, no proposal | Unverified |

## South Shore Express (high-speed), the Cape and Buzzards Bay (unchanged stops)

| Stop | Route | Basis | Sources |
|---|---|---|---|
| Carson Beach | South Shore | Max's idea, beside the L St bathhouse | line_audit.md: invented |
| Columbia Point | South Shore | Real study (Fallon Pier). Drawn as Max's "UMass Boston" from November 7 | line_audit.md: Boston Harbor Now only. One, Unverified |
| Squantum Point | South Shore | Real service (Marina Bay) | line_audit.md: MBTA Quincy ferry page, Boston Harbor Now, Patriot Ledger. Two |
| Quincy | South Shore | Max's idea (Town River) | line_audit.md: invented |
| Quincy Point | South Shore | Real past service (Fore River, 1996 to 2013) | line_audit.md: Boston Globe and Wikipedia. Two |
| Hingham Shipyard | South Shore | Real service. Drawn as Max's "Hingham" (Fore River) from November 7 | line_audit.md: one source for the terminal name. Unverified |
| Hull | South Shore, Harbor Islands | Real service | See Harbor Islands |
| Minot (Scituate) | South Shore | Max's idea. Real place, no proposal | Unverified |
| Mill Wharf | South Shore | Max's idea. Real Scituate Harbor wharf, no proposal | Unverified |
| Humarock | South Shore | Max's idea. Real place, no proposal | Unverified |
| Brant Rock / Green Harbor | South Shore, Cape Cod Bay run starts | Max's idea. Real place, no proposal | Unverified |
| Duxbury via Powder Point Footbridge | Cape Cod Bay run | Max's idea. Real bridge, no proposal | Unverified |
| Plymouth Rock | Cape Cod Bay run | Max's idea. Plymouth to Provincetown boats run in summer | Unverified |
| Sandwich Boardwalk | Cape Cod Bay run, Canal Pass | Max's idea. Real boardwalk, no proposal | Unverified |
| N. Barnstable / Sandy Neck | Cape Cod Bay run | Max's idea. Real place, no proposal | Unverified |
| Sesuit | Cape Cod Bay run | Max's idea. Real harbor, no proposal | Unverified |
| Namskaket | Cape Cod Bay run | Max's idea. Real place, no proposal | Unverified |
| Thumpertown | Cape Cod Bay run | Max's idea. Real beach, no proposal | Unverified |
| Wellfleet Pier | Cape Cod Bay run | Max's idea. Real pier, no proposal | Unverified |
| Provincetown | Cape Cod Bay run | Real service (summer boats from Boston and Plymouth) | Unverified |
| Race Point / P-Town Airport | Cape Cod Bay run | Max's idea. Real place, no proposal | Unverified |
| Marconi Beach | South Shore (Outer Cape) | Max's idea. Real beach, no proposal | Unverified |
| Coast Guard Beach | South Shore (Outer Cape) | Max's idea. Real beach, no proposal | Unverified |
| Nauset Beach | South Shore (Outer Cape) | Max's idea. Real beach, no proposal | Unverified |
| Chatham | South Shore, Islands leg | Max's idea. Real harbor, no proposal | Unverified |
| Harwich Point | South Shore | Max's idea. Real place, no proposal | Unverified |
| Dennis Port | South Shore | Max's idea. Real place, no proposal | Unverified |
| Shad Hole Rd | South Shore | Max's idea. Real road, no proposal | Unverified |
| Old Wharf | South Shore | Max's idea. Real place, no proposal | Unverified |
| West Dennis | South Shore | Max's idea. Real place, no proposal | Unverified |
| Yarmouth | South Shore, Bass River loop | Max's idea. Real place, no proposal | Unverified |
| South Yarmouth | Bass River loop | Max's idea. Real place, no proposal | Unverified |
| Wilbur | Bass River loop | Max's idea. Not checked what place this is | Unverified |
| Bass River / Rte 28 | Bass River loop | Max's idea. Real bridge crossing, no proposal | Unverified |
| Wrinkle Point | Bass River loop | Max's idea. Real place, no proposal | Unverified |
| West Yarmouth | South Shore | Max's idea. Real place, no proposal | Unverified |
| Hyannis | South Shore | Real service (Hyannis to Nantucket boats) | Unverified |
| Hyannisport | South Shore | Max's idea. Real place, no proposal | Unverified |
| Osterville | South Shore | Max's idea. Real place, no proposal | Unverified |
| Popponesett | South Shore | Max's idea. Real place, no proposal | Unverified |
| Acapesket | South Shore | Max's idea. Real place, no proposal | Unverified |
| Falmouth | South Shore | Real service (Falmouth to Edgartown summer boat) | Unverified |
| Woods Hole | South Shore, Buzzards Bay leg, Islands leg | Real service (Steamship Authority to Martha's Vineyard) | Unverified |
| West Falmouth | Buzzards Bay leg | Max's idea. Real harbor, no proposal | Unverified |
| New Silver Beach | Buzzards Bay leg | Max's idea. Real place, no proposal | Unverified |
| Pocasset | Buzzards Bay leg | Max's idea. Real place, no proposal | Unverified |
| Buzzards Bay | Buzzards Bay leg, Canal Pass | Max's idea. Real village at the canal's west end | Unverified |
| Onset | Buzzards Bay leg | Max's idea. Real harbor, no proposal | Unverified |
| Wareham | Buzzards Bay leg | Max's idea. Real place, no proposal | Unverified |
| Marion | Buzzards Bay leg | Max's idea. Real harbor, no proposal | Unverified |
| Mattapoisett | Buzzards Bay leg | Max's idea. Real harbor, no proposal | Unverified |
| West Island | Buzzards Bay leg | Max's idea. Real place, no proposal | Unverified |
| Fairhaven | Buzzards Bay leg | Max's idea. Real place, no proposal | Unverified |
| New Bedford | South Shore, Buzzards Bay leg, Canal Pass, express | Real service (boats to Cuttyhunk, Martha's Vineyard, Nantucket) | Unverified |
| South Dartmouth | South Shore | Max's idea. Real harbor (Padanaram), no proposal | Unverified |
| Newport | South Shore | Max's idea. Real harbor, no proposal checked | Unverified |
| Fall River | South Shore (end) | Max's idea. Real waterfront, no proposal checked | Unverified |
| Cuttyhunk | Express, Aquinnah spur | Real service (New Bedford to Cuttyhunk boat) | Unverified |

## Islands leg (Chatham to Woods Hole)

| Stop | Route | Basis | Sources |
|---|---|---|---|
| Wauwinet | Islands | Max's idea. Real place, no proposal | Unverified |
| Siasconset | Islands | Max's idea. Real place, no proposal | Unverified |
| Nantucket Memorial Airport / Nobadeer | Islands | Max's idea. Real airport and beach, no proposal | Unverified |
| South Shore (Nantucket) | Islands | Max's idea. Real shore, no proposal | Unverified |
| Cisco | Islands | Max's idea. Real beach, no proposal | Unverified |
| Smith Point | Islands | Max's idea. Real place, no proposal | Unverified |
| Tuckernuck Is. | Islands | Max's idea. Real island, no proposal | Unverified |
| Brant Point | Islands | Max's idea. Real place at the harbor mouth | Unverified |
| Nantucket Downtown | Islands | Real service (Steamship Authority and Hy-Line to Nantucket) | Unverified |
| Coskata | Islands | Max's idea. Real place, no proposal | Unverified |
| Oak Bluffs | Islands ring, express | Real service (summer boats from Woods Hole, Falmouth, New Bedford, Hyannis) | Unverified |
| Edgartown | Islands ring | Real service (Falmouth to Edgartown summer boat) | Unverified |
| Chappaquiddick | Islands ring | Real service (the Chappy ferry from Edgartown) | Unverified |
| Katama Beach | Islands ring | Max's idea. Real beach, no proposal | Unverified |
| MVY Connection via Scrubby Neck | Islands ring | Max's idea. Shuttles to the airport and Lagoon Pond | Unverified |
| Chilmark | Islands ring | Max's idea. Real place (Menemsha harbor is in Chilmark) | Unverified |
| Aquinnah | Islands ring, Cuttyhunk and Noman's Land spurs | Max's idea. Real place, no proposal | Unverified |
| Vineyard Haven | Islands ring, link to Woods Hole | Real service (Steamship Authority, year round) | Unverified |
| Lagoon Pond | Islands ring | Max's idea. Real pond, airport shuttle per Max | Unverified |
| Noman's Land | Islands spur (end) | Max's idea. Real island, a closed wildlife refuge with no public access | Unverified. Worth a look: the real island is off limits |

## Transfer pills on the poster

| Dock | Pill | Basis | Sources |
|---|---|---|---|
| Inner Harbor docks, Kendall | As in make_tmap.FERRY_ROUTES | Main map | make_tmap.py |
| Assembly | OL, CL | Station of that name in make_tmap.lines() | make_tmap.py |
| Carson Beach | CL | Dock links to L Street in make_tmap.DOCKS (Cyan, dashed) | make_tmap.py |
| Lynn Harbor | BL | make_tmap.DOCKS link | make_tmap.py |
| Swampscott, Marblehead, Salem Wharf, Beverly | CR | make_tmap.DOCKS links to commuter stops | make_tmap.py |
| Beverly Farms, Manchester-by-the-Sea, Gloucester, Rockport | CR | Real Rockport Line stations a short walk from the water | Unverified |
| Prides Crossing | None | Station closed indefinitely in April 2021, so the pill was removed November 7 | See line_audit.md |
| New Bedford, Fall River | CR | Real South Coast Rail stations, opened 2025 | Unverified |
| Quincy | RL, CR | The dock sits on the Town River below Quincy Center (make_tmap.DOCKS), a Red Line and commuter rail station (MBTA; Wikipedia). Added November 7 at Max's request | Two for the station; the walk is our estimate |
| Buzzards Bay, Hyannis | CR | CapeFLYER stations, summer weekends: Buzzards Bay on Main St and the Hyannis Transportation Center (capeflyer.com; Cape Cod Regional Transit Authority CapeFLYER page). Added November 7 | Two |
| Hingham Shipyard, Minot (Scituate), Mill Wharf, Plymouth Rock | None | The nearest Greenbush and Kingston Line stations are about 2 to 3.5 km from these docks by our estimate, too far to call a transfer (same rule as Ipswich below). Plymouth station has been closed since April 2021 (Wikipedia, Plymouth station and Kingston Line) | Distances unverified |
| Ipswich, Newburyport | None | Real stations, but about a mile from the water, so left off | Unverified |

### Pills added November 7 for Max's inner routes

Walking distances are Claude's estimates (about 400 m or less), not measured: **Unverified**. Station lines are from `make_tmap.lines()`, copied into the poster script.

| Dock | Pill | Station it walks to |
|---|---|---|
| Nashua St, Museum of Science | GL | Science Park |
| North Point | GL, YL | Lechmere |
| Weld | RL, GL | Harvard |
| Ames St, Broad Canal | RL, YL | Kendall/MIT |
| DeWolfe | YL | BU Bridge (Yellow) |
| BU Bridge | GL, YL | BU Central (Green B) and BU Bridge (Yellow) |
| Agganis | GL | Amory St, Babcock St (Green B) |
| Paul Revere Park | CL | City Square |
| Stadium | CL, YL | Stadium |
| Suffolk Downs | BL | Suffolk Downs |
| Piers Park | BL | Maverick |
| Langone | CL | North End |
| Central Wharf | BL, CL | Aquarium |
| Rowes Wharf | CL, CR | Boston Central |
| Dorchester Ave | RL, IL, CR | South Station |
| Seaport | CL, YL | Seaport |
| M St | CL | City Point |
| Revere Beach, Beachmont | BL | Stations of the same names |
| Hatch Shell, Esplanade, Northeastern, Herter, Alford St, Admirals Hill, Bennington St, Porzio, Pavilion, UMass Boston, Wollaston Beach, Bay Pointe | None | Nearest stations look 500 m or more away by Claude's estimate |

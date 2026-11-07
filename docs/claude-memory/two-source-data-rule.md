---
name: two-source-data-rule
description: "Assembled data needs 2 sources before it can be called accurate, or an explicit override from Max; the override question must be typed in ALL CAPS"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6191c34a-246f-4fb5-a839-115daa477823
  modified: 2026-11-04T00:51:54.173Z
---

Any time Max asks Claude to assemble data, find 2 sources before calling it accurate, or get an override from Max. When asking whether Max wants to override a data rule, type the question in ALL CAPS. (Set 2026-11-03.)

**Why:** Max's standing rule. One-source data has already fallen short here: Day 7's OSM-only pull found 2,317 pizza places against 7,351 once Overture was added, and Day 3 had 12 wrong town founding dates.

**How to apply:**
- Before describing assembled data as accurate, name the 2 sources behind it. Say which ones agree and where they differ.
- With only 1 source, label the data unverified and ask for the override. Example: "I ONLY FOUND ONE SOURCE FOR THIS DATA. DO YOU WANT TO OVERRIDE THE TWO-SOURCE RULE?"
- Only Max can grant an override. It covers that dataset only, not later ones, and it isn't assumed from silence.
- All caps applies to the override question, not the rest of the reply.

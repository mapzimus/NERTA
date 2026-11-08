# Image specs for a tall map poster (checked 2026-11-07)

**Source key.** IGH = Instagram Help "Image resolution of photos you share" (read through the search index; the page itself would not load). MAPI = Meta Instagram Graph API docs. TAPI = Meta Threads API docs. FBA = Meta Ads Guide, Facebook Feed image. XAPI = X API media best practices (docs.x.com). TC = TechCrunch, 2026-04-23. GH = Bluesky atproto GitHub discussion #2887 (users, 2024-25). LIA = LinkedIn Images API (Microsoft Learn, 2026-06). LIH = LinkedIn Help a563309. SP = Sprout Social guide (2026-11-02). HS = Hootsuite guide (2026-11-02). BF = Buffer guide (2026-05-12). SMT = Social Media Today, 2019-01-08.

| Platform | Best portrait size | Tallest ratio before crop | Max file size | PNG kept or recompressed |
|---|---|---|---|---|
| Instagram feed | 1080x1350, 4:5 (IGH, SP, HS agree). 1080x1440, 3:4 (BF, SP) | 3:4 in the app (BF, SP). 4:5 per IGH and for API/scheduler posts (MAPI, SP). **Differ** | 30 MB in the app (SP + other guides) vs 8 MB through the API (MAPI). **Differ** | Recompressed. The API takes JPEG only (MAPI), and the app sizes width down to 1080 (IGH). SP: the platform compresses |
| X | 1080x1350 (BF only). **Unverified** | 3:4 (BF + 1 guide) vs 4:5 (other guides). **Differ, unverified** | 5 MB (XAPI, HS agree. SP says 20 MB) | Converted to JPEG unless under 900 px or PNG8 (SMT + derpibooru, both 2019). Rule is old, so current behavior is **unverified** |
| Bluesky | Up to 4000 px on the long edge (TC + Gigazine agree) | No crop, keeps the original ratio (TC, SP agree) | 2 MB (TC, SP agree. HS and BF still say 1 MB, which is out of date) | Re-encoded to JPEG to fit the cap (GH users; BF says "compressed and resized"). Behavior after April 2026 is **unverified** |
| Reddit | No official spec. Original kept at full size (user reports). **Unverified** | Not documented. **Unverified** | 20 MB (PictureSizes 2026 guide + an r/help thread. No Reddit help page found, so weak) | Original kept on i.redd.it; feed previews served as WebP (r/WidescreenWallpaper threads + a Chrome extension listing). Community reports only |
| LinkedIn | 1080x1350 (BF + Pixotter guide agree) | 4:5 (BF; Pixotter says taller images are cut from the bottom). LIH says mobile won't crop and other ratios get white padding. **Differ** | 5 MB (SP; HS for ads). The API caps at 36,152,320 pixels with no byte cap (LIA) | **Unverified.** The API serves "image-shrink_1280" copies (LIA), so expect a resize |
| Threads | 1440 wide: 1440x1800 (SP) or 1440x1920 (HS). Max width 1440 (TAPI) | Upload allowed up to 10:1 (TAPI, HS agree). Where the feed crops is not documented. **Unverified** | 8 MB (TAPI, HS, SP agree) | PNG accepted, scaled to 1440 wide, color converted to sRGB (TAPI). Whether it recompresses is **unverified** |
| Facebook | 1440x1800 (FBA, SP agree). 1080x1350 is also common (BF, HS) | 4:5 (FBA, SP, HS agree) | 30 MB (FBA, SP agree) | Keep PNGs under 1 MB. Larger ones may look pixelated (Facebook Help via search index + Orlo support page) |

## Notes
1. Some official pages could not be read. help.x.com returned a 403 error. The Instagram and Facebook help pages would not render, so their wording comes from the search index. Reddit's help center blocks the fetch tool.
2. Instagram has two conflicts. On ratio, the help page and the API still say 4:5, while Buffer and Sprout say the app takes native 3:4 photos. Posts sent through a scheduler or the API are held to 4:5. On width, IGH says 1080 and MAPI allows 1440.
3. X's crop point is the weakest number in this table. The 5 MB cap is the only solid X figure.
4. Bluesky's April 2026 update (v1.121) raised the file cap from 1 MB to 2 MB and the size from 2000 px to 4000 px. The Hootsuite and Buffer pages still show the old limits.
5. Any cell marked unverified or differ has fewer than 2 agreeing sources. Treat it as a test-post item.

## Recommended exports (3)
1. **1440x1800 JPEG, 4:5, sRGB, under 2 MB.** One file for every feed. 4:5 is the only portrait ratio that every source accepts, and it fits Bluesky's 2 MB cap. Instagram shrinks it cleanly to 1080x1350.
2. **Full-resolution PNG at the poster's own ratio, long edge 4000-6000 px, under 20 MB.** For Reddit, which keeps the original, and as the zoomable link everywhere else.
3. **JPEG at the poster's own ratio, 4000 px on the long edge, under 2 MB.** A second image for Bluesky (no crop, 4000 px cap) and X (under 5 MB) so readers can zoom in on the small text.

## Instagram and TikTok (checked 2026-11-08)

**New sources.** TTAPI = TikTok Content Posting API, media transfer guide (developers.tiktok.com). AYR = Ayrshare TikTok media guidelines (scheduler API docs). SPS = Sprout Social support "How do I post TikTok photo posts" (read through the search index; the page returned 403). MREF = Meta IG User Media API reference. 9TM = 9to5Mac, 2025-05-29, reporting Adam Mosseri's Threads post. LTR = Later, "Instagram image size" (dated 2021-11-19, so out of date). SP, HS and BF are the same guides as above, re-read today.

| Item | Size and ratio | Max file size | Format |
|---|---|---|---|
| TikTok photo post / carousel | 1080x1920, 9:16 (HS, SP, BF agree). TTAPI caps photos at "1080p"; AYR caps at 1080x1920. HS: 1:1 and 4:5 work but don't fill the screen | 20 MB a photo (TTAPI, AYR, SPS agree) | JPEG (TTAPI, AYR, SPS agree). WebP also (TTAPI, SPS). PNG: SP's guide says yes, AYR says not on the photo-post endpoint. **Differ** |
| Instagram Stories | 1080x1920, 9:16 (HS, SP, BF, LTR agree; MREF recommends 9:16). Keep text inside the middle 1080x1610 (HS, SP) | 8 MB through the API (MREF). App cap **unverified** | JPEG, sRGB (MREF) |
| Instagram Reels cover | 1080x1920 (BF) vs 420x654, about 1:1.55 (SP). **Differ.** The grid shows a 3:4 center crop of the cover (BF, HS agree) | Not found | Not found |
| Instagram feed 4:5 | 1080x1350 (HS, SP, BF, LTR agree) | 8 MB through the API (MREF); 30 MB in the app (SP, from the table above) | JPEG, sRGB (MREF) |
| Instagram feed 3:4 | 1080x1440. Accepted in the app for single photos and carousels since May 2025 (9TM, BF, SP agree). Through the API and schedulers the feed still takes only 4:5 to 1.91:1 (MREF, SP agree). HS lists 3:4 only as the grid ratio. **App yes, API no** | Same as 4:5 | Same as 4:5 |

**What this means for export_social.py.** It now also writes `_ig_feed.jpg` (1080x1350), `_ig_portrait.jpg` (1080x1440, app upload only) and `_tiktok.jpg` (1080x1920, also the Stories file). Each is padded with paper, never cropped, and held under 8 MB, the stricter of Instagram's API cap and TikTok's 20 MB. A Reels cover crop to 3:4 takes 240 px off the top and bottom of a 1080x1920 file, which is only padding for maps wider than 3:4.

**Carousel limits (checked 2026-11-08).** MCP = Meta Instagram Content Publishing docs. PP = PetaPixel, 2024-08-09. TTPP = TikTok Content Posting API, photo post reference.
- Instagram carousel: 20 images or videos. MCP says "Carousels are limited to 20 images, videos, or a mix of the two," and PP reports the 10 to 20 change rolled out to all users in August 2024. **Agree**, and the API matches the app.
- TikTok photo post: 35 photos. TTPP gives "up to 35" photos, and BF says the same. **Agree.**
- export_social.py keeps each carousel to 20 slides: the whole map first (so the disclaimer is slide 1), then up to 19 tiles.

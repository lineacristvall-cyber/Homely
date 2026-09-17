# Homely UI decision-flow coverage audit

**2026-09-13 · Proposed UX architecture, not an implemented app.** The [current editable decision flow](flows/Homely-UI-Decision-Flows-v3.drawio) contains a connected end-to-end overview and one linked, downward action tree per named state: 129 pages, 128 reachable states, 335 action branches and 1,040 actual connected arrow edges. The [previous v2 atlas](flows/Homely-UI-State-Atlas-v2.drawio) and its [audit](FLOW_COVERAGE_AUDIT-v2.md) remain as rejected historical material. Each blue destination on a state page links to the exact state page with its next choices. XML connectivity, target links and state reachability were checked programmatically.

The flow represents material user actions, events and outcomes. It does not claim to enumerate arbitrary combinations of devices, retailers, locations or simultaneous failures. Source access, stock confirmation, visualization fidelity and cost are validation gates, not working integrations.

## Screen/state coverage

| Screen | Template | Named states | Action branches |
| --- | --- | ---: | ---: |
| S01 | Welcome & intent | 5 | 11 |
| S02 | Permissions at point of use | 3 | 13 |
| S03 | Project home & session | 4 | 13 |
| S04 | Room canvas & voice | 4 | 14 |
| S05 | Capture, edit & dimensions | 10 | 18 |
| S06 | Taste & inspiration | 5 | 11 |
| S07 | Structured brief & constraints | 5 | 12 |
| S08 | Research job & progress | 6 | 15 |
| S09 | No result & source gap | 3 | 9 |
| S10 | Findings & spoken briefing | 6 | 16 |
| S11 | Exact candidate evidence | 7 | 19 |
| S12 | Unconfirmed lead | 4 | 9 |
| S13 | Actual product in room | 6 | 16 |
| S14 | Mobile comparison | 4 | 13 |
| S15 | Desktop project canvas | 3 | 13 |
| S16 | Decision, budget & stock gate | 6 | 17 |
| S17 | External seller handoff & earned usage | 5 | 11 |
| S18 | Stock-change alert & replacement | 3 | 10 |
| S19 | Saved hunts & notification inbox | 7 | 17 |
| S20 | Client share, approval & revisions | 7 | 17 |
| S21 | Decision & purchase ledger | 6 | 13 |
| S22 | Account, privacy & data | 7 | 16 |
| S23 | Offline, reconnect & conflicts | 7 | 17 |
| S24 | Desktop research workspace | 5 | 15 |

## Requirement paths

| Requirement | Decision-flow screens |
| --- | --- |
| Pro/DIY entry and project continuity | S01 → S03 → S04; S15 laptop path |
| Permission, voice, capture and manual recovery | S02, S04–S05, S07 |
| Research job, partial/no result and source gap | S07 → S08 → S09/S10; S19 hunt; S24 desktop |
| Exact product variant, quantity, freshness and unconfirmed lead | S10 → S11/S12 → S16 |
| Actual-product visualization and measured fit | S11 → S13 → S14; S05 measurements |
| Hard cap, live stock/price recheck and seller handoff | S14 → S16 → S17 or S18 |
| Client approval, privacy and offline conflict | S20, S22, S23 |
| Purchase and earned usage history | S17 → S21 |

## Complete action and destination ledger

### S01 · Welcome & intent

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S01-A01 | S01.START | Open Homely | Restore signed-in session if valid | S03.HOME |
| S01-A02 | S01.START | Open logged-out link | Show pro/DIY choice and sign-in | S01.INTENT |
| S01-A03 | S01.INTENT | Choose professional | Save provisional intent; explain team workflow | S01.AUTH |
| S01-A04 | S01.INTENT | Choose DIY | Save provisional intent; simpler guidance | S01.AUTH |
| S01-A05 | S01.INTENT | Preview without account | Local draft only; disclose sync limits | S03.EMPTY |
| S01-A06 | S01.AUTH | Submit sign-in | Show progress; keep unsent draft | S01.LOADING |
| S01-A07 | S01.LOADING | Authentication succeeds | Merge draft with account project | S03.HOME |
| S01-A08 | S01.LOADING | Authentication fails | Inline error; Retry and recover draft | S01.AUTH_ERROR |
| S01-A09 | S01.AUTH_ERROR | Retry or edit credentials | Clear error, preserve draft | S01.AUTH |
| S01-A10 | S01.AUTH | Back or cancel | Keep preview draft; no consent granted | S01.INTENT |
| S01-A11 | S01.AUTH | Deep link to scoped share | Authenticate or limited token route | S20.REVIEW |

### S02 · Permissions at point of use

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S02-A01 | S02.PRIMER | Read purpose and choose Allow | Invoke platform permission for requested feature | S02.REQUESTING |
| S02-A02 | S02.REQUESTING | Platform grants camera | Resume capture; record consent | S05.CAPTURE |
| S02-A03 | S02.REQUESTING | Platform grants microphone | Resume visible listening action | S04.LISTENING |
| S02-A04 | S02.REQUESTING | Platform grants notifications | Enable push where supported | S19.ACTIVE |
| S02-A05 | S02.REQUESTING | Platform denies or restricts | Explain manual/silent/in-app equivalent | S02.DENIED |
| S02-A06 | S02.DENIED | Choose manual photo path | Never block room creation | S05.MANUAL |
| S02-A07 | S02.DENIED | Choose typed or touch path | Never block brief editing | S07.EDITING |
| S02-A08 | S02.DENIED | Choose in-app alerts | Save hunt without push | S19.INBOX |
| S02-A09 | S02.DENIED | Open system settings help | No repeated prompt loop | S02.DENIED |
| S02-A10 | S02.PRIMER | Not now on microphone request | Return to room without recording | S04.IDLE |
| S02-A11 | S02.PRIMER | Not now on camera request | Return to manual photo entry | S05.MANUAL |
| S02-A12 | S02.PRIMER | Not now on push request | Keep hunt and in-app activity | S19.INBOX |
| S02-A13 | S02.REQUESTING | Permission revoked mid-capture | Stop audio/video immediately | S02.DENIED |

### S03 · Project home & session

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S03-A01 | S03.HOME | Open project card | Restore room and last task | S04.IDLE |
| S03-A02 | S03.EMPTY | Create first project | Name, pro/DIY role and location | S03.CREATING |
| S03-A03 | S03.HOME | Create new project | Blank project form | S03.CREATING |
| S03-A04 | S03.CREATING | Save valid name | Persist project version; show room setup | S05.CAPTURE |
| S03-A05 | S03.CREATING | Cancel | Discard only unsaved form | S03.HOME |
| S03-A06 | S03.HOME | Open saved hunt | Restore activity and cadence | S19.ACTIVE |
| S03-A07 | S03.HOME | Open pending client review | Enforce scoped permission | S20.REVIEW |
| S03-A08 | S03.HOME | Open desktop planning | Same project model | S15.CANVAS |
| S03-A09 | S03.HOME | Open account/settings | Show consent, export, billing | S22.SETTINGS |
| S03-A10 | S03.HOME | Sign out | Warn about unsynced draft; keep safe local draft | S01.INTENT |
| S03-A11 | S03.HOME | Deep link to missing/denied project | Explain permission or deleted room | S03.NOT_FOUND |
| S03-A12 | S03.NOT_FOUND | Back to projects | No phantom project creation | S03.HOME |
| S03-A13 | S03.HOME | Sync conflict event | Freeze overwritten edit, compare versions | S23.CONFLICT |

### S04 · Room canvas & voice

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S04-A01 | S04.IDLE | Tap microphone | Permission at point of use | S02.PRIMER |
| S04-A02 | S04.IDLE | Mic already allowed | Explicit waveform and Stop control | S04.LISTENING |
| S04-A03 | S04.LISTENING | Speak room goal | Show live provisional transcript | S04.TRANSCRIPT |
| S04-A04 | S04.LISTENING | Tap Stop or interrupt | Preserve partial text, stop capture | S04.TRANSCRIPT |
| S04-A05 | S04.TRANSCRIPT | Correct text or recognized amount | Highlight edited phrase before apply | S04.CORRECTING |
| S04-A06 | S04.CORRECTING | Save correction | Propose exact constraint chips | S07.REVIEW |
| S04-A07 | S04.TRANSCRIPT | Accept speech | Parse and preview fields, not auto-search | S07.REVIEW |
| S04-A08 | S04.TRANSCRIPT | Cancel | Discard provisional transcript only | S04.IDLE |
| S04-A09 | S04.IDLE | Tag table Keep / undo tag | Version retained-item annotation | S04.IDLE |
| S04-A10 | S04.IDLE | Tap measurement marker | Open table/room values | S05.MEASURE |
| S04-A11 | S04.IDLE | Add or replace room photo | Keep original/history and request capture | S05.CAPTURE |
| S04-A12 | S04.IDLE | Tap Explore | Use current versioned brief | S07.EDITING |
| S04-A13 | S04.IDLE | Back to projects | Persist annotations | S03.HOME |
| S04-A14 | S04.LISTENING | Permission revoked or recognition failure | Stop capture; typed equivalent | S02.DENIED |

### S05 · Capture, edit & dimensions

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S05-A01 | S05.CAPTURE | Use camera | Request camera only now, show capture overlay | S02.PRIMER |
| S05-A02 | S05.CAPTURE | Import photo | Pick image; explain storage and rights | S05.UPLOADING |
| S05-A03 | S05.MANUAL | Upload from files | Same photo validation | S05.UPLOADING |
| S05-A04 | S05.UPLOADING | Image accepted | Save original, orientation and version | S05.PHOTO |
| S05-A05 | S05.UPLOADING | Upload fails / blurred / quota | Keep draft and offer Retry | S05.UPLOAD_ERROR |
| S05-A06 | S05.UPLOAD_ERROR | Retake or retry | Do not lose existing original | S05.CAPTURE |
| S05-A07 | S05.PHOTO | Retake / add another view | Preserve earlier original and choose current | S05.CAPTURE |
| S05-A08 | S05.PHOTO | Crop, rotate or annotate | Store edit layer; Undo available | S05.EDITING |
| S05-A09 | S05.EDITING | Save or undo image edit | Maintain original photo | S05.PHOTO |
| S05-A10 | S05.PHOTO | Mark existing furniture Keep | Link item to room photo | S04.IDLE |
| S05-A11 | S05.PHOTO | Measure table underside | Prompt units, measured/estimated source | S05.MEASURE |
| S05-A12 | S05.MEASURE | Enter positive dimension | Validate units and record source/confidence | S05.MEASURED |
| S05-A13 | S05.MEASURE | Skip unknown value | Show unknown fit state; ask later | S05.UNKNOWN |
| S05-A14 | S05.MEASURED | Save and continue | Version geometry; invalidate prior fit | S06.STYLE |
| S05-A15 | S05.UNKNOWN | Continue with uncertainty | No validated physical-fit badge | S07.EDITING |
| S05-A16 | S05.PHOTO | Delete image | Recoverable remove with Undo; warn if last | S05.DELETING |
| S05-A17 | S05.DELETING | Undo / confirm | Return or choose another photo | S05.PHOTO |
| S05-A18 | S05.PHOTO | Back / cancel capture | Keep saved image; discard unsaved edit | S04.IDLE |

### S06 · Taste & inspiration

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S06-A01 | S06.STYLE | Pick inspiration cards | Show why each relates to room | S06.EDITING |
| S06-A02 | S06.STYLE | Import inspiration image | Request file, preserve source label | S06.UPLOADING |
| S06-A03 | S06.UPLOADING | Image accepted | Add to board; user confirms rights | S06.EDITING |
| S06-A04 | S06.UPLOADING | Failure or no image | Retry or continue without image | S06.EMPTY |
| S06-A05 | S06.EDITING | Mark like/dislike/material ban | Update visible preference chips | S06.EDITING |
| S06-A06 | S06.EDITING | Remove inferred taste label | Undo; prevent hidden preference | S06.EDITING |
| S06-A07 | S06.EDITING | Explain style rationale | Show room/retained-piece evidence | S06.RATIONALE |
| S06-A08 | S06.RATIONALE | Close | Return with no implicit preference change | S06.EDITING |
| S06-A09 | S06.EDITING | Continue | Version taste and merge into brief | S07.EDITING |
| S06-A10 | S06.EMPTY | Continue without inspiration | No invented aesthetic certainty | S07.EDITING |
| S06-A11 | S06.EDITING | Back or cancel unsaved changes | Restore last saved style version | S04.IDLE |

### S07 · Structured brief & constraints

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S07-A01 | S07.EDITING | Edit quantity/category/location | Validate positive count and deliverability | S07.EDITING |
| S07-A02 | S07.EDITING | Edit flexible target | Show comparison premium rule | S07.EDITING |
| S07-A03 | S07.EDITING | Edit absolute hard cap | Flag any target/cap conflict | S07.VALIDATING |
| S07-A04 | S07.EDITING | Add dimensional hard constraint | Require unit/source or mark unknown | S07.VALIDATING |
| S07-A05 | S07.EDITING | Add style/condition/source preference | Distinguish hard vs soft chip | S07.EDITING |
| S07-A06 | S07.REVIEW | Correct parsed voice chip | Highlight field; no search yet | S07.EDITING |
| S07-A07 | S07.VALIDATING | Target exceeds cap or invalid units | Inline exact-field error; no silent cap raise | S07.INVALID |
| S07-A08 | S07.INVALID | Edit indicated field | Preserve other valid chips | S07.EDITING |
| S07-A09 | S07.VALIDATING | All hard constraints valid | Show snapshot and Start research | S07.READY |
| S07-A10 | S07.READY | Start research | Save version, invalidate old comparisons | S08.QUEUED |
| S07-A11 | S07.EDITING | Save draft or back | Version brief without starting research | S04.IDLE |
| S07-A12 | S07.READY | Cancel new search | Keep draft and prior result history | S07.EDITING |

### S08 · Research job & progress

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S08-A01 | S08.QUEUED | Begin approved source job | Show actual source set and progress | S08.RUNNING |
| S08-A02 | S08.RUNNING | Open source ledger | Show checked time, errors and exclusions | S08.LEDGER |
| S08-A03 | S08.LEDGER | Close | Keep job running | S08.RUNNING |
| S08-A04 | S08.RUNNING | Pause checks | Halt future cycles where feasible; in-flight caveat | S08.PAUSED |
| S08-A05 | S08.PAUSED | Resume | Requeue allowed sources; show new check time | S08.QUEUED |
| S08-A06 | S08.RUNNING | Refine query | Edit brief; cancel/version old job | S07.EDITING |
| S08-A07 | S08.RUNNING | Cancel job | Keep partial evidence as history | S08.CANCELLED |
| S08-A08 | S08.CANCELLED | Back to brief | No hidden running task | S07.EDITING |
| S08-A09 | S08.RUNNING | Source blocked/timeout | Mark source explicitly, keep partial evidence | S08.PARTIAL |
| S08-A10 | S08.PARTIAL | Retry permitted source | Backoff; never promise unavailable integration | S08.RUNNING |
| S08-A11 | S08.PARTIAL | View partial verified findings | Show missing coverage | S10.PARTIAL |
| S08-A12 | S08.RUNNING | Verified candidates ready | Complete job and show briefing | S10.RESULTS |
| S08-A13 | S08.RUNNING | No verified candidates | Explain binding constraints/source gaps | S09.EMPTY |
| S08-A14 | S08.RUNNING | Save ongoing hunt | Explain server checks and alert cost/scope | S19.SETUP |
| S08-A15 | S08.RUNNING | Offline | Job state unknown; cached ledger labeled stale | S23.OFFLINE |

### S09 · No result & source gap

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S09-A01 | S09.EMPTY | Inspect why no verified matches | Show constraint and source-specific causes | S09.DIAGNOSIS |
| S09-A02 | S09.DIAGNOSIS | Open unconfirmed leads | Separate investigational lane | S12.LEAD |
| S09-A03 | S09.DIAGNOSIS | Widen chosen soft preference | Preview exact change and re-search | S07.EDITING |
| S09-A04 | S09.DIAGNOSIS | Change hard cap explicitly | Require user's direct edit | S07.EDITING |
| S09-A05 | S09.DIAGNOSIS | Retry failed permitted sources | Queue retry with ledger | S08.QUEUED |
| S09-A06 | S09.DIAGNOSIS | Save hunt | Choose cadence and legal source coverage | S19.SETUP |
| S09-A07 | S09.EMPTY | Back to last results | Preserve prior version and timestamp | S10.RESULTS |
| S09-A08 | S09.EMPTY | Source access unavailable | Explain gap and manual source option | S09.SOURCE_GAP |
| S09-A09 | S09.SOURCE_GAP | Back or close | No fake coverage claim | S03.HOME |

### S10 · Findings & spoken briefing

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S10-A01 | S10.RESULTS | Play brief spoken summary | Captions, mute and Stop visible | S10.PLAYING |
| S10-A02 | S10.PLAYING | Pause/mute/open transcript | Full silent equivalent | S10.RESULTS |
| S10-A03 | S10.RESULTS | Open Best fit option | Exact variant evidence | S11.DETAIL |
| S10-A04 | S10.RESULTS | Open Within target option | Exact variant evidence | S11.DETAIL |
| S10-A05 | S10.RESULTS | Open Savings option | Exact variant evidence | S11.DETAIL |
| S10-A06 | S10.RESULTS | Expand all results/filter/sort | Explain ranking criteria; no commission rank | S10.FILTERING |
| S10-A07 | S10.FILTERING | Apply filters | Recompute visible set and count | S10.RESULTS |
| S10-A08 | S10.FILTERING | Clear filters / no match | Preserve original results and show empty filter | S10.FILTER_EMPTY |
| S10-A09 | S10.FILTER_EMPTY | Reset filters | Restore ranked set | S10.RESULTS |
| S10-A10 | S10.RESULTS | Open unconfirmed leads | Never ready badge | S12.LEAD |
| S10-A11 | S10.RESULTS | Compare selected options | All-in logistics and hard cap | S14.COMPARE |
| S10-A12 | S10.RESULTS | Save hunt | Set scope and cadence | S19.SETUP |
| S10-A13 | S10.PARTIAL | Open source ledger | List missing sources and last checked | S08.LEDGER |
| S10-A14 | S10.RESULTS | Pull to refresh | Recheck exact stock/price, stale until done | S10.REFRESHING |
| S10-A15 | S10.REFRESHING | Stock changed | Move lost item to history/replacement | S18.CHANGE |
| S10-A16 | S10.RESULTS | Back to research | Restore ledger/job version | S08.RUNNING |

### S11 · Exact candidate evidence

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S11-A01 | S11.DETAIL | Choose finish/size variant | Clear prior stock/price and reverify | S11.VARIANT_PENDING |
| S11-A02 | S11.VARIANT_PENDING | Recheck succeeds exact six | Show source/time/method; ready badge | S11.VERIFIED |
| S11-A03 | S11.VARIANT_PENDING | Variant wrong or count short | Remove ready badge and offer substitute | S11.UNAVAILABLE |
| S11-A04 | S11.DETAIL | Open stock evidence | Source URL, count, location, timestamp/expiry | S11.EVIDENCE |
| S11-A05 | S11.EVIDENCE | Close or back | Return to same variant | S11.DETAIL |
| S11-A06 | S11.DETAIL | Inspect fit dimensions | Seat/arm/clearance measured vs estimated | S11.FIT |
| S11-A07 | S11.FIT | Missing table/seat measure | Prompt specific input; no verified fit | S05.MEASURE |
| S11-A08 | S11.FIT | Back | Retain evidence view | S11.DETAIL |
| S11-A09 | S11.DETAIL | Inspect all-in cost | Item, tax, delivery, condition/restoration | S16.BUDGET |
| S11-A10 | S11.DETAIL | Tap See in room | Bind exact variant/source photo | S13.LOADING |
| S11-A11 | S11.DETAIL | Add to compare or save | Snapshot variant and evidence time | S14.COMPARE |
| S11-A12 | S11.DETAIL | Recheck availability | Pending state, stale badge meanwhile | S11.RECHECKING |
| S11-A13 | S11.RECHECKING | Confirm exact variant & count | Update time/evidence | S11.VERIFIED |
| S11-A14 | S11.RECHECKING | Count drops, stale or error | Unavailable/unknown; no purchase action | S11.UNAVAILABLE |
| S11-A15 | S11.UNAVAILABLE | Find close replacement | Preserve prior choice/history | S18.CHANGE |
| S11-A16 | S11.DETAIL | Back to results | Preserve selected filters/scroll | S10.RESULTS |
| S11-A17 | S11.VERIFIED | Open updated product details | Exact six and timestamp remain visible | S11.DETAIL |
| S11-A18 | S11.VERIFIED | Recheck again | Mark stale while checking | S11.RECHECKING |
| S11-A19 | S11.VERIFIED | See exact variant in room | Bind verified SKU to visualization | S13.LOADING |

### S12 · Unconfirmed lead

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S12-A01 | S12.LEAD | Open listing/source | Show access limits and timestamp | S12.SOURCE |
| S12-A02 | S12.SOURCE | Return | Keep lead status | S12.LEAD |
| S12-A03 | S12.LEAD | Ask seller / request quantity | Record pending inquiry, no ready badge | S12.PENDING |
| S12-A04 | S12.PENDING | Seller confirms exact variant/count | Require evidence and freshness policy check | S11.VARIANT_PENDING |
| S12-A05 | S12.PENDING | No response / listing removed | Label unresolved or unavailable | S12.UNKNOWN |
| S12-A06 | S12.UNKNOWN | Save to hunt | Monitor only if access permitted | S19.SETUP |
| S12-A07 | S12.LEAD | Save or reject lead | Store reason without polluting ready rank | S12.LEAD |
| S12-A08 | S12.LEAD | Try manual source entry | Validate URL/rights and mark unverified | S12.PENDING |
| S12-A09 | S12.LEAD | Back to findings | Maintain separate lane | S10.RESULTS |

### S13 · Actual product in room

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S13-A01 | S13.LOADING | Render exact variant in original room | Bind image, SKU, geometry and renderer version | S13.PROCESSING |
| S13-A02 | S13.PROCESSING | Displayable output validated | Label illustrative, never physical proof | S13.PLACEMENT |
| S13-A03 | S13.PROCESSING | Missing exact finish/source image | No substitute claiming same SKU | S13.NEEDS_INPUT |
| S13-A04 | S13.PROCESSING | Geometry unknown or occluded | Ask specific measure; show low confidence | S13.NEEDS_INPUT |
| S13-A05 | S13.PROCESSING | Render/rights failure | Source photo plus dimension fallback | S13.ERROR |
| S13-A06 | S13.NEEDS_INPUT | Enter measurement | Version geometry, rerender | S05.MEASURE |
| S13-A07 | S13.NEEDS_INPUT | Continue without render | Honest source/fit view | S11.FIT |
| S13-A08 | S13.ERROR | Retry when permitted | Keep original photo visible | S13.LOADING |
| S13-A09 | S13.ERROR | View source image only | No fabricated composite | S11.EVIDENCE |
| S13-A10 | S13.PLACEMENT | Toggle Original / Placement / Dimensions | Maintain camera framing and disclosure | S13.PLACEMENT |
| S13-A11 | S13.PLACEMENT | Swap alternative exact variant | Invalidate old render; bind new SKU | S13.LOADING |
| S13-A12 | S13.PLACEMENT | Adjust placement or orientation | Preview reversible transform; scale bounds | S13.EDITING |
| S13-A13 | S13.EDITING | Save / undo / reset | Version composite without altering original | S13.PLACEMENT |
| S13-A14 | S13.PLACEMENT | Open source image or fit caveat | Explain lineage/measurements | S11.EVIDENCE |
| S13-A15 | S13.PLACEMENT | Compare options | Preserve photo/geometry baseline | S14.COMPARE |
| S13-A16 | S13.PLACEMENT | Back to candidate | Preserve chosen variant | S11.DETAIL |

### S14 · Mobile comparison

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S14-A01 | S14.COMPARE | Add/remove candidate | Update columns, retain source snapshot | S14.COMPARE |
| S14-A02 | S14.COMPARE | Swipe options / expand evidence | Show fit, stock time, condition, source | S11.DETAIL |
| S14-A03 | S14.COMPARE | Toggle room visual | Same original frame and caveats | S13.PLACEMENT |
| S14-A04 | S14.COMPARE | Edit delivery location | Recompute shipping/taxes; mark pending | S14.RECALCULATING |
| S14-A05 | S14.COMPARE | Edit flexible target | Show dollar and percent premium | S14.RECALCULATING |
| S14-A06 | S14.COMPARE | Edit hard cap | Exclude over-cap candidates, no auto override | S14.RECALCULATING |
| S14-A07 | S14.RECALCULATING | Cost complete | Re-rank eligible options | S14.COMPARE |
| S14-A08 | S14.RECALCULATING | Cost unknown | Label estimate and block certainty | S14.COST_UNKNOWN |
| S14-A09 | S14.COST_UNKNOWN | Ask for quote / choose other | Preserve explicit unknown | S12.LEAD |
| S14-A10 | S14.COMPARE | Select option within hard cap | Snapshot evidence and brief version | S16.BUDGET |
| S14-A11 | S14.COMPARE | Choose over hard cap | Disable selection; edit cap deliberately | S14.OVER_CAP |
| S14-A12 | S14.OVER_CAP | Back / choose eligible | Preserve hard cap | S14.COMPARE |
| S14-A13 | S14.COMPARE | Back to findings | Restore filters and scroll | S10.RESULTS |

### S15 · Desktop project canvas

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S15-A01 | S15.CANVAS | Choose project/room in rail | Load same object/version | S15.LOADING |
| S15-A02 | S15.LOADING | Room ready | Original photo and retained pieces | S15.CANVAS |
| S15-A03 | S15.LOADING | Image missing/error | Placeholder and Retry; no lost brief | S15.ERROR |
| S15-A04 | S15.ERROR | Retry or choose other room | Restore last view | S15.CANVAS |
| S15-A05 | S15.CANVAS | Toggle Original/Placement/Measures | Sync selected layer, confidence labels | S15.CANVAS |
| S15-A06 | S15.CANVAS | Click retained item | Edit Keep/tag/dimensions with Undo | S05.MEASURE |
| S15-A07 | S15.CANVAS | Edit brief in inspector | Version chips and invalidate old rank | S07.EDITING |
| S15-A08 | S15.CANVAS | Start research | Show source ledger | S08.QUEUED |
| S15-A09 | S15.CANVAS | Open research workspace | Same candidate model | S24.WORKSPACE |
| S15-A10 | S15.CANVAS | Speak shortcut | Same permission/transcript/undo lifecycle | S04.LISTENING |
| S15-A11 | S15.CANVAS | Client preview | Scope share only | S20.PREVIEW |
| S15-A12 | S15.CANVAS | Sync conflict | Show actor/time versions | S23.CONFLICT |
| S15-A13 | S15.CANVAS | Back to projects | Persist canvas/brief state | S03.HOME |

### S16 · Decision, budget & stock gate

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S16-A01 | S16.BUDGET | Inspect line items | Product, delivery, tax, fees, pickup/restoration | S16.BUDGET |
| S16-A02 | S16.BUDGET | Adjust quantity/location | Recalculate and reverify exact variant | S16.RECALCULATING |
| S16-A03 | S16.RECALCULATING | New cost/evidence ready | Show target delta and hard-cap status | S16.BUDGET |
| S16-A04 | S16.RECALCULATING | Cost unknown | Explain uncertainty; block ready handoff | S16.COST_UNKNOWN |
| S16-A05 | S16.BUDGET | Save choice | Version decision with evidence snapshot | S16.SAVED |
| S16-A06 | S16.BUDGET | Share with client | Preview scoped content | S20.PREVIEW |
| S16-A07 | S16.BUDGET | Tap open seller | Start mandatory stock, price, cap recheck | S16.RECHECKING |
| S16-A08 | S16.RECHECKING | Exact six/variant/cost under cap | Show timestamp and external destination | S17.HANDOFF |
| S16-A09 | S16.RECHECKING | Stock lost / count short | Preserve choice, offer replacement | S18.CHANGE |
| S16-A10 | S16.RECHECKING | Price rises over cap | Block handoff; edit cap or choose other | S16.OVER_CAP |
| S16-A11 | S16.RECHECKING | Source error/unknown | Keep as lead; retry, no ready CTA | S16.COST_UNKNOWN |
| S16-A12 | S16.OVER_CAP | Choose other or explicitly edit cap | Never silently increase cap | S14.COMPARE |
| S16-A13 | S16.SAVED | Resume decision | Recheck because evidence may expire | S16.RECHECKING |
| S16-A14 | S16.BUDGET | Back to comparison | Preserve alternatives | S14.COMPARE |
| S16-A15 | S16.COST_UNKNOWN | Retry cost and source check | Keep seller handoff disabled | S16.RECALCULATING |
| S16-A16 | S16.COST_UNKNOWN | Choose another option | Preserve unknown-cost record | S14.COMPARE |
| S16-A17 | S16.COST_UNKNOWN | Back to budget | Show missing amount prominently | S16.BUDGET |

### S17 · External seller handoff & earned usage

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S17-A01 | S17.HANDOFF | Open external seller | Disclose destination and stale-risk recheck time | S17.EXTERNAL |
| S17-A02 | S17.EXTERNAL | Return to Homely | Ask purchased, still considering or canceled | S17.RETURN |
| S17-A03 | S17.RETURN | Still considering | Keep decision saved, no purchase claim | S16.SAVED |
| S17-A04 | S17.RETURN | Mark purchased | User confirmation with optional receipt | S21.PURCHASED |
| S17-A05 | S17.RETURN | Cancel / seller unavailable | Keep history, recheck or replace | S18.CHANGE |
| S17-A06 | S17.HANDOFF | Eligible affiliate link | Record contracted attribution only | S17.PENDING_CREDIT |
| S17-A07 | S17.PENDING_CREDIT | Eligible realized commission | Hold return reserve and cost-limit credit | S17.RESERVED |
| S17-A08 | S17.PENDING_CREDIT | No contract/attribution | No assumed earning, transparent ledger | S21.LEDGER |
| S17-A09 | S17.RESERVED | Reserve clears under program terms | Release permitted usage credit | S21.CREDIT |
| S17-A10 | S17.RESERVED | Return/refund/reversal | Reverse pending credit with ledger reason | S21.REVERSED |
| S17-A11 | S17.HANDOFF | Back before opening seller | No purchase or attribution invented | S16.BUDGET |

### S18 · Stock-change alert & replacement

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S18-A01 | S18.CHANGE | Open meaningful alert | Show what changed and checked time | S18.DETAIL |
| S18-A02 | S18.DETAIL | Lost quantity (4 of 6) | Prior saved item unavailable for brief | S18.LOST |
| S18-A03 | S18.LOST | View previous decision | Retain snapshot and approval history | S16.SAVED |
| S18-A04 | S18.LOST | Open replacement candidate | Explain differences and reverify six | S11.DETAIL |
| S18-A05 | S18.LOST | No verified replacement | Show honest gap, save hunt | S09.EMPTY |
| S18-A06 | S18.DETAIL | New high-fit result | Open exact variant and evidence | S11.DETAIL |
| S18-A07 | S18.DETAIL | Unconfirmed local lead | Separate from ready replacements | S12.LEAD |
| S18-A08 | S18.DETAIL | Dismiss duplicate alert | Keep in activity without re-notifying | S19.ACTIVE |
| S18-A09 | S18.DETAIL | Change cadence/pause | Save notification preference | S19.SETTINGS |
| S18-A10 | S18.DETAIL | Back to inbox | Preserve read/unread and event | S19.INBOX |

### S19 · Saved hunts & notification inbox

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S19-A01 | S19.SETUP | Set sources/radius/category | Show unavailable sources and check limits | S19.SETTINGS |
| S19-A02 | S19.SETTINGS | Choose cadence/quiet hours | Estimate notification volume/cost | S19.SETTINGS |
| S19-A03 | S19.SETTINGS | Save active hunt | Version query; schedule allowed server checks | S19.ACTIVE |
| S19-A04 | S19.SETTINGS | Enable push | Permission primer only now | S02.PRIMER |
| S19-A05 | S19.ACTIVE | Open activity card | New/lost/price event with exact timestamp | S18.CHANGE |
| S19-A06 | S19.ACTIVE | Pause hunt | Stop future scheduled checks as feasible | S19.PAUSED |
| S19-A07 | S19.PAUSED | Resume hunt | Revalidate rights, sources, location and freshness | S19.ACTIVE |
| S19-A08 | S19.ACTIVE | End hunt | Confirm, retain historical results | S19.ENDED |
| S19-A09 | S19.ACTIVE | Refine brief | New job/query version, old activity retained | S07.EDITING |
| S19-A10 | S19.ACTIVE | Push denied/unsupported | In-app inbox remains usable | S19.INBOX |
| S19-A11 | S19.INBOX | Open read/unread event | Recheck before action | S18.CHANGE |
| S19-A12 | S19.ACTIVE | Source access suspended | Explain coverage gap, no phantom checks | S19.SOURCE_GAP |
| S19-A13 | S19.SOURCE_GAP | Retry allowed source or edit scope | Respect rights and backoff | S19.SETTINGS |
| S19-A14 | S19.ACTIVE | Offline | Cached inbox stale, no live claim | S23.OFFLINE |
| S19-A15 | S19.ACTIVE | Back to project | Keep hunt server status visible | S03.HOME |
| S19-A16 | S19.ENDED | Start a new hunt | Revalidate source scope and cadence | S19.SETUP |
| S19-A17 | S19.ENDED | Back to project | Historical activity remains visible | S03.HOME |

### S20 · Client share, approval & revisions

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S20-A01 | S20.PREVIEW | Select photos/notes to share | Show exact client-visible preview | S20.PREVIEW |
| S20-A02 | S20.PREVIEW | Choose client role and expiry | Enforce least-privilege scope | S20.VALIDATING |
| S20-A03 | S20.VALIDATING | Create link/invite | Log actor, permission, version | S20.REVIEW |
| S20-A04 | S20.VALIDATING | Invalid contact/scope | Inline correction, no sharing | S20.PREVIEW |
| S20-A05 | S20.REVIEW | Client opens link | Auth or limited token, check expiry/revocation | S20.REVIEW |
| S20-A06 | S20.REVIEW | Link expired/revoked | Access denied, owner renewal route | S20.EXPIRED |
| S20-A07 | S20.REVIEW | Compare option / room image | Show illustrative visual + stock time | S13.PLACEMENT |
| S20-A08 | S20.REVIEW | Comment on product | Thread to exact variant/version | S20.COMMENTING |
| S20-A09 | S20.COMMENTING | Post or cancel | Notify owner only if posted | S20.REVIEW |
| S20-A10 | S20.REVIEW | Approve variant | Record actor/time/version; no stock hold | S20.APPROVED |
| S20-A11 | S20.REVIEW | Request changes | Record reason and route designer brief | S20.REVISION |
| S20-A12 | S20.REVISION | Designer refine | Preserve earlier comments/approval record | S07.EDITING |
| S20-A13 | S20.APPROVED | Proceed toward seller | Mandatory stock/cost recheck | S16.RECHECKING |
| S20-A14 | S20.REVIEW | Owner revoke share | Prevent future access; exports remain outside scope | S20.EXPIRED |
| S20-A15 | S20.REVIEW | Back to project | Persist decision trail | S03.HOME |
| S20-A16 | S20.EXPIRED | Owner renews share | Preview scope and new expiry | S20.PREVIEW |
| S20-A17 | S20.EXPIRED | Client signs in or requests access | No expired content exposed | S01.INTENT |

### S21 · Decision & purchase ledger

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S21-A01 | S21.LEDGER | Open decision history | Show saved, proposed, approved, changed | S21.LEDGER |
| S21-A02 | S21.LEDGER | Mark purchased explicitly | Record actor/time, optional receipt evidence | S21.PURCHASED |
| S21-A03 | S21.LEDGER | External order unknown | Do not infer purchase from click | S21.UNKNOWN |
| S21-A04 | S21.UNKNOWN | Confirm later or stay considering | No false commission credit | S21.LEDGER |
| S21-A05 | S21.PURCHASED | Add receipt/warranty/condition | Private project attachment controls | S21.PURCHASED |
| S21-A06 | S21.PURCHASED | Mark returned/canceled | Update decision and credit reversal | S21.RETURNED |
| S21-A07 | S21.LEDGER | Inspect earned usage | Pending/reserved/released/reversed terms | S21.CREDIT |
| S21-A08 | S21.CREDIT | Open attribution explanation | Ranking independent of commission | S21.CREDIT |
| S21-A09 | S21.REVERSED | Inspect reversal reason | Refund/return and held reserve shown | S21.CREDIT |
| S21-A10 | S21.LEDGER | Reopen sourcing | Keep purchased history, new brief version | S07.EDITING |
| S21-A11 | S21.LEDGER | Back to project | Persist ledger | S03.HOME |
| S21-A12 | S21.RETURNED | Inspect changed decision ledger | Show return and credit reversal | S21.LEDGER |
| S21-A13 | S21.RETURNED | Start a replacement hunt | Preserve purchase history | S19.SETUP |

### S22 · Account, privacy & data

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S22-A01 | S22.SETTINGS | Edit profile or project memory | Show what is remembered and source | S22.MEMORY |
| S22-A02 | S22.MEMORY | Correct/delete preference | Version change, Undo when recoverable | S22.SETTINGS |
| S22-A03 | S22.SETTINGS | Change transcript/recording retention | Explain storage and deletion timing | S22.PRIVACY |
| S22-A04 | S22.PRIVACY | Save consent/retention | Stop capture/use if revoked | S22.SETTINGS |
| S22-A05 | S22.SETTINGS | Edit push/quiet hours | Sync to hunts; browser support caveat | S19.SETTINGS |
| S22-A06 | S22.SETTINGS | Inspect billing/credits | Model and ledger separate from ranking | S21.CREDIT |
| S22-A07 | S22.SETTINGS | Export photos/data | Queue archive, show status/download | S22.EXPORTING |
| S22-A08 | S22.EXPORTING | Export ready | Download to device; log time | S22.SETTINGS |
| S22-A09 | S22.EXPORTING | Export error | Retry without losing data | S22.EXPORT_ERROR |
| S22-A10 | S22.EXPORT_ERROR | Retry/cancel | Keep account state | S22.SETTINGS |
| S22-A11 | S22.SETTINGS | Delete photo/project recoverably | Show affected room, Undo/recovery period | S22.TRASH |
| S22-A12 | S22.TRASH | Restore or confirm | Return to account with history | S22.SETTINGS |
| S22-A13 | S22.SETTINGS | Request permanent purge | Action-time confirmation of irreversibility | S22.PURGE_CONFIRM |
| S22-A14 | S22.PURGE_CONFIRM | Confirm/abort | Purge only on confirmation; otherwise return | S22.SETTINGS |
| S22-A15 | S22.SETTINGS | Sign out | Warn about unsynced local edits | S01.INTENT |
| S22-A16 | S22.SETTINGS | Back | Return to invoking project | S03.HOME |

### S23 · Offline, reconnect & conflicts

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S23-A01 | S23.OFFLINE | Open cached room | Clearly label last sync time, allow viewing | S23.CACHED |
| S23-A02 | S23.CACHED | Edit note/brief offline | Queue versioned safe local edit | S23.QUEUED |
| S23-A03 | S23.CACHED | Try stock check/seller handoff | Disable live action, explain reconnection | S23.OFFLINE |
| S23-A04 | S23.CACHED | Storage quota exceeded | Keep unsaved work visible and export/copy fallback | S23.QUOTA |
| S23-A05 | S23.QUOTA | Resolve storage / retry | Do not claim edit synced | S23.QUEUED |
| S23-A06 | S23.QUEUED | Reconnect | Compare remote revision and permissions | S23.RECONCILING |
| S23-A07 | S23.RECONCILING | No conflict | Sync safe edits, refresh stock before action | S23.SYNCED |
| S23-A08 | S23.RECONCILING | Concurrent edit or revoked role | Present both actor/time versions | S23.CONFLICT |
| S23-A09 | S23.CONFLICT | Merge selected fields | Preview resolved version; save | S23.SYNCED |
| S23-A10 | S23.CONFLICT | Keep remote or local copy | Preserve losing version in history | S23.SYNCED |
| S23-A11 | S23.SYNCED | Return to project caller | Resume with refreshed project | S03.HOME |
| S23-A12 | S23.SYNCED | Return to room caller | Refresh room, preserve focus | S04.IDLE |
| S23-A13 | S23.SYNCED | Return to research caller | Refresh source ledger and job | S08.RUNNING |
| S23-A14 | S23.SYNCED | Return to decision caller | Require fresh stock/cost | S16.RECHECKING |
| S23-A15 | S23.SYNCED | Return to hunt caller | Refresh activity | S19.ACTIVE |
| S23-A16 | S23.SYNCED | Return to desktop caller | Refresh same project version | S15.CANVAS |
| S23-A17 | S23.OFFLINE | Back/cancel | Keep queued edit and status visible | S03.HOME |

### S24 · Desktop research workspace

| Action ID | From state | Control or event | Guard / feedback | Exact next state |
| --- | --- | --- | --- | --- |
| S24-A01 | S24.WORKSPACE | Change project/brief in rail | Load versioned results and scroll state | S24.LOADING |
| S24-A02 | S24.LOADING | Data ready | Show cards, source ledger and total budget | S24.WORKSPACE |
| S24-A03 | S24.LOADING | Failure/empty | Retry or edit brief, no fabricated cards | S09.EMPTY |
| S24-A04 | S24.WORKSPACE | Filter/sort candidates | Show objective criteria and eligible count | S24.FILTERED |
| S24-A05 | S24.FILTERED | Reset or inspect candidate | Preserve selected variant/filters | S11.DETAIL |
| S24-A06 | S24.WORKSPACE | Expand provenance/source gap | Show source URLs, times, unavailable access | S24.EVIDENCE |
| S24-A07 | S24.EVIDENCE | Close inspector | Return same comparison position | S24.WORKSPACE |
| S24-A08 | S24.WORKSPACE | Open unconfirmed leads | Separate from ready matrix | S12.LEAD |
| S24-A09 | S24.WORKSPACE | Select chairs and compare | All-in and hard-cap gate | S14.COMPARE |
| S24-A10 | S24.WORKSPACE | See variant in room | Preserve same original photo geometry | S13.LOADING |
| S24-A11 | S24.WORKSPACE | Recheck all | Stale badges until exact count/price confirmed | S24.REFRESHING |
| S24-A12 | S24.REFRESHING | Stock changed | Preserve historical choice, replacement route | S18.CHANGE |
| S24-A13 | S24.WORKSPACE | Share client review | Scope preview and permissions | S20.PREVIEW |
| S24-A14 | S24.WORKSPACE | Back to project canvas | Same data/version | S15.CANVAS |
| S24-A15 | S24.WORKSPACE | Sync conflict/offline | Status and reconciliation | S23.CONFLICT |


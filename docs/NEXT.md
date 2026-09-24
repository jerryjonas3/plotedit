# Next

In order. Each step should leave something that runs.

## 1. Make the Python importable as a package ✅ done 2026.09.23

- `scaled_pdf.py` now uses relative imports for `photometrics` and `dxf_bridge`.
- `make-eos-asc.py` renamed **`eos_ascii.py`** — a hyphen cannot be imported — and
  turned from a script with module-level constants into `build(show, groups, cues)`.
  The *Without Consent* data is kept as `EXAMPLE_*` and still prints via
  `python3 -m plotedit.eos_ascii`.
- `gels.csv` resolves off `__file__`, so it survived the move unchanged.
- `server/test_package.py` added — a smoke test, not a unit suite.

**🔴 It found a real bug, which is why this step exists.** `Sheet.unit()` tested
`color_gel.upper() in ph.GELS`, a plain dict lookup, so any compound notation
missed and **silently fell back to open white**. `R52+R119` — the acting-area wash,
the most common color in the archive — reported **729 fc instead of 169**. Fixed
here and in `My AI Brain/my-skills/plot/`, and the test now pins the value.

**Run it:** `cd server && python3 test_package.py`

## 2. A read-only service ✅ done 2026.09.23

`server/plotedit/api.py`. Six endpoints, nothing that writes:

| | |
|---|---|
| `GET /health` | fixture and gel counts |
| `GET /fixtures` | all 28, with beam/field, penumbra, candela, modes **and source** |
| `GET /gels` | all 11, with transmission and source, plus what `+` and `/` mean |
| `POST /compute` | instruments in; throw, elevation, pan, pools, footcandles out |
| `POST /wash` | field-to-beam spacing, and how many units cover a width |
| `GET /lens` | which barrel gives the pool you want at that throw |

**Run it:** `cd server && uvicorn plotedit.api:app --reload`
**Test it:** `cd server && python3 test_api.py` *(TestClient — no server needed)*

### Two decisions worth keeping

**Sources travel with the numbers.** `/fixtures` returns `"ETC S4 LED Photometry
Guide p7: Series 2 Lustr 26° EDLT"` alongside the candela. Strip that and the front
end has no way to show that a Lustr figure is EDLT-only — which is exactly the
mistake that had to be corrected once already.

**The API refuses rather than guesses.** No trim or focus → `computed: false` and
a reason. Unknown fixture → the same. Unknown gel → the level is returned but
flagged as open white. A fixture with no published beam angle → HTTP 400 quoting
the manual. **A missing number must never arrive looking like a real one.**

### CORS is localhost only

This runs on the designer's laptop at tech, not on a network. Origins are pinned
to the Vite dev server.

## 3. A drawing surface that renders a plot it cannot edit ✅ done 2026.09.23

Vite + TypeScript, SVG, no interaction yet.

| File | |
|---|---|
| `web/src/geometry.ts` | the transform, with its own test — `npm test` |
| `web/src/plot.ts` | the `.plot.json` types |
| `web/src/render.ts` | SVG drawing: room, positions, symbols, focus, pools, USITT annotation |
| `web/src/api.ts` | talks to the Python |
| `web/src/main.ts` | loads the sample, computes, draws, fills the schedule |
| `samples/bluver.plot.json` | ten instruments in the Bluver |
| `server/plot_to_pdf.py` | the same file through `scaled_pdf` — the start of step 5 |

**Run it:** `cd server && uvicorn plotedit.api:app` and `cd web && npm run dev`

### Decisions

**SVG, not canvas.** A 60-unit plot is small either way, SVG is easier to get right,
and every instrument is a DOM node — which is hit testing for free in step 4.

**Everything inside the root `<g>` is drawn in real feet.** The group transform
carries the scale and the y flip, so the markup reads in the units of the room.
Text needs `counterFlip()`.

**Screen scale is pixels per foot, not an architectural scale.** ¼" = 1'-0"
belongs to paper and stays in `scaled_pdf.py`. On screen it zooms; on paper it
must measure true. Keep the two apart.

### 🔴 It found the second real bug

`scaled_pdf.unit()` had **no `mode` parameter**, so an LED fixture was computed at
its reference output no matter what the plot asked for. The Lustr units read
**441 fc on paper and 382 on screen** — the same rig, disagreeing, because
"Regulated 3200K" never reached the function. Fixed in both copies.

**`server/test_agreement.py` now pins it:** both paths start from the same
`.plot.json` and every throw, pool and footcandle must match.

## 4. Editing ✅ done 2026.09.23

| File | |
|---|---|
| `web/src/store.ts` | one plot, one selection, an undo stack, and pipe snapping. Own test: `npm run test:store` |
| `web/src/interact.ts` | pointer and keyboard — drag, select, nudge, delete, undo |
| `web/src/inspector.ts` | the selected record, editable, nineteen fields |

**Verified in the browser:** dragging unit 1 from GRID C onto GRID D re-set its
`position` by itself, and the server recomputed — throw 13'-4" → 16'-5", pool
5'-11" → 7'-4", level **179 fc → 118 fc**. One undo restored all of it and left
the stack empty. Changing a color in the inspector took unit 3 from 185 fc to
**72 fc through R80 at 9%**.

### Decisions

**A whole drag is one undo step.** `store.begin(key)` coalesces consecutive edits
sharing a key; `commit()` ends the run. Eight pointer moves, one undo.

**Snapshots are deep clones of the whole plot.** A plot is a few dozen
instruments. No diffing, no proxies, nothing to debug at two in the morning
during a tech.

**⭐ Instruments snap to pipes, and set their own `position`.** A unit at y = 20.3
when the pipe is at 20 is wrong on paper and wrong in the room, and nobody
notices until it is printed. Alt-drag places one off a pipe deliberately.
Dragging *far* past the end of a pipe does not snap back — silently yanking a
unit seven feet is worse than leaving it where it was put.

**Focus is a separate handle.** Aiming a unit and moving it are different
decisions; conflating them is how a focus gets lost while tidying a hang.

**Positions round to the nearest inch.** Sub-inch precision on a light plot is a
lie.

**Photometric fields recompute; paperwork fields do not.** Type, trim, focus,
color, lamp and mode hit the server, debounced. Purpose and notes do not — a
round trip per keystroke is noise.

**Edits commit on `change`, not `input`**, so half-typed values never reach the
server.

### Keyboard

`↑↓←→` nudge an inch · `⇧` + arrow nudges a foot · `Delete` removes ·
`Esc` deselects · `⌘Z` / `⇧⌘Z` undo and redo

## 5. Import and export ✅ done 2026.09.23

**Out** — `server/plotedit/exports.py`, offered from the toolbar:

| | |
|---|---|
| Plot PDF | architectural scale, scale bar, 1-inch check. Scale picker: ⅛ ¼ ⅜ ½ |
| Plot DXF | layered, in feet — for a rented Vectorworks month |
| Instrument schedule | CSV, by position then unit — hanging order |
| Channel hookup | CSV, by channel — what the board sees |
| Eos patch | USITT ASCII ⚠ **format unverified** |
| Magic sheet | JSON, channels grouped by purpose — no layout yet |

**In** — a venue's `.dxf` becomes the base drawing. Layers are listed first with
their counts and the declared units, the chosen ones come back as polylines in
feet, and they draw in gray under everything.

### Decisions

**A plot that will not fit FAILS with the scale that would.** `/export/pdf`
returns 422 carrying the sheet's own warning, and the front end puts it in the
status line. A clipped PDF looks finished and is not.

**The imported extents are announced.** *"imported 8 paths, 33.0' × 38.0' —
check that against something you measured."* Unit headers lie, and a venue's
drawing is their claim rather than a survey.

**🔴 The Eos patch format has never been tested against a console.** The cue
exporter was reverse-engineered from a real Eos export after three guesses
failed; no real *patch* export was available. **The warning is written into the
file's own header**, so it travels with it. Units missing a channel or an
address are listed as comments rather than dropped — a silently missing unit at
tech is worse than a noisy file.

### 🔴 It found the third real bug

`Content-Disposition` is a latin-1 header, and the export filenames carry an em
dash — *"Without Consent — Plot.pdf"*. Every download raised
`UnicodeEncodeError`. Fixed with RFC 5987: an ASCII fallback plus
`filename*=UTF-8''…`, verified present in both forms.

**Test:** `cd server && python3 test_export.py`

---

## Next, in no particular order

- ~~Fixture names from paperwork do not match the photometric table keys.~~
  ✅ **Done 2026.09.23 — `server/plotedit/fixture_names.py`.** Measured against
  the real archive first: **none of the 38 distinct names matched**, so an
  imported plot drew correctly and was silently unlit. Now **81% resolve**
  (196 of 242 instruments) and the rest carry a stated reason.

  Three layers: **normalise** (strip the maker, unify Source4/S4, deg/°, repair
  latin-1 mojibake), **ALIASES** for what normalising cannot reach, and
  **NO_DATA** for real fixtures with no figures on file. Photometrics, the symbol
  picker and `POST /resolve-names` all go through it, and the footcandle note
  says how a name was read: *"at HPL 575 (MF 0.78) ['ETC Source4 26deg' read as
  'S4 36']"*.

  **ColorSource datasheets fetched 2026.09.23** — the Spot photometry guide (13
  pp, all nine lenses plus the zooms, three output modes) and the CYC datasheet.
  **The archive is now at 91%**, 221 of 242 instruments.

  **The archive is at 98%** — 237 of 242 instruments. The last ambiguous name,
  `ETC Source4 LED 26deg`, was settled by asking: Jerry confirmed the eight on
  *Wizard of Oz* (2022) were **Lustrs**. The paperwork itself had already
  narrowed it — they load at 140w against 166w for the ColorSource units in the
  same rig, so they were a different fixture — but only he could say which array.

  **All that remains is a hazer and a strobe, which are not luminaires.** That is
  the correct floor, not a gap.

- ~~Ask Altman for the Spectra Cyc IES file.~~ ✅ **Jerry found them on Altman's
  support page, 2026.09.23.** No email needed — Altman publish IES for the
  Spectra Cyc **100 and 200** (not the 50). `ies.py` parses LM-63, and the
  Spectra Cyc 100 is now the one fixture in the table whose figures come from a
  **real 46 × 73 goniometric measurement** rather than a datasheet table:
  4,612 cd, 4,727 lm, 94.1 W, peak at 70° off nadir. The datasheet corroborates
  the lumens exactly.

- **🔴 Were the Wizard of Oz cycs 50s or 100s?** The paperwork says
  `Altman Spectra CYC 50` at 50w — but in Lightwright the load comes from the
  library entry for the named fixture, so the name and the wattage are ONE fact,
  not two. **Jerry believes they were 100s.** Both models are in the table; the
  alias still points the paperwork name at the 50, which has no photometrics.
  **Settle it and the alias changes, and four instruments gain real numbers.**

- **More IES files are worth having.** Altman publish them for several fixtures;
  ETC publish IES for the whole Source Four and ColorSource range. Anywhere a
  datasheet is thin, the IES is not.

- ✅ **Symbols approved 2026.09.23.** Jerry passed all 18 of Rev 3 plus the three line weights. **The gate on drawing more is open.** Next: §6.6 cyc units and §6.7 striplights — both are in his archive (Altman Sky Cyc, ColorSource CYC, Altman Spectra Cyc). Then followspots §6.10 and accessories §6.13.

  **Still not settled by approval:** the PARNel axis line means either beam axis or lens rotation, and both look identical, so his eye cannot resolve it.

---

**⚠ Resist the urge to start at step 4.** Steps 1–3 are where the coordinate
system and the data model get settled, and they are cheap to change until
something is drawn on top of them.

---

## Positions — started 2026.09.23

**Jerry: "we should do positions next — for now, horizontal ones — catwalks,
electrics, etc," and then: "catwalks are also FOH (front of house) positions."**

Done:

- **`type` on a position** — `electric` · `pipe` · `grid` · `catwalk` · `truss`.
  It decides the drawing, and the distinction is physical. An electric is one
  heavy batten line. **A catwalk is a WALKWAY**: two architectural edges with a
  hanging pipe inboard of the downstage one, because a person stands on it and
  the units hang off the rail rather than down the middle. A unit drawn on the
  centre of a catwalk is drawn three feet from where it is.
- **FOH.** A catwalk is front of house, over the audience, downstage of the
  plaster line — **negative y**. `foh_extent()` reports how far downstage the
  positions reach and `plot_to_pdf` shifts the origin to cover it. Without that
  the catwalk is clipped off the bottom and only the clipping guard would say so.
- `railOffset` overrides the pipe's inboard distance — **it varies by house, so
  take it off the venue's section rather than from the default.**

### ✅ Which end is unit 1 — answered 2026.09.23

**Jerry: *"SR is unit 1 because the numbers actually go house left to house
right — easier to read, and visualize from the house."*** And: *"on a pipe that
runs US -> DS, I tend to have unit 1 be farthest DS."*

**⭐ The principle is the reading direction from the house, not the geometry.**
Unit numbers run the way a person reads the plot while standing in the room:
left to right across a lateral position, near to far on one running up and down
the stage. It is a rule about legibility, and the coordinates are only how it
gets expressed.

| Position runs | Unit 1 at | In this file's coordinates |
|---|---|---|
| Stage left–right | stage right (= house left) | the maximum x, counting down |
| Upstage–downstage | farthest downstage | the minimum y, counting up |

The two move opposite ways along their axes. **That looks like an inconsistency
and is not one** — they are the same rule seen from the house. ⚠ So if this is
ever unified, unify it on the **reading direction**, never on the sign of a
coordinate.

*(Corrected 2026.09.23: an earlier version of this note led with the coordinate
mechanics and called the two rules opposites, which is true and is not the
point. Jerry: "I don't really care about x and y, it's not used except for maybe
hanging." The reason is what generalises to the cases nobody has coded yet.)*

`positions.py` has `axis()`, `number_from()`, `order()`, `number()` and
`describe()`, which states the convention in words for the plot's own notes —
*"Elect 1: unit 1 at stage right — numbers read house left to house right."*
**`numberFrom`** (`SR`/`SL`/`DS`/`US`) is the override, and always wins.

Two refusals: **two units at one coordinate warn** rather than being ordered
arbitrarily, and **nothing renumbers automatically**, because on a hung plot a
renumber is a different document from the one taped to the pipe.

### ✅ Circuits — 2026.09.23

**Jerry: *"circuits depend on the house — no set order."*** That one sentence is
the whole design. **`circuits.py` never invents a circuit number.** Unit numbers
follow a rule and can be generated; circuits do not and cannot. A house wired its
pipes in whatever order made sense to whoever did it, and the only source of
truth is that house — its rep plot, its circuit map, or its ME standing under the
pipe.

So the module **records what the house says and checks the plot against it**:

- `circuits` on a position is an **inventory** in the house's own order. Bare
  numbers (`[7, 8, 9]`) or records with a location along the pipe.
- `circuitSource` — **a circuit list without a provenance is a rumour**, and an
  unsourced list is reported as one. This is what `/venue` asks for the rep plot
  to fill.
- `check()` catches a circuit the house has not got, a position not in the plot,
  and a position with nothing recorded (not an error — but no load table can be
  built for it).
- **A twofer is reported, never rejected.** Two units on one circuit is legal and
  common; it is a LOAD question, and it goes to Art.
- `match_to_units()` **refuses when the house gave no locations.** Pairing a
  circuit list against units in order would look like a result and be a guess,
  and a plot patched to the wrong circuits reads as correct until half the rig
  does not come on.
- ⚠ And when it *can* match, it **reports every doubling it creates** — there are
  routinely more units on a pipe than circuits under it. A matcher that silently
  doubles up is worse than one that refuses: the refusal gets dealt with, the
  silent twofer gets discovered by a breaker.

The circuit is drawn in a **hexagon** (§6.14.1 — the shape carries the meaning)
and has a column on both the instrument schedule and the hookup.

### ✅ Dimmer per circuit — 2026.09.23

**Jerry: *"most houses have circuit per dimmer. We need to account for that."***

RP-2 §6.14.1 gives **three control models and notates them differently**, so this
changes the drawing, not only the data:

| `control` | Containers | |
|---|---|---|
| **`dimmer-per-circuit`** *(default)* | hexagon + circle | The circuit is hard-wired to its own dimmer. **One number, not two** — RP-2 labels the hexagon "Circuit & Dimmer" |
| `hard-and-soft-patch` | hexagon + rectangle + circle | All three differ, so all three are drawn |
| `no-soft-patch` | hexagon + circle | The console addresses dimmers directly |

**Drawing two containers in a dimmer-per-circuit house is not harmlessly
redundant — it tells the electrician there is a patch to make, and there is
not.** A dimmer that merely repeats the circuit is dropped, and a plot that gives
them *different* numbers is reported: either the control model is wrong or one of
them is a typo.

**And the load follows.** With no patch to hide behind, **the load on a circuit
IS the load on a dimmer.** `circuits.load()` totals watts per circuit and, given
the house's per-dimmer rating, reports headroom. The 2026.09 fault was a pack
over capacity, and this is the arithmetic that would have shown it.

- **The rating is never assumed.** 2400W is the common 20-amp figure and it is
  also wrong in plenty of buildings. Without it, loads are reported and nothing
  is judged — a capacity check against an unconfirmed number reads as a *pass*.
- **A tungsten unit's watts belong to its LAMP**, not its body: the same Source
  Four is 575W or 750W depending on what is in it. `lamp_watts()` reads it off
  the lamp name, which is exact rather than inferred.
- ⚠ **And it refuses to read a number out of just any string.** "Regulated 3200K"
  is an LED output mode; a loose search finds 3200 in it and calls it 3200 watts
  — a number that looks real, lands in a load total and trips a breaker. A lamp
  name has to look like one.

**🔴 Only 2 of 47 fixtures carry a wattage** (the two Spectra Cycs, from their
IES). Tungsten is covered by the lamp name, but **every LED's draw has to come
from its datasheet** — ETC's are already on file. Until then an LED counts as
zero and the total is reported as *a floor, not a total*.

### Still to do

- Auto-numbering along a position, once the direction is known.
- **Vertical positions — booms, box booms, ladders.** Explicitly out of scope
  until asked: RP-2 §6.12 makes them a different drawing problem, with their own
  height-designation conventions and two accepted layouts.

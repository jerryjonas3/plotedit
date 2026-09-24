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

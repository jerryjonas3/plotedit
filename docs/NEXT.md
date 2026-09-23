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

## 3. A drawing surface that renders a plot it cannot edit  ← next

Load a `.plot.json`, draw the room and the instruments, no interaction.
Get the coordinate transform right once — real feet in, screen pixels out —
and everything after is easier.

**Done when:** `samples/test.plot.json` renders and matches the PDF `scaled_pdf.py`
produces from the same data.

## 4. Editing

Drag to move, click to select, edit the record in a side table. Both views on
one record.

## 5. Import and export

DXF ground plan in. Plot PDF, schedule, hookup, DXF and Eos patch out —
all five already exist server-side.

---

**⚠ Resist the urge to start at step 4.** Steps 1–3 are where the coordinate
system and the data model get settled, and they are cheap to change until
something is drawn on top of them.

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

## 2. A read-only service

FastAPI, three endpoints:

- `GET /fixtures` — the FIXTURES table with sources
- `GET /gels` — the gel table
- `POST /compute` — a list of instruments in, throw/pool/footcandles out

**Done when:** it answers `curl localhost:8000/fixtures`.

## 3. A drawing surface that renders a plot it cannot edit

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

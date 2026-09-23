# Next

In order. Each step should leave something that runs.

## 1. Make the Python importable as a package

The modules were written as scripts that import each other by bare name
(`import photometrics`). Inside a package they need relative imports, and
`scaled_pdf.py` looks for `gels.csv` beside itself — check that still resolves.

**Done when:** `python -c "from plotedit import photometrics; print(photometrics.report('S4 26', (6,20,14), (10,10,5.5), lamp='HPL 575'))"` works from the repo root.

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

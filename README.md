# plotedit

A light plot editor. Draw the plot, get the paperwork.

**Not a CAD program.** The ground plan comes in as DXF; this never draws architecture.
See [docs/SPEC.md](docs/SPEC.md) for what it is, what it is not, and why it is
TypeScript over Python rather than Rust.

## Why it exists

Vectorworks is subscription-only and Lightwright has followed. A designer lighting
ten units on a pipe in a 75-seat room pays a professional-tier subscription to do it.
The tools exist for large productions; nobody serves the small room.

It also fixes a real problem: a `.vwx` file needs a live subscription to open. Two
shows in this designer's own archive are locked inside drawings nothing on the
machine can read. **A plot here is plain JSON** — readable in a text editor, diffable,
and still openable in twenty years.

## Status

**Draws a plot, edits it, imports a ground plan and exports the paperwork.**
All five steps of `docs/NEXT.md` are done. What is left is in the list at its end.
The computation half was already working and is in `server/plotedit/`:

| Module | Does |
|---|---|
| `photometrics.py` | Throw, elevation, pan, beam and field pools, footcandles, gel transmission, wash spacing, lens choice |
| `scaled_pdf.py` | Architectural-scale PDF with a scale bar and a 1-inch check; section drawings; warns rather than clipping |
| `dxf_bridge.py` | DXF in (a venue's ground plan as the base drawing) and DXF out |
| `paperwork.py` | Reads Lightwright XLSX exports, Vectorworks/Lightwright SLData XML, and `.lw6` vocabularies |
| `make-eos-asc.py` | USITT ASCII cue and patch files that ETC Eos actually imports |

**What is missing is interaction** — clicking and dragging instead of editing a script.
That is what this repo is for.

## Layout

```
server/plotedit/   the Python that does the work, plus a FastAPI wrapper
web/src/           the TypeScript front end
symbols/           instrument symbols, drawn to USITT RP-2
samples/           a test ground plan and a test plot
docs/SPEC.md       scope, architecture, the instrument record, v1 vs later
```

## Running it

The service runs; the front end does not exist yet.

```bash
cd server
pip install -r requirements.txt
uvicorn plotedit.api:app --reload      # http://localhost:8000/docs for the API browser
python3 test_package.py                # the computation half
python3 test_api.py                    # the service
```

```bash
cd web
npm install
npm run dev          # http://localhost:5173 — needs the service running
npm test             # the coordinate transform
npm run test:store   # undo, selection, pipe snapping
```

Both halves must agree about the numbers:

```bash
cd server
python3 test_package.py      # the computation half
python3 test_api.py          # the service
python3 test_agreement.py    # screen and paper must agree
python3 test_export.py       # exports, and DXF import
```

Eventually: one command, opens a browser tab, no network.

## Data sources

Photometrics come from ETC's own datasheets; gel transmissions from Rosco's product
pages and the myColor swatch app. **Every fixture row names its source.** Where two
sources disagree — the ETC Europe spread table of 2000 and the modern US datasheets
differ on the 26° and 36° — both are kept and the preferred one is marked.

## Names

Paperwork calls a fixture `ETC Source4 36deg`; the photometric table calls it
`S4 36`. **None of the 38 distinct instrument names in the source archive matched
a table key** — plots imported from Lightwright drew correctly and were silently
unlit, every throw computed and every pool and level blank.

`server/plotedit/fixture_names.py` resolves them: normalise, then explicit
aliases, then a list of real fixtures with no photometrics on file and the reason
why. **81% of the archive resolves**; the remainder say what is missing rather
than returning nothing.

```bash
cd server && python3 test_names.py
```

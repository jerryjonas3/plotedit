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

Scaffolded 2026.09.23. The computation half already works and is in `server/plotedit/`:

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

Not runnable yet. When it is: one command, opens a browser tab, no network.

## Data sources

Photometrics come from ETC's own datasheets; gel transmissions from Rosco's product
pages and the myColor swatch app. **Every fixture row names its source.** Where two
sources disagree — the ETC Europe spread table of 2000 and the modern US datasheets
differ on the 26° and 36° — both are kept and the preferred one is marked.

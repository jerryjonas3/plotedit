# Decisions

Short entries. What was decided, when, and why — so it is not re-argued.

## 2026.09.23 — A plot editor, not a CAD program

Vectorworks is a general platform: walls, stairs, 3D solids, a plant database.
Building a "simple version" means building 95% of it to use 5%. **Scope is a light
plot and its paperwork.** Architecture arrives as DXF and is never drawn here.

## 2026.09.23 — TypeScript over Python, not Rust

The original thought was Rust. Set aside because:

- No Rust toolchain on the machine; Node 22 and .NET 7 are installed.
- The computation half is already written and tested in Python.
- What is missing is **interaction**, which is a front-end problem.
- It has to run at tech on a laptop with no internet — a local server and a
  browser tab is the least fragile way.

**Rust remains legitimate as a second version once the shape is proven.** It was
set aside because the goal is the tool.

## 2026.09.23 — The file format is plain JSON

One `.plot.json` per show. Readable, diffable, git-able, and openable without a
subscription. This is a direct response to two shows in the designer's archive
being locked inside `.vwx` files nothing can read.

## 2026.09.23 — Field names follow the Vectorworks/Lightwright exchange

`position · unit · channel · dimmer · address · universe · type · wattage · color ·
gobo · purpose · focus · trim · accessory · notes`. Using the names the industry
already uses means `paperwork.py` imports old shows with no translation layer.

## Open

- **Symbols.** The designer's own convention is Field Template / SoftSymbols for ETC
  with AutoPlot for cable and truss, but those are `.vwx` and cannot be reused.
  This needs its own set drawn to USITT RP-2. `scaled_pdf.py` has a first pass;
  **it needs marking up before more are drawn.**
- **Canvas or SVG** for the drawing surface. SVG is easier to get right, canvas
  scales better with instrument count. A 60-unit plot is small either way.

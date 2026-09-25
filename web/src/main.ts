/*
 * plotedit — a light plot editor for small rigs.
 * Copyright (C) 2026 Jerry Jonas
 *
 * This program is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the Free
 * Software Foundation, either version 3 of the License, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <https://www.gnu.org/licenses/>.
 */
/** Load a plot, draw it, let it be edited. */
import { fitView, fohExtent, type View } from "./geometry.js";
import { isPlot, symbolKey, plotFileName, newPlot, type Plot } from "./plot.js";
import { render, POS_CHAR_W, POS_TEXT, type Computed, type RenderOptions } from "./render.js";
import { compute, fixtures, exportFile, dxfLayers, dxfPaths, symbols, booms,
         positionLabels, savePlot, listPlots, loadPlot, pdfPages, pdfPaths,
         type FixtureRow, type ExportKind, type DxfPaths, type SymbolPrim,
         type BoomElevation, type PositionLabel } from "./api.js";
import { Store } from "./store.js";
import { attachPointer, attachKeyboard } from "./interact.js";
import { renderInspector } from "./inspector.js";
import { renderPositions } from "./positions.js";
import { renderDetails } from "./details.js";

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const svg = $<HTMLElement>("plot") as unknown as SVGSVGElement;

let store: Store;
let computed: Computed[] = [];
let fixtureTable: Record<string, FixtureRow> = {};
let basePlan: DxfPaths | null = null;
let symbolCache: Record<string, SymbolPrim[]> = {};

function view(): View {
  const pxPerFoot = Number($<HTMLInputElement>("zoom").value);
  const margin = VIEW_MARGIN;
  const { width, depth } = store.plot.room;
  // ⭐ The canvas has to be tall enough for the HOUSE as well as the stage.
  // Front-of-house positions sit at negative y, and a view fitted to the room
  // alone simply does not show them — no warning, no clipping guard, just a
  // catwalk that is not there.
  const house = fohExtent(store.plot.positions);
  // ⭐ And WIDE enough for the boom elevations, which sit off the stage-left
  // edge at negative x. The server says how much room they need — the same
  // figure plot_to_pdf uses to set its origin.
  return fitView(width, depth,
                 (width + boomSpace + margin * 2) * pxPerFoot,
                 (depth + house + margin * 2) * pxPerFoot, margin, house, boomSpace);
}

/** The height to cut the pools at. Aiming and cutting are different choices:
 *  a unit aimed at a face still throws a much larger pool on the deck. */
/** How much width the §6.12 boom elevations need, in feet. Filled by the
 *  server; 0 until it answers, which simply means no elevations are drawn yet. */
/** Clear air drawn around the room, in feet. Also what a position name is
 *  allowed to use beyond the walls. */
const VIEW_MARGIN = 4;
let boomSpace = 0;
let boomLayout: BoomElevation[] = [];
let labelLayout: PositionLabel[] = [];

function poolPlane(): number | undefined {
  const v = ($<HTMLSelectElement>("poolplane")?.value ?? "");
  return v === "" ? undefined : Number(v);
}

function opts(): RenderOptions {
  return {
    showPools: $<HTMLInputElement>("pools").checked,
    showFocus: $<HTMLInputElement>("focus").checked,
    showLabels: $<HTMLInputElement>("labels").checked,
    selected: store.selected,
    basePaths: $<HTMLInputElement>("base").checked ? basePlan?.paths : undefined,
    symbols: symbolCache,
    booms: boomLayout,
    labels: labelLayout,
  };
}

function draw() { render(svg, store.plot, view(), computed, opts()); }

function fillTable() {
  const tb = $<HTMLTableElement>("schedule").querySelector("tbody")!;
  tb.replaceChildren();
  store.plot.instruments.forEach((inst, i) => {
    const c = computed[i];
    const tr = document.createElement("tr");
    tr.dataset.index = String(i);
    if (i === store.selected) tr.classList.add("sel");
    const cells: [string, boolean][] = [
      [inst.position ?? "", false], [String(inst.unit), false],
      [inst.channel !== undefined ? String(inst.channel) : "", false],
      [inst.type, false], [inst.color ?? "—", false],
      // ⚠ UNKNOWN, never a blank. An empty cell in a load column reads as
      // "nothing on that circuit", which is how a dimmer gets loaded past its
      // rating on paper.
      [c ? (c.watts != null ? `${c.watts}` : "UNKNOWN") : "—", true],
      [c?.throw_ft ?? "—", true], [c?.field_ft ?? "—", true],
      [c?.footcandles != null ? String(c.footcandles) : "—", true],
    ];
    for (const [text, num] of cells) {
      const td = document.createElement("td");
      if (num) td.className = "num";
      td.textContent = text;
      tr.appendChild(td);
    }
    if (c && !c.computed) tr.classList.add("warn");
    tr.title = c?.footcandles_note ?? c?.note ?? "";
    tr.addEventListener("click", () => store.select(i));
    tb.appendChild(tr);
  });
}

function drawInspector() {
  // ⚠ Two callbacks, because two kinds of field. A designer's name only prints;
  // a room width moves every position and every check that depends on one.
  // Wiring both to draw() would leave the throws and the headroom warnings
  // describing a room that is no longer there.
  renderDetails($("details"), store, {
    onChange: () => { paintChrome(); draw(); },
    onGeometry: () => { paintChrome(); draw(); recompute(); },
  });
  renderPositions($("positions"), store, {
    onChange: () => { draw(); recompute(); },
    onStatus: (msg, bad) => status(msg, bad),
  });
  renderInspector($("inspector"), store, computed, {
    fixtures: Object.keys(fixtureTable).sort(),
    lamps: ["HPL 750", "HPL 575", "HPL 575X"],
    modes: ["Boost Full", "Regulated Full", "Regulated 3200K", "Regulated 5600K"],
    onStatus: (msg, bad) => status(msg, bad),
    onPhotometricChange: () => { paint(); recompute(); },
    onPaperworkChange: () => paint(),
  });
}

/** Redraw everything from current state. Cheap — no network. */
function paint() {
  draw();
  fillTable();
  drawInspector();
  paintChrome();
  // ⚠ Clicking a light has to SHOW the light. Leaving the Instrument panel shut
  // while its fields quietly change behind the header is worse than the space
  // it costs — the click would look like it did nothing.
  if (store.selected !== null) {
    const inst = document.getElementById("panel-instrument") as HTMLDetailsElement | null;
    if (inst && !inst.open) inst.open = true;
  }
  $("dirty").textContent = store.dirty ? "Unsaved changes" : "";
  ($("undo") as HTMLButtonElement).disabled = !store.canUndo;
  ($("redo") as HTMLButtonElement).disabled = !store.canRedo;
  // ⭐ Each section header says what is IN it. The three panels were three grey
  // blocks that had to be read to be told apart; a count in the header answers
  // "which one is this" and "is there anything here" in one glance.
  const sel = store.selected;
  const inst = sel === null ? undefined : store.plot.instruments[sel];
  $("inst-count").textContent = inst
    ? `Unit ${inst.unit}${inst.channel === undefined ? "" : ` · ch ${inst.channel}`}`
    : "none selected";
  $("pos-count").textContent = String(store.plot.positions.length);
  $("sched-count").textContent = String(store.plot.instruments.length);
}

/** Remember which panels are open, per browser.
 *
 * ⭐ Jerry, 2026.09.24: "can the cards showing positions, schedule, show etc be
 * accordions so they don't take up real estate when we don't want them."
 * Collapsing one is only useful if it STAYS collapsed — reopening everything on
 * every reload would mean doing the tidying again each time.
 *
 * ⚠ localStorage throws in a private window and can come back empty, so every
 * read and write is guarded and the panels simply default to open. A layout
 * preference is not worth an exception that stops the editor loading.
 */
const PANELS = ["details", "instrument", "positions", "schedule"] as const;

function wirePanels(): void {
  for (const name of PANELS) {
    const el = document.getElementById(`panel-${name}`) as HTMLDetailsElement | null;
    if (!el) continue;
    try {
      const saved = localStorage.getItem(`plotedit.panel.${name}`);
      if (saved !== null) el.open = saved === "1";
    } catch { /* no storage — leave it open */ }
    el.addEventListener("toggle", () => {
      try { localStorage.setItem(`plotedit.panel.${name}`, el.open ? "1" : "0"); }
      catch { /* nothing to do; the panel still works this session */ }
    });
  }
}

/** The header's own copy of the show and venue, so editing them in the panel
 *  is visibly the same fact as the one at the top of the window. */
function paintChrome(): void {
  $("show").textContent = store.plot.show || "Untitled";
  $("venue").textContent =
    [store.plot.venue, store.plot.revision].filter(Boolean).join(" · ");
  $("det-count").textContent = store.plot.venue || "no venue";
}

/** Fetch RP-2 outlines for any fixture type not already held. */
async function ensureSymbols() {
  const want = [...new Set(store.plot.instruments.map(symbolKey))]
    .filter(t => t && !(t in symbolCache));
  if (!want.length) return;
  try {
    Object.assign(symbolCache, await symbols(want));
  } catch (e) {
    // Drawing the wrong shape is worse than drawing a plain ring, which is
    // what render() falls back to when a type is missing from the cache.
    status(e instanceof Error ? e.message : String(e), true);
  }
}

/** Where the §6.12 boom elevations go. Asked of the server, never worked out
 *  here: the compression is a drawing decision, and a second copy of it in
 *  TypeScript is how the screen and the paper drifted three times in a week. */
async function ensureBooms() {
  try {
    const r = await booms(store.plot);
    boomLayout = r.booms;
    boomSpace = r.space;
  } catch (e) {
    // ⚠ Say so. A boom whose elevation failed to load is a boom whose units are
    // not on the drawing at all — silence would read as "there are none".
    boomLayout = [];
    boomSpace = 0;
    status(e instanceof Error ? e.message : String(e), true);
  }
}

/** Where the position names go, fitted around the units and each other. Asked
 *  of the server so the screen and the paper choose the same slots. */
async function ensureLabels() {
  try {
    // ⚠ The canvas edge, in plot feet. Without it the fitter will happily put
    // a long name in clear air past the stage-right wall — clear of every
    // symbol and off the side of the view, which is a position with no name.
    // The margin is a CONSTANT chosen before fitting, so there is no circle
    // between "where do the labels go" and "how wide is the canvas".
    const { width, depth } = store.plot.room;
    labelLayout = await positionLabels(store.plot, POS_CHAR_W, POS_TEXT,
      [-boomSpace, -VIEW_MARGIN, width + VIEW_MARGIN, depth + VIEW_MARGIN]);
  } catch (e) {
    // ⚠ Fall back to the old stage-left-end placement rather than dropping the
    // names. A collision is untidy; an unnamed pipe is unusable.
    labelLayout = [];
    status(e instanceof Error ? e.message : String(e), true);
  }
}

/** Ask the Python what the light does. Debounced — a drag is one request. */
let pending: ReturnType<typeof setTimeout>;
function recompute(delay = 120) {
  clearTimeout(pending);
  pending = setTimeout(async () => {
    try {
      computed = await compute(store.plot, poolPlane());
      await ensureSymbols();
      await ensureBooms();
      await ensureLabels();
      paint();
    } catch (e) {
      showError(e);
    }
  }, delay);
}

/** The file on disk this plot belongs to, or null for one never saved.
 *
 * ⭐ Jerry, 2026.09.24: "the save is not automatically overwriting the file —
 * it tries a new name Without Consent.plot (1).json." That bracket is the
 * browser's DOWNLOAD behaviour. Save was built on the File System Access API,
 * which can overwrite in place — but only Chrome and Edge have it, so anywhere
 * else every press dropped another copy in Downloads and the real plot was
 * whichever had the longest number in brackets.
 *
 * ⚠ ONE code path now, through the server, which has a filesystem and needs no
 * permission to use it. Two paths — a browser API here, a server call there —
 * would mean Save behaved differently on different machines, which is exactly
 * the class of divergence that has cost a day already in this repo.
 */
let savedAs: string | null = null;

function plotJson(): string {
  return JSON.stringify(store.plot, null, 2);
}

async function saveTo(name: string): Promise<void> {
  const { path } = await savePlot(name, store.plot);
  savedAs = name;
  store.markSaved();
  status(`Saved ${path}`);
  void refreshOpenList();
}

async function saveAs(): Promise<void> {
  const suggested = savedAs ?? plotFileName(store.plot.show);
  const name = window.prompt(
    "Save this plot as — a file name, saved in the plots folder:", suggested);
  if (name === null) return;          // cancelled is not an error
  try {
    await saveTo(name.trim());
  } catch (e) {
    status(e instanceof Error ? e.message : String(e), true);
  }
}

async function save(): Promise<void> {
  if (!savedAs) { await saveAs(); return; }
  try {
    await saveTo(savedAs);
  } catch (e) {
    // ⚠ Say so, and say which file. A save that did not happen and reports
    // nothing is how a day of work goes missing.
    status(e instanceof Error ? e.message : String(e), true);
  }
}

/** Keep the Open menu in step with what is actually on disk. */
async function refreshOpenList(): Promise<void> {
  const sel = $("open") as HTMLSelectElement;
  try {
    const { plots, folder } = await listPlots();
    sel.replaceChildren();
    const head = document.createElement("option");
    head.value = ""; head.textContent = plots.length ? "Open…" : "Open… (none saved yet)";
    sel.appendChild(head);
    for (const p of plots) {
      const o = document.createElement("option");
      o.value = p.name;
      o.textContent = p.show ? `${p.show} — ${p.name}` : p.name;
      sel.appendChild(o);
    }
    sel.title = `Plots in ${folder}`;
  } catch (e) {
    // The list is a convenience; failing to fetch it must not stop the editor.
    sel.title = e instanceof Error ? e.message : String(e);
  }
}

/** Bring in a ground plan from a PDF.
 *
 * ⚠ TWO THINGS A PDF CANNOT TELL US, and both are asked rather than guessed:
 *
 *   THE SCALE. A PDF measures paper — points, 72 to the printed inch. The only
 *   route to feet is the "1/4\" = 1'-0\"" printed in its title block, and
 *   nothing in the file states it in a form anything can read.
 *
 *   WHICH PAGE. A set of drawings is one file; the ground plan is rarely page 1.
 *
 * ⚠ And no layers. A DXF import can take WALLS and leave the title block
 * behind; a PDF is one flat pile of strokes, so the border and every dimension
 * line arrive with the walls. Said out loud rather than discovered.
 */
async function importPdf(file: File): Promise<void> {
  try {
    status("reading the PDF…");
    const { pages, scales } = await pdfPages(file);

    // ⚠ A scanned plan has no vectors at all. Saying so beats importing nothing
    // and looking broken.
    const usable = pages.filter(p => p.items > 0);
    if (!usable.length) {
      status(`${file.name} has no vector drawing in it — if the plan is a scan `
             + `there is nothing to import`, true);
      return;
    }

    let page = usable[0]!.page;
    if (usable.length > 1) {
      const list = usable.map(p =>
        `  page ${p.page}: ${p.width_in}" x ${p.height_in}", ${p.items} lines`).join("\n");
      const answer = window.prompt(`${file.name}\n\n${list}\n\nWhich page?`,
                                   String(page));
      if (answer === null) { status(""); return; }
      page = Number(answer);
    }

    const scale = window.prompt(
      `What scale is that drawing?\n\nIt is printed in the title block — a PDF `
      + `does not record it.\n\nOne of: ${scales.join(", ")}`, "1/4");
    if (scale === null) { status(""); return; }

    const got = await pdfPaths(file, page, scale.trim());
    basePlan = got;
    const [x0, y0, x1, y1] = got.extents ?? [0, 0, 0, 0];
    // ⚠ Say the size out loud. At the wrong scale this is still a believable
    // drawing, just of a different building — the number is the only way to
    // catch it.
    status(`${got.paths.length} paths at ${scale}" = 1'-0" — `
           + `${(x1 - x0).toFixed(1)}' x ${(y1 - y0).toFixed(1)}' including the sheet border. `
           + `Check that against something you measured.`);
    ($("base") as HTMLInputElement).checked = true;
    draw();
  } catch (err) {
    status(err instanceof Error ? err.message : String(err), true);
  }
}

/** Ask before throwing away unsaved work. `what` completes "…and lose them?" */
function mayDiscard(what: string): boolean {
  if (!store.dirty) return true;
  return window.confirm(
    `This plot has unsaved changes.\n\n${what} and lose them?`);
}

/** Put a different plot in the editor.
 *
 * ⚠ Shared by Open and New, because both have to do the SAME five things — a
 * fresh store, a fresh subscription, the pointer and keyboard handlers
 * reattached to it, the symbol cache emptied, and a recompute. New was written
 * as a copy of Open first, and copy number three is where one of them quietly
 * stops re-attaching a handler and dragging silently edits the plot you closed.
 */
async function adoptPlot(plot: Plot, savedName: string | null): Promise<void> {
  store = new Store(plot);
  savedAs = savedName;
  store.subscribe(paint);
  attachPointer(svg, store, { view, onChange: draw, onSettled: () => recompute() });
  attachKeyboard(store, { view, onChange: draw, onSettled: () => recompute() });
  symbolCache = {};
  await recompute(0);
}

async function openPlot(name: string): Promise<void> {
  if (!mayDiscard("Open a different plot")) return;
  try {
    await adoptPlot(await loadPlot(name), name);
    status(`Opened ${name}`);
  } catch (e) {
    status(e instanceof Error ? e.message : String(e), true);
  }
}

async function newFile(): Promise<void> {
  if (!mayDiscard("Start a new plot")) return;
  const show = window.prompt("What is the show called?", "Untitled");
  if (show === null) return;                 // cancelled is not an error
  // ⚠ savedAs is null, so the first Save ASKS where to put it rather than
  // overwriting whatever was open a moment ago.
  await adoptPlot(newPlot(show.trim() || "Untitled"), null);
  status("New plot — set the room and the venue in Show & Venue, "
         + "then add a position.");
}

function status(msg: string, bad = false) {
  const el = $("status");
  el.textContent = msg;
  el.className = bad ? "warn" : "muted";
}

function showError(e: unknown) {
  const box = $("err");
  box.hidden = false;
  box.textContent = `${e instanceof Error ? e.message : String(e)}

Is the Python service running?
    cd server && uvicorn plotedit.api:app --reload`;
}

async function boot() {
  try {
    // ⭐ Open what you were last working on. Starting on the bundled sample
    // every time means a designer's first act at every session is to find their
    // own plot again — and, for anyone who has just downloaded this, it means
    // their work disappears the moment they reload.
    let opened: Plot | null = null;
    try {
      const { plots } = await listPlots();          // newest first
      const newest = plots[0];
      if (newest) {
        opened = await loadPlot(newest.name);
        savedAs = newest.name;
      }
    } catch {
      // No server answer, or no plots folder yet. The sample below is a fine
      // first screen; it is not worth refusing to start over.
    }

    if (!opened) {
      // ⚠ The DEMO, not the test fixture. samples/bluver.plot.json is what the
      // suites assert against and it is labelled "test data, not a design";
      // demo.plot.json is the one a stranger should meet first.
      const r = await fetch("/demo.plot.json");
      if (!r.ok) throw new Error(`cannot load the demo plot: ${r.status}`);
      const json: unknown = await r.json();
      if (!isPlot(json)) throw new Error("that file is not a plot (formatVersion must be 1)");
      opened = json as Plot;
    }

    store = new Store(opened);
    fixtureTable = await fixtures();

    paintChrome();
    // ⚠ The room's provenance and the plot notes are not shown in the app at
    // all — not as a block, not as a tooltip. Jerry, 2026.09.24: "lose it."
    // The PDF still prints the room's source across the top of the drawing,
    // which is the copy that leaves the building.

    store.subscribe(paint);
    attachPointer(svg, store, { view, onChange: draw, onSettled: () => recompute() });
    attachKeyboard(store, { view, onChange: draw, onSettled: () => recompute() });

    // ⚠ poolplane is NOT in this list — it changes the NUMBERS, not just what is
    // shown, so it has to recompute rather than redraw. Wired separately below;
    // adding it here would have moved the picker and left the pools unchanged.
    for (const id of ["pools", "focus", "labels", "base", "zoom"])
      $(id).addEventListener("input", draw);
    $("poolplane").addEventListener("change", () => { void recompute(); });

    // ---- export
    $("export").addEventListener("change", async (e) => {
      const sel = e.target as HTMLSelectElement;
      const kind = sel.value as ExportKind;
      sel.value = "";
      if (!kind) return;
      try {
        await exportFile(kind, store.plot, { scale: $<HTMLSelectElement>("scale").value });
        status("");
      } catch (err) {
        // The commonest failure is the sheet refusing to clip, and it says
        // which scale would fit. That belongs in front of the user, not a console.
        status(err instanceof Error ? err.message : String(err), true);
      }
    });

    // ---- import a venue ground plan
    $("dxf").addEventListener("change", async (e) => {
      const input = e.target as HTMLInputElement;
      const file = input.files?.[0];
      input.value = "";
      if (!file) return;
      // ⭐ Jerry, 2026.09.24: "could we do the same for PDFs too?" A PDF is what
      // comes back when you ask a house for its plan — it is what their drawing
      // office exports for everybody. Same button, because to the reader it is
      // the same act: here is the room, draw it underneath.
      if (file.name.toLowerCase().endsWith(".pdf")) { await importPdf(file); return; }
      try {
        status("reading the DXF…");
        const info = await dxfLayers(file);
        const names = info.layers.map(l => `${l.name} (${l.entities})`).join(", ");
        const want = prompt(
          `${file.name}\nUnits declared: ${info.units}\nLayers: ${names}\n\n` +
          `Which layers? Comma-separated, or blank for all.`, "");
        if (want === null) { status(""); return; }
        const units = info.units === "unitless"
          ? prompt("The file declares no units. in / ft / mm / cm / m?", "in") ?? undefined
          : undefined;
        basePlan = await dxfPaths(file, want ? want.split(",").map(s => s.trim()) : undefined, units);
        const [x0, y0, x1, y1] = basePlan.extents ?? [0, 0, 0, 0];
        // Unit headers lie. Say the size out loud so it can be checked against
        // a dimension that is actually known.
        status(`imported ${basePlan.paths.length} paths, ` +
               `${(x1 - x0).toFixed(1)}' x ${(y1 - y0).toFixed(1)}' — check that against something you measured`);
        $<HTMLInputElement>("base").checked = true;
        draw();
      } catch (err) {
        status(err instanceof Error ? err.message : String(err), true);
      }
    });
    $("undo").addEventListener("click", () => { store.undo(); recompute(); });
    $("redo").addEventListener("click", () => { store.redo(); recompute(); });
    $("new").addEventListener("click", () => void newFile());
    $("save").addEventListener("click", () => void save());
    $("saveas").addEventListener("click", () => void saveAs());
    $("open").addEventListener("change", (e) => {
      const sel = e.target as HTMLSelectElement;
      const name = sel.value;
      sel.value = "";
      if (name) void openPlot(name);
    });
    wirePanels();
    void refreshOpenList();
    // ⌘S saves, ⇧⌘S saves as. The browser's own Save-page dialog is not what
    // anyone means by ⌘S with a plot open.
    window.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        void (e.shiftKey ? saveAs() : save());
      }
    });
    window.addEventListener("beforeunload", (e) => {
      if (store.dirty) { e.preventDefault(); e.returnValue = ""; }
    });

    computed = await compute(store.plot, poolPlane());
    await ensureSymbols();
    await ensureBooms();
    await ensureLabels();
    paint();
  } catch (e) {
    showError(e);
  }
}

boot();

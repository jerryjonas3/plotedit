/** Load a plot, draw it, let it be edited. */
import { fitView, fohExtent, type View } from "./geometry.js";
import { isPlot, symbolKey, plotFileName, type Plot } from "./plot.js";
import { render, POS_CHAR_W, POS_TEXT, type Computed, type RenderOptions } from "./render.js";
import { compute, fixtures, exportFile, dxfLayers, dxfPaths, symbols, booms,
         positionLabels,
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
  renderPositions($("positions"), store, { onChange: () => { draw(); recompute(); } });
  renderInspector($("inspector"), store, computed, {
    fixtures: Object.keys(fixtureTable).sort(),
    lamps: ["HPL 750", "HPL 575", "HPL 575X"],
    modes: ["Boost Full", "Regulated Full", "Regulated 3200K", "Regulated 5600K"],
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

/** The file this plot was last saved to, if the browser can hold one.
 *
 * ⭐ Jerry, 2026.09.24: "we should have a save and save as button." There was
 * only one button and it was Save As in disguise — every press pushed another
 * copy into Downloads, so a session of ten saves left ten files and the newest
 * one was whichever had the longest numeric suffix.
 *
 * ⚠ The File System Access API is not everywhere. Where it is missing, Save
 * cannot overwrite anything and both buttons download — which is the OLD
 * behaviour, so nothing is lost, but the app SAYS so rather than letting the
 * button quietly mean something different from what it says.
 */
let fileHandle: FileSystemFileHandle | null = null;
const canWriteFiles = typeof window.showSaveFilePicker === "function";

function plotJson(): string {
  return JSON.stringify(store.plot, null, 2);
}

function suggestedName(): string {
  return plotFileName(store.plot.show);
}

function download(): void {
  const blob = new Blob([plotJson()], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = suggestedName();
  a.click();
  URL.revokeObjectURL(a.href);
  store.markSaved();
  status(canWriteFiles ? `Downloaded ${suggestedName()}`
                       : `Downloaded ${suggestedName()} — this browser cannot save in place`);
}

async function writeTo(handle: FileSystemFileHandle): Promise<void> {
  const w = await handle.createWritable();
  await w.write(plotJson());
  await w.close();
  store.markSaved();
  status(`Saved ${handle.name}`);
}

async function saveAs(): Promise<void> {
  if (!canWriteFiles) { download(); return; }
  try {
    const handle = await window.showSaveFilePicker!({
      suggestedName: suggestedName(),
      types: [{ description: "Light plot", accept: { "application/json": [".json"] } }],
    });
    fileHandle = handle;
    await writeTo(handle);
  } catch (e) {
    // ⚠ Cancelling a file dialog is not an error. Reporting it as one trains
    // the reader to ignore the status line, which is where the REAL failures
    // are about to appear.
    if (e instanceof DOMException && e.name === "AbortError") return;
    status(e instanceof Error ? e.message : String(e), true);
  }
}

async function save(): Promise<void> {
  if (!fileHandle) { await saveAs(); return; }
  try {
    await writeTo(fileHandle);
  } catch (e) {
    // The file moved, or permission lapsed. Ask again rather than silently
    // failing to save what the button said it saved.
    status(`Could not write ${fileHandle.name} — choose where to save it`, true);
    fileHandle = null;
    await saveAs();
  }
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
    const r = await fetch("/bluver.plot.json");
    if (!r.ok) throw new Error(`cannot load the sample plot: ${r.status}`);
    const json: unknown = await r.json();
    if (!isPlot(json)) throw new Error("that file is not a plot (formatVersion must be 1)");

    store = new Store(json as Plot);
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
    $("save").addEventListener("click", () => void save());
    $("saveas").addEventListener("click", () => void saveAs());
    if (!canWriteFiles) {
      ($("save") as HTMLButtonElement).title =
        "This browser cannot save in place — both buttons download a copy";
    }
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

/** Load a plot, draw it, let it be edited. */
import { fitView, type View } from "./geometry.js";
import { isPlot, type Plot } from "./plot.js";
import { render, type Computed, type RenderOptions } from "./render.js";
import { compute, fixtures, exportFile, dxfLayers, dxfPaths,
         type FixtureRow, type ExportKind, type DxfPaths } from "./api.js";
import { Store } from "./store.js";
import { attachPointer, attachKeyboard } from "./interact.js";
import { renderInspector } from "./inspector.js";

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const svg = $<HTMLElement>("plot") as unknown as SVGSVGElement;

let store: Store;
let computed: Computed[] = [];
let fixtureTable: Record<string, FixtureRow> = {};
let basePlan: DxfPaths | null = null;

function view(): View {
  const pxPerFoot = Number($<HTMLInputElement>("zoom").value);
  const margin = 4;
  const { width, depth } = store.plot.room;
  return fitView(width, depth, (width + margin * 2) * pxPerFoot,
                 (depth + margin * 2) * pxPerFoot, margin);
}

function opts(): RenderOptions {
  return {
    showPools: $<HTMLInputElement>("pools").checked,
    showFocus: $<HTMLInputElement>("focus").checked,
    showLabels: $<HTMLInputElement>("labels").checked,
    selected: store.selected,
    basePaths: $<HTMLInputElement>("base").checked ? basePlan?.paths : undefined,
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
  $("dirty").textContent = store.dirty ? "unsaved" : "";
  ($("undo") as HTMLButtonElement).disabled = !store.canUndo;
  ($("redo") as HTMLButtonElement).disabled = !store.canRedo;
}

/** Ask the Python what the light does. Debounced — a drag is one request. */
let pending: ReturnType<typeof setTimeout>;
function recompute(delay = 120) {
  clearTimeout(pending);
  pending = setTimeout(async () => {
    try {
      computed = await compute(store.plot);
      paint();
    } catch (e) {
      showError(e);
    }
  }, delay);
}

function save() {
  const blob = new Blob([JSON.stringify(store.plot, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${store.plot.show.replace(/[^\w -]/g, "")}.plot.json`;
  a.click();
  URL.revokeObjectURL(a.href);
  store.markSaved();
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

    $("show").textContent = store.plot.show;
    $("venue").textContent = [store.plot.venue, store.plot.revision].filter(Boolean).join(" · ");
    $("notes").textContent =
      [store.plot.room.source, ...(store.plot.notes ?? [])].filter(Boolean).join("  ");

    store.subscribe(paint);
    attachPointer(svg, store, { view, onChange: draw, onSettled: () => recompute() });
    attachKeyboard(store, { view, onChange: draw, onSettled: () => recompute() });

    for (const id of ["pools", "focus", "labels", "base", "zoom"])
      $(id).addEventListener("input", draw);

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
    $("save").addEventListener("click", save);
    window.addEventListener("beforeunload", (e) => {
      if (store.dirty) { e.preventDefault(); e.returnValue = ""; }
    });

    computed = await compute(store.plot);
    paint();
  } catch (e) {
    showError(e);
  }
}

boot();

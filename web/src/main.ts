/** Load a plot, ask the Python what the light does, draw it. No editing yet. */
import { fitView } from "./geometry.js";
import { isPlot, type Plot } from "./plot.js";
import { render, type Computed, type RenderOptions } from "./render.js";
import { compute } from "./api.js";

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const svg = $<HTMLElement>("plot") as unknown as SVGSVGElement;

let plot: Plot;
let computed: Computed[] = [];

function opts(): RenderOptions {
  return {
    showPools: $<HTMLInputElement>("pools").checked,
    showFocus: $<HTMLInputElement>("focus").checked,
    showLabels: $<HTMLInputElement>("labels").checked,
  };
}

function draw() {
  const pxPerFoot = Number($<HTMLInputElement>("zoom").value);
  const margin = 4;
  const w = (plot.room.width + margin * 2) * pxPerFoot;
  const h = (plot.room.depth + margin * 2) * pxPerFoot;
  render(svg, plot, fitView(plot.room.width, plot.room.depth, w, h, margin), computed, opts());
}

function fillTable() {
  const tb = $<HTMLTableElement>("schedule").querySelector("tbody")!;
  tb.replaceChildren();
  plot.instruments.forEach((inst, i) => {
    const c = computed[i];
    const tr = document.createElement("tr");
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
    tb.appendChild(tr);
  });
}

async function boot() {
  try {
    const r = await fetch("/bluver.plot.json");
    if (!r.ok) throw new Error(`cannot load the sample plot: ${r.status}`);
    const json: unknown = await r.json();
    if (!isPlot(json)) throw new Error("that file is not a plot (formatVersion must be 1)");
    plot = json;

    $("show").textContent = plot.show;
    $("venue").textContent = [plot.venue, plot.revision].filter(Boolean).join(" · ");
    // The room's provenance belongs on screen, not buried in the file.
    $("notes").textContent = [plot.room.source, ...(plot.notes ?? [])].filter(Boolean).join("  ");

    computed = await compute(plot);
    fillTable();
    draw();
    for (const id of ["pools", "focus", "labels", "zoom"])
      $(id).addEventListener("input", draw);
  } catch (e) {
    const box = $("err");
    box.hidden = false;
    box.textContent = `${e instanceof Error ? e.message : String(e)}

Is the Python service running?
    cd server && uvicorn plotedit.api:app --reload`;
  }
}

boot();

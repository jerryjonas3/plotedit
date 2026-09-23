/**
 * Draw a plot as SVG. Read-only — no interaction yet.
 *
 * SVG rather than canvas: a 60-unit plot is small either way, SVG is easier to
 * get right, and every instrument becomes a DOM node, which is hit testing for
 * free when step 4 needs dragging.
 *
 * Everything inside the root <g> is drawn in REAL FEET. The group's transform
 * carries the scale and the y flip, so the markup reads in the units of the
 * room — which matters when something looks wrong on screen.
 */
import { svgTransform, counterFlip, fmtFt, type View } from "./geometry.js";
import type { Plot, Instrument } from "./plot.js";

const NS = "http://www.w3.org/2000/svg";

/** What the server said about each instrument, keyed by array index. */
export interface Computed {
  computed: boolean;
  throw?: number; throw_ft?: string;
  elevation?: number; pan?: number;
  field?: number; field_ft?: string;
  beam?: number; beam_ft?: string;
  footcandles?: number | null;
  footcandles_note?: string;
  gel_warning?: string;
  note?: string;
}

export interface RenderOptions {
  showPools: boolean;
  showFocus: boolean;
  showLabels: boolean;
}

function el(name: string, attrs: Record<string, string | number>): SVGElement {
  const e = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  return e;
}

/** Line widths and text sizes are in FEET, so they scale with the drawing.
 *  Divided by the view scale they would be constant on screen; we want them
 *  to grow with zoom, the way ink on paper does. */
const W = { room: 0.25, position: 0.4, focus: 0.08, pool: 0.06, dim: 0.06 };
const TEXT = 1.0;      // feet — about 12" tall, legible at a whole-room zoom

export function render(
  svg: SVGSVGElement, plot: Plot, view: View,
  computed: Computed[], opts: RenderOptions,
): void {
  svg.replaceChildren();
  svg.setAttribute("width", String(view.width));
  svg.setAttribute("height", String(view.height));
  svg.setAttribute("viewBox", `0 0 ${view.width} ${view.height}`);

  const root = el("g", { transform: svgTransform(view) });
  svg.appendChild(root);

  const layer = (cls: string) => {
    const g = el("g", { class: cls });
    root.appendChild(g);
    return g;
  };
  // draw order: room, pools, positions, focus, instruments, labels
  const gRoom = layer("room"), gPools = layer("pools"), gPos = layer("positions");
  const gFocus = layer("focus"), gInst = layer("instruments"), gText = layer("labels");

  // ---- the room
  gRoom.appendChild(el("rect", {
    x: 0, y: 0, width: plot.room.width, height: plot.room.depth,
    fill: "none", stroke: "#333", "stroke-width": W.room,
  }));
  // a foot grid, faint, so distances are readable without measuring
  for (let x = 5; x < plot.room.width; x += 5)
    gRoom.appendChild(el("line", { x1: x, y1: 0, x2: x, y2: plot.room.depth,
      stroke: "#e8e8e8", "stroke-width": W.dim }));
  for (let y = 5; y < plot.room.depth; y += 5)
    gRoom.appendChild(el("line", { x1: 0, y1: y, x2: plot.room.width, y2: y,
      stroke: "#e8e8e8", "stroke-width": W.dim }));

  // ---- positions
  for (const p of plot.positions) {
    gPos.appendChild(el("line", {
      x1: p.x1, y1: p.y1, x2: p.x2, y2: p.y2,
      stroke: "#222", "stroke-width": W.position, "stroke-linecap": "round",
    }));
    if (opts.showLabels) {
      const t = el("text", {
        transform: counterFlip(p.x1, p.y1 + 0.8),
        "font-size": TEXT * 0.8, "font-family": "system-ui, sans-serif",
        "font-weight": "600", fill: "#222",
      });
      t.textContent = p.trim ? `${p.name} — trim ${fmtFt(p.trim)}` : p.name;
      gText.appendChild(t);
    }
  }

  // ---- instruments
  plot.instruments.forEach((inst, i) => {
    const c = computed[i];
    const hasFocus = inst.focusX !== undefined && inst.focusY !== undefined;

    if (opts.showPools && c?.field && hasFocus) {
      gPools.appendChild(el("circle", {
        cx: inst.focusX!, cy: inst.focusY!, r: c.field / 2,
        fill: "none", stroke: "#bbb", "stroke-width": W.pool, "stroke-dasharray": "0.6 0.4",
      }));
    }
    if (opts.showFocus && hasFocus) {
      gFocus.appendChild(el("line", {
        x1: inst.x, y1: inst.y, x2: inst.focusX!, y2: inst.focusY!,
        stroke: "#999", "stroke-width": W.focus, "stroke-dasharray": "0.5 0.35",
      }));
      gFocus.appendChild(el("circle", {
        cx: inst.focusX!, cy: inst.focusY!, r: 0.25,
        fill: "none", stroke: "#999", "stroke-width": W.focus,
      }));
    }
    gInst.appendChild(symbol(inst, c));
    if (opts.showLabels) gText.appendChild(labels(inst, c));
  });
}

/**
 * A first-pass instrument symbol, drawn at real size and pointed at the focus.
 *
 * ⚠ These approximate USITT RP-2. Jerry's own convention is Field Template /
 * SoftSymbols, which are .vwx and cannot be reused. He has not marked up the
 * draft sheet yet — see docs/DECISIONS.md. Do not draw more until he has.
 */
function symbol(inst: Instrument, c?: Computed): SVGElement {
  const g = el("g", { class: "instrument", "data-unit": inst.unit, "data-channel": inst.channel ?? "" });
  // pan is degrees clockwise from pointing downstage (-y)
  const pan = c?.pan ?? 0;
  const body = el("g", { transform: `translate(${inst.x} ${inst.y}) rotate(${-pan})` });

  const t = inst.type;
  if (/PAR/i.test(t)) {
    body.appendChild(el("rect", { x: -0.34, y: -0.5, width: 0.68, height: 1.0,
      fill: "#fff", stroke: "#111", "stroke-width": 0.08, rx: 0.3 }));
  } else if (/Fresnel/i.test(t)) {
    body.appendChild(el("rect", { x: -0.34, y: -0.42, width: 0.68, height: 0.84,
      fill: "#fff", stroke: "#111", "stroke-width": 0.08 }));
    body.appendChild(el("line", { x1: -0.34, y1: -0.42, x2: 0.34, y2: -0.42,
      stroke: "#111", "stroke-width": 0.18 }));
  } else {
    // ellipsoidal: body plus a lens tube whose LENGTH codes the beam angle —
    // narrower field, longer tube, the way the real barrels look.
    const field = fieldOf(t);
    const tube = field ? Math.max(0.35, Math.min(1.1, 22 / field * 0.42)) : 0.6;
    body.appendChild(el("rect", { x: -0.3, y: -0.38, width: 0.6, height: 0.76,
      fill: "#fff", stroke: "#111", "stroke-width": 0.08 }));
    body.appendChild(el("rect", { x: -0.21, y: -0.38 - tube, width: 0.42, height: tube,
      fill: "#fff", stroke: "#111", "stroke-width": 0.08 }));
  }
  // the yoke point, which is where the unit actually is
  body.appendChild(el("circle", { cx: 0, cy: 0, r: 0.12, fill: "#111" }));
  g.appendChild(body);
  return g;
}

/** Field angle by name, for tube length only. The server holds the real table. */
function fieldOf(type: string): number | null {
  const m = /(\d+(?:\.\d+)?)\s*(?:deg|°)?\s*(?:EDLT|LT)?$/.exec(type.trim());
  return m?.[1] ? Number(m[1]) : null;
}

/** Unit number above, channel in a bubble below, color and type beside —
 *  the USITT annotation positions. */
function labels(inst: Instrument, c?: Computed): SVGElement {
  const g = el("g", { class: "annot" });
  const add = (dx: number, dy: number, s: string, size: number, weight = "400", fill = "#111") => {
    const t = el("text", {
      transform: counterFlip(inst.x + dx, inst.y + dy),
      "font-size": size, "font-family": "system-ui, sans-serif",
      "font-weight": weight, fill, "text-anchor": "middle",
    });
    t.textContent = s;
    g.appendChild(t);
  };
  add(0, 1.1, String(inst.unit), TEXT * 0.75, "700");
  if (inst.channel !== undefined) {
    g.appendChild(el("circle", { cx: inst.x, cy: inst.y - 1.5, r: 0.55,
      fill: "#fff", stroke: "#111", "stroke-width": 0.07 }));
    add(0, -1.7, String(inst.channel), TEXT * 0.62, "600");
  }
  const side: string[] = [];
  if (inst.type) side.push(inst.type);
  if (inst.color) side.push(inst.color);
  if (side.length) {
    const t = el("text", {
      transform: counterFlip(inst.x + 0.75, inst.y - 0.1),
      "font-size": TEXT * 0.5, "font-family": "system-ui, sans-serif", fill: "#555",
    });
    t.textContent = side.join(" · ");
    g.appendChild(t);
  }
  if (c?.footcandles) {
    const t = el("text", {
      transform: counterFlip(inst.x + 0.75, inst.y - 0.7),
      "font-size": TEXT * 0.45, "font-family": "system-ui, sans-serif", fill: "#888",
    });
    t.textContent = `${c.throw_ft} @ ${c.elevation?.toFixed(0)}° · ${c.footcandles} fc`;
    g.appendChild(t);
  }
  return g;
}

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
import { svgTransform, counterFlip, fmtFt, notationAnchor, symbolRadius, type View } from "./geometry.js";
import { symbolKey, isVertical, isFoh, type Plot, type Instrument } from "./plot.js";
import type { SymbolPrim } from "./api.js";

const NS = "http://www.w3.org/2000/svg";

/** What the server said about each instrument, keyed by array index. */
export interface Computed {
  /** The REAL pool: an ellipse on a horizontal plane. A cone only cuts a circle
   *  when it points straight down, and at 30° elevation a 26° field lands more
   *  than twice as long as it is wide. `angle` is the plan direction of the
   *  major axis; the centre is NOT the aim point — it sits beyond it. */
  pool?: { a: number; b: number; cx: number; cy: number; angle: number;
           near: number; far: number; length: number; width: number };
  /** Why there is no pool — grazing, or a plane above the unit. */
  pool_note?: string;
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
  /** Index into plot.instruments, or null. */
  selected?: number | null;
  /** A venue's DXF, already in feet. Drawn under everything, in gray. */
  basePaths?: { layer: string; points: [number, number][] }[];
  /** RP-2 symbol outlines by fixture type, from GET /symbols. */
  symbols?: Record<string, SymbolPrim[]>;
}

function isSelNow(opts: RenderOptions, i: number): boolean {
  return opts.selected === i;
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
  const gBase = layer("base"), gRoom = layer("room"), gPools = layer("pools"),
        gPos = layer("positions");

  // ---- the venue's own drawing, if one was imported.
  // Their claim, not a measurement — drawn quietly, under everything.
  for (const path of opts.basePaths ?? []) {
    const d = path.points.map((p, i) => `${i ? "L" : "M"}${p[0]} ${p[1]}`).join(" ");
    gBase.appendChild(el("path", {
      d, fill: "none", stroke: "#c9c9c9", "stroke-width": W.dim * 2,
      "vector-effect": "non-scaling-stroke",
    }));
  }
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
  //
  // ⭐ The TYPE decides the drawing, and the difference is physical — not a
  // style. An electric is a pipe. A catwalk is a WALKWAY you stand on, with the
  // units hanging off a rail rather than down its middle, so a unit drawn on its
  // centre is drawn three feet from where it is. A boom is a POINT in plan.
  // Mirrors Sheet.position() and Sheet.boom() in the Python.
  const bar = (x1: number, y1: number, x2: number, y2: number, w: number) =>
    gPos.appendChild(el("line", {
      x1, y1, x2, y2, stroke: "#222", "stroke-width": w, "stroke-linecap": "round",
    }));

  for (const p of plot.positions) {
    const kind = (p.type ?? "electric").trim().toLowerCase();

    if (isVertical(p)) {
      // A boom in plan: its mount, and one hatched symbol standing for the
      // stack. Drawing four units on top of each other is just a heavier blob.
      const half = (p.width ?? 1.4) / 2;
      if ((p.mount ?? "boom-base") === "floor-plate") {
        gPos.appendChild(el("rect", {
          x: p.x1 - half, y: p.y1 - half, width: half * 2, height: half * 2,
          fill: "none", stroke: "#222", "stroke-width": W.position * 0.7,
        }));
      } else if (p.mount === "flange") {
        gPos.appendChild(el("circle", { cx: p.x1, cy: p.y1, r: half * 0.36,
          fill: "none", stroke: "#222", "stroke-width": W.position * 0.7 }));
      } else {
        gPos.appendChild(el("circle", { cx: p.x1, cy: p.y1, r: half,
          fill: "none", stroke: "#222", "stroke-width": W.position * 0.7 }));
        gPos.appendChild(el("circle", { cx: p.x1, cy: p.y1, r: half * 0.16,
          fill: "none", stroke: "#222", "stroke-width": W.position * 0.5 }));
      }
    } else if (kind === "catwalk" || kind === "truss") {
      const half = (p.width ?? (kind === "catwalk" ? 3.0 : 1.5)) / 2;
      for (const side of [1, -1])
        bar(p.x1, p.y1 + side * half, p.x2, p.y2 + side * half,
            kind === "catwalk" ? W.room : W.position);
      if (kind === "catwalk") {
        // the pipe, INBOARD of the downstage rail — on the rail the two lines
        // coincide and the pipe disappears
        const off = p.railOffset ?? half * 0.55;
        bar(p.x1, p.y1 - off, p.x2, p.y2 - off, W.position);
      }
    } else {
      bar(p.x1, p.y1, p.x2, p.y2, W.position);
    }

    if (opts.showLabels) {
      const half = isVertical(p) ? (p.width ?? 1.4) / 2
                 : (kind === "catwalk" || kind === "truss")
                   ? (p.width ?? (kind === "catwalk" ? 3.0 : 1.5)) / 2 : 0;
      const t = el("text", {
        transform: counterFlip(p.x1, Math.max(p.y1, p.y2 ?? p.y1) + half + 0.8),
        "font-size": TEXT * 0.8, "font-family": "system-ui, sans-serif",
        "font-weight": "600", fill: "#222",
      });
      const foh = isFoh(p, plot.room.plasterLine) && !p.name.toUpperCase().includes("FOH") ? "  (FOH)" : "";
      // ⚠ Trim only on a position that can MOVE. RP-2 §2.1 asks for "trim
      // measurements for MOVABLE mounting positions" — a dead-hung grid pipe is
      // not one, and printing a number that cannot change is clutter on every
      // pipe in the room. The section carries trim for everything; the plan
      // carries it only where it is a decision. (Jerry, 2026.09.24.)
      const showTrim = p.trim !== undefined && p.movable === true;
      t.textContent = (showTrim ? `${p.name} — trim ${fmtFt(p.trim!)}` : p.name) + foh;
      gText.appendChild(t);
    }
  }

  // ---- instruments
  plot.instruments.forEach((inst, i) => {
    const c = computed[i];
    const hasFocus = inst.focusX !== undefined && inst.focusY !== undefined;

    // ⭐ The pool is an ELLIPSE. A cone only cuts a circle when it points
    // straight down; at 30° elevation a 26° field lands more than twice as long
    // as it is wide, and the long end is the one that reaches the scenery. The
    // circle that used to be drawn here understated the far end by half and hid
    // a grazing focus entirely.
    if (opts.showPools && hasFocus && c?.pool) {
      gPools.appendChild(el("ellipse", {
        cx: c.pool.cx, cy: c.pool.cy, rx: c.pool.a, ry: c.pool.b,
        transform: `rotate(${c.pool.angle} ${c.pool.cx} ${c.pool.cy})`,
        fill: "none", stroke: "#bbb", "stroke-width": W.pool, "stroke-dasharray": "0.6 0.4",
      }));
    } else if (opts.showPools && hasFocus && c?.pool_note) {
      // ⚠ Never silently. "No far edge" is a fact about the focus, not an
      // absence of information — mark the aim point so it is visible.
      gPools.appendChild(el("circle", {
        cx: inst.focusX!, cy: inst.focusY!, r: 0.5,
        fill: "none", stroke: "#e08a2e", "stroke-width": W.pool * 2,
        "stroke-dasharray": "0.3 0.3",
      }));
    }
    if (opts.showFocus && hasFocus) {
      gFocus.appendChild(el("line", {
        x1: inst.x, y1: inst.y, x2: inst.focusX!, y2: inst.focusY!,
        stroke: "#999", "stroke-width": W.focus, "stroke-dasharray": "0.5 0.35",
      }));
      const fh = el("g", { class: "focus-handle" + (isSelNow(opts, i) ? " selected" : "") });
      fh.appendChild(el("circle", {
        cx: inst.focusX!, cy: inst.focusY!, r: 0.25,
        fill: "none", stroke: "#999", "stroke-width": W.focus,
      }));
      fh.appendChild(el("circle", {
        cx: inst.focusX!, cy: inst.focusY!, r: 0.9, fill: "transparent",
        class: "hit", "data-index": String(i), "data-handle": "focus",
      }));
      gFocus.appendChild(fh);
    }
    const isSel = opts.selected === i;
    const g = symbol(inst, c, opts.symbols?.[symbolKey(inst)], plot.symbolAngle);
    g.setAttribute("data-index", String(i));
    if (isSel) g.classList.add("selected");
    // A generous invisible disc so a 9-inch symbol is still easy to grab.
    g.appendChild(el("circle", {
      cx: inst.x, cy: inst.y, r: 1.1, fill: "transparent",
      class: "hit", "data-index": String(i), "data-handle": "body",
    }));
    gInst.appendChild(g);
    if (opts.showLabels) gText.appendChild(
      labels(inst, c, plot.symbolAngle, opts.symbols?.[symbolKey(inst)]));
  });
}

/**
 * Draw an instrument from the RP-2 primitives the server supplies.
 *
 * The geometry is NOT defined here. It lives in server/plotedit/symbols.py,
 * traced from USITT RP-2 (2006). Reimplementing it in TypeScript would
 * guarantee the screen and the printed plot drift apart.
 *
 * Local coordinates: +a toward the back of the instrument, -a the front,
 * c across, origin at the yoke. Rotation puts the front toward the focus.
 */
function symbol(inst: Instrument, c: Computed | undefined,
                prims: SymbolPrim[] | undefined,
                symbolAngle?: string): SVGElement {
  const g = el("g", { class: "instrument", "data-unit": inst.unit,
                      "data-channel": inst.channel ?? "" });
  // ⭐ RP-2 p.2 allows orienting a symbol "to either focus points or 90° axes",
  // and the plot defaults to the axes. The paper has snapped since 2026.09.23;
  // the screen was still drawing the true angle, so the same unit pointed two
  // different ways on the two drawings.
  //
  // 🔴 COSMETIC ONLY. `c.pan` remains the real aim and every number is computed
  // from it — this rotates ink, nothing else.
  const truePan = c?.pan ?? 0;
  const pan = (symbolAngle ?? "orthogonal").startsWith("orth")
    ? Math.round(truePan / 90) * 90 : truePan;
  const body = el("g", { transform: `translate(${inst.x} ${inst.y}) rotate(${-pan})` });

  if (!prims) {
    // The server has not answered yet, or the type is unknown. Draw a plain
    // ring rather than guessing a shape — a wrong symbol is read as fact.
    body.appendChild(el("circle", { cx: 0, cy: 0, r: 0.42, fill: "#fff",
                                    stroke: "#111", "stroke-width": 0.07 }));
  }
  for (const p of prims ?? []) {
    if (p.k === "poly") {
      const d = p.pts.map((q, i) => `${i ? "L" : "M"}${q[1]} ${q[0]}`).join(" ")
                + (p.closed ? " Z" : "");
      body.appendChild(el("path", { d, fill: p.closed ? "#fff" : "none",
                                    stroke: "#111", "stroke-width": 0.075 }));
    } else if (p.k === "line") {
      body.appendChild(el("line", { x1: p.a[1], y1: p.a[0], x2: p.b[1], y2: p.b[0],
                                    stroke: "#111", "stroke-width": 0.06 }));
    } else if (p.k === "circle") {
      body.appendChild(el("circle", {
        cx: p.c[1], cy: p.c[0], r: p.r,
        fill: p.filled ? "#111" : "none", stroke: "#111",
        "stroke-width": p.dashed ? 0.04 : 0.06,
        ...(p.dashed ? { "stroke-dasharray": "0.16 0.12" } : {}),
      }));
    } else if (p.k === "text") {
      const t = el("text", {
        transform: `translate(${p.c[1]} ${p.c[0]}) scale(1 -1)`,
        "font-size": p.size, "font-family": "system-ui, sans-serif",
        "font-weight": "700", fill: "#111", "text-anchor": "middle",
      });
      t.textContent = p.s;
      body.appendChild(t);
    }
  }
  // the yoke point — where the unit actually is, per RP-2 2.2
  body.appendChild(el("circle", { cx: 0, cy: 0, r: 0.09, fill: "#111" }));
  g.appendChild(body);
  return g;
}


/** Field angle by name, for tube length only. The server holds the real table. */
function fieldOf(type: string): number | null {
  const m = /(\d+(?:\.\d+)?)\s*(?:deg|°)?\s*(?:EDLT|LT)?$/.exec(type.trim());
  return m?.[1] ? Number(m[1]) : null;
}

/** §6.14.2: the unit number goes INSIDE the body, the channel in a circle below,
 *  colour and type beside.
 *
 * ⚠ The unit number used to be drawn 1.1 ft ABOVE the symbol — where it lands on
 * the position's own label. The paper has had it in the body since 2026.09.23;
 * the screen had not caught up, so the two drawings disagreed about the one
 * number an electrician reads first.
 */
function labels(inst: Instrument, c?: Computed, symbolAngle?: string,
                prims?: SymbolPrim[]): SVGElement {
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
  // In the body, offset along the instrument's own axis so the batten does not
  // run through it — the same rule the PDF uses, and it has to follow the
  // symbol as it turns.
  const drawn = (symbolAngle ?? "orthogonal").startsWith("orth")
    ? Math.round((c?.pan ?? 0) / 90) * 90
    : (c?.pan ?? 0);
  const OFF = 0.17;   // ft toward the back of the body, matching scaled_pdf
  const body = notationAnchor(0, 0, drawn, OFF);
  add(body.x, body.y, String(inst.unit), TEXT * 0.7, "700");
  // ⭐ THE STACK GOES BEHIND THE LIGHT, THE COLOUR IN FRONT ACROSS THE LENS.
  // §6.14.2 draws circuit/dimmer/channel off the back of an instrument and the
  // colour and focus beyond its lens. Jerry, 2026.09.24: "the channel number
  // should be behind the light, not in front. The colour label should be along
  // the width of the lens in the front."
  //
  // ⚠ Both used to sit at fixed page offsets — channel at -1.5 y, colour beside
  // at +0.75 x — regardless of where the unit pointed. On a unit aimed
  // downstage that put the channel IN THE BEAM. Front is along -axis, back is
  // +axis, and both follow the symbol as it turns.
  const behind = (d: number) => notationAnchor(inst.x, inst.y, drawn, d);
  // Clear the SYMBOL by its own size, exactly as scaled_pdf does — a constant
  // put the channel circle on the body of the long ones, and on anything with
  // an accessory hung off the nose.
  const clear = symbolRadius(prims) + 0.25;

  // ⚠ Clear the symbol by the CIRCLE'S OWN RADIUS. The screen draws this circle
  // at 0.55 ft where the paper's is 0.24, so the paper's offset left the screen
  // circle lapping over the instrument body.
  const R = 0.55;
  if (inst.channel !== undefined) {
    const b = behind(clear + R + 0.1);
    g.appendChild(el("circle", { cx: b.x, cy: b.y, r: R,
      fill: "#fff", stroke: "#111", "stroke-width": 0.07 }));
    add(b.x - inst.x, b.y - inst.y - 0.2, String(inst.channel), TEXT * 0.62, "600");
  }
  // ⚠ COLOUR ONLY. The screen used to print the type here too — "S4 26 · R52+R119"
  // — which the paper has never drawn: §6.14.2 puts colour and focus at the
  // lens, and the TYPE is what the symbol and the key are for. The long string
  // also ran back across the unit. Type is still in the inspector and the key.
  if (inst.color) {
    const size = TEXT * 0.5;
    // ⚠ A CENTRED label is right in front of a unit aimed up or downstage and
    // wrong in front of one aimed to a side: centring puts half the string on
    // the far side, so clearing the symbol means pushing the whole label out by
    // half its width. "R52+R119" landed 2'-5" out where its neighbours sat at
    // 1'-6", which is what made the sideways units look unlike the rest.
    // Anchor the INNER EDGE and let the label run outward instead.
    const rad = (drawn * Math.PI) / 180;
    const across = Math.abs(Math.sin(rad)) > Math.abs(Math.cos(rad));
    const f = behind(-(clear + (across ? 0 : size / 2)));
    const t = el("text", {
      transform: counterFlip(f.x, f.y),
      "font-size": size, "font-family": "system-ui, sans-serif", fill: "#555",
      "text-anchor": across ? (Math.sin(rad) > 0 ? "start" : "end") : "middle",
    });
    t.textContent = inst.color;
    g.appendChild(t);
  }
  // ⚠ NO throw, elevation or footcandles on the drawing. Jerry, 2026.09.24:
  // "the fc and throw isn't needed on the plot, we can see it if we inspect the
  // instrument." They are working numbers, not something an electrician reads
  // off a pipe — and the paper never printed them either (scaled_pdf's
  // `annotate` defaults to False), so the screen was the odd one out.
  //
  // They are still computed, still in the inspector, and still on the schedule.
  return g;
}

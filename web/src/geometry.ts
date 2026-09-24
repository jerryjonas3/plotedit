/**
 * Real feet in, screen pixels out. Get this right once.
 *
 * Two coordinate systems, and they disagree about which way is up:
 *
 *   PLOT    x → stage right, y → upstage (away from the audience), origin at
 *           the downstage-left corner of the room. Feet. This is what the JSON
 *           holds and what the Python thinks in.
 *   SCREEN  x → right, y → DOWN, origin top-left. Pixels. SVG and canvas both.
 *
 * So the y axis flips. Everything else is a scale and an offset.
 *
 * ⚠ Scale here is pixels per foot, NOT an architectural scale. Architectural
 * scale (¼" = 1'-0") belongs to paper and lives in scaled_pdf.py. On screen the
 * drawing zooms; on paper it must measure true. Do not confuse the two.
 */

export interface View {
  /** Pixels per foot. */
  scale: number;
  /** Plot coordinates (feet) of the point shown at the screen origin's column. */
  panX: number;
  panY: number;
  /** Size of the drawing surface, pixels. */
  width: number;
  height: number;
}

export interface Pt { x: number; y: number }

/** Plot feet → screen pixels. */
export function toScreen(p: Pt, v: View): Pt {
  return {
    x: (p.x - v.panX) * v.scale,
    y: v.height - (p.y - v.panY) * v.scale,
  };
}

/** Screen pixels → plot feet. The inverse; step 4 needs it for dragging. */
export function toPlot(p: Pt, v: View): Pt {
  return {
    x: p.x / v.scale + v.panX,
    y: (v.height - p.y) / v.scale + v.panY,
  };
}

/** Feet → pixels for a length (no offset, no flip). */
export function len(feet: number, v: View): number {
  return feet * v.scale;
}

/**
 * An SVG transform that lets the rest of the code draw in real feet.
 *
 * Wrap the drawing in <g transform={svgTransform(view)}> and then emit
 * coordinates in feet directly — the group handles the scale and the y flip.
 * The SVG source then reads in the units of the room, which is worth having
 * when something looks wrong.
 *
 * ⚠ It flips text too. Use counterFlip() on any <text>.
 */
export function svgTransform(v: View): string {
  return `translate(${-v.panX * v.scale} ${v.height + v.panY * v.scale}) scale(${v.scale} ${-v.scale})`;
}

/** Undo the y flip for a text element sitting at (x, y) in plot feet. */
export function counterFlip(x: number, y: number): string {
  return `translate(${x} ${y}) scale(1 -1)`;
}

/** Fit a room of w × h feet into the surface, with a margin in feet. */
export function fitView(
  roomW: number, roomH: number, width: number, height: number, marginFt = 3,
  houseFt = 0,
): View {
  // ⭐ `houseFt` is how far DOWNSTAGE the plot reaches past the room — front of
  // house positions sit over the audience at negative y. Fit to the room alone
  // and a catwalk is simply not on screen, which is the same failure the PDF had
  // before foh_extent(); there the clipping guard caught it, and here nothing
  // would: the drawing just quietly lacks a position.
  const totalH = roomH + houseFt;
  const scale = Math.min(width / (roomW + marginFt * 2), height / (totalH + marginFt * 2));
  // center what is actually drawn, not just the room
  const slackX = (width / scale - roomW) / 2;
  const slackY = (height / scale - totalH) / 2;
  // ⚠ MINUS houseFt. toScreen() is y_screen = height − (y_plot − panY)·scale, so
  // a point is on the canvas only while y_plot ≥ panY. The house sits at
  // NEGATIVE y, so panY has to move further negative to reach it. Adding it
  // opened the space upstage instead — empty paper at the back of the room and
  // the catwalk still off the bottom.
  return { scale, panX: -slackX, panY: -slackY - houseFt, width, height };
}

/** DEPRECATED — always 0. Kept so callers do not break.
 *
 * It existed to extend the canvas downstage for front-of-house positions drawn
 * at negative y. That was a wrong model: the room is the whole room, house and
 * stage, and an FOH position belongs inside it (Jerry, 2026.09.24). Nothing
 * needs extra canvas any more.
 */
export function fohExtent(
  _positions: { y1: number; y2?: number; width?: number; type?: string; foh?: boolean }[],
): number {
  return 0;
}

/** Feet as feet-and-inches: 13.75 → 13'-9" */
export function fmtFt(feet: number | null | undefined): string {
  if (feet === null || feet === undefined || !isFinite(feet)) return "—";
  const neg = feet < 0;
  const a = Math.abs(feet);
  let whole = Math.floor(a);
  let inches = Math.round((a - whole) * 12);
  if (inches === 12) { whole += 1; inches = 0; }
  return `${neg ? "-" : ""}${whole}'-${inches}"`;
}

/** Where a piece of notation sits relative to an instrument, in FEET.
 *
 * ⭐ Front and back belong to the INSTRUMENT, not to the page. `d` is measured
 * along the unit's own axis: positive is BEHIND the light (where RP-2 §6.14.2
 * puts circuit, dimmer and channel), negative is in FRONT, beyond the lens
 * (colour and focus).
 *
 * ⚠ This lived twice — as fixed page offsets in render.ts and as `_along` in
 * symbols.py — and the two drifted: the screen put the channel 1.5 ft down the
 * PAGE whatever way the unit aimed, so a unit focused downstage had its channel
 * number sitting in its own beam and its colour behind it. One formula, tested
 * on both sides, is what stops that.
 *
 * @param drawnDeg the angle the SYMBOL is drawn at — after any orthogonal
 *   snap. Not the true pan, or the label follows a rotation the reader cannot
 *   see.
 */
export function notationAnchor(x: number, y: number, drawnDeg: number, d: number): Pt {
  const r = (drawnDeg * Math.PI) / 180;
  return { x: x - d * Math.sin(r), y: y + d * Math.cos(r) };
}

/** The farthest any part of a symbol reaches from its yoke, in FEET.
 *
 * The mirror of symbols.py's `radius()`. Notation has to clear the symbol, and
 * symbols are not one size — an ERS is 1'-8" long, a striplight is six feet,
 * and an accessory on the nose adds more. A fixed offset put the channel circle
 * on top of every ellipsoidal on the paper; the screen had the same constant.
 *
 * ⚠ Match each kind explicitly. A fall-through default is what made the Python
 * version unpack a point LIST as one pair when the "fill" primitive arrived.
 */
export function symbolRadius(prims: readonly unknown[] | undefined): number {
  let best = 0;
  for (const raw of prims ?? []) {
    const p = raw as { k: string; pts?: [number, number][]; a?: [number, number];
                       b?: [number, number]; c?: [number, number]; r?: number };
    let pts: [number, number][] = [];
    let pad = 0;
    if (p.k === "poly" || p.k === "fill") pts = p.pts ?? [];
    else if (p.k === "line") pts = [p.a, p.b].filter(Boolean) as [number, number][];
    else if (p.k === "circle") { pts = p.c ? [p.c] : []; pad = p.r ?? 0; }
    else if (p.k === "text") pts = p.c ? [p.c] : [];
    else continue;
    for (const [a, c] of pts) best = Math.max(best, Math.hypot(a, c) + pad);
  }
  return best;
}

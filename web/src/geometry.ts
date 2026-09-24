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

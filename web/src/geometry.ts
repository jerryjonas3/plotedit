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
): View {
  const scale = Math.min(width / (roomW + marginFt * 2), height / (roomH + marginFt * 2));
  // center the room in whatever space is left over
  const slackX = (width / scale - roomW) / 2;
  const slackY = (height / scale - roomH) / 2;
  return { scale, panX: -slackX, panY: -slackY, width, height };
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

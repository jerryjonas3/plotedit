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
/**
 * Hold a point of the drawing still across a change of scale.
 *
 * #163: `canvas.scrollLeft` and `scrollTop` are kept in PIXELS across a change
 * of scale. The content expands, the offset does not, so the plot point at the
 * top-left of the viewport afterwards is whatever was that many pixels in at
 * the OLD scale — a point much nearer the drawing's origin, which is blank
 * margin outside the room.
 *
 * 🔴 WHY IT READS AS THE DRAWING DISAPPEARING. On `samples/Sample Big House`
 * (135 × 103 ft) a fitted view is about 7.8 px/ft. #162's ceiling is 400, so
 * the drawing goes from ~1,050 × 800 px to 54,000 × 41,200 — a 51× expansion
 * with the offset held constant, leaving under 0.1% of it in view. ⚠ #163's own
 * table measures 26× against a 200 ceiling; the merged ceiling is 400 and the
 * real figure is worse.
 *
 * ⭐ THE RULE IS "ANCHOR TO THE VIEWPORT CENTRE", chosen by Jerry 2026.11.27
 * from the four in #163. It is the cheapest and the selection rule would need
 * it underneath anyway, so it is not a dead end if that is wanted later.
 *
 * ⭐ WHY A FRACTION AND NOT A PLOT COORDINATE. The obvious implementation
 * converts the centre to feet, re-multiplies by the new px/ft and adds the
 * canvas padding back. That needs three things this module would rather not
 * know: that `scale === pxPerFoot` exactly (it does today, because `fitView`
 * divides by the same figure `drawingFeet` multiplied by, but that is an
 * identity two files apart), where the drawing's plot-space origin sits, and
 * how much padding is on the canvas.
 * ➡ A fraction of the drawing's own box needs none of them. The drawing scales
 * uniformly, so the fraction is invariant, and `getBoundingClientRect` already
 * accounts for padding, for the `place-items:center` that centres a drawing
 * smaller than the viewport, and for the current scroll.
 *
 * ⚠ SO THIS FILE IS DELIBERATELY SCALE-BLIND. It is never told the zoom, and it
 * must not be: every assumption it could make about the mapping is one that
 * could drift out of step with geometry.ts.
 */

/** A rectangle in client coordinates — what `getBoundingClientRect` returns. */
export interface Box {
  left: number;
  top: number;
  width: number;
  height: number;
}

/** A point of the drawing, as a fraction of the drawing's own box. */
export interface Anchor {
  fx: number;
  fy: number;
}

/** The middle of a box, which is what "the centre of the drawing" means. */
export const CENTRE: Anchor = { fx: 0.5, fy: 0.5 };

const clamp01 = (v: number): number => (v < 0 ? 0 : v > 1 ? 1 : v);

/**
 * Where `(cx, cy)` sits within `drawing`, as a fraction on each axis.
 *
 * ⚠ CLAMPED TO THE DRAWING, and that is not tidiness. A drawing smaller than
 * the viewport is CENTRED by `#canvas { place-items:center }`, so the viewport
 * centre can be out over the grey background — a fraction of -0.4 or 1.7. Left
 * unclamped, zooming in from there would faithfully anchor to a point outside
 * the paper and land on blank margin, which is the bug this file exists to fix
 * wearing different arithmetic.
 *
 * ⚠ A zero-width box yields the centre rather than a division by zero. That is
 * the first frame, before the plot has loaded and the svg has a size.
 */
export function anchorOf(drawing: Box, cx: number, cy: number): Anchor {
  return {
    fx: drawing.width > 0 ? clamp01((cx - drawing.left) / drawing.width) : CENTRE.fx,
    fy: drawing.height > 0 ? clamp01((cy - drawing.top) / drawing.height) : CENTRE.fy,
  };
}

/**
 * How far to scroll so `a` sits at `(cx, cy)` again, given the drawing's box
 * AFTER the scale changed.
 *
 * ⚠ A DELTA, not an absolute offset, because the caller adds it to
 * `scrollLeft`. The browser then clamps to the scrollable range, which is
 * wanted: when the drawing is smaller than the viewport there is nothing to
 * scroll and the centring has already put it where it belongs.
 */
export function scrollShift(
  a: Anchor, drawing: Box, cx: number, cy: number,
): { dx: number; dy: number } {
  return {
    dx: drawing.left + a.fx * drawing.width - cx,
    dy: drawing.top + a.fy * drawing.height - cy,
  };
}

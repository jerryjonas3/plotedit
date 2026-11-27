import assert from "node:assert/strict";
import { anchorOf, scrollShift, CENTRE, type Box } from "./anchor.js";

const near = (a: number, b: number, tol: number, what: string) =>
  assert.ok(Math.abs(a - b) <= tol, `${what}: ${a} is not within ${tol} of ${b}`);

/*
 * A drawing's box in client coordinates, as getBoundingClientRect gives it.
 * There is no DOM under tsx, so the boxes are written out — which is the point
 * of keeping this arithmetic in a module that is never handed an element.
 */
const box = (left: number, top: number, width: number, height: number): Box =>
  ({ left, top, width, height });

// ---- anchorOf ---------------------------------------------------------------

// The middle of the box is the middle.
assert.deepEqual(anchorOf(box(0, 0, 1000, 800), 500, 400), CENTRE);

// Offsets are measured from the box, not from the viewport.
assert.deepEqual(anchorOf(box(200, 100, 400, 200), 300, 150), { fx: 0.25, fy: 0.25 });

// A scrolled drawing has a NEGATIVE left, and that is the normal case: the
// canvas is scrolled 600px in, so the box starts off the left of the viewport.
assert.deepEqual(anchorOf(box(-600, -400, 1200, 800), 0, 0), { fx: 0.5, fy: 0.5 });

// ⚠ Clamped. place-items:center leaves the viewport centre out over the grey
// background when the drawing is smaller than the canvas — anchoring there
// would land on blank margin, which is the bug, not the fix.
assert.deepEqual(anchorOf(box(400, 300, 200, 100), 100, 50), { fx: 0, fy: 0 },
  "a centre left of the drawing clamps to its left edge");
assert.deepEqual(anchorOf(box(0, 0, 200, 100), 900, 700), { fx: 1, fy: 1 },
  "and right of it to the right edge");

// The first frame, before the plot has loaded and the svg has a size.
assert.deepEqual(anchorOf(box(0, 0, 0, 0), 500, 400), CENTRE,
  "a zero-size drawing yields the centre, not a division by zero");

// ---- scrollShift ------------------------------------------------------------

// Nothing moved, so nothing to scroll.
const same = box(-600, -400, 1200, 800);
assert.deepEqual(scrollShift(CENTRE, same, 0, 0), { dx: 0, dy: 0 });

// ---- 🔴 #163's own case, end to end ----------------------------------------

// 🔴 THIS IS THE REGRESSION. Sample Big House fitted is ~1,050 × 800 px; at
// #162's 400 px/ft ceiling it is ~54,000 × 41,200. Hold the centre across that.
const VIEW_W = 1200, VIEW_H = 800;
const centreX = VIEW_W / 2, centreY = VIEW_H / 2;

// Fitted and unscrolled: the whole drawing is on screen, centred by the canvas.
const fitted = box((VIEW_W - 1050) / 2, (VIEW_H - 800) / 2, 1050, 800);
const a = anchorOf(fitted, centreX, centreY);
near(a.fx, 0.5, 1e-12, "a fitted, centred drawing is anchored at its middle");

// Zoom to the ceiling. The svg grows 51×; the browser leaves scroll at 0, so
// the box still starts at the canvas padding and the old centre is now 27,000
// px off the right of the viewport.
const GROW = 54000 / 1050;
const zoomed = box(16, 16, 1050 * GROW, 800 * GROW);
const naive = anchorOf(zoomed, centreX, centreY);
assert.ok(naive.fx < 0.03,
  `without the shift the viewport sits ${(naive.fx * 100).toFixed(2)}% into a 54,000px drawing`);

// With the shift, the point that was in the middle is back in the middle.
const { dx, dy } = scrollShift(a, zoomed, centreX, centreY);
const after = box(zoomed.left - dx, zoomed.top - dy, zoomed.width, zoomed.height);
near(anchorOf(after, centreX, centreY).fx, a.fx, 1e-9, "the anchored point returns to the centre");
near(anchorOf(after, centreX, centreY).fy, a.fy, 1e-9, "on both axes");

// ⭐ And the shift is the size of the problem: over half the zoomed drawing.
assert.ok(dx > 26_000, `the correction is ${Math.round(dx)}px, which is why this reads as loss`);

// ---- it is an involution: zoom out and you are back ------------------------

// Zooming back to the fitted scale returns the view, so the rule does not
// accumulate drift over a drag of the slider.
let b = box(16, 16, 1050 * GROW, 800 * GROW);
for (const g of [GROW, 8, 3, 1]) {
  const held = anchorOf(b, centreX, centreY);
  const grown = box(b.left, b.top, 1050 * g, 800 * g);
  const s = scrollShift(held, grown, centreX, centreY);
  b = box(grown.left - s.dx, grown.top - s.dy, grown.width, grown.height);
  near(anchorOf(b, centreX, centreY).fx, held.fx, 1e-9, `held across a change to ${g}×`);
}

// ---- the fit buttons go through the same rule ------------------------------

// 🔴 #163 asks whether the fit buttons should anchor at all. They do, because
// the rule belongs where the scale changes rather than in four of the five
// handlers — and on a fit it asks for nothing to happen.
//
// ⚠ The boxes below have to be CONSISTENT to mean anything. A drawing that
// fits an axis is CENTRED on it by `place-items:center`, so it cannot also be
// scrolled on that axis. Writing a fitting drawing at a scrolled offset tests
// a state the canvas never produces.
const overflowsWidthOnly = box(-400, (VIEW_H - 700) / 2, 2000, 700);
const held = anchorOf(overflowsWidthOnly, centreX, centreY);
near(held.fy, 0.5, 1e-12, "an axis that fits is centred, so it anchors at the middle");
near(held.fx, 0.5, 1e-12, "and this one is scrolled to its middle");

const fitsBoth = box((VIEW_W - 900) / 2, (VIEW_H - 600) / 2, 900, 600);
const onFit = scrollShift(held, fitsBoth, centreX, centreY);
near(onFit.dx, 0, 1e-9, "fitting from a centred view asks for no horizontal scroll");
near(onFit.dy, 0, 1e-9, "nor vertical — 'show everything' is already the right answer");

// ⚠ AND WHERE IT IS NOT A NO-OP, THE CALLER'S CLAMP IS THE ANSWER. Fit from a
// view scrolled to a corner and the rule does ask for a shift; the drawing no
// longer overflows, so `scrollLeft` has nowhere to go and the browser drops it.
// 🔴 That clamp is a DOM behaviour and is deliberately NOT emulated here — this
// module reports the shift and the caller assigns it.
const corner = anchorOf(box(0, 0, 2000, 700), centreX, centreY);
const fromCorner = scrollShift(corner, fitsBoth, centreX, centreY);
assert.ok(Math.abs(fromCorner.dx) > 1,
  "a corner view does ask for a shift, which the scroll range then refuses");

console.log("anchor.test.ts — ok");

import assert from "node:assert/strict";
import { pxFromPos, posFromPx, ZOOM_MIN, ZOOM_MAX, ZOOM_STEPS, ZOOM_DEFAULT } from "./zoom.js";

const near = (a: number, b: number, tol: number, what: string) =>
  assert.ok(Math.abs(a - b) <= tol, `${what}: ${a} is not within ${tol} of ${b}`);

// ---- the ends are exactly the ends ----------------------------------------

assert.equal(pxFromPos(0), ZOOM_MIN);
assert.equal(pxFromPos(ZOOM_STEPS), ZOOM_MAX);
assert.equal(posFromPx(ZOOM_MIN), 0);
assert.equal(posFromPx(ZOOM_MAX), ZOOM_STEPS);

// Off the ends is clamped, not extrapolated — a fit button can ask for a zoom
// smaller or larger than the slider can hold.
assert.equal(pxFromPos(-50), ZOOM_MIN);
assert.equal(pxFromPos(ZOOM_STEPS + 50), ZOOM_MAX);
assert.equal(posFromPx(0.001), 0, "a fit on a huge plot asks for less than the minimum");
assert.equal(posFromPx(10_000), ZOOM_STEPS, "fit-to-width on a tiny plot asks for more");

// ---- it only ever goes up -------------------------------------------------

let prev = -Infinity;
for (let p = 0; p <= ZOOM_STEPS; p += 7) {
  const px = pxFromPos(p);
  assert.ok(px > prev, `not monotonic at ${p}`);
  prev = px;
}

// ---- round trip, within one step ------------------------------------------

// One step is a fixed RATIO, so the tolerance is a ratio too.
const stepRatio = (ZOOM_MAX / ZOOM_MIN) ** (1 / ZOOM_STEPS);
for (const px of [2, 5, 14, 20, 40, 63.25, 120, 400]) {
  const back = pxFromPos(posFromPx(px));
  assert.ok(back / px < stepRatio && px / back < stepRatio,
    `round trip of ${px} came back ${back}, more than one step out`);
}

// ---- 🔴 #122's own acceptance test ----------------------------------------

// "One should be able to zoom in almost to the point where one instrument is
// visible." ⭐ The ceiling that satisfies this is GreedyC's, merged in #160.
// These assertions guard it rather than set it: an instrument is 25⅛"–39⅜"
// (SHAKESPEARE_LENGTH_IN), so 2.1 ft at the short end, and 84 px at the old 40.
const SHORTEST_UNIT_FT = 25.125 / 12;
assert.ok(SHORTEST_UNIT_FT * ZOOM_MAX >= 700,
  "the shortest instrument must be able to fill the view, not just part of it");
assert.ok(1000 / ZOOM_MAX <= 3,
  "a 1000px canvas must be able to show about one instrument's worth of stage");

// ---- 🔴 the regression the log mapping exists to prevent --------------------

// 🔴 THIS IS THE WHOLE POINT OF THE FILE. On the LINEAR slider #160 raised,
// 2–400 leaves the everyday 2–40 range 9.5% of the travel and puts the default
// 3% from the end — about nine pixels along a 300px slider.
const linearShare = (40 - ZOOM_MIN) / (ZOOM_MAX - ZOOM_MIN);
assert.ok(linearShare < 0.12, "sanity: linearly, the everyday range really is tiny");

const everydayShare = posFromPx(40) / ZOOM_STEPS;
assert.ok(everydayShare > 0.5,
  `2–40 px/ft must keep most of the slider; it has ${(everydayShare * 100) | 0}%`);
assert.ok(everydayShare > linearShare * 4,
  "the mapping has to be a large improvement on linear, not a rounding of it");

const defaultShare = posFromPx(ZOOM_DEFAULT) / ZOOM_STEPS;
assert.ok(defaultShare > 0.3 && defaultShare < 0.55,
  `the home zoom should sit near the middle; it is at ${(defaultShare * 100) | 0}%`);

// ⚠ index.html carries this as a literal `value=`, because the markup has to
// render before any script runs. If the constants move and that literal does
// not, the slider opens at the wrong zoom — so it is pinned here.
assert.equal(posFromPx(ZOOM_DEFAULT), 367,
  "index.html's value=\"367\" must match posFromPx(ZOOM_DEFAULT)");
near(pxFromPos(367), ZOOM_DEFAULT, 0.05, "the home position really is the home zoom");

// ---- the old ceiling is still reachable ------------------------------------

// Nobody's habitual zoom should have become unreachable.
near(pxFromPos(posFromPx(40)), 40, 0.2, "40 px/ft, the old maximum");
near(pxFromPos(posFromPx(2)), 2, 0.01, "2 px/ft, the old minimum");

console.log("zoom.test.ts — ok");

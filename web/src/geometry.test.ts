/** Run: cd web && npm test */
import { toScreen, toPlot, len, fitView, fohExtent, fmtFt, svgTransform, notationAnchor, symbolRadius, type View } from "./geometry.js";

let fails = 0;
function check(label: string, got: unknown, want: unknown) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  console.log(`  ${ok ? "ok  " : "FAIL"} ${label.padEnd(44)} ${JSON.stringify(got)}`);
  if (!ok) { fails++; console.log(`       wanted ${JSON.stringify(want)}`); }
}
const round = (p: { x: number; y: number }) => ({ x: +p.x.toFixed(4), y: +p.y.toFixed(4) });

const v: View = { scale: 10, panX: 0, panY: 0, width: 400, height: 300 };

console.log("the y axis flips");
check("plot origin sits at the bottom-left", round(toScreen({ x: 0, y: 0 }, v)), { x: 0, y: 300 });
check("upstage is UP the screen", round(toScreen({ x: 0, y: 10 }, v)), { x: 0, y: 200 });
check("stage right is right", round(toScreen({ x: 10, y: 0 }, v)), { x: 100, y: 300 });

console.log("\nround trip");
for (const p of [{ x: 0, y: 0 }, { x: 16.5, y: 20 }, { x: -3, y: 41.25 }]) {
  check(`(${p.x}, ${p.y}) survives there and back`, round(toPlot(toScreen(p, v), v)), p);
}

console.log("\nlengths carry no offset and no flip");
check("10 feet at 10 px/ft", len(10, v), 100);
check("panning does not change a length", len(10, { ...v, panX: 99, panY: -7 }), 100);

console.log("\nfitView");
const f = fitView(33, 38, 800, 600);      // the Bluver
check("scale fits the tall axis", +f.scale.toFixed(4), +(600 / 44).toFixed(4));
const c1 = toScreen({ x: 0, y: 0 }, f), c2 = toScreen({ x: 33, y: 38 }, f);
check("room is inside the surface", c1.x > 0 && c2.x < 800 && c2.y > 0 && c1.y < 600, true);
check("room is centered horizontally", +(c1.x - (800 - (c2.x - c1.x)) / 2).toFixed(2), 0);

console.log("\nsvgTransform puts the origin where toScreen does");
const t = svgTransform(v);
check("has scale with a negative y", t.includes("scale(10 -10)"), true);

console.log("\nfmtFt");
check("13.75", fmtFt(13.75), `13'-9"`);
check("12 inches rolls over", fmtFt(4.9999), `5'-0"`);
check("null is not zero", fmtFt(null), "—");

console.log();

// ⭐ CORRECTED 2026.09.24. These used to assert that front of house sat at
// NEGATIVE y and that the canvas had to be extended downstage to reach it. That
// was a wrong model, and Jerry named it: "the FOH catwalk would need to be
// inside the room."
//
// The room is the WHOLE room. The Bluver is 33' x 38' with its plaster line at
// y = 10, so the house is y 0–10 and the stage 10–38 — one rectangle holding
// both. An FOH position belongs INSIDE it, and a view fitted to the room shows
// it without any extension at all.
{
  const v = fitView(33, 38, 600, 900, 3);
  const cat = toScreen({ x: 16, y: 4 }, v);      // a catwalk over the house
  const wall = toScreen({ x: 16, y: 38 }, v);    // the back wall
  check("an FOH position inside the room is on the canvas",
        cat.y > 0 && cat.y < v.height, true);
  check("...and so is the back wall", wall.y > 0 && wall.y < v.height, true);
  check("the house is still BELOW the stage on screen", cat.y > wall.y, true);

  // The extension existed only to reach outside the room. Nothing is outside it.
  check("no canvas extension is needed any more",
        fohExtent([{ y1: 4, y2: 4, width: 3, type: "catwalk" }]), 0);
}


// ⚠ The verdict goes LAST. It used to sit in the middle of the file, so
// anything appended after it ran WITHOUT affecting the exit code — the suite
// could print failures and still exit 0. The same defect was found in two of the
// Python suites on 2026.09.23; verify_suites.py checks those, and did not cover
// these.
console.log("\nnotation follows the instrument, not the page");
// ⭐ Colour in FRONT of the lens, channel BEHIND — for every way a unit can aim.
// The screen drew both at fixed page offsets until 2026.09.24, which put the
// channel number inside the beam of anything focused downstage.
// d > 0 is behind, d < 0 is in front.
// 0° points the instrument toward -y (downstage) — symbols.draw()'s convention,
// where local -a is the lens. Getting this backwards is exactly the bug.
for (const [name, deg, front] of [
  ["aimed downstage", 0, { x: 0, y: -1 }],
  ["aimed upstage", 180, { x: 0, y: 1 }],
  ["aimed stage right", 90, { x: 1, y: 0 }],
  ["aimed stage left", 270, { x: -1, y: 0 }],
] as [string, number, { x: number; y: number }][]) {
  check(`${name}: colour at the lens`, round(notationAnchor(0, 0, deg, -1)), round(front));
  check(`${name}: channel behind`, round(notationAnchor(0, 0, deg, 1)),
        round({ x: -front.x, y: -front.y }));
}
check("off-axis follows the symbol", round(notationAnchor(10, 20, 45, -1)),
      { x: 10.7071, y: 19.2929 });

console.log("\nnotation clears the symbol by the symbol's own size");
// The mirror of symbols.py radius(). An ERS reaches ~1 ft past its yoke; a
// striplight reaches six.
check("nothing", symbolRadius(undefined), 0);
check("a body", +symbolRadius([{ k: "poly", pts: [[0.8, 0.3], [-0.9, 0.3]], closed: true }]).toFixed(4), 0.9487);
check("a circle counts its radius", symbolRadius([{ k: "circle", c: [1, 0], r: 0.5 }]), 1.5);
check("an unknown primitive is skipped, not unpacked", symbolRadius([{ k: "arc", pts: [[9, 9]] }]), 0);
check("the farthest wins", symbolRadius([{ k: "line", a: [0, 0], b: [3, 4] }, { k: "circle", c: [0, 0], r: 1 }]), 5);

if (fails) { console.log(`${fails} FAILED`); process.exit(1); }
console.log("all passed");

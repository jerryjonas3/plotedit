/** Run: cd web && npm test */
import { toScreen, toPlot, len, fitView, fohExtent, fmtFt, svgTransform, type View } from "./geometry.js";

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

// ⭐ Front of house sits at NEGATIVE y — over the audience, downstage of the
// plaster line. A view fitted to the room alone does not show it, and nothing
// warns: the catwalk is simply not drawn. (The PDF had the same bug; there the
// clipping guard caught it.)
{
  const positions = [
    { name: "Cat 1", type: "catwalk", y1: -11, y2: -11, width: 3 },
    { name: "Elect 1", type: "electric", y1: 16, y2: 16 },
  ];
  const house = fohExtent(positions);
  check("the house depth is measured to the catwalk's outer rail", house, 12.5);
  check("an electric alone needs none", fohExtent([positions[1]!]), 0);

  const v = fitView(33, 38, 600, 900, 3, house);
  const cat = toScreen({ x: 16, y: -11 }, v);
  check("the catwalk lands ON the canvas", cat.y > 0 && cat.y < v.height, true);
  const up = toScreen({ x: 16, y: 38 }, v);
  check("...and so does the back wall", up.y > 0 && up.y < v.height, true);
  check("the house is BELOW the stage on screen", cat.y > up.y, true);
}


// ⚠ The verdict goes LAST. It used to sit in the middle of the file, so
// anything appended after it ran WITHOUT affecting the exit code — the suite
// could print failures and still exit 0. The same defect was found in two of the
// Python suites on 2026.09.23; verify_suites.py checks those, and did not cover
// these.
if (fails) { console.log(`${fails} FAILED`); process.exit(1); }
console.log("all passed");

/** Run: cd web && npm run test:store */
import { Store, snapToPosition } from "./store.js";
import { plotFileName, type Plot } from "./plot.js";
import { feet } from "./details.js";

let fails = 0;
function check(label: string, got: unknown, want: unknown) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  console.log(`  ${ok ? "ok  " : "FAIL"} ${label.padEnd(48)} ${JSON.stringify(got)}`);
  if (!ok) { fails++; console.log(`       wanted ${JSON.stringify(want)}`); }
}

const base = (): Plot => ({
  formatVersion: 1, show: "T",
  room: { width: 33, depth: 38 },
  positions: [
    { name: "GRID C", x1: 0, y1: 20, x2: 33, y2: 20, trim: 14 },
    { name: "GRID D", x1: 0, y1: 24, x2: 33, y2: 24, trim: 14 },
  ],
  instruments: [
    { unit: 1, channel: 1, type: "S4 26", x: 5, y: 20 },
    { unit: 2, channel: 2, type: "S4 26", x: 10, y: 20 },
  ],
});

console.log("undo");
let s = new Store(base());
s.begin(null); s.update(0, { x: 7 });
check("edit applied", s.plot.instruments[0]!.x, 7);
check("dirty", s.dirty, true);
s.undo();
check("undo restores", s.plot.instruments[0]!.x, 5);
s.redo();
check("redo reapplies", s.plot.instruments[0]!.x, 7);

console.log("\nundo does not alias the live plot");
s = new Store(base());
s.begin(null); s.update(0, { x: 7 }); s.undo();
s.begin(null); s.update(0, { x: 9 });
check("the snapshot was a deep copy", s.plot.instruments[0]!.x, 9);
s.undo();
check("and still restores", s.plot.instruments[0]!.x, 5);

console.log("\na drag is ONE undo step");
s = new Store(base());
for (let i = 0; i < 50; i++) { s.begin("drag:0"); s.update(0, { x: 5 + i * 0.1 }); }
s.commit();
s.undo();
check("fifty moves collapse to one", +s.plot.instruments[0]!.x.toFixed(2), 5);
check("nothing left to undo", s.canUndo, false);

console.log("\nadd and remove");
s = new Store(base());
s.add({ unit: 3, type: "S4 36", x: 1, y: 1 });
check("added", s.plot.instruments.length, 3);
check("and selected", s.selected, 2);
s.remove(2);
check("removed", s.plot.instruments.length, 2);
check("selection follows", s.selected, 1);
s.undo();
check("undo brings it back", s.plot.instruments.length, 3);

console.log("\nsnap to a pipe — units hang on pipes, not in mid-air");
const p = base();
check("near GRID C snaps to it", snapToPosition(12, 20.4, p), { x: 12, y: 20, position: "GRID C" });
check("far from any pipe does not", snapToPosition(12, 22, p), { x: 12, y: 22, position: null });
check("picks the nearer of two", snapToPosition(12, 23.4, p).position, "GRID D");
check("just past the end clamps to the end", snapToPosition(33.6, 20, p),
      { x: 33, y: 20, position: "GRID C" });
// Far past the end must NOT snap — dragging a unit seven feet off the pipe and
// having it silently jump back is worse than leaving it where it was put.
check("far past the end does not snap", snapToPosition(40, 20, p).position, null);

console.log();


// ⚠ The verdict goes LAST. It used to sit in the middle of the file, so
// anything appended after it ran WITHOUT affecting the exit code — the suite
// could print failures and still exit 0. The same defect was found in two of the
// Python suites on 2026.09.23; verify_suites.py checks those, and did not cover
// these.
console.log("\na show title is not a filename");
// ⚠ Free text on one side, a filesystem on the other.
check("an ordinary title", plotFileName("Without Consent"), "Without Consent.plot.json");
check("a slash would make a directory", plotFileName("Without Consent: Act 2/3"),
      "Without Consent Act 2 3.plot.json");
check("punctuation only does NOT give a hidden dotfile", plotFileName("???"), "plot.plot.json");
check("nor does an empty title", plotFileName(""), "plot.plot.json");
check("runs of spaces collapse", plotFileName("A   B"), "A B.plot.json");
check("a very long title is cut", plotFileName("x".repeat(200)).length, 90);

console.log("\nshow and venue are editable, and undoable");
{
  const start = base();
  const s2 = new Store(structuredClone(start));
  s2.setMeta({ designer: "A N Other", studio: "Some Other Shop" });
  check("the designer is set", s2.plot.designer, "A N Other");
  check("...and the studio", s2.plot.studio, "Some Other Shop");
  check("...and the plot is dirty", s2.dirty, true);
  s2.undo();
  check("...and undo puts the old name back", s2.plot.designer, start.designer);

  // ⚠ A patch, not a replacement. Setting the width used to be the moment to
  // find out the rest of the room had gone with it.
  const w0 = s2.plot.room.depth;
  s2.setRoom({ width: 60 });
  check("the room width changes", s2.plot.room.width, 60);
  check("...and the depth is untouched", s2.plot.room.depth, w0);
  s2.undo();
  check("...and undo restores the width", s2.plot.room.width, start.room.width);
}

console.log("\nan empty box is NOT zero");
// 🔴 A grid height of 0 claims the ceiling is on the floor. Undefined means
// "not known", and the headroom checks already say so out loud rather than
// passing quietly — reading "" as 0 would turn a missing measurement into a
// confident, wrong one.
check("blank is unknown", feet(""), undefined);
check("nonsense is unknown too", feet("abc"), undefined);
check("zero is zero", feet("0"), 0);
check("a real number survives", feet("16.5"), 16.5);

if (fails) { console.log(`${fails} FAILED`); process.exit(1); }
console.log("all passed");

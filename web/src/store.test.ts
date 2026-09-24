/** Run: cd web && npm run test:store */
import { Store, snapToPosition } from "./store.js";
import { plotFileName, newPlot, isPlot, type Plot } from "./plot.js";
import { feet } from "./details.js";
import { nextBoomHeight } from "./positions.js";
import { deleteMessage, describeUnit } from "./confirm.js";
import { parseFeet } from "./feet.js";

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

console.log("\nadding a unit to a boom gives it a HEIGHT");
// 🔴 The bug: a boom position carries no trim, so `height: p.trim` was
// undefined — and an undefined height puts a unit in the elevation's NO HEIGHT
// RECORDED list and skips it in plan. The unit was in the file and on neither
// drawing. Jerry: "adding an instrument to a boom doesn't seem to work."
check("an empty boom starts at high side", nextBoomHeight([]), 12);
check("...or at the position's own trim if it has one", nextBoomHeight([], 16), 16);
check("the sample boom's next unit goes below the lowest",
      nextBoomHeight([12, 8, 4.5]), 1);   // gaps 4 and 3.5, mean 3.75 -> 0.75, snapped
check("a boom hung at 4ft intervals carries on at 4ft",
      nextBoomHeight([16, 12, 8]), 4);
check("one unit alone uses a sensible default step", nextBoomHeight([12]), 8);

// ⚠ NEVER the same height twice. Two units at one height on a boom are one
// point in plan and one mark on the elevation — the drawing would show one and
// the paperwork two, with nothing saying which was which.
{
  // Fill a boom until it refuses, and check the whole run: every height
  // distinct, every one on the boom, and it STOPS — a rule that keeps finding
  // room forever is one that is about to return a duplicate.
  const hs = [12, 8, 4.5];
  let adds = 0;
  for (;;) {
    const h = nextBoomHeight(hs);
    if (h === undefined) break;
    if (hs.includes(h)) { fails++; console.log(`  FAIL add ${adds + 1} repeated ${h}`); break; }
    if (h < 1) { fails++; console.log(`  FAIL add ${adds + 1} went below the deck: ${h}`); break; }
    hs.push(h);
    if (++adds > 40) { fails++; console.log("  FAIL it never refuses"); break; }
  }
  check("a 12ft boom takes several more units, all at distinct heights", adds > 3, true);
  check("...and then refuses instead of stacking", nextBoomHeight(hs), undefined);
  check("...having never repeated a height", new Set(hs).size, hs.length);
}
check("a boom with no room at all refuses", nextBoomHeight([2, 1]), undefined);

console.log("\nevery delete asks, and the question NAMES the thing");
// ⚠ "Are you sure?" on its own asks the reader to remember what they just
// clicked — which is exactly what someone about to delete the wrong thing has
// got wrong. The message has to say WHICH unit.
check("a unit is named by number, position and channel",
      describeUnit({ unit: 3, channel: 33, position: "GRID C", type: "S4 36" }),
      "unit 3 on GRID C (channel 33, S4 36)");
check("...and reads sensibly with nothing but a number",
      describeUnit({ unit: 7 }), "unit 7");
check("...and channel 0 is a channel, not a missing one",
      describeUnit({ unit: 7, channel: 0 }), "unit 7 (channel 0)");

check("the question leads with the subject",
      deleteMessage("unit 3 on GRID C").split("\n")[0], "Delete unit 3 on GRID C?");
check("...and says it can be undone",
      deleteMessage("unit 3").includes("undone"), true);
check("...and carries the consequence when there is one",
      deleteMessage("the position GRID C", "4 units will be KEPT.").includes("4 units"), true);

console.log("\nthe boxes take feet and inches, because the drawing prints them");
// 🔴 They were <input type="number">, which SILENTLY DISCARDS 1'6" — the field
// goes empty, the handler reads that as "clear this", and the value reverts to
// its default. Jerry set a focus height of 1'-6" and got no pool, because the
// focus height was never set.
for (const [typed, want] of [
  ["1'6\"", 1.5], ["1'-6\"", 1.5], ["1' 6\"", 1.5], ["1'6", 1.5],
  ["1'", 1], ["18\"", 1.5], ["1.5", 1.5], ["12", 12], ["-3", -3],
  ["5\u20326\u2033", 5.5],          // the prime marks a word processor produces
] as [string, number][]) {
  check(`${typed} is ${want}ft`, +(parseFeet(typed) as number).toFixed(4), want);
}
// ⚠ The sign belongs to the whole length: -1'6" is a foot and a half BELOW
// zero, not minus one foot plus six inches.
check("-1'6\" is -1.5, not -0.5", parseFeet("-1'6\""), -1.5);

// ⚠ Empty and nonsense are DIFFERENT. Empty clears a field; nonsense means the
// reader meant something and mistyped it, and must not silently wipe the value
// that was there.
check("empty means no value", parseFeet(""), undefined);
check("spaces are empty too", parseFeet("   "), undefined);
check("nonsense is refused, not treated as empty", parseFeet("about 6"), null);
check("...so is a stray word", parseFeet("6ft"), null);
check("...and 5'14\" is a typo, not 6'2\"", parseFeet("5'14\""), null);

console.log("\na new plot is empty, and honest about it");
{
  const p = newPlot("Studio Test");
  check("it is a valid plot", isPlot(p), true);
  check("named what was asked", p.show, "Studio Test");
  check("no instruments", p.instruments.length, 0);
  check("no positions", p.positions.length, 0);

  // 🔴 No designer, no studio. Those print in the TITLE BLOCK, and a new plot
  // inheriting whoever used the tool last would put one person's name on
  // another person's drawing.
  check("nobody's name on it", p.designer, undefined);
  check("nobody's studio either", p.studio, undefined);

  // ⚠ The room has a size because the canvas has to fit to something, but the
  // size is NOT a measurement and the plot says so — that text prints across
  // the top of the drawing until it is replaced.
  check("the room has a workable size", p.room.width > 0 && p.room.depth > 0, true);
  check("...and says it is not measured",
        (p.room.source ?? "").includes("NOT MEASURED"), true);

  check("two new plots do not share a room object", newPlot().room === p.room, false);
}

if (fails) { console.log(`${fails} FAILED`); process.exit(1); }
console.log("all passed");

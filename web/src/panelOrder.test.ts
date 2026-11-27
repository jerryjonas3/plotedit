import assert from "node:assert/strict";
import { move, sanitize, canMove } from "./panelOrder.js";

const DEFAULT = ["details", "instrument", "positions", "schedule"] as const;
type Panel = (typeof DEFAULT)[number];
const d = (): Panel[] => [...DEFAULT];

// ---- move -------------------------------------------------------------------

assert.deepEqual(move(d(), "positions", -1),
  ["details", "positions", "instrument", "schedule"], "up swaps with the one above");
assert.deepEqual(move(d(), "instrument", 1),
  ["details", "positions", "instrument", "schedule"], "...and down is the same swap, from the other side");

// ⚠ No wrap. A panel jumping from the bottom to the top because the button was
// pressed once too often would read as a bug.
assert.deepEqual(move(d(), "details", -1), d(), "the first panel cannot go up");
assert.deepEqual(move(d(), "schedule", 1), d(), "nor the last one down");

// A name that is not in the order at all leaves it alone rather than throwing.
assert.deepEqual(move(d(), "layers" as Panel, 1), d());

// ⭐ It does not mutate. The caller stores the result; a move that edited the
// array in place would have already changed what it was about to compare to.
const before = d();
move(before, "schedule", -1);
assert.deepEqual(before, d(), "the input is untouched");

// Moving by more than one, which the keyboard could ask for.
assert.deepEqual(move(d(), "schedule", -3),
  ["schedule", "details", "instrument", "positions"]);
assert.deepEqual(move(d(), "schedule", -4), d(), "...but not past the top");

// A move and its reverse is where you started.
for (const name of DEFAULT)
  for (const delta of [-2, -1, 1, 2])
    if (canMove(d(), name, delta))
      assert.deepEqual(move(move(d(), name, delta), name, -delta), d(),
        `${name} ${delta} then back`);

// ---- sanitize ---------------------------------------------------------------

// 🔴 THE POINT OF THE FUNCTION. Stored data outlives the code that wrote it.
assert.deepEqual(sanitize(null, DEFAULT), d(), "nothing stored is the default order");
assert.deepEqual(sanitize(undefined, DEFAULT), d());
assert.deepEqual(sanitize([], DEFAULT), d(), "an empty stored order is not an empty column");

// A name nothing answers to any more — a panel renamed or removed in a release.
assert.deepEqual(sanitize(["schedule", "layers", "details"] as Panel[], DEFAULT),
  ["schedule", "details", "instrument", "positions"],
  "the unknown name is dropped and the real panels all survive");

// A panel added in a later release is missing from an order stored before it.
assert.deepEqual(sanitize(["schedule", "positions"] as Panel[], DEFAULT),
  ["schedule", "positions", "details", "instrument"],
  "what was stored keeps its arrangement; what is new is appended");

// A half-written value that repeats a name must not render the panel twice.
assert.deepEqual(sanitize(["details", "details", "schedule"] as Panel[], DEFAULT),
  ["details", "schedule", "instrument", "positions"]);

// 🔴 THE FAILURE THIS PREVENTS: whatever is stored, every known panel is in the
// result exactly once. A preference must never be able to delete part of the
// interface.
for (const stored of [
  null, [], ["layers"], ["details"], ["schedule", "schedule", "schedule"],
  ["positions", "nope", "details", "positions"],
  [...DEFAULT].reverse(),
] as (Panel[] | null)[]) {
  const got = sanitize(stored, DEFAULT);
  assert.equal(got.length, DEFAULT.length, `${JSON.stringify(stored)} → wrong length`);
  for (const name of DEFAULT)
    assert.equal(got.filter((n) => n === name).length, 1,
      `${JSON.stringify(stored)} → ${name} appears ${got.filter((n) => n === name).length} times`);
}

// A full, valid, rearranged order comes back exactly as stored.
const arranged: Panel[] = ["positions", "schedule", "details", "instrument"];
assert.deepEqual(sanitize(arranged, DEFAULT), arranged);

// ---- canMove ----------------------------------------------------------------

// What disables the buttons at the ends.
assert.equal(canMove(d(), "details", -1), false);
assert.equal(canMove(d(), "details", 1), true);
assert.equal(canMove(d(), "schedule", 1), false);
assert.equal(canMove(d(), "schedule", -1), true);
assert.equal(canMove(d(), "layers" as Panel, 1), false, "a panel not in the order cannot move");

// canMove and move agree: if it says no, move is a no-op.
for (const name of DEFAULT)
  for (const delta of [-1, 1])
    assert.equal(canMove(d(), name, delta),
      JSON.stringify(move(d(), name, delta)) !== JSON.stringify(d()),
      `canMove disagrees with move for ${name} ${delta}`);

console.log("panelOrder.test.ts — ok");

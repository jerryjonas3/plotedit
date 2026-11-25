import assert from "node:assert/strict";
import { attachHelp, nearestHelp, HELP_ATTR, HELP_HINT } from "./help.js";

/*
 * A hand-rolled element, in the style of interact.test.ts — there is no DOM
 * under tsx and no jsdom in this project.
 */
class El {
  attrs = new Map<string, string>();
  parentElement: El | null = null;
  constructor(attrs: Record<string, string> = {}) {
    for (const [k, v] of Object.entries(attrs)) this.attrs.set(k, v);
  }
  getAttribute(name: string) { return this.attrs.has(name) ? this.attrs.get(name)! : null; }
}
/**
 * Links a chain child -> parent -> grandparent and returns the child.
 * ⚠ `first` is named rather than indexed: tsconfig has noUncheckedIndexedAccess,
 * so `nodes[0]` is `El | undefined` and will not typecheck.
 */
const chain = (first: El, ...rest: El[]): El => {
  let prev = first;
  for (const next of rest) { prev.parentElement = next; prev = next; }
  return first;
};

// ---- nearestHelp -----------------------------------------------------------

// On the element itself.
assert.equal(nearestHelp(new El({ title: "Undo (⌘Z)" })), "Undo (⌘Z)");

// data-help overrides, so a control can explain itself without a tooltip.
assert.equal(nearestHelp(new El({ [HELP_ATTR]: "override", title: "original" })), "override");
assert.equal(nearestHelp(new El({ [HELP_ATTR]: "alone" })), "alone");

// Walks up: focus lands on the input, the help is authored on the label.
const field = new El();
chain(field, new El({ title: "Move the backdrop left or right, in feet" }));
assert.equal(nearestHelp(field), "Move the backdrop left or right, in feet");

// Surrounding whitespace is trimmed, not rendered.
assert.equal(nearestHelp(new El({ title: "  padded  " })), "padded");

// A blank title is not help.
assert.equal(nearestHelp(new El({ title: "   " })), "");

// Nothing anywhere above it is not an error, it is "".
assert.equal(nearestHelp(chain(new El(), new El(), new El())), "");
assert.equal(nearestHelp(null), "");

// ⚠ maxHops: a control must not inherit an explanation written far above it.
const deep = new El();
chain(deep, new El(), new El(), new El(), new El(), new El(),
      new El({ title: "about something else entirely" }));
assert.equal(nearestHelp(deep), "", "6 hops up is too far to inherit");
assert.equal(nearestHelp(deep, 6), "about something else entirely", "...unless asked for");

// ---- attachHelp ------------------------------------------------------------

const handlers = new Map<string, (e: Event) => void>();
let focused: unknown = null;
const titled = 34;
const root = {
  querySelectorAll: (sel: string) => {
    assert.match(sel, /title/, "counts the authored help strings");
    return { length: titled };
  },
  addEventListener: (t: string, fn: (e: Event) => void) => { handlers.set(t, fn); },
};
const out = { textContent: null as string | null };
const count = attachHelp(root, out, () => focused);

assert.equal(count, titled, "reports how many controls carry help");

// 🔴 #156: focus-triggered as well as hover, or this is no better than title.
assert.ok(handlers.has("focusin"), "keyboard focus must drive the help line");
assert.ok(handlers.has("mouseover"), "the pointer must drive it too");

// It starts with the hint rather than an empty bar.
assert.equal(out.textContent, HELP_HINT);

const button = new El({ title: "Fit the whole plot" });
handlers.get("focusin")!({ target: button } as unknown as Event);
assert.equal(out.textContent, "Fit the whole plot", "shown on keyboard focus");

handlers.get("mouseover")!({ target: field } as unknown as Event);
assert.equal(out.textContent, "Move the backdrop left or right, in feet",
  "found on the wrapping label, where it is authored");

// Moving between two controls inside the panel is not a departure.
focused = button;
handlers.get("mouseout")!({ relatedTarget: new El() } as unknown as Event);
assert.equal(out.textContent, "Move the backdrop left or right, in feet", "still inside");

// Leaving it entirely falls back to what the keyboard is on.
handlers.get("mouseout")!({ relatedTarget: null } as unknown as Event);
assert.equal(out.textContent, "Fit the whole plot", "falls back to the focused control");

// And to the hint when nothing is focused either.
focused = null;
handlers.get("mouseout")!({ relatedTarget: null } as unknown as Event);
assert.equal(out.textContent, HELP_HINT);

// A control with no help shows the hint, never an empty bar.
handlers.get("focusin")!({ target: new El() } as unknown as Event);
assert.equal(out.textContent, HELP_HINT);

console.log("help.test.ts — ok");

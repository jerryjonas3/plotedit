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
 * One help string per control, read on hover AND on keyboard focus.
 *
 * #156: every explanation in this app was a `title=` — the browser's native
 * tooltip. Hover only, after a delay, nothing on a keyboard, nothing on a
 * touch screen, nothing on a disabled control. So the way to find out what a
 * field did was to own a mouse and wait.
 *
 * ⭐ The string stays authored ONCE, as `title` in the markup. This module
 * renders it a second way: into the help line at the foot of the side panel,
 * driven by focus as well as the pointer. #156 warns that a help string
 * written twice will drift, so there is no second copy anywhere.
 *
 * ⚠ WHY `title` IS NOT REMOVED, and why no `aria-describedby` is minted here.
 * A `title` on a control is already exposed to assistive technology as that
 * control's accessible DESCRIPTION. Replacing it with visually-hidden spans
 * would put thirty-odd sentences into the linear reading order to say what AT
 * already says — a regression for the people it would be for. The gap #156
 * found is sighted keyboard and touch users, and the help line is that fix.
 * ➡ The separate real bug was NAMES: icon-only buttons whose Material
 * ligature was their accessible name, so "fit_screen" was read aloud. Those
 * are fixed in index.html with `aria-hidden` and `aria-label`, not here.
 */

/** The parts of an element this module needs. Kept narrow so it can be faked. */
export interface HelpNode {
  getAttribute(name: string): string | null;
  parentElement: HelpNode | null;
}

/** An override, for a control that should explain itself without a tooltip. */
export const HELP_ATTR = "data-help";

/** Shown when nothing is focused or hovered. */
export const HELP_HINT = "Point at a control, or Tab to one, to read what it does.";

/**
 * The nearest authored help string at or above `node`, or "" if there is none.
 *
 * Focus and hover land on the inner control, but the help is often authored on
 * the `<label>` wrapping it, so this walks up. `maxHops` stops a control deep
 * in the tree from inheriting an explanation written for something far above
 * it, which would be worse than saying nothing.
 */
export function nearestHelp(node: HelpNode | null, maxHops = 4): string {
  let n: HelpNode | null = node;
  for (let hops = 0; n && hops <= maxHops; n = n.parentElement, hops++) {
    const text = n.getAttribute(HELP_ATTR) ?? n.getAttribute("title");
    if (text && text.trim()) return text.trim();
  }
  return "";
}

/** Anything with getAttribute — avoids `instanceof Element`, absent under tsx. */
function isNode(value: unknown): value is HelpNode {
  return !!value && typeof (value as HelpNode).getAttribute === "function";
}

interface HelpRoot {
  querySelectorAll(sel: string): { length: number };
  addEventListener(type: string, fn: (e: Event) => void): void;
}

/**
 * Keep `out` in step with whatever is hovered or focused under `root`.
 *
 * Returns how many controls carry a help string, which is what the regression
 * counts — if a future edit strips the tooltips out of the markup, that number
 * drops and the suite says so.
 */
export function attachHelp(root: HelpRoot, out: { textContent: string | null },
                           active: () => unknown = () => null): number {
  const show = (value: unknown) => {
    const text = isNode(value) ? nearestHelp(value) : "";
    out.textContent = text || HELP_HINT;
  };

  root.addEventListener("focusin", (e: Event) => show(e.target));
  root.addEventListener("mouseover", (e: Event) => show(e.target));
  // Leaving the panel falls back to whatever the keyboard is on, not to a
  // sentence about a control nobody is pointing at any more.
  root.addEventListener("mouseout", (e: Event) => {
    const to = (e as MouseEvent).relatedTarget;
    if (to && isNode(to)) return;
    show(active());
  });

  out.textContent = HELP_HINT;
  return root.querySelectorAll(`[title],[${HELP_ATTR}]`).length;
}

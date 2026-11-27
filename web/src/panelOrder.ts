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
 * What order the side panels sit in, and keeping a stored order honest.
 *
 * #156, part 1: the whole interface is one 380px `<aside>` holding every panel
 * there is, and #88 — scrolling a selected position's card into view and
 * rolling the others up — "is the workaround, not the fix … it exists because
 * six panels cannot fit in 380 pixels."
 *
 * ⭐ COLLAPSE ALREADY SHIPPED. Jerry asked for accordions on 2026.09.24 and the
 * four panels have been `<details>` with remembered open state since. So the
 * half of "collapse and reorder" that was still missing is REORDER, and that is
 * all this file is.
 *
 * ⭐ WHY NOT DRAG AND DROP. #156's other half was that every explanation in the
 * app was a mouse-only tooltip, and the fix for it shipped in #161. Introducing
 * a mouse-only way to arrange the panels in the same breath would be the same
 * mistake with a different control: HTML5 drag-and-drop does not fire on touch
 * at all and needs a parallel keyboard affordance built anyway.
 * ➡ Two buttons per header are keyboard-reachable and touch-friendly by
 * construction, and they are the smaller change.
 *
 * ⚠ THE ORDER IS A PREFERENCE, NOT PART OF A SHOW. #156 is explicit, and it
 * cites #154 and the #63 failure behind it. This goes to browser storage or
 * nowhere — never to the .plot.json.
 */

/** A no-surprises copy with `name` moved by `delta`, or the same order back. */
export function move<T>(order: readonly T[], name: T, delta: number): T[] {
  const from = order.indexOf(name);
  const to = from + delta;
  // ⚠ Off either end is a NO-OP rather than a wrap. A panel that jumped from
  // the bottom to the top because the button was pressed once too often would
  // read as a bug, and the button is disabled at the ends anyway — this is the
  // guard for the keyboard and for a caller that did not check.
  if (from < 0 || to < 0 || to >= order.length) return [...order];
  const next = [...order];
  next.splice(from, 1);
  next.splice(to, 0, name);
  return next;
}

/**
 * A stored order made safe to use against the panels that actually exist.
 *
 * 🔴 STORED DATA OUTLIVES THE CODE THAT WROTE IT. A browser holds this across
 * every future release: a panel renamed or removed leaves a name nothing
 * answers to, a panel added is missing from it, and a half-written value can
 * repeat one. Trusting it would drop a real panel out of the column — the
 * preference would have deleted part of the interface.
 *
 * ⚠ A MISSING NAME IS APPENDED, NOT INSERTED AT ITS DEFAULT INDEX. Splicing a
 * new panel into a rearranged column puts it somewhere neither the default nor
 * the user chose; the bottom is at least predictable, and it is where a reader
 * will look for something that was not there last time. ➡ The cost is real and
 * is accepted: a panel added in a later release arrives below the ones that
 * were rearranged, and whoever adds it should say so in the release notes.
 */
export function sanitize<T>(stored: readonly T[] | null | undefined,
                            known: readonly T[]): T[] {
  if (!stored) return [...known];
  const seen = new Set<T>();
  const out: T[] = [];
  for (const name of stored)
    if (known.includes(name) && !seen.has(name)) { seen.add(name); out.push(name); }
  for (const name of known) if (!seen.has(name)) out.push(name);
  return out;
}

/** Whether a panel can go further in that direction — for disabling a button. */
export function canMove<T>(order: readonly T[], name: T, delta: number): boolean {
  const from = order.indexOf(name);
  return from >= 0 && from + delta >= 0 && from + delta < order.length;
}

/**
 * Reading and writing lengths the way a plot is written: feet and inches.
 *
 * 🔴 Jerry, 2026.09.24, after being told to set a focus height of 1'-6":
 * "I think the 1'6\" trim isn't working cause it doesn't hit the floor."
 *
 * It was never set. Every dimension box was <input type="number">, and a number
 * input SILENTLY DISCARDS anything it cannot parse — type 1'6" and the field
 * goes empty, the change handler reads "" as "clear this field", and the focus
 * height reverts to its 5'-6" default. No error, no red box, nothing: the value
 * just did not happen, and the pool that vanished was the only clue.
 *
 * ⚠ And the app SHOWS feet and inches everywhere — 13'-4" throws, 5'-11" pools,
 * trims on the plot, heights on the boom elevations. Displaying a notation and
 * then refusing to accept it is the part that makes this a trap rather than a
 * limitation: the reader is typing back exactly what the tool just printed.
 *
 * ⚠ Unparseable is NOT the same as empty. Empty means "no value" and clears the
 * field; nonsense means the reader meant something and mistyped it, and must be
 * told rather than have their old value quietly wiped.
 */

/** Feet as a decimal, or null for nonsense, or undefined for empty.
 *
 * Accepts 1'6", 1'-6", 1' 6", 1'6, 1', 18", 1.5, -3, and the prime marks ′ ″
 * that a word processor produces.
 */
export function parseFeet(raw: string): number | null | undefined {
  const s = (raw ?? "").trim().replace(/[′ʹ]/g, "'").replace(/[″ʺ]/g, '"');
  if (s === "") return undefined;

  // feet and inches: 12'6", 12' 6", 12'-6", 12'6, 12'
  const both = /^(-?\d+(?:\.\d+)?)\s*'\s*-?\s*(\d+(?:\.\d+)?)?\s*"?$/.exec(s);
  if (both) {
    const ft = Number(both[1]);
    const inch = both[2] === undefined ? 0 : Number(both[2]);
    if (inch >= 12) return null;           // 5'14" is a typo, not 6'2"
    // ⚠ The sign belongs to the whole length. -1'6" is a foot and a half BELOW
    // zero, not minus one foot plus six inches.
    return ft < 0 ? ft - inch / 12 : ft + inch / 12;
  }

  // inches alone: 18"
  const inches = /^(-?\d+(?:\.\d+)?)\s*"$/.exec(s);
  if (inches) return Number(inches[1]) / 12;

  // plain decimal feet
  if (/^-?\d+(\.\d+)?$/.test(s)) return Number(s);

  return null;
}

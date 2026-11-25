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
 * The zoom slider's position, and the pixels-per-foot it means.
 *
 * #122: "Currently the user is limited when he zooms into the plot… One should
 * be able to zoom in almost to the point where one instrument is visible."
 *
 * ⭐ THE CEILING IS GreedyC's, FROM #160, AND THIS FILE DOES NOT MOVE IT.
 * An instrument is 25⅛" to 39⅜" long — `SHAKESPEARE_LENGTH_IN` in symbols.py —
 * so 2.1 ft at the short end. At the old ceiling of 40 px/ft that was 84 px and
 * a 1000 px canvas showed about 24 ft of stage: a stretch of pipe, not a unit.
 * At 400 it is 840 px, which is one fixture filling the view — what #122 asked
 * for. This file is only about HOW THE SLIDER REACHES IT.
 *
 * 🔴 WHY THE SLIDER IS LOGARITHMIC. #160 raised the ceiling on a LINEAR input,
 * which is the whole of the problem this file exists for: 2–400 linearly leaves
 * the everyday 2–40 range just 9.5% of the travel, and puts the 14 px/ft default
 * 3% from the left end — about nine pixels along a 300px slider. Deep zoom is
 * bought by making every ordinary zoom a one-pixel nudge.
 * ⭐ Mapping position to px/ft exponentially means equal travel is equal RATIO,
 * which is how zoom is read anyway. The same 2–40 then keeps 56.5% of the
 * slider and the default sits at 37%, with the deep end still reaching 400.
 *
 * ⚠ So `slider.value` is NO LONGER pixels per foot. It is a position, 0 to
 * 1000. Everything that reads or writes the slider converts here, and nowhere
 * else knows the mapping exists.
 */

/** Pixels per foot at the left-hand end. */
export const ZOOM_MIN = 2;

/** Pixels per foot at the right-hand end. GreedyC's figure, from #160. */
export const ZOOM_MAX = 400;

/** Slider positions. One step is a 0.46% change, which reads as smooth. */
export const ZOOM_STEPS = 1000;

/** The editor's home zoom, in pixels per foot. What the "100%" button sets. */
export const ZOOM_DEFAULT = 14;

/** Pixels per foot for a slider position. */
export function pxFromPos(pos: number): number {
  const p = Math.max(0, Math.min(ZOOM_STEPS, pos));
  return ZOOM_MIN * (ZOOM_MAX / ZOOM_MIN) ** (p / ZOOM_STEPS);
}

/**
 * The slider position that shows `px` pixels per foot, clamped to the ends.
 *
 * ⚠ Lossy, and harmlessly so: a position is a whole step, and one step is
 * 0.46%, so asking for 14 gives back 14.03. That is three hundredths of a
 * pixel per foot and finer than the slider can express.
 */
export function posFromPx(px: number): number {
  const v = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, px));
  return Math.round(ZOOM_STEPS * Math.log(v / ZOOM_MIN) / Math.log(ZOOM_MAX / ZOOM_MIN));
}

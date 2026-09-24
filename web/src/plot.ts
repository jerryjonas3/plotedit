/**
 * The .plot.json file format.
 *
 * Plain JSON, one file per show: readable in a text editor, diffable in git,
 * and openable in twenty years without a subscription. That is the whole point —
 * two shows in this designer's archive are locked inside .vwx files nothing on
 * the machine can read.
 *
 * Field names follow the Vectorworks/Lightwright exchange so paperwork.py can
 * import old shows with no translation layer.
 */

export interface Instrument {
  /** Unit number, unique within a position. */
  unit: number;
  channel?: number;
  /** The house circuit this unit is plugged into. §6.14.1 draws it in a HEXAGON.
   *
   *  ⚠ Never generated. Circuits depend on the house and have no set order
   *  (Jerry, 2026.09.23) — the only source is the venue's own circuit map. */
  circuit?: number | string;
  dimmer?: number;
  address?: number;
  universe?: number;
  /** A key in the server's FIXTURES table, e.g. "S4 26". */
  type: string;
  /** Feet, plot coordinates. */
  x: number;
  y: number;
  /** Hang height in feet. Without it there is no throw and no level. */
  trim?: number;
  /** Height above the deck, for a unit on a BOOM. ⭐ On a vertical position
   *  every unit shares one x and y, so the height is the only thing that tells
   *  them apart — and the only thing to hang by. */
  height?: number;
  /** Where it points, in feet. focusH defaults to head height. */
  focusX?: number;
  focusY?: number;
  focusH?: number;
  /** "R52+R119" stacks; "R52/R119" is a split frame. */
  color?: string;
  gobo?: string;
  /** Tungsten lamp, e.g. "HPL 575". */
  lamp?: string;
  /** LED output mode, e.g. "Regulated 3200K". */
  mode?: string;
  /** Oval-beam units only (PARNel). Degrees the lens is turned — an oval beam
   *  whose angle nobody recorded is one somebody will hang wrong. */
  lensRotation?: number;
  wattage?: number;
  position?: string;
  purpose?: string;
  /** Barn doors, hats, gobos, irises. RP-2 puts GATE accessories (gobo, iris,
   *  rotator) inside the body and FRONT-of-lens ones (barn doors, hats) at the
   *  nose, so only the name is stored — the drawing works out where it goes.
   *  A list because a unit routinely carries two: a hat and a gobo. */
  accessories?: string[];
  notes?: string;
}

/** A hanging position: a pipe, a boom, a grid line. */
export interface Position {
  name: string;
  /** Endpoints in feet. A boom is drawn as a short line or a point. */
  x1: number; y1: number;
  x2: number; y2: number;
  /** Trim height in feet, if the whole position shares one. */
  trim?: number;
  /** What KIND of position, which decides how it is drawn.
   *
   *  An electric, pipe or grid is one heavy batten line. A catwalk is a
   *  WALKWAY — two architectural edges with a hanging pipe inboard of the
   *  downstage one — because a person stands on it and the units hang off the
   *  rail, not down the middle. A truss gets two chords and diagonals.
   *
   *  Vertical positions (boom, box boom, ladder) are NOT handled yet. */
  type?: "electric" | "pipe" | "grid" | "catwalk" | "truss"
        | "boom" | "box-boom" | "ladder" | "tormentor";
  /** How a FLOOR-STANDING vertical position meets the floor. Not decoration: a
   *  floor plate needs floor space and a sandbag, a flange is already in the
   *  building, and an electrician reading one as the other brings the wrong
   *  hardware.
   *
   *  ⚠ A ladder does not take one — it HANGS, so it carries a `trim` instead.
   *  A tormentor takes neither: it is bolted to the building. */
  mount?: "floor-plate" | "boom-base" | "flange";
  /** RP-2 §6.12 layout for this boom. The standard allows only ONE per plot. */
  layout?: "option1" | "option2";
  /** Front of house — over the audience, downstage of the plaster line, so its
   *  y is NEGATIVE. Catwalks are FOH by default (Jerry, 2026.09.23). The sheet
   *  has to be sized to reach the house or an FOH position is clipped off. */
  foh?: boolean;
  /** Real width in feet. Catwalks default to 3', trusses to 1'-6". */
  width?: number;
  /** How far inboard of the centre the hanging pipe sits. Varies by house —
   *  take it off the venue's section, not from a default. */
  railOffset?: number;
  /** Which end unit 1 sits at. Defaults to Jerry's habit: stage right on a
   *  lateral position, farthest downstage on one running upstage-downstage.
   *
   *  ⚠ Those defaults run in OPPOSITE directions here, because x increases
   *  toward stage right but y increases upstage — so stage right is the MAXIMUM
   *  x and downstage is the MINIMUM y. Do not "simplify" them into one rule. */
  numberFrom?: "SR" | "SL" | "DS" | "US" | "TOP" | "BOTTOM" | "PLASTER" | "CENTER";
  /** The circuits the HOUSE has on this position, in its own order. Bare
   *  numbers, or records with a location along the pipe. With locations, units
   *  can be matched to the nearest circuit; without them, matching refuses. */
  circuits?: Array<number | string | { id: number | string; x?: number; y?: number }>;
  /** Where the circuit list came from. A circuit list without a provenance is
   *  a rumour — this is what `/venue` asks for the rep plot to fill. */
  circuitSource?: string;
}

/** The room. Dimensions carry their source — a rental listing is not a survey. */
export interface Room {
  width: number;
  depth: number;
  /** Downstage edge of the stage, in feet from the room's downstage wall. It
   *  divides the ROOM into house and stage — everything downstage of it is
   *  front of house, and it is what makes an FOH position placeable INSIDE the
   *  room rather than beyond it. */
  plasterLine?: number;
  /** Floor to grid, in feet — the CEILING. Trims are checked against it. */
  gridHeight?: number;
  /** Where that figure came from. A grid height off a rental listing is not a
   *  measurement, and the difference decides whether a 14' trim is comfortable
   *  or impossible. */
  gridSource?: string;
  /** The ceiling over the AUDIENCE, for front-of-house positions. Usually higher
   *  than the stage grid — a catwalk at 18' in a room with a 15' grid is
   *  ordinary, and checking it against the grid reports a fault that is not
   *  there. */
  houseCeiling?: number;
  /** Where these numbers came from, and how old they are. */
  source?: string;
  /** Optional imported DXF, drawn underneath. Path is relative to the plot file. */
  basePlan?: string;
}

/** How the HOUSE gets power to a lamp — RP-2 §6.14.1, and it changes the plot's
 *  notation, not just its data.
 *
 *  "dimmer-per-circuit" is most houses (Jerry, 2026.09.23): the circuit is
 *  hard-wired to its own dimmer, so circuit and dimmer are ONE number and RP-2
 *  draws a single hexagon labelled "Circuit & Dimmer". Drawing two containers
 *  there is not harmlessly redundant — it tells the electrician there is a patch
 *  to make, and there is not. */
export type ControlModel = "dimmer-per-circuit" | "hard-and-soft-patch" | "no-soft-patch";

export interface Plot {
  /** The house's control model. Defaults to dimmer-per-circuit. */
  control?: ControlModel;
  /** RP-2 §6.12: "choose only one type of layout per plot." */
  boomLayout?: "option1" | "option2";
  /** How instruments are ANGLED on the drawing. RP-2 p.2: "It is acceptable to
   *  visually orient the angle of each drawn luminaire to either focus points
   *  or 90° axes." Most plots use 90° mounts, so that is the default: a unit
   *  aiming at 320° is drawn at 0°.
   *
   *  🔴 Cosmetic ONLY. Every throw, pool and footcandle comes from the real
   *  focus — a unit DRAWN at 0° is a convention, a unit COMPUTED at 0° is a lie
   *  about where the light lands. test_agreement.py renders the same plot both
   *  ways and requires identical numbers. */
  symbolAngle?: "orthogonal" | "focus";
  /** Bump when the shape changes incompatibly. */
  formatVersion: 1;
  show: string;
  venue?: string;
  designer?: string;
  /** ISO date. */
  date?: string;
  revision?: string;
  room: Room;
  positions: Position[];
  instruments: Instrument[];
  /** Anything true about this plot that the fields cannot hold. */
  notes?: string[];
}

export function isPlot(x: unknown): x is Plot {
  const p = x as Plot;
  return !!p && p.formatVersion === 1 && !!p.room && Array.isArray(p.instruments);
}

/** The symbol cache key for one instrument: its type, plus its accessories.
 *
 * Two units of the same type with different accessories are different SHAPES,
 * so they cannot share a cache entry keyed on type alone. Built in one place
 * because main.ts asks the server for these keys and render.ts looks them up —
 * if the two ever spelled a key differently the symbol would silently fall back
 * to a plain ring and nobody would know why.
 */
export function symbolKey(inst: Instrument): string {
  const acc = (inst.accessories ?? []).map(a => a.trim()).filter(Boolean);
  return acc.length ? `${inst.type}|${acc.join("+")}` : inst.type;
}

/** Is this position a pipe that STANDS UP — a boom, box boom, ladder, torm?
 *
 * ⭐ In plan a vertical position is a POINT: every unit on it shares one x and y
 * and is told apart only by its height. Mirrors positions.is_vertical() in the
 * Python, including the part that measures rather than trusting the name — a
 * "box boom" is a point in some houses and a rail with real extent in others.
 */
export function isVertical(p: Position): boolean {
  const t = (p.type ?? "").trim().toLowerCase();
  const dx = Math.abs((p.x2 ?? p.x1) - p.x1);
  const dy = Math.abs((p.y2 ?? p.y1) - p.y1);
  if (["boom", "box-boom", "boom-box", "ladder", "tormentor", "torm"].includes(t))
    return !(dx > 0.5 || dy > 0.5);
  if (t) return false;
  return dx < 0.5 && dy < 0.5;
}

/** Front of house — DOWNSTAGE OF THE PLASTER LINE.
 *
 * ⚠ Corrected 2026.09.24. This used to mean "negative y", assuming `room` was
 * the stage and the house lay beyond it. The room is the WHOLE room: the Bluver
 * is 33' x 38' with its plaster line at y = 10, so the house is y 0–10 and the
 * stage 10–38, both inside one rectangle. An FOH position belongs inside it.
 */
export function isFoh(p: Position, plasterLine?: number): boolean {
  if (p.foh !== undefined) return p.foh;
  if (plasterLine === undefined) return false;
  return p.y1 < plasterLine;
}

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
  type?: "electric" | "pipe" | "grid" | "catwalk" | "truss";
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
  numberFrom?: "SR" | "SL" | "DS" | "US";
}

/** The room. Dimensions carry their source — a rental listing is not a survey. */
export interface Room {
  width: number;
  depth: number;
  gridHeight?: number;
  /** Where these numbers came from, and how old they are. */
  source?: string;
  /** Optional imported DXF, drawn underneath. Path is relative to the plot file. */
  basePlan?: string;
}

export interface Plot {
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

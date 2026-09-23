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
  wattage?: number;
  position?: string;
  purpose?: string;
  accessory?: string;
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

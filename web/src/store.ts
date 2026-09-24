/**
 * One plot, one selection, one undo stack. Both views read from here.
 *
 * Deliberately small: a plot is a few dozen instruments, so the whole thing is
 * cloned on every edit and history is just an array of snapshots. No diffing,
 * no proxies, nothing to debug at two in the morning during a tech.
 */
import type { Plot, Instrument, Position } from "./plot.js";

export type Listener = () => void;

/** A snapshot is the plot plus which unit was selected when it was taken, so
 *  undo puts the selection back where the eye expects it. */
interface Snapshot { plot: Plot; selected: number | null }

const HISTORY_LIMIT = 200;

export class Store {
  private _plot: Plot;
  private _selected: number | null = null;      // index into instruments
  private _undo: Snapshot[] = [];
  private _redo: Snapshot[] = [];
  private _dirty = false;
  private listeners = new Set<Listener>();

  constructor(plot: Plot) {
    this._plot = plot;
  }

  get plot(): Plot { return this._plot; }
  get selected(): number | null { return this._selected; }
  get selectedInstrument(): Instrument | null {
    return this._selected === null ? null : this._plot.instruments[this._selected] ?? null;
  }
  get dirty(): boolean { return this._dirty; }
  get canUndo(): boolean { return this._undo.length > 0; }
  get canRedo(): boolean { return this._redo.length > 0; }

  subscribe(fn: Listener): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  private emit(): void { for (const fn of this.listeners) fn(); }

  private snapshot(): Snapshot {
    return { plot: structuredClone(this._plot), selected: this._selected };
  }

  /**
   * Take a history entry before changing anything.
   *
   * `coalesceKey` merges consecutive edits of the same kind — one drag is one
   * undo step, not two hundred. Pass null to force a new entry.
   */
  private lastKey: string | null = null;
  begin(coalesceKey: string | null = null): void {
    if (coalesceKey !== null && coalesceKey === this.lastKey) return;
    this._undo.push(this.snapshot());
    if (this._undo.length > HISTORY_LIMIT) this._undo.shift();
    this._redo.length = 0;
    this.lastKey = coalesceKey;
  }

  /** End a coalescing run, so the next edit starts a fresh undo entry. */
  commit(): void { this.lastKey = null; }

  select(index: number | null): void {
    if (this._selected === index) return;
    this._selected = index;
    this.emit();
  }

  /** Change fields on one instrument. Caller calls begin() first. */
  update(index: number, patch: Partial<Instrument>): void {
    const inst = this._plot.instruments[index];
    if (!inst) return;
    Object.assign(inst, patch);
    this._dirty = true;
    this.emit();
  }

  add(inst: Instrument): number {
    this.begin(null);
    this._plot.instruments.push(inst);
    this._selected = this._plot.instruments.length - 1;
    this._dirty = true;
    this.emit();
    return this._selected;
  }

  /** Add a position. Returns its index.
   *
   * ⚠ Positions had no add or remove at all — a boom or a catwalk could only be
   * created by hand-editing the .plot.json, which meant the editor could not
   * build a plot, only adjust one somebody else had written.
   */
  addPosition(pos: Position): number {
    this.begin(null);
    this._plot.positions.push(pos);
    this._dirty = true;
    this.emit();
    return this._plot.positions.length - 1;
  }

  /** Remove a position. Instruments hung on it are NOT deleted — they are
   *  orphaned and reported, because losing a unit because a pipe was deleted is
   *  a much worse surprise than a unit with no position. */
  removePosition(index: number): string[] {
    const pos = this._plot.positions[index];
    if (!pos) return [];
    const name = pos.name.trim().toLowerCase();
    const orphaned = this._plot.instruments
      .filter(i => (i.position ?? "").trim().toLowerCase() === name)
      .map(i => `unit ${i.unit}`);
    this.begin(null);
    this._plot.positions.splice(index, 1);
    for (const inst of this._plot.instruments) {
      if ((inst.position ?? "").trim().toLowerCase() === name) inst.position = undefined;
    }
    this._dirty = true;
    this.emit();
    return orphaned;
  }

  remove(index: number): void {
    if (!this._plot.instruments[index]) return;
    this.begin(null);
    this._plot.instruments.splice(index, 1);
    if (this._selected !== null && this._selected >= this._plot.instruments.length) {
      this._selected = this._plot.instruments.length ? this._plot.instruments.length - 1 : null;
    }
    this._dirty = true;
    this.emit();
  }

  undo(): void {
    const s = this._undo.pop();
    if (!s) return;
    this._redo.push(this.snapshot());
    this._plot = s.plot;
    this._selected = s.selected;
    this._dirty = true;
    this.lastKey = null;
    this.emit();
  }

  redo(): void {
    const s = this._redo.pop();
    if (!s) return;
    this._undo.push(this.snapshot());
    this._plot = s.plot;
    this._selected = s.selected;
    this._dirty = true;
    this.lastKey = null;
    this.emit();
  }

  markSaved(): void { this._dirty = false; this.emit(); }
}

/**
 * Snap a dragged point to a hanging position.
 *
 * Instruments hang on pipes. A unit sitting at y = 20.3 when the pipe is at 20
 * is wrong on paper and wrong in the room, and nobody notices until the plot is
 * printed. Within `threshold` feet the point lands on the line and the
 * instrument's `position` is set to that pipe's name.
 *
 * Returns the snapped point and the position name, or the original point and
 * null when nothing is near.
 */
export function snapToPosition(
  x: number, y: number, plot: Plot, threshold = 1.0,
): { x: number; y: number; position: string | null } {
  let best: { x: number; y: number; position: string; d: number } | null = null;
  for (const p of plot.positions) {
    const dx = p.x2 - p.x1, dy = p.y2 - p.y1;
    const lenSq = dx * dx + dy * dy;
    // projection of the point onto the segment, clamped to its ends
    const t = lenSq === 0 ? 0 : Math.max(0, Math.min(1, ((x - p.x1) * dx + (y - p.y1) * dy) / lenSq));
    const px = p.x1 + t * dx, py = p.y1 + t * dy;
    const d = Math.hypot(x - px, y - py);
    if (d <= threshold && (!best || d < best.d)) best = { x: px, y: py, position: p.name, d };
  }
  return best ? { x: best.x, y: best.y, position: best.position } : { x, y, position: null };
}

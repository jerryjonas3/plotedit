/** Talk to the Python. Vite proxies /api to localhost:8000. */
import type { Plot } from "./plot.js";
import type { Computed } from "./render.js";

export async function compute(plot: Plot): Promise<Computed[]> {
  const instruments = plot.instruments.map(i => ({
    unit: i.unit, channel: i.channel, type: i.type, x: i.x, y: i.y,
    trim: i.trim, focus_x: i.focusX, focus_y: i.focusY, focus_h: i.focusH ?? 5.5,
    color: i.color, lamp: i.lamp, mode: i.mode,
    position: i.position, purpose: i.purpose,
  }));
  const r = await fetch("/api/compute", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ instruments }),
  });
  if (!r.ok) throw new Error(`compute failed: ${r.status} ${await r.text()}`);
  return (await r.json()).instruments as Computed[];
}

export interface FixtureRow {
  field: number | null; beam: number | null; candela: number | null;
  reference_lamp: string; family: string; modes: string[] | null; source: string;
}

/** The fixture table, so the inspector can offer real types rather than free text. */
export async function fixtures(): Promise<Record<string, FixtureRow>> {
  const r = await fetch("/api/fixtures");
  if (!r.ok) throw new Error(`fixtures failed: ${r.status}`);
  return (await r.json()).fixtures as Record<string, FixtureRow>;
}

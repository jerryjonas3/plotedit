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

// ------------------------------------------------------------------ export

export type ExportKind = "pdf" | "dxf" | "schedule" | "hookup" | "eos";

/** Ask the server for a file and hand it to the browser as a download. */
export async function exportFile(
  kind: ExportKind, plot: Plot, opts: { scale?: string; landscape?: boolean } = {},
): Promise<void> {
  const r = await fetch(`/api/export/${kind}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ plot, scale: opts.scale ?? "1/4", landscape: opts.landscape ?? false }),
  });
  if (!r.ok) {
    // 422 is the sheet refusing to clip — it names the scale that would fit.
    const detail = await r.json().then(j => j.detail).catch(() => r.statusText);
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  const blob = await r.blob();
  const name = filenameFrom(r.headers.get("content-disposition")) ?? `${kind}`;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
}

/** RFC 5987: prefer filename*, fall back to the ASCII filename. */
function filenameFrom(disposition: string | null): string | null {
  if (!disposition) return null;
  const star = /filename\*=UTF-8''([^;]+)/i.exec(disposition);
  if (star?.[1]) return decodeURIComponent(star[1]);
  const plain = /filename="([^"]+)"/i.exec(disposition);
  return plain?.[1] ?? null;
}

// ------------------------------------------------------------------ import

export interface DxfLayers {
  units: string;
  layers: { name: string; entities: number }[];
}

export interface DxfPaths {
  units: string;
  units_from: string;
  layers: string[];
  extents: [number, number, number, number] | null;
  paths: { layer: string; points: [number, number][] }[];
  truncated: boolean;
}

export async function dxfLayers(file: File): Promise<DxfLayers> {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch("/api/import/dxf/layers", { method: "POST", body: fd });
  if (!r.ok) throw new Error((await r.json()).detail ?? r.statusText);
  return r.json();
}

export async function dxfPaths(
  file: File, layers?: string[], units?: string,
): Promise<DxfPaths> {
  const fd = new FormData();
  fd.append("file", file);
  if (layers?.length) fd.append("layers", layers.join(","));
  if (units) fd.append("units", units);
  const r = await fetch("/api/import/dxf", { method: "POST", body: fd });
  if (!r.ok) throw new Error((await r.json()).detail ?? r.statusText);
  return r.json();
}

// ------------------------------------------------------------------ symbols

export type SymbolPrim =
  | { k: "poly"; pts: [number, number][]; closed: boolean }
  | { k: "line"; a: [number, number]; b: [number, number] }
  | { k: "circle"; c: [number, number]; r: number; dashed: boolean; filled: boolean }
  | { k: "text"; c: [number, number]; s: string; size: number };

/** RP-2 symbol outlines, fetched rather than reimplemented.
 *  The geometry lives once, in symbols.py, so the screen and the paper cannot
 *  drift apart the way the photometrics did before test_agreement.py existed. */
export async function symbols(types: string[]): Promise<Record<string, SymbolPrim[]>> {
  const want = [...new Set(types)].filter(Boolean);
  if (!want.length) return {};
  const r = await fetch(`/api/symbols?types=${encodeURIComponent(want.join(","))}`);
  if (!r.ok) throw new Error(`symbols failed: ${r.status}`);
  return (await r.json()).symbols as Record<string, SymbolPrim[]>;
}

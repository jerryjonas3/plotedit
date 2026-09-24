/**
 * The record for the selected instrument, editable.
 *
 * Fields that change the light — type, trim, focus, color, lamp, mode — trigger
 * a recompute. Fields that are only paperwork — purpose, notes — do not, because
 * a round trip per keystroke while typing a purpose is noise.
 */
import { isVertical, type Instrument } from "./plot.js";
import type { Store } from "./store.js";
import type { Computed } from "./render.js";

export interface Field {
  key: keyof Instrument;
  label: string;
  kind: "number" | "text" | "select" | "list";
  /** Does changing it change the light? */
  photometric?: boolean;
  options?: string[];
  step?: number;
  hint?: string;
}

export const FIELDS: Field[] = [
  { key: "unit", label: "Unit", kind: "number", step: 1 },
  { key: "channel", label: "Channel", kind: "number", step: 1 },
  { key: "circuit", label: "Circuit", kind: "text",
    hint: "The HOUSE circuit. Never generated — circuits depend on the house and have no set order" },
  { key: "dimmer", label: "Dimmer", kind: "number", step: 1 },
  { key: "address", label: "Address", kind: "number", step: 1 },
  { key: "type", label: "Type", kind: "select", photometric: true },
  { key: "position", label: "Position", kind: "select" },
  { key: "purpose", label: "Purpose", kind: "text" },
  { key: "x", label: "X (ft)", kind: "number", step: 0.0833, photometric: true },
  { key: "y", label: "Y (ft)", kind: "number", step: 0.0833, photometric: true },
  { key: "trim", label: "Trim (ft)", kind: "number", step: 0.5, photometric: true,
    hint: "Hang height above the deck. On a BOOM this is the height on the "
        + "boom, and it is written to both fields — the elevation reads one, "
        + "the photometrics read the other." },
  { key: "focusX", label: "Focus X", kind: "number", step: 0.5, photometric: true },
  { key: "focusY", label: "Focus Y", kind: "number", step: 0.5, photometric: true },
  { key: "focusH", label: "Focus height", kind: "number", step: 0.5, photometric: true,
    hint: "Head height, 5'-6\" unless the light lands somewhere else" },
  { key: "color", label: "Color", kind: "text", photometric: true,
    hint: "R52+R119 stacks · R52/R119 is a split frame" },
  { key: "gobo", label: "Gobo", kind: "text" },
  { key: "lamp", label: "Lamp", kind: "select", photometric: true },
  { key: "mode", label: "LED mode", kind: "select", photometric: true },
  { key: "lensRotation", label: "Lens angle", kind: "number", step: 15,
    hint: "Oval-beam units (PARNel): degrees the lens is turned" },
  { key: "accessories", label: "Accessories", kind: "list",
    hint: "Separate with + — \"top hat + gobo\". Barn doors, hats, gobo, iris, rotator" },
  { key: "notes", label: "Notes", kind: "text" },
];

/** Is this unit hung on a boom, box boom, ladder or tormentor? */
function onVerticalPosition(store: Store, inst: Instrument): boolean {
  const name = (inst.position ?? "").trim().toLowerCase();
  if (!name) return false;
  const pos = store.plot.positions.find(p => p.name.trim().toLowerCase() === name);
  return pos ? isVertical(pos) : false;
}

export interface InspectorDeps {
  fixtures: string[];
  lamps: string[];
  modes: string[];
  onPhotometricChange: () => void;
  onPaperworkChange: () => void;
}

export function renderInspector(
  host: HTMLElement, store: Store, computed: Computed[], deps: InspectorDeps,
): void {
  host.replaceChildren();
  const i = store.selected;
  const inst = store.selectedInstrument;
  if (i === null || !inst) {
    const p = document.createElement("p");
    p.className = "muted";
    p.textContent = "Click an instrument to edit it. Drag the body to move it, the ring to re-aim it. Alt-drag to place it off a pipe.";
    host.appendChild(p);
    return;
  }

  const c = computed[i];
  if (c) {
    const box = document.createElement("div");
    box.className = "computed";
    if (c.computed) {
      box.innerHTML =
        `<b>${c.throw_ft}</b> throw · <b>${c.elevation?.toFixed(0)}°</b> · ` +
        `pool <b>${c.field_ft ?? "—"}</b><br>` +
        (c.footcandles != null ? `<b>${c.footcandles} fc</b> ` : "") +
        `<span class="muted">${escape(c.footcandles_note ?? "")}</span>`;
    } else {
      box.innerHTML = `<span class="warn">Not computed — ${escape(c.note ?? "")}</span>`;
    }
    if (c.gel_warning) {
      box.innerHTML += `<br><span class="warn">${escape(c.gel_warning)}</span>`;
    }
    host.appendChild(box);
  }

  const grid = document.createElement("div");
  grid.className = "fields";
  for (const f of FIELDS) {
    const id = `f-${String(f.key)}`;
    const label = document.createElement("label");
    label.htmlFor = id;
    label.textContent = f.label;
    if (f.hint) label.title = f.hint;

    let input: HTMLInputElement | HTMLSelectElement;
    if (f.kind === "select") {
      input = document.createElement("select");
      const opts = f.key === "type" ? deps.fixtures
        : f.key === "lamp" ? deps.lamps
        : f.key === "mode" ? deps.modes
        : store.plot.positions.map(p => p.name);
      const blank = document.createElement("option");
      blank.value = ""; blank.textContent = "—";
      input.appendChild(blank);
      for (const o of opts) {
        const el = document.createElement("option");
        el.value = o; el.textContent = o;
        input.appendChild(el);
      }
      input.value = String(inst[f.key] ?? "");
    } else {
      input = document.createElement("input");
      input.type = f.kind === "number" ? "number" : "text";
      if (f.step) input.step = String(f.step);
      const cur = inst[f.key];
      input.value = f.kind === "list"
        // " + " matches the schedule export and the gel notation, where + means
        // "and this as well". A comma would be ambiguous inside a CSV cell.
        ? (Array.isArray(cur) ? cur.join(" + ") : "")
        : cur === undefined || cur === null ? "" : String(cur);
    }
    input.id = id;
    if (f.hint) input.title = f.hint;

    const apply = () => {
      const raw = input.value.trim();
      let value: string | number | undefined;
      if (raw === "") value = undefined;
      else if (f.kind === "list") {
        const parts = raw.split(/\s*[+,]\s*/).map(t => t.trim()).filter(Boolean);
        store.begin(null);
        store.update(i, { [f.key]: parts.length ? parts : undefined } as Partial<Instrument>);
        f.photometric ? deps.onPhotometricChange() : deps.onPaperworkChange();
        return;
      }
      else if (f.kind === "number") {
        const n = Number(raw);
        if (!isFinite(n)) return;
        value = n;
      } else value = raw;
      store.begin(null);
      // 🔴 On a VERTICAL position the trim and the height are the same fact, and
      // they were two fields with only one of them reachable: the inspector had
      // no Height box at all, so a boom unit's height could be set by hand
      // editing the .plot.json and nowhere else. Typing a trim now writes both,
      // rather than leaving a unit whose elevation says one thing and whose
      // throw is computed from another.
      const patch: Record<string, unknown> = { [f.key]: value };
      if (f.key === "trim" && onVerticalPosition(store, inst)) patch.height = value;
      store.update(i, patch as Partial<Instrument>);
      f.photometric ? deps.onPhotometricChange() : deps.onPaperworkChange();
    };
    // change, not input — committing on blur or Enter, so half-typed values
    // never reach the server
    input.addEventListener("change", apply);

    grid.appendChild(label);
    grid.appendChild(input);
  }
  host.appendChild(grid);

  const del = document.createElement("button");
  del.className = "danger";
  del.textContent = "Delete instrument";
  del.addEventListener("click", () => { store.remove(i); deps.onPhotometricChange(); });
  host.appendChild(del);
}

function escape(s: string): string {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

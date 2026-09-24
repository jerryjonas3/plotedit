/**
 * The positions panel — edit the pipes, not just what hangs on them.
 *
 * ⭐ Until now a position could only be created or changed by hand-editing the
 * .plot.json. That made booms, catwalks and trims effectively unreachable from
 * the editor, which is backwards: the trim is the number a designer changes most
 * often at tech, and the position type decides how the whole plot draws.
 *
 * Not selection-based. A plot has a handful of positions and they are all worth
 * seeing at once — unlike instruments, where a list of sixty would be a wall.
 */
import type { Plot, Position } from "./plot.js";
import { isVertical } from "./plot.js";
import type { Store } from "./store.js";

const TYPES = ["electric", "pipe", "grid", "catwalk", "truss",
               "boom", "box-boom", "ladder", "tormentor"] as const;
const MOUNTS = ["", "boom-base", "floor-plate", "flange"] as const;

export interface PositionDeps {
  onChange: () => void;
}

function field(
  label: string, value: string | number | undefined,
  apply: (raw: string) => void, opts?: { options?: readonly string[]; step?: number; hint?: string },
): HTMLElement {
  const wrap = document.createElement("label");
  wrap.className = "pos-field";
  const cap = document.createElement("span");
  cap.textContent = label;
  if (opts?.hint) cap.title = opts.hint;
  wrap.appendChild(cap);

  let input: HTMLInputElement | HTMLSelectElement;
  if (opts?.options) {
    input = document.createElement("select");
    for (const o of opts.options) {
      const el = document.createElement("option");
      el.value = o; el.textContent = o || "—";
      input.appendChild(el);
    }
    input.value = String(value ?? "");
  } else {
    input = document.createElement("input");
    input.type = opts?.step ? "number" : "text";
    if (opts?.step) input.step = String(opts.step);
    input.value = value === undefined || value === null ? "" : String(value);
  }
  // change, not input — a half-typed trim never reaches the server
  input.addEventListener("change", () => apply(input.value.trim()));
  wrap.appendChild(input);
  return wrap;
}

export function renderPositions(
  host: HTMLElement, store: Store, deps: PositionDeps,
): void {
  host.replaceChildren();
  const plot: Plot = store.plot;

  // forEach, not an index loop: `noUncheckedIndexedAccess` is on, so
  // positions[i] is Position | undefined and every read needs a guard. The
  // callback hands back a Position that is known to exist.
  plot.positions.forEach((p) => {
    const box = document.createElement("div");
    box.className = "pos-row";

    const set = (patch: Partial<Position>) => {
      store.begin(null);
      Object.assign(p, patch);
      store.commit();
      deps.onChange();
    };
    const num = (raw: string) => (raw === "" ? undefined : Number(raw));

    box.appendChild(field("Name", p.name, v => set({ name: v })));
    box.appendChild(field("Type", p.type ?? "electric",
      v => set({ type: v as Position["type"] }), { options: TYPES }));
    // ⭐ Moving a pipe MOVES ITS RIG. Setting the trim alone changed only the
    // label while every unit went on computing from the old height — the plot
    // would state one trim and compute another. Units keep any deliberate
    // offset, so a drop-arm stays a drop-arm.
    box.appendChild(field("Trim", p.trim, v => {
      const t = num(v);
      const old = p.trim;
      store.begin(null);
      p.trim = t;
      if (t !== undefined && old !== undefined) {
        for (const inst of plot.instruments) {
          if ((inst.position ?? "").trim().toLowerCase() !== p.name.trim().toLowerCase()) continue;
          if (inst.trim === undefined) continue;
          inst.trim = inst.trim + (t - old);
        }
      }
      store.commit();
      deps.onChange();
    }, { step: 0.5, hint: "Moves every unit on this position with it, keeping any deliberate offset" }));

    if (isVertical(p)) {
      // ⚠ A ladder HANGS and a tormentor is bolted to the building — neither
      // takes a floor mount. Offering one invites hardware that does not exist.
      const t = (p.type ?? "").toLowerCase();
      if (t !== "ladder" && t !== "tormentor" && t !== "torm") {
        box.appendChild(field("Mount", p.mount ?? "",
          v => set({ mount: (v || undefined) as Position["mount"] }),
          { options: MOUNTS, hint: "A floor plate needs floor space and a sandbag; a flange is already in the building" }));
      }
      box.appendChild(field("X", p.x1, v => set({ x1: Number(v), x2: Number(v) }), { step: 0.5 }));
      box.appendChild(field("Y", p.y1, v => set({ y1: Number(v), y2: Number(v) }), { step: 0.5 }));
    } else {
      box.appendChild(field("X1", p.x1, v => set({ x1: Number(v) }), { step: 0.5 }));
      box.appendChild(field("Y1", p.y1, v => set({ y1: Number(v), y2: Number(v) }), { step: 0.5 }));
      box.appendChild(field("X2", p.x2, v => set({ x2: Number(v) }), { step: 0.5 }));
      if ((p.type ?? "") === "catwalk" || (p.type ?? "") === "truss")
        box.appendChild(field("Width", p.width, v => set({ width: num(v) }), { step: 0.5 }));
    }

    const note = document.createElement("p");
    note.className = "muted pos-note";
    const bits: string[] = [];

    // ⭐ A trim above the ceiling cannot be hung. Nothing checked until
    // 2026.09.24, when a pipe was raised to 18' in a room with a 15' grid and
    // the tool drew it, computed levels from it and printed it without a word.
    const grid = plot.room.gridHeight;
    const foh = p.foh ?? (plot.room.plasterLine !== undefined && p.y1 < plot.room.plasterLine);
    if (p.trim !== undefined && grid !== undefined && !foh) {
      if (p.trim > grid) {
        bits.push(`🔴 ABOVE THE ${grid}' CEILING — this cannot be hung`);
      } else if (p.trim > grid - 1.5) {
        bits.push(`under 1'-6" below the ${grid}' grid — a Source Four and its clamp need about that`);
      }
    }
    if (isVertical(p)) bits.push("vertical — a POINT in plan; units differ by height");
    if (foh) bits.push("front of house — downstage of the plaster line, over the audience");
    if (p.circuits?.length) bits.push(`${p.circuits.length} circuits recorded`);
    else bits.push("no circuits recorded — no load table can be built");
    note.textContent = bits.join(" · ");
    box.appendChild(note);

    const actions = document.createElement("div");
    actions.className = "pos-actions";

    const addUnit = document.createElement("button");
    addUnit.textContent = "+ unit";
    addUnit.title = "Hang a unit on this position, at its trim";
    addUnit.addEventListener("click", () => {
      const name = p.name.trim().toLowerCase();
      const on = plot.instruments.filter(
        i => (i.position ?? "").trim().toLowerCase() === name);
      // ⭐ Copy the LAST unit on this pipe. A designer hanging a wash hangs the
      // same thing six times; starting from a blank one every time would be six times
      // the typing for no gain. Falls back to the plot's most recent unit.
      const model = on[on.length - 1] ?? plot.instruments[plot.instruments.length - 1];
      const nextUnit = on.length ? Math.max(...on.map(i => i.unit)) + 1 : 1;
      const nextCh = plot.instruments.length
        ? Math.max(...plot.instruments.map(i => i.channel ?? 0)) + 1 : 1;
      // Drop it at the middle of the pipe — visible, and on the position rather
      // than at the origin where it would be missed.
      const mid = isVertical(p)
        ? { x: p.x1, y: p.y1 }
        : { x: (p.x1 + p.x2) / 2, y: (p.y1 + p.y2) / 2 };
      store.add({
        unit: nextUnit,
        channel: nextCh,
        type: model?.type ?? "S4 26",
        x: mid.x, y: mid.y,
        trim: p.trim,
        ...(isVertical(p) ? { height: p.trim } : {}),
        position: p.name,
        color: model?.color,
        lamp: model?.lamp,
        focusX: model?.focusX, focusY: model?.focusY,
      });
      deps.onChange();
    });
    actions.appendChild(addUnit);

    const del = document.createElement("button");
    del.textContent = "delete";
    del.className = "danger";
    del.addEventListener("click", () => {
      const idx = plot.positions.indexOf(p);
      const name = p.name.trim().toLowerCase();
      const on = plot.instruments.filter(
        i => (i.position ?? "").trim().toLowerCase() === name).length;
      // ⚠ Ask when it costs something. Deleting a pipe with a rig on it is not
      // the same action as deleting an empty one.
      if (on && !confirm(
        `${p.name} has ${on} unit${on > 1 ? "s" : ""} on it.\n\n` +
        `Delete the position? The units are KEPT but lose their position.`)) return;
      const orphaned = store.removePosition(idx);
      if (orphaned.length) {
        alert(`${p.name} deleted. ${orphaned.join(", ")} now ` +
              `${orphaned.length > 1 ? "have" : "has"} no position — ` +
              `reassign ${orphaned.length > 1 ? "them" : "it"} in the inspector.`);
      }
      deps.onChange();
    });
    actions.appendChild(del);
    box.appendChild(actions);

    host.appendChild(box);
  });

  const addPos = document.createElement("button");
  addPos.textContent = "+ Add position";
  addPos.addEventListener("click", () => {
    const n = plot.positions.length + 1;
    store.addPosition({
      name: `Electric ${n}`,
      type: "electric",
      x1: 0, y1: Math.min(plot.room.depth - 2, 8 + n * 4),
      x2: plot.room.width, y2: Math.min(plot.room.depth - 2, 8 + n * 4),
      trim: plot.room.gridHeight !== undefined
        ? Math.max(0, plot.room.gridHeight - 2) : undefined,
    });
    deps.onChange();
  });
  host.appendChild(addPos);
}

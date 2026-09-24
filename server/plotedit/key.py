"""The legend / instrument key — RP-2 §5.

    §5.0: "Placement is acceptable in any location that does not conflict with
    other information."

⭐ A key is not a parts list. It is the drawing's own dictionary: it says what
each shape means, so a stranger can read the plot without asking the designer.
That is why §5.1 asks for the SYMBOLS themselves and not just names, and why
they are drawn at the plot's own scale here — a key drawn at a different size
teaches the reader a shape they will not see again.

§5.1 wants, and this produces:
  · symbols of every luminaire and device on the plot, with descriptions
  · beam spread where the name does not already carry it
  · every notation used, explained
  · colour manufacturer designations (R = Rosco, L = Lee, G = Gam …)
  · template manufacturer designation, when there is one
  · wattage and/or ANSI lamp code
  · symbols for any accessories

⚠ It reports what is ON THE PLOT, never the whole fixture table. A key listing
instruments nobody hung is a key nobody finishes reading.
"""
from collections import Counter
from typing import Any, Dict, List

from . import photometrics as ph
from . import symbols as sym
from .scaled_pdf import ft

# §5.1: "Color manufacturer designation (e.g., R = Rosco, L = Lee, G = Gam)".
COLOR_MAKERS = {"R": "Rosco", "L": "Lee", "G": "Gam", "A": "Apollo", "AP": "Apollo"}


def colors_used(plot: Dict[str, Any]) -> List[str]:
    """Every gel on the plot, in order of first appearance."""
    seen, out = set(), []
    for i in plot.get("instruments", []):
        c = (i.get("color") or "").strip()
        if c and c.upper() not in seen:
            seen.add(c.upper()); out.append(c)
    return out


def makers_used(plot: Dict[str, Any]) -> List[str]:
    """Which manufacturers' prefixes actually appear, expanded.

    Only the ones used: a key that explains L = Lee on a plot with no Lee in it
    is teaching the reader something they do not need.
    """
    found = []
    for c in colors_used(plot):
        for part in c.replace("/", "+").split("+"):
            part = part.strip().upper()
            for n in (2, 1):
                if part[:n] in COLOR_MAKERS and COLOR_MAKERS[part[:n]] not in found:
                    found.append(COLOR_MAKERS[part[:n]]); break
    return found


def types_used(plot: Dict[str, Any]) -> List[Dict[str, Any]]:
    """One row per fixture type on the plot: symbol, description, angle, watts, count."""
    counts = Counter((i.get("type") or "").strip()
                     for i in plot.get("instruments", []) if i.get("type"))
    rows = []
    for name, n in counts.most_common():
        key, row, note = ph.lookup(name)
        # §5.1 asks for beam spread "if the numeric value is not part of the
        # luminaire's name". It is worth giving even when it looks like it is:
        # "S4 26" names the NOMINAL barrel, and the measured field is 25° with a
        # beam of 18°. The nominal number is the product; these are the light.
        # Repeating a name would be clutter — publishing the real angles is not.
        field = row.get("field") if row else None
        beam = row.get("beam") if row else None
        watts, wnote = ph.watts_for(name) if row else (None, "")
        rows.append({"name": name, "key": key, "count": n,
                     "field": field, "beam": beam,
                     "watts": watts, "watt_note": wnote,
                     "unknown": row is None, "note": note})
    return rows


def accessories_used(plot: Dict[str, Any]) -> List[str]:
    seen, out = set(), []
    for i in plot.get("instruments", []):
        for a in i.get("accessories") or []:
            if str(a).lower() not in seen:
                seen.add(str(a).lower()); out.append(str(a))
    return out


def draw(sheet, plot, x, y, width=11.0, line=0.85, title="INSTRUMENT KEY"):
    """Draw the key at (x, y) — its TOP-left corner — in plot feet.

    Symbols are drawn at the sheet's own scale. A key drawn at some other size
    teaches the reader a shape they will never see again.

    Returns the y it finished at, so a caller can stack a schedule under it.
    """
    from reportlab.lib.colors import grey
    sheet.layer("NOTES")
    cy = y
    sheet.text(x, cy, title, size=8, bold=True)
    cy -= line * 1.2

    # ── the luminaires themselves ──────────────────────────────────────────
    for r in types_used(plot):
        prims = sym.for_type(r["name"])
        # ⚠ Space each row by the SYMBOL's own size, and lay the instruments
        # horizontally. Drawn nose-up on a fixed row height they overlapped each
        # other — a key whose symbols collide teaches the reader the wrong shape,
        # which is worse than no key.
        rad = sym.radius(prims)
        cy -= rad                                  # drop to this row's centre
        sym.draw(sheet, prims, x + 0.9, cy, rotate_deg=90, width=1.0)
        desc = f"{r['count']} × {r['name']}"
        sheet.text(x + 2.2, cy + line * 0.3, desc, size=6, bold=True)
        bits = []
        if r["field"]:
            bits.append(f"field {r['field']:.0f}°" +
                        (f" / beam {r['beam']:.0f}°" if r.get("beam") else ""))
        if r["watts"]:
            bits.append(f"{r['watts']:.0f} W")
        if r["unknown"]:
            # ⚠ Never silently. A type the tool cannot identify is a type the
            # reader should be told about, not one quietly given no angle.
            bits.append("NOT IN THE FIXTURE TABLE — angles and load unknown")
        if bits:
            sheet.text(x + 2.2, cy - line * 0.35, " · ".join(bits), size=5.5, color=grey)
        cy -= rad + line * 0.5

    # ── §5.1: every notation used, explained ───────────────────────────────
    control = plot.get("control", "dimmer-per-circuit")
    cy -= line * 0.4
    sheet.text(x, cy, "NOTATION", size=7, bold=True)
    cy -= line
    rows = [("hexagon", "circuit & dimmer" if control == "dimmer-per-circuit" else "circuit"),
            ("circle", "channel"),
            ("number in the body", "unit number"),
            ("small number below it", "wattage")]
    if control == "hard-and-soft-patch":
        rows.insert(1, ("rectangle", "dimmer"))
    for shape, means in rows:
        sheet.text(x + 0.4, cy, f"{shape} = {means}", size=5.5)
        cy -= line * 0.72
    if control == "dimmer-per-circuit":
        sheet.text(x + 0.4, cy, "This house is DIMMER PER CIRCUIT — circuit and "
                                "dimmer are one number.", size=5.5, color=grey)
        cy -= line * 0.72

    # ── §5.1: colour, and the manufacturer designations actually used ──────
    cols = colors_used(plot)
    if cols:
        cy -= line * 0.4
        sheet.text(x, cy, "COLOR", size=7, bold=True)
        cy -= line
        for c in cols:
            factor, note = ph.gel_factor(c)
            txt = c + (f"  —  {factor * 100:.0f}% transmission" if factor else "")
            if "SPLIT" in (note or "").upper():
                txt += "  (SPLIT FRAME — no single figure describes the pool)"
            sheet.text(x + 0.4, cy, txt, size=5.5)
            cy -= line * 0.72
        makers = makers_used(plot)
        if makers:
            pref = ", ".join(f"{k} = {v}" for k, v in COLOR_MAKERS.items() if v in makers)
            sheet.text(x + 0.4, cy, pref, size=5.5, color=grey)
            cy -= line * 0.72
        sheet.text(x + 0.4, cy, "+ stacks (transmissions multiply) · / is a split frame",
                   size=5.5, color=grey)
        cy -= line * 0.72

    # ── §5.1: accessories, with their symbols ──────────────────────────────
    acc = accessories_used(plot)
    if acc:
        cy -= line * 0.4
        sheet.text(x, cy, "ACCESSORIES", size=7, bold=True)
        cy -= line * 1.1
        ax = x + 0.7
        for a in acc:
            where, k, _ = sym.resolve_accessory(a)
            if where == "front":
                shape = (sym.barn_door(2) if k == "bd2" else sym.barn_door(4)
                         if k == "bd4" else sym.top_hat(half=(k == "halfhat")))
                sym.draw(sheet, shape, ax, cy, rotate_deg=180, width=1.0)
            elif where == "gate":
                sheet.circle(ax, cy, 0.09, fill=None if k == "iris" else sym._black())
            sheet.text(ax + 0.55, cy - 0.06, a, size=5.5)
            ax += max(3.0, width / max(len(acc), 1))
        cy -= line * 1.3

    return cy

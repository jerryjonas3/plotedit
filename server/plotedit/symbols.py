#!/usr/bin/env python3
"""Instrument symbols drawn to USITT RP-2 (2006).

The standard is in docs/reference/USITT-RP-2-2006.pdf; the plates are pages 4–9,
and docs/SYMBOLS.md maps each fixture family to its section. **Read those before
changing anything here.** The previous symbols were drawn from memory and were
wrong in most respects; these are traced from the plates.

COORDINATES. Every symbol is defined in a local frame:

    +a  is toward the BACK of the instrument (the reflector end)
    -a  is toward the FRONT (the lens, where the light goes)
    +c / -c are the two sides
    the ORIGIN is the yoke — the hanging point, which is where RP-2 §2.2 says
    the symbol must be positioned

Sizes are in FEET and approximate the real instrument, per §2.2: "luminaire
symbols ... should represent the approximate size and shape of the luminaires in
scale." A Source Four is about 22" long and 7" across the body.

Each builder returns a list of (kind, payload) primitives so the same definition
can be drawn to PDF, to SVG, or to DXF without three copies of the geometry:

    ("poly",  [(a, c), ...], closed)      an outline
    ("line",  (a1, c1), (a2, c2))         a single stroke
    ("circle", (a, c), r, filled)
    ("text",  (a, c), "T", size)          a letter inside the symbol
"""
import math

# ------------------------------------------------------------------ helpers

def _mirror(pts):
    """Given the upper half of a symmetrical outline, return the whole thing."""
    return list(pts) + [(a, -c) for a, c in reversed(pts)]


# ------------------------------------------------------- §6.1.6 Enhanced ERS

# The Source Four family. RP-2 codes the beam angle by the MARK INSIDE THE LENS
# HOUSING, not by the length of the barrel:
#
#   70°        stepped rings at the front
#   50°        a wedge pointing back into the body
#   36°–40°    no mark
#   26°–30°    one diagonal
#   19°–20°    an X
#
# Only the very narrow units (15°, 10°, 5°) get a longer body, and those are a
# different sub-family in §6.1.6.

ERS_MARKS = {
    90: "rings", 70: "rings", 50: "wedge", 40: None, 36: None,
    30: "diagonal", 26: "diagonal", 20: "cross", 19: "cross",
    15: "long", 14: "long", 10: "long", 5: "long",
}


def enhanced_ers(angle=26, length=1.667, width=0.625):
    """§6.1.6. Defaults are a Source Four: 20" long, 7.5" across the body.

    Shape grammar traced from the plate. Reading from the FRONT backwards:

        0.00 - 0.26 L   lens housing — a SHORT, STEEP flare to a flat front face
        0.26 - 0.34 L   the neck, at 62% of the body width
        0.34 - 1.00 L   the body, at full width, tapered at the back

    The flare is short and steep in RP-2, not a long gentle cone. Getting that
    wrong is what made the second attempt read as a funnel rather than an ERS.

    The front face is a touch TALLER than the body — that flare is what makes an
    ERS read as an ERS, and getting it backwards was the first attempt's worst error.

    ⚠ RP-2 draws the symbol at about 2:1; a real Source Four is nearer 2.7:1.
    §2.2 asks for approximate real size and shape, so the REAL footprint is used
    and RP-2's shape grammar is stretched along it. The silhouette reads the same
    and the plot does not under-state how much pipe a unit occupies.
    """
    w = width / 2
    front = -length * 0.60          # yoke sits 40% back from the front
    back = length + front
    face = front
    flare_end = front + 0.26 * length
    neck_end = front + 0.34 * length
    chamfer = 0.15 * length

    neck_w = 0.62 * w
    face_w = 1.08 * w

    upper = [
        (face, face_w),                 # flat front face
        (flare_end, neck_w),            # flare back to the neck
        (neck_end, neck_w),             # the neck
        (neck_end, w),                  # step out to the body — the shoulder
        (back - chamfer, w),            # body at full width
        (back, w * 0.55),               # tapered back
    ]
    out = [("poly", _mirror(upper), True)]

    mark = ERS_MARKS.get(int(angle))
    if mark == "cross":                                   # 19°-20°
        out += [("line", (flare_end, neck_w), (face, -face_w)),
                ("line", (flare_end, -neck_w), (face, face_w))]
    elif mark == "diagonal":                              # 26°-30°
        out += [("line", (flare_end, -neck_w), (face, face_w))]
    elif mark == "wedge":                                 # 50°
        out += [("poly", [(face, face_w), (flare_end, 0.0), (face, -face_w)], False)]
    elif mark == "rings":                                 # 70°-90°
        for t in (0.34, 0.68):
            x = face + t * (flare_end - face)
            out += [("line", (x, face_w * 0.92), (x, -face_w * 0.92))]
    return out


def ers_zoom(angle=30, **kw):
    """§6.1.11 variable focus — the same body carrying a Z."""
    out = enhanced_ers(angle, **kw)
    return out + [("text", (0.0, 0.0), "Z", 0.30)]


# --------------------------------------------------------------- §6.2 Fresnel

def fresnel(size_in=6):
    """§6.2. Rounded back, straight body, and a lens ring standing proud at the
    front — the ring is what distinguishes a Fresnel from an ERS at a glance."""
    width = 0.055 * size_in + 0.16
    length = width * 1.5
    w = width / 2
    front = -0.58 * length
    back = length + front
    ring = front + 0.20 * length
    upper = [
        (front, w * 1.18),          # the lens ring, wider than the body
        (ring, w * 1.18),
        (ring, w),
        (back - 0.18 * length, w),
        (back, w * 0.55),           # rounded/chamfered back
    ]
    return [("poly", _mirror(upper), True)]


def oval_beam_fresnel(length=1.05, width=0.72, rotation=None):
    """§6.2 "Oval Beam Fresnel" — which is what an ETC Source Four PARNel is.

    A PARNel is ETC's oval-beam unit: a PAR-style body with a Fresnel-type lens
    that throws a soft oval, and a lens that ROTATES so the oval can be turned.
    RP-2 has no "PARNel" but it has this, and it is the same instrument class.

    Distinctive against a plain Fresnel: shorter and squatter, with a lens flange
    that stands proud and is clearly WIDER than the body.

    `rotation` in degrees adds the oval-axis bar. An oval beam that nobody has
    been told the angle of is an oval beam somebody will hang wrong, and §6.14.4
    requires an axis note for PAR lamps for exactly this reason.
    """
    w = width / 2
    front = -0.55 * length
    back = length + front
    flange = front + 0.17 * length
    upper = [
        (front, w * 1.22),            # lens flange, proud and wider than the body
        (flange, w * 1.22),
        (flange, w),
        (back - 0.22 * length, w),
        (back - 0.06 * length, w * 0.82),   # curved back, two chords
        (back, w * 0.40),
    ]
    out = [("poly", _mirror(upper), True)]
    if rotation is not None:
        # The oval-axis bar goes across the BODY, not the lens flange — the
        # flange is only a fifth of the length deep, so a tilted bar drawn there
        # collapses to nothing. Sized to stay inside the outline at any angle.
        a = math.radians(rotation)
        body_half_len = (back - flange) / 2
        cx = (flange + back) / 2
        r = min(w * 0.82 / max(abs(math.cos(a)), 1e-6),
                body_half_len * 0.82 / max(abs(math.sin(a)), 1e-6))
        out.append(("line",
                    (cx - r * math.sin(a), -r * math.cos(a)),
                    (cx + r * math.sin(a), r * math.cos(a))))
    return out


# ------------------------------------------------------------------- §6.3 PAR

# §6.3.2: the beam spread is a MARK ON THE FRONT, and §6.14.4 adds a lamp-axis
# rotation arrow — a PAR's filament has an orientation and the electrician needs it.
PAR_MARKS = {"XWFL": "square", "WFL": "triangle", "MFL": "bar",
             "NSP": "narrow", "VNSP": "cross"}


def par(lamp=64, spread="MFL"):
    """§6.3. A rounded capsule sized by lamp, with the beam spread marked on the
    front per §6.3.2. §6.14.4 also requires a lamp-axis arrow, which the plot
    adds as an annotation rather than as part of the symbol."""
    width = {16: 0.17, 38: 0.33, 46: 0.40, 56: 0.48, 64: 0.65}.get(lamp, 0.65)
    length = width * 1.35
    w = width / 2
    front = -0.55 * length
    back = length + front
    r = w * 0.55
    upper = [
        (front, w),
        (back - r, w),
        (back - r * 0.3, w * 0.85),      # rounded back, three chords
        (back, w * 0.45),
    ]
    out = [("poly", _mirror(upper), True)]

    m = PAR_MARKS.get(spread)
    d = 0.30 * length
    if m == "cross":
        out += [("line", (front + d, w), (front, -w)), ("line", (front + d, -w), (front, w))]
    elif m == "narrow":
        out += [("line", (front + d, -w), (front, w))]
    elif m == "triangle":
        out += [("poly", [(front, w), (front + d, 0.0), (front, -w)], False)]
    elif m == "square":
        out += [("poly", [(front + 0.08 * length, w * 0.55), (front + d, w * 0.55),
                          (front + d, -w * 0.55), (front + 0.08 * length, -w * 0.55)], True)]
    elif m == "bar":
        out += [("line", (front + d * 0.6, w * 0.8), (front + d * 0.6, -w * 0.8))]
    return out


# --------------------------------------------------------- §6.16 LED fixtures

def led(colors=7, length=1.5, width=0.62):
    """§6.16. Dots inside the body — THE NUMBER OF DOTS IS THE NUMBER OF COLORS.

    A Lustr's x7 array is seven dots; an ADJ Mega Tri Bar is three.
    """
    back, front = 0.40 * length, -0.60 * length
    w = width / 2
    upper = [(back - 0.12 * length, w * 0.5), (back, w * 0.9), (back, w), (front, w)]
    out = [("poly", _mirror(upper), True)]
    # lay the dots out in the front half, in rows, the way the plate shows
    n = max(1, int(colors))
    per_row = 1 if n <= 1 else (2 if n <= 4 else 3)
    rows = math.ceil(n / per_row)
    placed = 0
    for r in range(rows):
        a = front + (0.20 + 0.16 * r) * length
        k = min(per_row, n - placed)
        for i in range(k):
            c = 0 if k == 1 else (-w * 0.45 + i * (w * 0.9 / (k - 1)))
            out.append(("circle", (a, c), width * 0.045, True))
            placed += 1
    return out


# ------------------------------------------------- §6.8 automated luminaires

def moving_head(kind="wash", body=0.95, swing=1.45):
    """§6.8.2. Moving yoke / head. Drawn inside a DASHED SWING-RADIUS circle —
    RP-2: "should approximate size, shape, and swing radius." The dashed circle
    is the useful part: it is the space the unit needs to not hit anything."""
    w = body / 2
    out = [("circle", (0.0, 0.0), swing / 2, "dashed")]
    nose = -w * 1.05
    upper = [(nose, w * 0.72), (-w * 0.55, w), (w * 0.55, w), (w, w * 0.6)]
    out += [("poly", _mirror(upper), True)]
    if kind == "yoke":
        out += [("text", (0.0, 0.0), "Y", 0.26)]
    elif kind == "spot":
        out += [("line", (nose, w * 0.55), (nose, -w * 0.55))]
    return out


# ------------------------------------------------------------- §6.9 practical

def practical(size=0.5):
    """§6.9. A triangle. Nothing else."""
    h = size
    return [("poly", [(h * 0.5, 0.0), (-h * 0.5, h * 0.55), (-h * 0.5, -h * 0.55)], True)]


# --------------------------------------------------------------- §6.10 / 6.6

def followspot(length=2.4, width=0.9):
    """§6.10. A long body with a stepped waist."""
    back, front = 0.45 * length, -0.55 * length
    w = width / 2
    upper = [(back - 0.10 * length, w * 0.55), (back, w * 0.8), (back, w * 0.8),
             (back - 0.42 * length, w * 0.8), (back - 0.48 * length, w),
             (front + 0.12 * length, w), (front, w * 0.78)]
    return [("poly", _mirror(upper), True)]


def cyc_unit(cells=3, cell=1.0, depth=0.75):
    """§6.6.2. Rectangles divided into cells — one box per cell."""
    total = cells * cell
    out = []
    for i in range(cells):
        a0 = depth / 2
        c0 = -total / 2 + i * cell
        out.append(("poly", [(a0, c0), (a0, c0 + cell),
                             (-a0, c0 + cell), (-a0, c0)], True))
    return out


def striplight(length=6.0, depth=0.6, lamp="PAR 38"):
    """§6.7.1. Length follows the real unit — RP-2: 'Measure the instruments.'"""
    a, c = depth / 2, length / 2
    return [("poly", [(a, -c), (a, c), (-a, c), (-a * 0.7, c),
                      (-a * 0.7, -c), (-a, -c)], True)]


# ------------------------------------------------------------------ drawing

def draw(sheet, prims, x, y, rotate_deg=0.0, width=None):
    """Draw primitives onto a scaled_pdf.Sheet at (x, y) feet, pointing `rotate_deg`.

    0° points the instrument toward -y (downstage). RP-2 §2.2 allows orienting a
    symbol either to its focus point or to a 90° axis.
    """
    # §6.18: a luminaire is a HEAVY line — it is a thing that physically exists.
    from .scaled_pdf import LINE_STYLES
    lw = width if width is not None else LINE_STYLES["luminaire"][0]
    a = math.radians(rotate_deg)
    ca, sa = math.cos(a), math.sin(a)

    def T(pa, pc):
        # local (along-axis, cross-axis) -> plot (x, y); -a is the front, so the
        # instrument points toward -y when unrotated
        lx, ly = pc, pa
        return (x + lx * ca - ly * sa, y + lx * sa + ly * ca)

    for p in prims:
        kind = p[0]
        if kind == "poly":
            pts = [T(*q) for q in p[1]]
            closed = p[2]
            for i in range(len(pts) - 1 + (1 if closed else 0)):
                q1, q2 = pts[i], pts[(i + 1) % len(pts)]
                sheet.line(q1[0], q1[1], q2[0], q2[1], width=lw)
        elif kind == "line":
            q1, q2 = T(*p[1]), T(*p[2])
            sheet.line(q1[0], q1[1], q2[0], q2[1], width=lw * 0.8)
        elif kind == "circle":
            q = T(*p[1])
            dashed = len(p) > 3 and p[3] == "dashed"
            filled = len(p) > 3 and p[3] is True
            sheet.circle(q[0], q[1], p[2], width=lw * (0.45 if dashed else 0.8),
                         fill=None, dash=(2, 2) if dashed else None)
            if filled:
                sheet.circle(q[0], q[1], p[2], width=0.3, fill=_black())
        elif kind == "text":
            q = T(*p[1])
            sheet.text(q[0], q[1], p[2], size=p[3] * 26, center=True, bold=True)


def _black():
    from reportlab.lib.colors import black
    return black


# ------------------------------------------------------ §6.14 luminaire notation

def for_type(kind, lens_rotation=None):
    """Pick a symbol from a fixture-table key like "S4 26" or "Lustr 26 EDLT".

    lens_rotation (degrees) is used by oval-beam units — a PARNel's lens turns,
    and the angle is information the electrician needs, not decoration.
    """
    k = (kind or "").strip()
    # Resolve a paperwork name to a table key first — "ETC Source4 36deg" should
    # draw exactly what "S4 36" draws, not something the loose matcher guessed.
    try:
        from .fixture_names import resolve
        from . import photometrics as _ph
        _key, _ = resolve(k, _ph.FIXTURES)
        if _key:
            k = _key
    except Exception:
        pass
    low = k.lower()
    import re as _re
    # ⚠ "S4 26" must not parse as 4 degrees. Strip the product names that carry
    # a digit — Source4, S4, PAR 64, MR-16 — before looking for the beam angle.
    cleaned = _re.sub(r"(source\s*4|s4|par\s*\d+|mr-?\d+|\bx7\b|series\s*\d)", " ",
                      low, flags=_re.I)
    n = _re.findall(r"(\d+(?:\.\d+)?)\s*(?:deg|°)?", cleaned)
    deg = float(n[0]) if n else 26.0

    if "cyc" in low:
        return cyc_unit(3)
    if "lustr" in low or "colorsource" in low or "clrsrc" in low or "led" in low:
        # §6.16: dots = number of colors. A Lustr is the x7 array; ColorSource
        # is five — red, green, blue, lime, indigo — per ETC's own datasheets.
        colors = 7 if "lustr" in low else (5 if ("colorsource" in low or "clrsrc" in low) else 4)
        return led(colors)
    if "parnel" in low or "oval" in low:
        # An oval beam needs its axis called out. Default to level — the
        # commonest hang, and what an electrician assumes if nobody says.
        return oval_beam_fresnel(rotation=lens_rotation if lens_rotation is not None else 0)
    if "par" in low:
        spread = next((s for s in ("VNSP", "XWFL", "WFL", "MFL", "NSP") if s in k.upper()), "MFL")
        lamp = 64 if "64" in k else (56 if "56" in k else 64)
        return par(lamp, spread)
    if "fresnel" in low or "fres" in low:
        size = 8 if "8" in k else 6
        return fresnel(size)
    if "strip" in low:
        return striplight()
    if "mac" in low or "mover" in low or "moving" in low or "aura" in low:
        return moving_head("wash")
    if "zoom" in low:
        return ers_zoom(deg)
    # default: an ellipsoidal at whatever angle the name carries
    return enhanced_ers(deg)


def notation(sheet, x, y, *, channel=None, circuit=None, dimmer=None,
             color=None, purpose=None, unit=None, wattage=None,
             size=0.42, gap=0.30, above=1.0):
    """§6.14.1 — the SHAPE of the container carries the meaning.

        hexagon    circuit
        rectangle  dimmer (in a patch-panel house)
        circle     channel

    §6.14.2 stacks them below the symbol, with focus and color above it.

    RP-2's own caveat, worth honouring: "Notation shown on any plot is a
    case-by-case basis. It is not necessary to include all categories, when the
    combination runs the risk of making the plot's appearance cluttered." So
    anything passed as None is simply not drawn.
    """
    import math as _m
    from reportlab.lib.colors import black

    # above the symbol: color, then purpose (focus)
    ay = y + above
    for text in [t for t in (color, purpose) if t]:
        sheet.text(x, ay, text, size=7, center=True)
        ay += 0.32

    # below: circuit (hex), dimmer (rect), channel (circle)
    by = y - above
    if unit is not None:
        sheet.text(x, by, str(unit), size=7, center=True, bold=True)
        by -= gap
    if wattage:
        sheet.text(x, by, str(wattage), size=5.5, center=True)
        by -= gap * 0.8

    if circuit is not None:
        pts = [(x + size * 0.58 * _m.cos(a), by - size * 0.5 + size * 0.58 * _m.sin(a))
               for a in [_m.radians(30 + 60 * i) for i in range(6)]]
        for i in range(6):
            p, q = pts[i], pts[(i + 1) % 6]
            sheet.line(p[0], p[1], q[0], q[1], width=0.6)
        sheet.text(x, by - size * 0.62, str(circuit), size=6, center=True)
        by -= size + gap * 0.5

    if dimmer is not None:
        sheet.rect(x - size * 0.62, by - size, size * 1.24, size * 0.82, width=0.6)
        sheet.text(x, by - size * 0.74, str(dimmer), size=6, center=True)
        by -= size + gap * 0.5

    if channel is not None:
        sheet.circle(x, by - size * 0.5, size * 0.52, width=0.6)
        sheet.text(x, by - size * 0.62, str(channel), size=6, center=True)

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


def _double_arrow(p1, p2, head=0.10):
    """A double-headed arrow from p1 to p2 in (along-axis, cross-axis) feet.

    §6.3.2 draws lamp-axis orientation this way and says it shows "where beam
    lands or filament orientation". The ARROWHEADS are the meaning: a plain bar
    could be read as lens rotation, which is the opposite claim, and the two are
    indistinguishable once drawn. Both heads, always.
    """
    (a1, c1), (a2, c2) = p1, p2
    da, dc = a2 - a1, c2 - c1
    L = math.hypot(da, dc) or 1e-9
    ua, uc = da / L, dc / L
    na, nc = -uc, ua                      # unit normal
    out = [("line", p1, p2)]
    for (ta, tc), sign in (((a2, c2), -1), ((a1, c1), 1)):
        ba, bc = ta + sign * ua * head, tc + sign * uc * head
        out.append(("line", (ta, tc), (ba + na * head * 0.5, bc + nc * head * 0.5)))
        out.append(("line", (ta, tc), (ba - na * head * 0.5, bc - nc * head * 0.5)))
    return out


def oval_beam_fresnel(length=1.05, width=0.72, rotation=None):
    """§6.2 "Oval Beam Fresnel" — which is what an ETC Source Four PARNel is.

    A PARNel is ETC's oval-beam unit: a PAR-style body with a Fresnel-type lens
    that throws a soft oval, and a lens that ROTATES so the oval can be turned.
    RP-2 has no "PARNel" but it has this, and it is the same instrument class.

    Distinctive against a plain Fresnel: shorter and squatter, with a lens flange
    that stands proud and is clearly WIDER than the body.

    `rotation` in degrees adds the oval-axis arrow (§6.3.2 — double-headed,
    because it states where the beam lands, not how the lens is turned). An oval beam that nobody has
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
        out += _double_arrow((cx - r * math.sin(a), -r * math.cos(a)),
                             (cx + r * math.sin(a), r * math.cos(a)),
                             head=min(0.11, r * 0.42))
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


def cyc_unit(cells=3, cell=1.0, depth=0.75, focus=True):
    """§6.6.2. Rectangles divided into cells — one box per cell.

    RP-2 draws these as plain divided rectangles that "approximate an accurate
    size & shape", so `cell` and `depth` should be the real unit's dimensions
    rather than a house style.

    §6.6.1 shows the FOCUS DIRECTION as an arrow BESIDE the unit, not inside it.
    It matters more here than on any other symbol: a cyc light is asymmetric and
    aimed up the cloth, so which way it faces is the whole of its behaviour, and
    the body is a rectangle that looks identical either way round.
    """
    total = cells * cell
    out = []
    for i in range(cells):
        a0 = depth / 2
        c0 = -total / 2 + i * cell
        out.append(("poly", [(a0, c0), (a0, c0 + cell),
                             (-a0, c0 + cell), (-a0, c0)], True))
    if focus:
        tip, tail = -depth * 1.45, -depth * 0.78
        out.append(("line", (tail, 0.0), (tip, 0.0)))
        for side in (1, -1):
            out.append(("line", (tip, 0.0),
                        (tip + depth * 0.30, side * depth * 0.20)))
    return out


def striplight(length=6.0, depth=0.6, lamp="PAR 38", mount="pipe"):
    """§6.7.1. A long shallow body with a small tab at ONE end.

    **Length follows the real unit.** RP-2 is explicit: "Overall length of the
    instrument dependent on number of lamps. Measure the instruments." A strip
    drawn at a default length is the one symbol on a plot that is guaranteed
    wrong, because its length is the information.

    §6.7.2 distinguishes the mounting: `mount="pipe"` is hung, `mount="trunnion"`
    is a ground row and carries a second line along the back. An electrician
    reading a ground row as a hung unit hangs it.
    """
    a, c = depth / 2, length / 2
    tab = min(depth * 0.55, length * 0.10)
    out = [("poly", [(a, -c), (a, c - tab), (a + depth * 0.32, c - tab),
                     (a + depth * 0.32, c), (-a, c), (-a, -c)], True)]
    if mount == "trunnion":
        out.append(("line", (-a + depth * 0.22, -c * 0.94),
                    (-a + depth * 0.22, c * 0.94)))
    return out


# ------------------------------------------------------- §6.13 accessories

# RP-2 §6.13 lists ten accessory symbols. Only these four are drawn, because
# Jerry said 2026.09.23 that beam projectors, scoops and fluorescents are
# "basically gone" and asked for barn doors and top hats. The standard is from
# 2006 and still treats all of them as current; the working designer is the
# better authority on what is still in a rental stock.
#
# All four hang on a MOUNTING LINE that stands proud of the body at top and
# bottom — on the plate that line is the gel-frame edge they clip into, and it
# is what makes an accessory read as attached rather than as a second object
# floating in front of the instrument.


def barn_door(panels=2, size=0.55, flare=1.55):
    """§6.13. Two-panel is an OPEN trapezoid; four-panel is CLOSED at the front.

    That is the whole of the distinction on the plate, and it is enough: the
    reader is being told how many flaps there are, not what they look like.
    """
    w = size / 2
    d = size * 0.95
    out = [("line", (0.0, -w), (0.0, w)),
           ("line", (0.0, w), (-d, w * flare)),
           ("line", (0.0, -w), (-d, -w * flare))]
    if panels >= 4:
        out.append(("line", (-d, w * flare), (-d, -w * flare)))
    return out


def top_hat(size=0.5, half=False):
    """§6.13. A square on its mounting line; a half hat is that square cut corner
    to corner, so the two read apart at a glance even at 1/2" scale."""
    w = size / 2
    out = [("line", (0.0, -w * 1.55), (0.0, w * 1.55))]      # gel-frame edge, proud
    if half:
        out.append(("poly", [(0.0, w), (0.0, -w), (-size, -w)], True))
    else:
        out.append(("poly", [(0.0, -w), (-size, -w), (-size, w), (0.0, w)], True))
    return out


# --------------------------------------------- attaching accessories to a unit

# RP-2 puts accessories in two DIFFERENT places, and the difference is physical:
#
#   Gate accessories (§6.1.11, §6.14.2) go INSIDE the body — a gobo, an iris and
#   a rotator all sit at the gate, behind the lens, and RP-2 marks them with a
#   filled circle, an open circle and an R.
#
#   Front-of-lens accessories (§6.13) go at the FRONT — barn doors, hats,
#   scrollers and dousers all clip onto the colour frame.
#
# So the designer says only WHAT is on the unit; where the mark goes is the
# drawing's job, not theirs. One field on the instrument, two placements.

_GATE = {"gobo": "template", "template": "template", "pattern": "template",
         "gobo rotator": "rotator", "rotator": "rotator", "double rotator": "rotator2",
         "iris": "iris"}

_FRONT = {"top hat": "tophat", "tophat": "tophat", "hat": "tophat",
          "half hat": "halfhat", "halfhat": "halfhat", "half top hat": "halfhat",
          "barn door": "bd4", "barndoor": "bd4", "barn doors": "bd4",
          "barn door 2": "bd2", "2 panel barn door": "bd2", "bd2": "bd2",
          "barn door 4": "bd4", "4 panel barn door": "bd4", "bd4": "bd4"}


def _norm_acc(name):
    import re as _re
    t = _re.sub(r"[^a-z0-9 ]+", " ", str(name or "").lower())
    t = _re.sub(r"\b(\d+)\s*(way|panel|leaf)\b", r"\1", t)
    return _re.sub(r"\s+", " ", t).strip()


def resolve_accessory(name):
    """('gate'|'front'|None, key, note). Never guesses: an unknown accessory is
    reported, because a barn door nobody ordered is a barn door nobody brings."""
    t = _norm_acc(name)
    if not t:
        return None, None, "empty accessory"
    if t in _GATE:
        return "gate", _GATE[t], ""
    if t in _FRONT:
        return "front", _FRONT[t], ""
    # "4 way barn door" -> "4 barn door"; try the words in either order
    if "barn" in t and "door" in t:
        return "front", ("bd2" if "2" in t else "bd4"), f"{name!r} read as a barn door"
    if "hat" in t:
        return "front", ("halfhat" if "half" in t else "tophat"), f"{name!r} read as a hat"
    return None, None, (f"{name!r} is not an accessory this tool knows — "
                        "add it to _GATE or _FRONT in symbols.py")


def _extent(prims):
    """(min_a, max_a) of a symbol, so a front accessory can be put at its nose."""
    vals = []
    for p in prims:
        if p[0] == "poly":
            vals += [q[0] for q in p[1]]
        elif p[0] == "line":
            vals += [p[1][0], p[2][0]]
        elif p[0] in ("circle", "text"):
            vals.append(p[1][0])
    return (min(vals), max(vals)) if vals else (0.0, 0.0)


def with_accessories(prims, accessories, size=0.5):
    """Return prims plus every accessory, each drawn where RP-2 puts it.

    Returns (prims, unknown) — `unknown` is the list of names that resolved to
    nothing, so the caller can SAY so rather than dropping them silently.
    """
    if not accessories:
        return list(prims), []
    front_a, _ = _extent(prims)
    out, unknown, n_front = list(prims), [], 0
    gate_at = front_a * 0.42          # inside the body, behind the lens
    for name in accessories:
        where, key, note = resolve_accessory(name)
        if where is None:
            unknown.append(note or str(name)); continue
        if where == "gate":
            if key == "template":
                out.append(("circle", (gate_at, 0.0), size * 0.17, True))
            elif key == "iris":
                out.append(("circle", (gate_at, 0.0), size * 0.17))
            else:
                out.append(("text", (gate_at, 0.0), "RR" if key == "rotator2" else "R", 0.011))
        else:
            # Stack front accessories nose-outward so two never overlap.
            off = front_a - n_front * size * 1.15
            n_front += 1
            shape = (barn_door(2, size) if key == "bd2" else
                     barn_door(4, size) if key == "bd4" else
                     top_hat(size, half=(key == "halfhat")))
            out += [_shift(pr, off) for pr in shape]
    return out, unknown


def _shift(prim, da):
    """Move one primitive along the instrument axis by `da` feet."""
    k = prim[0]
    if k == "poly":
        return (k, [(a + da, c) for a, c in prim[1]], prim[2])
    if k == "line":
        return (k, (prim[1][0] + da, prim[1][1]), (prim[2][0] + da, prim[2][1]))
    return (k, (prim[1][0] + da, prim[1][1])) + tuple(prim[2:])


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


# §6.14.1 gives THREE house control models, and they are notated differently.
# Jerry, 2026.09.23: "most houses have circuit per dimmer" — so that is the
# default here, and it is the one where the third container is WRONG rather than
# merely absent.
CONTROL_MODELS = ("dimmer-per-circuit", "hard-and-soft-patch", "no-soft-patch")


def notation(sheet, x, y, *, channel=None, circuit=None, dimmer=None,
             color=None, purpose=None, unit=None, wattage=None,
             control="dimmer-per-circuit",
             size=0.42, gap=0.30, above=1.0):
    """§6.14.1 — the SHAPE of the container carries the meaning.

        hexagon    circuit
        rectangle  dimmer (in a patch-panel house)
        circle     channel

    ⭐ How many containers there are depends on the HOUSE, per §6.14.1:

      `dimmer-per-circuit`   Most houses (Jerry, 2026.09.23). The circuit is
                             hard-wired to its own dimmer, so the two numbers are
                             ONE fact. RP-2 draws a single hexagon and labels it
                             "Circuit & Dimmer". **Drawing two containers here is
                             not tidy-but-redundant — it tells the electrician
                             there is a patch to make, and there is not.**
      `hard-and-soft-patch`  Hexagon (circuit), rectangle (dimmer), circle
                             (channel). All three, because all three differ.
      `no-soft-patch`        Hexagon (circuit) and circle (dimmer). The console
                             addresses dimmers directly; there is no channel
                             number distinct from the dimmer.

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

    # In a dimmer-per-circuit house the circuit and the dimmer are one number,
    # so a dimmer that merely repeats the circuit is not drawn twice.
    if control == "dimmer-per-circuit":
        if circuit is None and dimmer is not None:
            circuit, dimmer = dimmer, None
        elif dimmer is not None and str(dimmer) == str(circuit):
            dimmer = None

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

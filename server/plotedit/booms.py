#!/usr/bin/env python3
"""Where a boom's units go when it is drawn in ELEVATION, per RP-2 §6.12.

⭐ In PLAN a boom is a POINT. Every unit on it shares one x and one y and
differs only in height, so the plan cannot separate them — §6.12 says "hatch or
shade acceptable for top view of boom" and puts the readable layout BESIDE the
plot. That layout is what this module computes.

⚠ THE ARITHMETIC LIVES HERE ONCE. The paper draws it through
`scaled_pdf.boom_elevation()`; the browser draws it through the `/booms`
endpoint. Both ask this module. A second copy in TypeScript is exactly how the
screen and the paper drifted three times in one week, and it is what
`test_agreement.py` exists to stop.
"""
from . import photometrics as _ph
from . import positions as _P

# How much width one boom elevation needs, including its labels. In feet.
BOOM_PITCH = 5.5

# How far off the room's stage-left edge the first elevation sits.
FIRST_X = -(BOOM_PITCH * 0.75)
BASE_Y = 1.0

# How far the unit symbols stand off the drawn pipe.
UNIT_GAP = 1.5


def _key(s):
    return (s or "").strip().lower()


def compress(heights, max_gap=2.5):
    """Where to DRAW a boom's units when the pipe is longer than the paper.

    Returns (drawn_y, breaks, top) — one drawn height per input height, the
    drawn heights at which a break mark goes, and where the pipe should stop.

    ⭐ RP-2 §6.12's Option 1 plate compresses the pipe and marks it with a break:
    "this continues, but not all of it is drawn." A boom eighteen feet tall with
    four units near the bottom does not need eighteen feet of paper.

    ⚠ The LABELLED HEIGHTS stay true — this only moves ink. The break says the
    paper is compressed; it never says a number is approximate.

    ⚠ And it breaks only where that actually buys paper. A three-foot gap
    squeezed to two-and-a-half saves half a foot and costs the reader a symbol to
    stop and interpret, which is a worse drawing rather than a shorter one. So
    the run has to exceed max_gap by a clear margin. RP-2's own plate carries ONE
    break on a boom with four units.
    """
    worth_it = max_gap + 1.5
    ys, breaks, cursor, last = [], [], 0.0, 0.0
    for h in sorted(heights):
        gap = h - last
        if gap > worth_it:
            breaks.append(cursor + max_gap / 2.0)
            cursor += max_gap
        else:
            cursor += gap
        ys.append(cursor)
        last = h
    return ys, breaks, cursor + min(max_gap, 1.2)


def units_on(pos, instruments):
    """The instruments hung on one position, by name."""
    return [i for i in instruments if _key(i.get("position")) == _key(pos.get("name"))]


def elevation(pos, units, max_gap=2.5, system=None):
    """One boom's elevation: where each unit is DRAWN, and what it is labelled.

    `dy` is feet above the elevation's base. `height` is the real trim and is
    never adjusted — see compress().
    """
    placed = sorted([u for u in units if u.get("height") is not None],
                    key=lambda z: z["height"])
    ys, breaks, top = compress([u["height"] for u in placed], max_gap)
    return {
        "name": (pos.get("name") or "").upper(),
        "unit_gap": UNIT_GAP,
        "top": top,
        "breaks": list(breaks),
        "units": [{"unit": u.get("unit"), "channel": u.get("channel"),
                   "type": u.get("type", ""), "color": u.get("color"),
                   "accessories": list(u.get("accessories") or []),
                   "height": u["height"], "label": _ph.fmt_ft(u["height"], system),
                   "dy": dy}
                  for u, dy in zip(placed, ys)],
        # ⚠ Never dropped. A unit with no height is a unit nobody can hang, and
        # the drawing has to say so rather than leave a gap the reader reads as
        # "there is no unit there".
        "no_height": [{"unit": u.get("unit"), "type": u.get("type", "")}
                      for u in units if u.get("height") is None],
    }


def layout(positions, instruments, max_gap=2.5, system=None):
    """Every boom that carries units, placed left of the room in drawing order.

    A boom with NO units gets no elevation — there is nothing to lay out — but
    it still gets its point and its mount in plan.
    """
    out = []
    x = FIRST_X
    for p in positions:
        if not _P.is_vertical(p):
            continue
        on = units_on(p, instruments)
        if not on:
            continue
        e = elevation(p, on, max_gap, system=system)
        e["x"], e["y"] = x, BASE_Y
        # Where the boom actually IS. In plan it is a point, drawn as its mount
        # with one hatched symbol standing for the whole stack.
        e["plan"] = {"x": p.get("x1"), "y": p.get("y1"),
                     "rotation": p.get("rotation", 0.0),
                     "mount": p.get("mount") or "boom-base",
                     "width": p.get("width", 1.4),
                     "type": on[0].get("type", "")}
        out.append(e)
        x -= BOOM_PITCH
    return out


def space_needed(positions, instruments):
    """How much room the elevations need off the stage-left edge, in feet.

    ⚠ Counted BEFORE the origin is set. The catwalks were discovered by the
    clipping guard after the fact, which is a guard doing a layout's job.
    """
    n = len(layout(positions, instruments))
    return n * BOOM_PITCH + 2.0 if n else 0.0

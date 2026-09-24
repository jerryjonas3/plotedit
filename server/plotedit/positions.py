"""Hanging positions: which way they run, and which end unit 1 is at.

⭐ THE PRINCIPLE, in Jerry's words (2026.09.23):

    "SR is unit 1 because the numbers actually go house left to house right —
     easier to read, and visualize from the house."

**Unit numbers run in the direction you READ the plot, standing in the house.**
Left to right across a lateral position. Near to far — downstage to upstage — on
one that runs up and down the stage. That is the whole rule, and it is a rule
about legibility, not about geometry: the numbers are for a person holding the
paper and looking at the room.

Everything below is just that principle expressed in this file's coordinates.

    x increases toward STAGE RIGHT.   y increases UPSTAGE.
    The origin is the downstage-LEFT corner of the room.

Stage right is house left, so "house left to house right" means starting at the
MAXIMUM x and counting down. Downstage is the MINIMUM y, so a longitudinal
position starts at the minimum and counts up. **The two therefore move opposite
ways along their axes** — which looks like an inconsistency and is not one. They
are the same rule seen from the house.

⚠ So if this is ever unified, unify it on the READING DIRECTION, not on the sign
of a coordinate. A plot numbered backwards looks entirely correct until someone
is up a ladder.
"""

from typing import Any, Dict, List, Optional, Tuple

# The four ends a position can be numbered from.
FROM_SR, FROM_SL, FROM_DS, FROM_US = "SR", "SL", "DS", "US"
# Vertical positions number by height, not by a compass direction.
FROM_TOP, FROM_BOTTOM = "TOP", "BOTTOM"
# §2.3.2, for FOH positions.
FROM_PLASTER = "PLASTER"        # parallel to centerline: nearest the plaster line
FROM_CENTER = "CENTER"          # non-parallel (box booms): nearest centerline


VERTICAL_TYPES = ("boom", "box-boom", "boom-box", "ladder", "tormentor", "torm")

# ⭐ A ladder and a tormentor are vertical, but they do NOT stand on the floor.
# A ladder hangs from a pipe and can be flown, so it has a TRIM and no base; a
# tormentor is bolted to the building beside the proscenium and is not chosen at
# all. Asking either for a boom base is asking for hardware that does not exist.
HANGING_TYPES = ("ladder",)
FIXED_TYPES = ("tormentor", "torm")


def is_vertical(pos: Dict[str, Any]) -> bool:
    """A boom, box boom, ladder or tormentor: a pipe that stands up.

    ⭐ In PLAN a vertical position is a POINT, not a line — every unit on it
    shares one x and y and differs only in height. That is why booms need their
    own everything: the two-dimensional drawing cannot separate the units, so
    RP-2 §6.12 puts the layout beside the plot instead of on it.
    """
    t = (pos.get("type") or "").strip().lower()
    dx = abs(pos.get("x2", pos["x1"]) - pos["x1"])
    dy = abs(pos.get("y2", pos["y1"]) - pos["y1"])
    if t in VERTICAL_TYPES:
        # ⚠ Measure, do not just read the name. "Box boom" covers two different
        # things: a plain vertical pipe in a box (a point, numbered top down) and
        # a rail with real horizontal extent, which §2.3.2 numbers from the units
        # closest to centerline. Trusting the word alone got the second one
        # wrong, and the plot would have looked right.
        return not (dx > 0.5 or dy > 0.5)
    if t:
        return False
    # Untyped: a position with no length is a point, so it stands up.
    return dx < 0.5 and dy < 0.5


def axis(pos: Dict[str, Any]) -> str:
    """'vertical' (a boom), 'lateral' (stage left to right) or 'longitudinal' (US-DS)."""
    if is_vertical(pos):
        return "vertical"
    dx = abs(pos.get("x2", pos["x1"]) - pos["x1"])
    dy = abs(pos.get("y2", pos["y1"]) - pos["y1"])
    return "longitudinal" if dy > dx else "lateral"


def number_from(pos: Dict[str, Any]) -> str:
    """Which end unit 1 sits at. An explicit `numberFrom` always wins.

    The default is the reading direction from the house: house left to house
    right across a lateral position (so stage right first), near to far on a
    longitudinal one (so downstage first). Jerry asked for the override the same
    day — "later we may want to be able to override that" — so the field exists
    now and simply defaults.
    """
    explicit = (pos.get("numberFrom") or "").strip().upper()
    if explicit in (FROM_SR, FROM_SL, FROM_DS, FROM_US, FROM_TOP, FROM_BOTTOM):
        return explicit
    a = axis(pos)
    t = (pos.get("type") or "").strip().lower()

    # §2.3.2: "Luminaires mounted on FOH positions non-parallel to centerline
    # (box booms) should number starting with the units closest to centerline."
    # ⚠ Only when the position HAS horizontal extent. Plenty of houses hang a box
    # boom as a plain vertical pipe, and then every unit is the same distance
    # from centerline and the rule says nothing — so fall through to top-down.
    if t in ("box-boom", "boom-box") and not is_vertical(pos):
        return FROM_CENTER

    if a == "vertical":
        # §2.3.2: "on onstage booms or other vertical hanging positions... from
        # top to bottom, downstage to upstage."
        return FROM_TOP

    # §2.3.2: "FOH positions parallel to centerline should number starting with
    # the units nearest to plaster line."
    if a == "longitudinal" and pos.get("foh"):
        return FROM_PLASTER

    return FROM_DS if a == "longitudinal" else FROM_SR


def _sort_key(pos: Dict[str, Any]):
    """(key, reverse) — how to order units along `pos` so unit 1 comes first."""
    end = number_from(pos)
    if end == FROM_SR:                      # stage right is the MAXIMUM x
        return (lambda i: i.get("x", 0.0)), True
    if end == FROM_SL:
        return (lambda i: i.get("x", 0.0)), False
    if end == FROM_DS:                      # downstage is the MINIMUM y
        return (lambda i: i.get("y", 0.0)), False
    if end == FROM_TOP:
        # §2.3.2: "from top to bottom, downstage to upstage." The second clause
        # is the TIEBREAK — two units at one height on a ladder's two sides are
        # ordered downstage first, which is why a ladder does not need somebody
        # to invent a rule for it.
        return (lambda i: (-(i.get("height", i.get("trim", 0.0)) or 0.0),
                           i.get("y", 0.0))), False
    if end == FROM_BOTTOM:
        return (lambda i: ((i.get("height", i.get("trim", 0.0)) or 0.0),
                           i.get("y", 0.0))), False
    if end == FROM_PLASTER:                 # §2.3.2, FOH parallel to centerline
        return (lambda i: i.get("y", 0.0)), True
    if end == FROM_CENTER:                  # §2.3.2, box booms
        return (lambda i: abs(i.get("x", 0.0) - i.get("_center_x", 0.0))), False
    return (lambda i: i.get("y", 0.0)), True    # US


def order(instruments: List[Dict[str, Any]], pos: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The instruments on `pos`, in hanging order — unit 1 first."""
    name = (pos.get("name") or "").strip().lower()
    on = [i for i in instruments if (i.get("position") or "").strip().lower() == name]
    key, rev = _sort_key(pos)
    return sorted(on, key=key, reverse=rev)


def number(instruments: List[Dict[str, Any]], pos: Dict[str, Any],
           start: int = 1) -> Tuple[int, Optional[str]]:
    """Renumber the units on one position in place. Returns (count, warning).

    ⚠ This OVERWRITES unit numbers. On a plot that has been hung, a renumber is
    a different document from the one taped to the pipe, so the caller has to
    mean it. Nothing calls this automatically.
    """
    on = order(instruments, pos)
    if not on:
        return 0, f"no instruments on {pos.get('name')!r}"
    warn = None
    # Two units at the same coordinate cannot be ordered, and picking one
    # arbitrarily is how a plot gets hung backwards. Say so.
    key, _ = _sort_key(pos)

    def _rounded(v):
        # A sort key may be a single number or a tuple — §2.3.2's vertical rule
        # is "top to bottom, DOWNSTAGE TO UPSTAGE", which needs two values. Two
        # units are only genuinely unorderable when the WHOLE key matches.
        return tuple(round(x, 3) for x in v) if isinstance(v, tuple) else (round(v, 3),)

    vals = [_rounded(key(i)) for i in on]
    if len(set(vals)) != len(vals):
        warn = (f"{pos.get('name')!r}: two units share a coordinate along the "
                f"position, so their order is arbitrary — move one or number by hand")
    for n, inst in enumerate(on, start):
        inst["unit"] = n
    return len(on), warn


def describe(pos: Dict[str, Any]) -> str:
    """One line for the plot's notes, so the drawing states its own convention."""
    # Phrased from the house, because that is where it will be read.
    end = {FROM_SR: "stage right — numbers read house left to house right",
           FROM_SL: "stage left — numbers read house right to house left",
           FROM_DS: "farthest downstage — numbers read front to back",
           FROM_US: "farthest upstage — numbers read back to front",
           FROM_TOP: "the highest unit — numbers read top to bottom",
           FROM_BOTTOM: "the lowest unit — numbers read bottom to top"}[number_from(pos)]
    how = "set" if pos.get("numberFrom") else "default"
    return f"{pos.get('name', '?')}: unit 1 at {end} ({how})"


def check_booms(plot: Dict[str, Any]) -> List[str]:
    """§6.12 rules that a plot can break. Returns plain-English problems.

    RP-2: **"Choose only one type of layout per plot."** Two layouts on one
    drawing means the reader has to work out which convention each boom follows,
    which is exactly the ambiguity the standard exists to remove.
    """
    problems: List[str] = []
    positions = plot.get("positions") or []
    instruments = plot.get("instruments") or []
    booms = [p for p in positions if is_vertical(p)]
    if not booms:
        return problems

    layouts = {(p.get("layout") or plot.get("boomLayout") or "option1") for p in booms}
    if len(layouts) > 1:
        problems.append(
            f"this plot uses {len(layouts)} boom layouts ({', '.join(sorted(layouts))}) "
            f"— RP-2 §6.12: choose only one type of layout per plot")

    for p in booms:
        name = (p.get("name") or "").strip().lower()
        on = [i for i in instruments
              if (i.get("position") or "").strip().lower() == name]
        # ⭐ On a boom the HEIGHT is the only thing separating one unit from
        # another. Without it the unit cannot be drawn, cannot be numbered and
        # cannot be hung — it is not a missing nicety, it is the position.
        missing = [i.get("unit") for i in on if i.get("height") is None]
        if missing:
            problems.append(
                f"{p.get('name')}: units {', '.join(str(u) for u in missing)} have no "
                f"height. On a boom every unit shares one x and y, so the height is "
                f"the only thing that tells them apart — and the only thing to hang by")
        if len(on) > 1:
            hs = [i.get("height") for i in on if i.get("height") is not None]
            if len(set(hs)) != len(hs):
                problems.append(f"{p.get('name')}: two units at the same height — "
                                f"legal on a sidearm, but say which side")
        t = (p.get("type") or "").strip().lower()
        if t in HANGING_TYPES:
            # ⭐ A ladder HANGS. Asking it for a boom base is asking for hardware
            # that does not exist — what it needs is a trim, and §3 requires one
            # for "all hanging positions that can change height."
            if p.get("trim") is None:
                problems.append(f"{p.get('name')}: a ladder hangs, so it needs a TRIM, "
                                f"not a floor mount. RP-2 §3 wants a trim on every "
                                f"position whose height can change")
            if p.get("mount"):
                problems.append(f"{p.get('name')}: a ladder has a mount recorded "
                                f"({p['mount']!r}) but it does not stand on the floor — "
                                f"is this a boom?")
        elif t in FIXED_TYPES:
            # A tormentor is bolted to the building. Nothing to specify, nothing
            # to choose, and no base to bring.
            pass
        elif not p.get("mount"):
            problems.append(f"{p.get('name')}: no mount recorded (floor plate, boom "
                            f"base or flange). A floor plate needs floor space and a "
                            f"sandbag; a flange is already in the building")
    return problems


# ---------------------------------------------------------------------------
# 🔴 Where this tool departs from the standard, on purpose.

RP2_DIVERGENCE = [
    (
        "lateral numbering",
        'RP-2 §2.3.2: "Luminaires on hanging positions perpendicular to '
        'centerline (e.g., battens) are numbered from stage left to stage right."',
        'Jerry, 2026.09.23: "unit 1 is stage right... the numbers actually go '
        'house left to house right — easier to read, and visualize from the house."',
        "These are OPPOSITE. Stage right is house left, so Jerry numbers a batten "
        "in the reverse of RP-2's direction. The tool follows Jerry, because it is "
        "his plot and he gave a reason. But a stranger reading the plot may expect "
        "the standard, so a plot going to an unfamiliar house should SAY which way "
        "it numbers.",
    ),
]


def rp2_divergence_note():
    """One line for a plot's legend, so the drawing states its own convention.

    A convention that disagrees with the published standard is not a problem —
    until it is unstated, and then it is somebody hanging a rig backwards.
    """
    return ("Unit numbering: unit 1 is STAGE RIGHT, reading house left to house "
            "right. (RP-2 §2.3.2 numbers battens stage left to stage right; this "
            "plot does not.)")

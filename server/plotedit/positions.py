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


def axis(pos: Dict[str, Any]) -> str:
    """'lateral' (runs stage left to stage right) or 'longitudinal' (US to DS)."""
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
    if explicit in (FROM_SR, FROM_SL, FROM_DS, FROM_US):
        return explicit
    return FROM_DS if axis(pos) == "longitudinal" else FROM_SR


def _sort_key(pos: Dict[str, Any]):
    """(key, reverse) — how to order units along `pos` so unit 1 comes first."""
    end = number_from(pos)
    if end == FROM_SR:                      # stage right is the MAXIMUM x
        return (lambda i: i.get("x", 0.0)), True
    if end == FROM_SL:
        return (lambda i: i.get("x", 0.0)), False
    if end == FROM_DS:                      # downstage is the MINIMUM y
        return (lambda i: i.get("y", 0.0)), False
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
    vals = [round(key(i), 3) for i in on]
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
           FROM_US: "farthest upstage — numbers read back to front"}[number_from(pos)]
    how = "set" if pos.get("numberFrom") else "default"
    return f"{pos.get('name', '?')}: unit 1 at {end} ({how})"

"""Hanging positions: which way they run, and which end unit 1 is at.

⚠ THE COORDINATE CONVENTION, because the numbering rules depend entirely on it
and getting it backwards is invisible until someone is up a ladder:

    x increases toward STAGE RIGHT.   y increases UPSTAGE.
    The origin is the downstage-LEFT corner of the room.

So stage right is the HIGH-x end, and downstage is the LOW-y end. That is fixed
in web/src/geometry.ts and corroborated by the sample plot, where "Special SR"
sits at x=22 and "Special SL" at x=11 in a 33-foot room.

Jerry's rules, 2026.09.23:

    "unit 1 is stage right"
    "on a pipe that runs US -> DS, I tend to have unit 1 be farthest DS"

⭐ Those two rules run in OPPOSITE directions in this coordinate system. Stage
right is the maximum x; downstage is the minimum y. They do not collapse into
"start at one end of the axis", and any refactor that tries to make them look
symmetrical will silently reverse one of them.
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

    The default is Jerry's habit: stage right on a lateral position, farthest
    downstage on one that runs upstage-downstage. He asked for the override
    2026.09.23 — "later we may want to be able to override that" — so the field
    exists now and simply defaults.
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
    end = {FROM_SR: "stage right", FROM_SL: "stage left",
           FROM_DS: "farthest downstage", FROM_US: "farthest upstage"}[number_from(pos)]
    how = "set" if pos.get("numberFrom") else "default"
    return f"{pos.get('name', '?')}: unit 1 at {end} ({axis(pos)}, {how})"

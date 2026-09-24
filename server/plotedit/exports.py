#!/usr/bin/env python3
"""Everything that leaves the editor.

    plot_pdf(plot, path)        architectural-scale PDF, scale bar, 1-inch check
    plot_dxf(plot, path)        layered DXF in feet
    schedule_csv(plot)          by position and unit — what gets hung
    hookup_csv(plot)            by channel — what the board sees
    eos_patch(plot)             USITT ASCII patch  ⚠ UNVERIFIED, see below
    magic_sheet_rows(plot)      channel, purpose, color, grouped

⚠ THE EOS PATCH FORMAT HAS NEVER BEEN TESTED AGAINST A CONSOLE.

The cue exporter in eos_ascii.py was reverse-engineered from a real Eos export
after three guesses at the format failed — the lesson being that a real file out
of the target application settles in minutes what documentation does not. No
real Eos *patch* export was available when this was written, so the layout below
follows the USITT spec and nothing more. **Import it into a scratch show file
before relying on it**, and if it is wrong, export a patch from Eos and diff.
The file says so in its own header, so nobody is misled downstream.
"""
import csv
import io
from typing import Any, Dict, List


# --------------------------------------------------------------- helpers

def _sorted_for_schedule(instruments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """By position, then unit — the order someone hangs in."""
    return sorted(instruments, key=lambda i: (str(i.get("position") or "~"),
                                              _num(i.get("unit"))))


def _sorted_for_hookup(instruments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """By channel — the order the board sees. Unpatched units go last."""
    return sorted(instruments, key=lambda i: (i.get("channel") is None,
                                              _num(i.get("channel"))))


def _num(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("inf")


def _csv(rows: List[List[Any]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerows(rows)
    return buf.getvalue()


# --------------------------------------------------------------- paperwork

SCHEDULE_COLUMNS = ["Position", "Unit", "Channel", "Dimmer", "Address",
                    "Type", "Wattage", "Color", "Gobo", "Purpose", "Accessory", "Notes"]


def _accessories(inst) -> str:
    """The accessory cell. A list on the instrument, one cell on the schedule.

    Joined with " + " rather than a comma: the schedule is a CSV and the shop
    reads this column as a line on the order, so a comma inside a cell is a
    quoting problem waiting to be somebody's missing barn door.
    """
    a = inst.get("accessories")
    if a is None:                     # tolerate the old single-string field
        a = inst.get("accessory") or []
    if isinstance(a, str):
        a = [a] if a else []
    return " + ".join(str(x) for x in a if str(x).strip())


def schedule_csv(plot: Dict[str, Any]) -> str:
    """The instrument schedule: what hangs where, in hanging order."""
    rows: List[List[Any]] = [[f"{plot.get('show', '')} — Instrument Schedule"],
                             [plot.get("venue", "")],
                             [f"Design: {plot.get('designer', '')}",
                              plot.get("date", ""), f"Rev {plot.get('revision', '')}"],
                             [], SCHEDULE_COLUMNS]
    for i in _sorted_for_schedule(plot["instruments"]):
        rows.append([i.get("position", ""), i.get("unit", ""), i.get("channel", ""),
                     i.get("dimmer", ""), i.get("address", ""), i.get("type", ""),
                     i.get("wattage", ""), i.get("color", ""), i.get("gobo", ""),
                     i.get("purpose", ""), _accessories(i), i.get("notes", "")])
    return _csv(rows)


HOOKUP_COLUMNS = ["Channel", "Position", "Unit", "Type", "Color", "Purpose",
                  "Dimmer", "Address"]


def hookup_csv(plot: Dict[str, Any]) -> str:
    """The channel hookup: what the board sees, in channel order."""
    rows: List[List[Any]] = [[f"{plot.get('show', '')} — Channel Hookup"],
                             [plot.get("venue", "")],
                             [f"Design: {plot.get('designer', '')}",
                              plot.get("date", ""), f"Rev {plot.get('revision', '')}"],
                             [], HOOKUP_COLUMNS]
    for i in _sorted_for_hookup(plot["instruments"]):
        rows.append([i.get("channel", ""), i.get("position", ""), i.get("unit", ""),
                     i.get("type", ""), i.get("color", ""), i.get("purpose", ""),
                     i.get("dimmer", ""), i.get("address", "")])
    return _csv(rows)


def magic_sheet_rows(plot: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Channels grouped by purpose — the one page looked at during tech."""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for i in _sorted_for_hookup(plot["instruments"]):
        groups.setdefault(str(i.get("purpose") or "unassigned"), []).append(i)
    out = []
    for purpose, insts in groups.items():
        chans = [i["channel"] for i in insts if i.get("channel") is not None]
        colors = sorted({str(i.get("color")) for i in insts if i.get("color")})
        out.append({"purpose": purpose, "channels": chans,
                    "count": len(insts), "colors": colors,
                    "types": sorted({str(i.get("type")) for i in insts if i.get("type")})})
    return out


# --------------------------------------------------------------- console

def eos_patch(plot: Dict[str, Any]) -> str:
    """USITT ASCII patch: channel < address.

    ⚠ UNVERIFIED — see the module docstring. The warning is written into the
    file itself so it travels with it.

    Units with no channel or no address are listed as comments rather than
    dropped, because a silently missing unit at tech is worse than a noisy file.
    """
    show = plot.get("show", "Untitled")
    L = ["Ident 3:0", "Manufacturer ETC", "Console Eos", "$$Format 3.10",
         f"$$Title {show}", "!",
         "! PATCH ONLY. Import as MERGE so existing cues survive.",
         "!",
         "! ⚠ THIS FORMAT HAS NOT BEEN TESTED AGAINST A CONSOLE.",
         "!   The cue exporter was reverse-engineered from a real Eos export;",
         "!   no real patch export was available when this was written. Load it",
         "!   into a scratch show file first. If it is wrong, export a patch",
         "!   from Eos and diff — that settles it in minutes.",
         "!"]

    patched, skipped = [], []
    for i in plot["instruments"]:
        ch, addr = i.get("channel"), i.get("address")
        if ch is None or addr is None:
            skipped.append(i)
        else:
            patched.append((int(ch), int(addr), i))

    if skipped:
        L.append("! Not patched — no channel or no address:")
        for i in skipped:
            L.append(f"!   {i.get('position', '?')} unit {i.get('unit', '?')} "
                     f"{i.get('type', '?')} ch={i.get('channel')} addr={i.get('address')}")
        L.append("!")

    L.append("Patch 1")
    for ch, addr, _ in sorted(patched):
        L.append(f"   {ch}<{addr}")
    L.append(" ")

    # Channel labels carry the purpose through to the board, which is the whole
    # value of exporting a patch rather than typing it.
    for ch, _, i in sorted(patched):
        label = i.get("purpose") or i.get("type") or ""
        if label:
            L.append(f"$ChanLabel {ch} {label}")
    L.append("Enddata")
    return "\n".join(L)


# --------------------------------------------------------------- drawings

def plot_pdf(plot: Dict[str, Any], pdf_path: str, dxf_path: str = None, **kw):
    """Delegates to plot_to_pdf.render, which both the PDF and the browser use."""
    import json
    import os
    import tempfile
    from plot_to_pdf import render
    fd, tmp = tempfile.mkstemp(suffix=".plot.json")
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(plot, fh)
        return render(tmp, pdf_path, dxf=dxf_path, **kw)
    finally:
        os.unlink(tmp)

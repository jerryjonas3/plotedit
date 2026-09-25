#!/usr/bin/env python3
"""Feet, metres, and the conversions that must happen exactly once.

    cd server && python3 test_units.py
"""
import sys

from plotedit import units as U
from plotedit.scaled_pdf import SCALES as PDF_SCALES

FAILS = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<52} {got}")
    if not ok:
        FAILS.append(f"{label}: got {got!r}, wanted {want!r}")


print("the bridge between the two systems is EXACT")
# ⭐ 1/4" = 1'-0" IS 1:48 — a foot is twelve inches and a quarter inch goes into
# twelve exactly forty-eight times. If this bridge is wrong, every metric
# drawing is wrong by a ratio nobody would think to check, and the drawing still
# looks like a drawing.
for scale, ratio in [("1/8", 96.0), ("1/4", 48.0), ("3/8", 32.0),
                     ("1/2", 24.0), ("3/4", 16.0), ("1", 12.0)]:
    check(f'{scale}" = 1\'-0" is 1:{ratio:g}', U.scale_ratio(scale), ratio)
check("and a metric ratio is itself", U.scale_ratio("1:50"), 50.0)

print("\n...so the new scale model is DROP-IN for every existing scale")
# 🔴 scaled_pdf computes pt_per_ft as paper_in_per_ft * 72 and its own comment
# calls that "the whole trick". If points_per_foot() disagrees by so much as a
# rounding error, every drawing already made changes size.
for name, inches_per_foot in PDF_SCALES.items():
    check(f"pt/ft at {name}\" unchanged",
          round(U.points_per_foot(name), 9), round(inches_per_foot * 72, 9))

print("\na length survives the round trip")
# 🔴 THE DANGER IS DOUBLE CONVERSION, and it is silent — a length converted
# twice is out by 10.76 and still describes a plausible room.
for system in U.SYSTEMS:
    for ft in (0.0, 1.0, 13.3333, 38.0, -4.5):
        back = U.to_feet(U.feet_to(ft, system), system)
        check(f"{system}: {ft} ft -> display -> {ft} ft", round(back, 9), round(ft, 9))

# The specific failure that guard is for, stated so it cannot creep back.
_twice = U.feet_to(U.feet_to(10.0, U.METRIC), U.METRIC)
check("converting twice is NOT the identity (it is the bug)",
      round(_twice, 4) == round(U.feet_to(10.0, U.METRIC), 4), False)

print("\nhow each system writes a length")
check("imperial rounds to the inch", U.fmt_length(13.3333), "13'-4\"")
check("...and carries a sign", U.fmt_length(-2.5), "-2'-6\"")
check("...exactly on the foot", U.fmt_length(14.0), "14'-0\"")
check("metric rounds to the centimetre", U.fmt_length(13.3333, U.METRIC), "4.06 m")
check("nothing is an em dash, not a zero", U.fmt_length(None), "—")

print("\nand what it calls the light")
# 🔴 THE LABEL IS THE POINT. "179 fc" printed over a lux number is a false
# statement that looks authoritative.
check("footcandles imperial", U.fmt_illuminance(773), "773 fc")
check("lux metric", U.fmt_illuminance(773, U.METRIC), "8321 lx")
check("1 fc is 10.7639 lx", round(U.LUX_PER_FC, 4), 10.7639)
check("unknown says so", U.fmt_illuminance(None, U.METRIC), "—")

print("\ndefaults are IDIOMATIC, not converted")
# 🔴 Head height is 5'-6" imperial; a metric designer says 1.7 m, not 1.676 m.
# Converted defaults produce numbers no European would type, and they then
# travel into drawings as evidence of a measurement nobody took.
_metric = {k: v for k, _, v in U.POOL_PLANES[U.METRIC]}
check("metric head height reads exactly 1.70 m",
      U.fmt_length(_metric[""], U.METRIC), "1.70 m")
check("...and is NOT a conversion of 5'-6\"",
      U.fmt_length(5.5, U.METRIC) == "1.70 m", False)

# ⚠ EVERY metric default, not just the first. Checking head height alone let a
# converted `face` default through when I broke it on purpose: 5'-2" is 1.5748 m,
# which displays as "1.57 m" — a number no designer would ever type, and the
# tell that it was converted rather than chosen. An idiomatic metric height
# lands on a round decimetre.
_odd = [(k, U.fmt_length(v, U.METRIC))
        for k, _, v in U.POOL_PLANES[U.METRIC]
        if not U.fmt_length(v, U.METRIC).endswith("0 m")]
check("every metric default is a round decimetre", _odd, [])
check("the deck is the deck in both", _metric["deck"], 0.0)
check("both systems offer the same planes",
      [k for k, _, _ in U.POOL_PLANES[U.IMPERIAL]],
      [k for k, _, _ in U.POOL_PLANES[U.METRIC]])

print("\nan existing plot keeps reading the way it was drawn")
check("no units field means imperial", U.system_of({"show": "x"}), U.IMPERIAL)
check("an empty plot too", U.system_of(None), U.IMPERIAL)
check("metric when it says so", U.system_of({"units": "metric"}), U.METRIC)

print()
print("a metric plot DRAWS metric")
import json as _json, os as _os, re as _re, tempfile as _tf
import fitz as _fitz
from plot_to_pdf import render as _render

_SAMPLE = _os.path.join(_os.path.dirname(__file__), "..", "samples", "bluver.plot.json")
_src = _json.load(open(_SAMPLE))
_FEET = _re.compile(r"-?\d+'-\d+\"|-?\d+'(?!\w)")
_METRES = _re.compile(r"-?\d+\.\d+\s?m\b")


def _drawn(**over):
    body = dict(_src); body.update(over); body["rulers"] = True
    d = _tf.mkdtemp()
    jp = _os.path.join(d, "p.json"); _json.dump(body, open(jp, "w"))
    out = _os.path.join(d, "p.pdf")
    sheet, _ = _render(jp, out, scale="1/4")
    return sheet, _fitz.open(out)[0].get_text()


_imp_sheet, _imp = _drawn()
_met_sheet, _met = _drawn(units="metric")

check("an imperial plot is full of feet", len(_FEET.findall(_imp)) > 30, True)
check("...and carries no metre lengths", _METRES.findall(_imp), [])
check("a metric plot carries metre lengths", len(_METRES.findall(_met)) > 0, True)

# ⚠ THE SCALE BAR AND THE SCALE LABEL ARE STILL IMPERIAL, on purpose. The
# drawing SCALE is its own piece of work (1:50 rather than 1/4" = 1'-0"), and
# relabelling the bar in metres while the ratio stayed imperial would be a
# worse lie than leaving it alone. Asserted as a KNOWN state so that finishing
# the scale work has to come back and change this line deliberately.
_left = sorted(set(_FEET.findall(_met)))
check("the only feet left on a metric sheet are the scale bar and label",
      _left, ["0'", "1'-0\"", "10'", "5'"])

check("the room DIMENSION converts", "10.06 m" in _met or "11.58 m" in _met, True)
check("the sheet knows its own system",
      (_imp_sheet.unit_system, _met_sheet.unit_system), ("imperial", "metric"))

print()
print("illuminance is labelled to match, or it is a false statement")
check("imperial says fc", _imp_sheet.fmt_lux(179.0), "179 fc")
check("metric says lx", _met_sheet.fmt_lux(179.0), "1927 lx")
check("and it is a real conversion, not a relabel",
      _met_sheet.fmt_lux(179.0) != "179 lx", True)

print()
print("the endpoint formats in the system it is asked for")
from fastapi.testclient import TestClient as _TC
from plotedit.api import app as _app
_client = _TC(_app)
_inst = [{"unit": 1, "channel": 1, "type": "S4 26", "x": 0, "y": 20, "trim": 14,
          "focus_x": 0, "focus_y": 8, "focus_h": 5.5}]
_a = _client.post("/compute", json={"instruments": _inst}).json()["instruments"][0]
_b = _client.post("/compute", json={"instruments": _inst, "units": "metric"}).json()["instruments"][0]
check("asking for nothing gets feet", _a["throw_ft"].endswith('"'), True)
check("asking for metric gets metres", _b["throw_ft"].endswith(" m"), True)
check("the underlying number is the SAME — only the label moved",
      _a["throw"], _b["throw"])

print()
if FAILS:
    print(f"{len(FAILS)} FAILED")
    for f in FAILS:
        print("   ", f)
    sys.exit(1)
print("all passed")

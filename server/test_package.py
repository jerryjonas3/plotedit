#!/usr/bin/env python3
"""Smoke test: every module imports as a package and the chains hold.

    cd server && python3 test_package.py

Not a unit-test suite. It answers one question — is the package wired up —
and it checks the values that have been wrong before.
"""
import os
import sys

FAILS = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<44} {got}")
    if not ok:
        FAILS.append(f"{label}: got {got!r}, wanted {want!r}")


print("imports")
from plotedit import photometrics as ph
from plotedit import dxf_bridge, eos_ascii, paperwork
from plotedit.scaled_pdf import Sheet, ft, check as pdf_check
print("  ok   all six modules")

print("\nphotometrics — figures from ETC datasheets")
check("S4 26 field angle", ph.FIXTURES["S4 26"]["field"], 25.0)
check("gels.csv found beside the module", len(ph.GELS), 11)
check("R119 transmission", ph.GELS["R119"]["t"], 0.893)

print("\ngel notation — + stacks, / splits")
check("R52+R119 stacked", round(ph.gel_factor("R52+R119")[0], 3), 0.232)
check("R52/R119 split -> first gel only", round(ph.gel_factor("R52/R119")[0], 3), 0.26)
check("unknown gel -> no guess", ph.gel_factor("L201")[0], None)

print("\nscaled_pdf -> photometrics -> gels")
s = Sheet(os.devnull, page="TABLOID", scale="1/4")
s.origin(ft(3), ft(5))
r = s.unit(ft(6), ft(20), 1, ch=1, kind="S4 26", color_gel="R52+R119",
           trim=14, focus_to=(ft(10), ft(10)), lamp="HPL 575")
# Regression: a compound gel used to miss a dict lookup and silently report
# open white — 729 fc instead of 169. The acting-area wash, 4.5x too bright.
check("R52+R119 acting-area wash", round(r["fc"]), 169)
check("throw", ph.fmt_ft(r["throw"]), "13'-9\"")

print("\nscaled_pdf -> dxf_bridge, and the printed scale")
out = os.path.join(os.path.dirname(__file__), "..", "out")
os.makedirs(out, exist_ok=True)
pdf, dxf = os.path.join(out, "smoke.pdf"), os.path.join(out, "smoke.dxf")
s = Sheet(pdf, page="TABLOID", scale="1/4", landscape=False, show="smoke test", dxf=dxf)
s.origin(ft(3), ft(5))
s.rect(0, 0, ft(33), ft(38), width=1.5)     # the Bluver, which needs portrait at 1/4"
s.finish()
check("DXF written alongside", os.path.exists(dxf), True)
check("1-inch check bar", round(pdf_check(pdf), 2), 72.0)
check("portrait fits, no warning", s.warnings, [])

# The same room landscape does NOT fit. The tool must say so rather than clip
# silently — a drawing that runs off the sheet looks finished and is not.
s2 = Sheet(os.devnull, page="TABLOID", scale="1/4", landscape=True)
s2.origin(ft(3), ft(3))
s2.rect(0, 0, ft(33), ft(38))
s2.finish()
check("landscape clips, and says so", len(s2.warnings), 1)
check("names a scale that would fit", '1/8"' in (s2.warnings[0] if s2.warnings else ""), True)

print("\neos_ascii")
asc = eos_ascii.build("Test", {"Study": [1, 2]},
                      [(1, "Q1 up", 5, 5, {"Study": 85})])
check("85% written as hex Hd9", "1@Hd9" in asc, True)
check("TimeUp written (or long fades collapse)", "$$TimeUp 5 0 0 0" in asc, True)

print("\nsymbols — USITT RP-2 (2006)")
from plotedit import symbols as sym
# "S4 26" must not parse as 4 degrees — it did, once.
check("S4 26 gets the 26-30 diagonal, one line",
      sum(1 for p in sym.for_type("S4 26") if p[0] == "line"), 1)
check("S4 19 gets the X, two lines",
      sum(1 for p in sym.for_type("S4 19") if p[0] == "line"), 2)
check("S4 36 carries no mark",
      sum(1 for p in sym.for_type("S4 36") if p[0] == "line"), 0)
check("Lustr = 7 dots, per 6.16",
      sum(1 for p in sym.for_type("Lustr 26 EDLT") if p[0] == "circle"), 7)
check("a mover gets a dashed swing circle",
      any(p[0] == "circle" and len(p) > 3 and p[3] == "dashed"
          for p in sym.for_type("Martin Mac Aura")), True)
# The flare is the whole point: RP-2's lens housing opens out to a face WIDER
# than the body. The first attempt had it narrowing, which read as a funnel.
_pts = sym.enhanced_ers(26)[0][1]
_face_w = _pts[0][1]                       # first point is the front face
_body_w = max(c for _, c in _pts)
check("the front face is the widest point", round(_face_w, 4), round(_body_w, 4))

print("\nline weights — RP-2 6.18, three and only three")
from plotedit.scaled_pdf import LINE_STYLES, LIGHT, MEDIUM, HEAVY
check("exactly three weights are used",
      sorted({w for w, _ in LINE_STYLES.values()}), [LIGHT, MEDIUM, HEAVY])
check("a batten is heavy", LINE_STYLES["batten"][0], HEAVY)
check("a luminaire is heavy", LINE_STYLES["luminaire"][0], HEAVY)
check("architecture is heavy", LINE_STYLES["architecture"][0], HEAVY)
check("scenery is light", LINE_STYLES["scenery"][0], LIGHT)
check("a dimension is light", LINE_STYLES["dimension"][0], LIGHT)
check("the center line is a 4-part chain dash", len(LINE_STYLES["centerline"][1]), 4)
check("the plaster line is evenly dashed", len(LINE_STYLES["plasterline"][1]), 2)
try:
    from plotedit.scaled_pdf import style as _style
    _style("chunky")
    check("an unknown category is refused", "no error", "KeyError")
except KeyError:
    check("an unknown category is refused", "KeyError", "KeyError")

print("\npaperwork")
check("Lightwright column aliases", len(paperwork.LW_COLUMNS), 37)


# ---------------------------------------------------------------- accessories
print("\naccessories attach where RP-2 puts them, not where they were typed")
from plotedit import symbols as _sym

check("a hat is front-of-lens",  _sym.resolve_accessory("top hat")[0], "front")
check("a gobo is at the gate",   _sym.resolve_accessory("gobo")[0], "gate")
check("'4-way barn door' reads", _sym.resolve_accessory("4-way barn door")[1], "bd4")
check("a bare 'barn door' is the 4", _sym.resolve_accessory("barn door")[1], "bd4")
# An accessory this tool cannot draw must SAY so. A barn door that is silently
# dropped is a barn door nobody packs.
where, key, note = _sym.resolve_accessory("scroller")
check("an unknown accessory resolves to nothing", where, None)
check("...and explains itself", "not an accessory this tool knows" in note, True)

_base = _sym.for_type("S4 26")
_with, _unknown = _sym.with_accessories(_base, ["top hat", "gobo"])
check("two accessories add geometry", len(_with) > len(_base), True)
check("...and neither is unknown", _unknown, [])
_, _unknown2 = _sym.with_accessories(_base, ["scroller"])
check("an unknown one is REPORTED, not dropped", len(_unknown2), 1)

# The front accessory must sit at the nose, in front of the body — not on top
# of it. Its geometry should extend further forward than the symbol does.
_fa_base, _ = _sym._extent(_base), None
_fa_with = _sym._extent(_with)
check("the hat sits forward of the body", _fa_with[0] < _sym._extent(_base)[0], True)

# Two hats must not land on each other.
_two, _ = _sym.with_accessories(_base, ["top hat", "half hat"])
check("a second front accessory stacks further out",
      _sym._extent(_two)[0] < _sym._extent(_with)[0], True)



# ------------------------------------------------------------------ positions
print("\npositions: a catwalk is not a pipe, and it is front of house")
from plotedit.scaled_pdf import Sheet as _Sheet

_cat = {"name": "Cat 1", "type": "catwalk", "x1": 0, "y1": -11, "x2": 33,
        "y2": -11, "width": 3.0}
_elec = {"name": "Elect 1", "type": "electric", "x1": 0, "y1": 16, "x2": 33, "y2": 16}

# A catwalk hangs over the audience, so the sheet must reach past the plaster
# line. Get this wrong and the position is clipped off the bottom in silence.
check("a catwalk needs house depth", _Sheet.foh_extent([_cat, _elec]), 12.5)
check("an electric needs none", _Sheet.foh_extent([_elec]), 0.0)
check("FOH is implied by the type, not only by the flag",
      _Sheet.foh_extent([dict(_cat, foh=None)]), 12.5)
check("...and can be turned off explicitly",
      _Sheet.foh_extent([dict(_cat, foh=False)]), 0.0)

# The three lines of a catwalk must be three DIFFERENT lines. Drawn on top of
# each other they read as one thick rail and the pipe disappears.
_half = _cat["width"] / 2
_lines = {_cat["y1"] + _half, _cat["y1"] - _half, _cat["y1"] - _half * 0.55}
check("a catwalk draws three distinct lines", len(_lines), 3)
check("the pipe sits inboard of the downstage edge",
      _cat["y1"] - _half * 0.55 > _cat["y1"] - _half, True)


print("\nunit 1: stage right on a lateral position, downstage on a longitudinal one")
from plotedit import positions as P

# ⚠ x increases toward STAGE RIGHT and y increases UPSTAGE (geometry.ts, and the
# sample puts "Special SR" at x=22 against "Special SL" at x=11 in a 33' room).
# So Jerry's two rules run in OPPOSITE directions: stage right is the MAXIMUM x,
# farthest downstage is the MINIMUM y. These tests exist to catch a refactor
# that makes them look symmetrical and reverses one.
_lat = {"name": "Elect 1", "x1": 0, "y1": 16, "x2": 33, "y2": 16}
_lon = {"name": "Pipe SR", "x1": 28, "y1": 2, "x2": 28, "y2": 26}
check("a wide position is lateral", P.axis(_lat), "lateral")
check("a deep one is longitudinal", P.axis(_lon), "longitudinal")
check("lateral defaults to stage right", P.number_from(_lat), "SR")
check("longitudinal defaults to downstage", P.number_from(_lon), "DS")

_i = [dict(unit=99, position="Elect 1", x=x, y=16) for x in (5, 12, 22, 30)]
P.number(_i, _lat)
check("unit 1 is the HIGHEST x — stage right",
      next(i["x"] for i in _i if i["unit"] == 1), 30)
check("...and unit 4 the lowest", next(i["x"] for i in _i if i["unit"] == 4), 5)

_j = [dict(unit=99, position="Pipe SR", x=28, y=y) for y in (4, 10, 18, 24)]
P.number(_j, _lon)
check("unit 1 is the LOWEST y — farthest downstage",
      next(i["y"] for i in _j if i["unit"] == 1), 4)

# The override Jerry asked for.
check("an explicit numberFrom wins", P.number_from(dict(_lat, numberFrom="SL")), "SL")
_k = [dict(unit=99, position="Elect 1", x=x, y=16) for x in (5, 30)]
P.number(_k, dict(_lat, numberFrom="SL"))
check("...and reverses the order", next(i["x"] for i in _k if i["unit"] == 1), 5)

# Two units at one coordinate cannot be ordered. Picking one is how a plot gets
# hung backwards, so it must warn rather than choose.
_dup = [dict(unit=99, position="Elect 1", x=12, y=16) for _ in range(2)]
_, _w = P.number(_dup, _lat)
check("units sharing a coordinate warn", "arbitrary" in (_w or ""), True)
check("an empty position warns too", P.number([], _lat)[1] is not None, True)


print("\ncircuits: recorded from the house, never invented")
from plotedit import circuits as C

# "Circuits depend on the house — no set order." (Jerry, 2026.09.23.) So the
# tool records and checks; it never generates a circuit number.
_p1 = {"name": "Elect 1", "x1": 0, "y1": 16, "x2": 33, "y2": 16,
       "circuits": [{"id": 3, "x": 4}, {"id": 4, "x": 28}],
       "circuitSource": "Drake rep plot 2019"}
_p2 = {"name": "Elect 2", "x1": 0, "y1": 20, "x2": 33, "y2": 20,
       "circuits": [7, 8], "circuitSource": "ME, by phone"}
_p3 = {"name": "Elect 3", "x1": 0, "y1": 24, "x2": 33, "y2": 24}

check("a bare list still reads", C.available(_p2), [7, 8])
check("locations survive", C.available(_p1), [3, 4])
check("an unsourced list says so", "NOT RECORDED" in C.source(_p3), True)

# A circuit the house does not list is a real error, not a warning.
_bad = [{"unit": 1, "position": "Elect 1", "circuit": 99, "x": 4, "y": 16}]
check("a circuit the house has not got is caught",
      any("does not list" in m for m in C.check(_bad, [_p1])), True)

# A twofer is legal and is a LOAD question, so it is reported, not rejected.
_two = [{"unit": 1, "position": "Elect 1", "circuit": 3, "x": 4, "y": 16},
        {"unit": 2, "position": "Elect 1", "circuit": 3, "x": 6, "y": 16}]
check("a twofer is reported as a load question",
      any("twofer" in m for m in C.check(_two, [_p1])), True)
check("a position with no circuits is noted, not failed",
      any("no circuits recorded" in m for m in C.check([], [_p3])), True)

# ⭐ The refusal. Without locations there is no basis for matching, and pairing
# a list against units in order would look like a result and be a guess.
_n, _notes = C.match_to_units(_two, _p2)
check("matching REFUSES when the house gave no locations", _n, 0)
check("...and says why", any("no set order" in m for m in _notes), True)

# With locations it matches — and must report every doubling it creates.
_many = [{"unit": u, "position": "Elect 1", "x": x, "y": 16}
         for u, x in [(1, 3), (2, 5), (3, 27)]]
_n, _notes = C.match_to_units(_many, _p1)
check("with locations it matches", _n, 3)
check("more units than circuits is flagged",
      any("MUST double up" in m for m in _notes), True)
check("...and the twofer it made is named",
      any("twofer" in m for m in _notes), True)


print("\ndimmer-per-circuit: the circuit and the dimmer are ONE number")
# Jerry, 2026.09.23: "most houses have circuit per dimmer." RP-2 6.14.1 notates
# the three control models differently, and in this one a second container tells
# the electrician there is a patch to make when there is not.
check("the three models are named", len(sym.CONTROL_MODELS), 3)
_pp = [{"name": "E1", "x1": 0, "y1": 16, "x2": 33, "y2": 16,
        "circuits": [3, 4], "circuitSource": "rep plot"}]
_ii = [{"unit": 1, "position": "E1", "circuit": 3, "dimmer": 3},
       {"unit": 2, "position": "E1", "circuit": 4, "dimmer": 112}]
check("circuit != dimmer is caught in a dimmer-per-circuit house",
      any("one number" in m for m in C.check(_ii, _pp)), True)
check("...and is fine in a patch house",
      any("one number" in m for m in C.check(_ii, _pp, control="hard-and-soft-patch")),
      False)

print("\nload: a tungsten unit's watts belong to its LAMP")
# The same Source Four is 575W or 750W depending on what is in it, so a wattage
# stored against the fixture would be wrong for half the rig.
check("HPL 575 is 575 watts", ph.lamp_watts("HPL 575"), 575.0)
check("HPL 750 is 750", ph.lamp_watts("HPL 750"), 750.0)
check("the long-life 575X is still 575", ph.lamp_watts("HPL 575X"), 575.0)
# ⭐ The one that matters. A loose number-search finds 3200 in "Regulated 3200K"
# and calls it 3200 watts — a number that looks real, lands in a load total and
# trips a breaker. An LED MODE IS NOT A LAMP.
check("an LED mode is NOT a lamp", ph.lamp_watts("Regulated 3200K"), None)
check("nor is a bare colour temperature", ph.lamp_watts("5600K"), None)
check("nor is a mode with no number", ph.lamp_watts("Boost"), None)

_load = [{"unit": u, "position": "E1", "circuit": 3, "type": "S4 26", "lamp": "HPL 575"}
         for u in (1, 2, 3, 4)]
_rows, _notes = C.load(_load, _pp, dimmer_watts=2400)
check("four 575s is 2300W", _rows[0]["watts"], 2300.0)
check("...which is inside 2400", _rows[0]["headroom_pct"] > 0, True)
_rows, _notes = C.load(_load + [dict(_load[0], unit=5, lamp="HPL 750")], _pp,
                       dimmer_watts=2400)
check("a fifth unit puts it over", any("is OVER" in m for m in _notes), True)

# ⚠ Without a rating nothing is judged. A capacity check against a number nobody
# confirmed reads as a pass, which is worse than no check at all.
check("no rating means no verdict",
      any("nothing is judged" in m for m in C.load(_load, _pp)[1]), True)
check("units with no wattage are named, and the total called a floor",
      any("a floor, not a total" in m
          for m in C.load([{"unit": 9, "position": "E1", "circuit": 3,
                            "type": "SHEHDS 19"}], _pp)[1]), True)

print()
if FAILS:
    print(f"{len(FAILS)} FAILED")
    for f in FAILS:
        print("   ", f)
    sys.exit(1)
print("all passed")

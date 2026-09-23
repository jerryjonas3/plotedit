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
check("the centre line is a 4-part chain dash", len(LINE_STYLES["centerline"][1]), 4)
check("the plaster line is evenly dashed", len(LINE_STYLES["plasterline"][1]), 2)
try:
    from plotedit.scaled_pdf import style as _style
    _style("chunky")
    check("an unknown category is refused", "no error", "KeyError")
except KeyError:
    check("an unknown category is refused", "KeyError", "KeyError")

print("\npaperwork")
check("Lightwright column aliases", len(paperwork.LW_COLUMNS), 37)

print()
if FAILS:
    print(f"{len(FAILS)} FAILED")
    for f in FAILS:
        print("   ", f)
    sys.exit(1)
print("all passed")

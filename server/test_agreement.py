#!/usr/bin/env python3
"""Step 3's condition: the screen and the paper must agree.

The browser asks the API. The PDF calls scaled_pdf. Both start from the same
.plot.json, so every number must match — and when they did not, it was because
scaled_pdf.unit() had no `mode` parameter and quietly computed LED fixtures at
their reference output instead of the mode the plot asked for. 441 fc where the
answer was 382.

    cd server && python3 test_agreement.py
"""
import json
import os
import sys

from fastapi.testclient import TestClient

from plotedit.api import app
from plot_to_pdf import render

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "samples", "bluver.plot.json")
OUT = os.path.join(os.path.dirname(__file__), "..", "out", "agreement.pdf")

plot = json.load(open(SAMPLE))

# --- what the browser gets
client = TestClient(app)
api_rows = client.post("/compute", json={"instruments": [
    {"unit": i["unit"], "channel": i.get("channel"), "type": i["type"],
     "x": i["x"], "y": i["y"], "trim": i.get("trim"),
     "focus_x": i.get("focusX"), "focus_y": i.get("focusY"),
     "focus_h": i.get("focusH", 5.5), "color": i.get("color"),
     "lamp": i.get("lamp"), "mode": i.get("mode")}
    for i in plot["instruments"]
]}).json()["instruments"]

# --- what the PDF gets
os.makedirs(os.path.dirname(OUT), exist_ok=True)
_, pdf_rows = render(SAMPLE, OUT)

fails = []
print(f"{'ch':<5} {'type':<15} {'API throw':<11} {'PDF throw':<11} {'API fc':>7} {'PDF fc':>7}")
for a, p in zip(api_rows, pdf_rows):
    if not a["computed"]:
        continue
    at, pt = round(a["throw"], 2), round(p["throw"], 2)
    af = round(a["footcandles"]) if a["footcandles"] else None
    pf = round(p["fc"]) if p.get("fc") else None
    ok = at == pt and af == pf
    print(f"{str(a['channel'] or ''):<5} {a['type']:<15} {at:<11} {pt:<11} "
          f"{str(af):>7} {str(pf):>7}  {'' if ok else '  <-- DISAGREE'}")
    if not ok:
        fails.append(f"ch {a['channel']}: API {at}ft/{af}fc vs PDF {pt}ft/{pf}fc")

    ap, pp = a.get("field"), p.get("field")
    if ap and pp and round(ap, 2) != round(pp, 2):
        fails.append(f"ch {a['channel']}: pool {ap} vs {pp}")

print(f"screen and paper agree on all {len(pdf_rows)} instruments")


# ---------------------------------------------------------------------------
print("\nthe 90-degree display option is COSMETIC")
# RP-2 p.2: "It is acceptable to visually orient the angle of each drawn
# luminaire to either focus points or 90° axes." Jerry, 2026.09.23: "most plots
# display the instruments on even 90 degree mounts... even though the lamp may
# be actually pointing 320 degrees, it would be displayed as 0 degrees."
#
# 🔴 The whole risk of that option is that it leaks into the arithmetic. A unit
# DRAWN at 0 while pointing at 320 is a drawing convention; a unit COMPUTED at 0
# would be a lie about where the light lands. So the same plot rendered both
# ways must produce identical numbers.
import json as _json
from plotedit.scaled_pdf import Sheet as _S
import plot_to_pdf as _p2p

_plot = _json.load(open("../samples/bluver.plot.json"))

def _numbers(mode):
    import tempfile, os
    _plot["symbolAngle"] = mode
    path = os.path.join(tempfile.mkdtemp(), f"{mode}.pdf")
    _json.dump(_plot, open(path + ".json", "w"))
    sheet, rows = _p2p.render(path + ".json", path, scale="1/4",
                              page="ARCH_D", landscape=True)
    return [(r["num"], round(r["throw"], 4), round(r["pan"], 4),
             round(r.get("fc") or 0, 4)) for r in rows if r]

_ortho = _numbers("orthogonal")
_focus = _numbers("focus")
if len(_ortho) < 5:
    fails.append("too few units to compare the two display modes")
if _ortho != _focus:
    for a, b in zip(_ortho, _focus):
        if a != b:
            fails.append(f"unit {a[0]}: orthogonal {a[1:]} vs focus {b[1:]} — the "
                         f"90-degree DISPLAY option has leaked into the arithmetic")
else:
    print(f"  ok   both display modes give identical numbers for {len(_ortho)} units")

# The suite's verdict comes LAST, so anything added after it still counts. It
# used to sit in the middle, which meant an appended check could fail while the
# suite exited 0 — the same defect found in test_package.py the same day.
print()
if fails:
    print(f"{len(fails)} DISAGREEMENTS")
    for f in fails:
        print("   ", f)
    sys.exit(1)
print("all agree")

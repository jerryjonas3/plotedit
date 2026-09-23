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

print()
if fails:
    print(f"{len(fails)} DISAGREEMENTS")
    for f in fails:
        print("   ", f)
    sys.exit(1)
print(f"screen and paper agree on all {len(pdf_rows)} instruments")

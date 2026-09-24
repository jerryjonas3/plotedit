#!/usr/bin/env python3
"""Step 5: everything that leaves the editor, and the ground plan coming in.

    cd server && python3 test_export.py
"""
import json
import os
import sys

from fastapi.testclient import TestClient

from plotedit.api import app
from plotedit import exports

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "samples", "bluver.plot.json")
plot = json.load(open(SAMPLE))
client = TestClient(app)
FAILS = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<50} {got}")
    if not ok:
        FAILS.append(f"{label}: got {got!r}, wanted {want!r}")


print("schedule — hanging order")
sched = exports.schedule_csv(plot).splitlines()
rows = [r.split(",") for r in sched[5:]]
check("every instrument present", len(rows), len(plot["instruments"]))
check("sorted by position then unit", [r[0] for r in rows][:4],
      ["GRID B", "GRID B", "GRID C", "GRID C"])
# Look the column up by NAME. A hard-coded index breaks the moment a column is
# inserted — which is exactly what adding Circuit did, and the failure read as
# "color is empty" rather than "the columns moved".
_col = exports.SCHEDULE_COLUMNS.index
check("color survives the CSV", rows[2][_col("Color")], "R52+R119")
check("the circuit column exists", "Circuit" in exports.SCHEDULE_COLUMNS, True)
check("circuit sits beside channel, not beside address",
      _col("Circuit") - _col("Channel"), 1)

print("\nhookup — channel order")
hook = [r.split(",") for r in exports.hookup_csv(plot).splitlines()[5:]]
check("channels ascend", [int(r[0]) for r in hook], sorted(int(r[0]) for r in hook))
check("starts at channel 1", hook[0][0], "1")

print("\nmagic sheet")
groups = exports.magic_sheet_rows(plot)
bax = next(g for g in groups if g["purpose"] == "BAX")
check("BAX grouped", bax["channels"], [11, 12, 13, 14])
check("BAX has no color, as in the archive", bax["colors"], [])

print("\neos patch — the format is UNVERIFIED and must say so")
asc = exports.eos_patch(plot)
check("warning is in the file itself", "HAS NOT BEEN TESTED" in asc, True)
check("unpatched units are listed, not dropped", asc.count("! Not patched") , 1)
# Count from the data, not from a number typed here — adding a boom to the
# sample broke this once already, and the failure read as "the exporter dropped
# units" rather than "the sample grew."
# Match the line's SHAPE, not a position name. The original counted lines
# starting "!   GRID", which quietly stopped counting when the sample gained
# booms — and the failure read as "the exporter dropped units" rather than "the
# sample grew a position whose name does not start with GRID".
import re as _re
check("every unit is listed as unpatched — the sample has no addresses",
      len(_re.findall(r"^!   .+ unit \d+ .* ch=", asc, _re.M)),
      len(plot["instruments"]))

print("\nexport endpoints")
req = {"plot": plot}
for path, kind, sniff in [("/export/schedule", "text/csv", b"Instrument Schedule"),
                          ("/export/hookup", "text/csv", b"Channel Hookup"),
                          ("/export/eos", "text/plain", b"Ident 3:0")]:
    r = client.post(path, json=req)
    check(f"{path} 200", r.status_code, 200)
    check(f"{path} content", sniff in r.content, True)
    check(f"{path} is a download", "attachment" in r.headers.get("content-disposition", ""), True)

# ⭐ The sample now carries booms, whose elevations sit beside the plot, and a
# FOH catwalk over the house. It no longer fits Tabloid at 1/4" — and the right
# behaviour is to REFUSE, not to clip. That is the guard working, so assert it.
r = client.post("/export/pdf", json=req)
check("a plot with booms will not fit Tabloid at 1/4", r.status_code, 422)
check("...and the refusal says which EDGE it runs off",
      any(w in r.json()["detail"] for w in ("LEFT", "RIGHT", "TOP", "BOTTOM")), True)

r = client.post("/export/pdf", json={"plot": plot, "page": "ARCH_D",
                                     "landscape": True})
check("/export/pdf 200 on the sheet Jerry actually draws on", r.status_code, 200)
check("/export/pdf is a PDF", r.content[:5], b"%PDF-")

r = client.post("/export/dxf", json=req)
check("/export/dxf 200", r.status_code, 200)
check("/export/dxf is a DXF", b"SECTION" in r.content[:2000], True)

print("\na plot that will not fit must FAIL, not clip")
r = client.post("/export/pdf", json={"plot": plot, "landscape": True})
check("landscape tabloid at 1/4 is refused", r.status_code, 422)
check("and names which edge it runs off",
      any(w in r.json()["detail"] for w in ("LEFT", "RIGHT", "TOP", "BOTTOM")), True)

# ⚠ Refuse only what makes the drawing WRONG. A grazing pool is a true note
# ABOUT the plot, not a reason to withhold the plot — refusing over it would
# mean a rig with one flat side light could never be exported at all.
r = client.post("/export/pdf", json={"plot": plot, "page": "ARCH_D", "landscape": True})
check("a non-fatal note does not block the export", r.status_code, 200)
check("...and travels back in a header", "X-Plot-Notes" in r.headers, True)
check("...naming the unit it is about", "unit" in r.headers.get("X-Plot-Notes", ""), True)

print("\ndxf import")

def make_venue_dxf(path):
    """A stand-in for what a venue sends: inches, walls, a grid, a door swing.
    Built fresh every run — a test must not read whatever is lying in out/."""
    import ezdxf
    d = ezdxf.new("R2010"); d.header["$INSUNITS"] = 1
    for L in ("WALLS", "GRID", "DOORS"):
        d.layers.add(L)
    m = d.modelspace(); W, D = 33 * 12, 38 * 12
    m.add_lwpolyline([(0, 0), (W, 0), (W, D), (0, D)], close=True, dxfattribs={"layer": "WALLS"})
    for y in range(48, D, 48):
        m.add_line((0, y), (W, y), dxfattribs={"layer": "GRID"})
    m.add_arc((W, 60), 36, 90, 180, dxfattribs={"layer": "DOORS"})
    d.saveas(path)

import tempfile
_tmp = tempfile.TemporaryDirectory()
venue = os.path.join(_tmp.name, "venue.dxf")
make_venue_dxf(venue)

with open(venue, "rb") as fh:
    r = client.post("/import/dxf/layers", files={"file": ("venue.dxf", fh, "application/dxf")})
check("layers listed", [l["name"] for l in r.json()["layers"]], ["DOORS", "GRID", "WALLS"])
check("units read from the header", r.json()["units"], "inches")

with open(venue, "rb") as fh:
    r = client.post("/import/dxf", files={"file": ("venue.dxf", fh, "application/dxf")},
                    data={"layers": "WALLS", "units": "in"})
g = r.json()
check("only the requested layer comes in", len(g["paths"]), 1)
check("inches converted to feet", g["extents"], [0.0, 0.0, 33.0, 38.0])

r = client.post("/import/dxf", files={"file": ("x.dxf", b"not a dxf", "application/dxf")})
check("a bad file is refused with a reason", r.status_code, 400)

print()
if FAILS:
    print(f"{len(FAILS)} FAILED")
    for f in FAILS:
        print("   ", f)
    sys.exit(1)
print("all passed")

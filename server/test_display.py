#!/usr/bin/env python3
"""Step 6: the editor's display choices, carried onto paper.

    cd server && python3 test_display.py

⭐ WHAT THIS IS FOR. The `pools`, `focus` and `labels` checkboxes changed the
screen and nothing else: Export gave back everything regardless, so the only way
to issue a clean plan was to delete the focus points and put them back after.

⚠ AND THE RULE THAT MATTERS MORE. A switch that hides a DRAWING must never hide
a FINDING. Turning the pools off used to take the "this pool never lands"
warning away with the ellipse, because the shape was only worked out inside the
branch that drew it — so a plot came out clean by showing less. Every assertion
below about warnings and rows exists to keep that from coming back.
"""
import contextlib
import io as _io
import json
import os
import sys
import tempfile

import fitz
from fastapi.testclient import TestClient

from plotedit.api import app
from plot_to_pdf import render

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "samples", "bluver.plot.json")
plot = json.load(open(SAMPLE))
client = TestClient(app)
FAILS = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<58} {got}")
    if not ok:
        FAILS.append(f"{label}: got {got!r}, wanted {want!r}")


def ink(path):
    """(curves, lines, characters) actually on the page."""
    page = fitz.open(path)[0]
    kinds = {}
    for drawing in page.get_drawings():
        for item in drawing["items"]:
            kinds[item[0]] = kinds.get(item[0], 0) + 1
    return kinds.get("c", 0), kinds.get("l", 0), len(page.get_text())


def draw(**kw):
    """Render the sample at a FIXED scale — comparing ink between two sheets
    drawn at different scales would measure the scale, not the switches."""
    path = os.path.join(tempfile.mkdtemp(), "x.pdf")
    sheet, rows = render(SAMPLE, path, scale="1/4", **kw)
    return ink(path), sorted(sheet.warnings), rows


print("the switches change what is DRAWN")
(on_c, on_l, on_t), on_w, on_rows = draw()
(np_c, np_l, np_t), np_w, np_rows = draw(show_pools=False)
(nf_c, nf_l, nf_t), nf_w, nf_rows = draw(show_focus=False)
(nl_c, nl_l, nl_t), nl_w, nl_rows = draw(show_labels=False)
(off_c, off_l, off_t), off_w, off_rows = draw(
    show_pools=False, show_focus=False, show_labels=False)

# Pools are drawn as flattened polylines, so they are LINES on the page, not
# curves. The focus target is a circle, which is curves. Said out loud because
# the obvious assertion — "pools off means fewer curves" — passes for the wrong
# reason and would go on passing if pools were never hidden at all.
check("pools off draws fewer lines", np_l < on_l, True)
check("...and pools are the bulk of them", np_l < on_l / 2, True)
check("focus off draws fewer curves", nf_c < on_c, True)
check("labels off prints less text", nl_t < on_t, True)
check("labels off is the only one that changes the text",
      (np_t, nf_t) == (on_t, on_t), True)
check("all three off is the least ink", (off_c < nf_c and off_l < np_l), True)

print()
print("...and NOTHING else — a hidden drawing is not a hidden finding")
check("the sample raises warnings at all", len(on_w) > 0, True)
check("pools off keeps every warning", np_w, on_w)
check("focus off keeps every warning", nf_w, on_w)
check("labels off keeps every warning", nl_w, on_w)
check("all three off keeps every warning", off_w, on_w)
check("every unit is still computed", [len(r) for r in (np_rows, nf_rows, nl_rows, off_rows)],
      [len(on_rows)] * 4)
check("the photometrics are identical with everything off",
      [r and r.get("fc") for r in off_rows], [r and r.get("fc") for r in on_rows])

print()
print("the fitted scale is measured on the drawing that will be ISSUED")
# A pool at a low elevation sprawls far past the room. With pools ON this plot
# cannot be fitted at all; with them OFF the room alone fits at 1/2". If the
# switches were not passed into the fit search, both would come back the same —
# a sheet scaled, and clipped, for a drawing nobody asked to see.
_probe = {
    "show": "fit probe", "venue": "", "revision": "0", "designer": "", "studio": "",
    "room": {"width": 25, "depth": 25}, "control": "dimmer-per-circuit",
    "positions": [{"name": "E1", "type": "electric",
                   "x1": 0, "y1": 24, "x2": 25, "y2": 24, "trim": 10}],
    "instruments": [{"unit": 1, "channel": 1, "type": "S4 26", "x": 12.5, "y": 24,
                     "trim": 10, "focusX": 12.5, "focusY": 1, "focusH": 0,
                     "position": "E1"}],
}
_d = tempfile.mkdtemp()
_jp = os.path.join(_d, "probe.plot.json")
json.dump(_probe, open(_jp, "w"))


def _fit(**kw):
    # The pools-on pass genuinely runs out of scales and says so. That is the
    # point of the probe, but it is not a failure, so its notes stay out of the
    # suite's output rather than looking like one.
    buf = _io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        sheet, _ = render(_jp, os.path.join(_d, "o.pdf"), scale="fit", **kw)
    return sheet.scale_label


check("pools on, the pool decides the scale", _fit(), "1/8\" = 1'-0\"")
check("pools off, the room does", _fit(show_pools=False), "1/2\" = 1'-0\"")

print()
print("the endpoint carries them")
def _post(body):
    r = client.post("/export/pdf", json=body)
    if r.status_code != 200:
        return None
    p = os.path.join(tempfile.mkdtemp(), "x.pdf")
    open(p, "wb").write(r.content)
    return ink(p)

_default = _post({"plot": plot, "scale": "1/4"})
_nopools = _post({"plot": plot, "scale": "1/4", "showPools": False})
_nolabels = _post({"plot": plot, "scale": "1/4", "showLabels": False})
check("a request that says nothing draws everything", _default, (on_c, on_l, on_t))
check("showPools:false reaches the paper", _nopools, (np_c, np_l, np_t))
check("showLabels:false reaches the paper", _nolabels, (nl_c, nl_l, nl_t))
check("an unknown field is still not a reason to refuse a plot",
      client.post("/export/pdf",
                  json={"plot": plot, "scale": "1/4", "somethingNew": 1}).status_code, 200)


print()
if FAILS:
    print(f"{len(FAILS)} FAILED")
    for f in FAILS:
        print("   ", f)
    sys.exit(1)
print("all passed")

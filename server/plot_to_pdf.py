#!/usr/bin/env python3
"""Render a .plot.json through scaled_pdf — the same file the browser draws.

    cd server && python3 plot_to_pdf.py ../samples/bluver.plot.json ../out/bluver.pdf

This is step 3's proof: the screen and the paper must agree. It is also the
beginning of step 5's export, so it lives in the package rather than in a test.
"""
import json
import sys

from plotedit.scaled_pdf import Sheet, ft, check
from plotedit import photometrics as ph


def render(plot_path, pdf_path, scale="1/4", page="TABLOID", landscape=False, dxf=None):
    plot = json.load(open(plot_path))
    room = plot["room"]
    s = Sheet(pdf_path, page=page, scale=scale, landscape=landscape,
              show=plot["show"], venue=plot.get("venue", ""),
              sheet=plot.get("revision", ""), rev=plot.get("revision", "0")[:3],
              designer=f"Design: {plot.get('designer', '')}", dxf=dxf)
    # ⭐ FOH positions — catwalks — sit over the AUDIENCE, downstage of the
    # plaster line and outside the stage rectangle, at negative y. The origin has
    # to make room for them or they are clipped straight off the bottom of the
    # sheet and only the clipping guard would ever say so.
    house = Sheet.foh_extent(plot.get("positions"))
    s.origin(ft(4), ft(4) + (house + 1.5 if house else 0))

    s.layer("BASE")
    # §6.18: architecture is HEAVY; the reference lines are MEDIUM and dashed;
    # dimensions are LIGHT.
    s.rect(0, 0, room["width"], room["depth"], style="architecture")
    s.center_line(room["width"] / 2, -1.0, room["depth"] + 1.0)
    if room.get("plasterLine") is not None:
        s.plaster_line(room["plasterLine"], -1.0, room["width"] + 1.0)
    s.dim(0, -1.5, room["width"], -1.5)
    s.dim(-1.5, 0, -1.5, room["depth"])

    for p in plot["positions"]:
        label = p["name"] + (f" — trim {ph.fmt_ft(p['trim'])}" if p.get("trim") else "")
        s.position(p, label=label)

    rows = []
    for inst in plot["instruments"]:
        focus = ((inst["focusX"], inst["focusY"])
                 if inst.get("focusX") is not None else None)
        r = s.unit(inst["x"], inst["y"], inst["unit"], ch=inst.get("channel"),
                   kind=inst["type"], color_gel=inst.get("color"),
                   trim=inst.get("trim"), focus_to=focus,
                   focus_h=inst.get("focusH", 5.5), lamp=inst.get("lamp"),
                   mode=inst.get("mode"),
                   lens_rotation=inst.get("lensRotation"),
                   accessories=inst.get("accessories"),
                   circuit=inst.get("circuit"), dimmer=inst.get("dimmer"),
                   control=plot.get("control", "dimmer-per-circuit"))
        rows.append(r)

    if room.get("source"):
        s.note(1, room["depth"] - 1.5, f"Room: {room['source'][:110]}")
    s.finish()
    return s, rows


if __name__ == "__main__":
    plot_path = sys.argv[1] if len(sys.argv) > 1 else "../samples/bluver.plot.json"
    pdf_path = sys.argv[2] if len(sys.argv) > 2 else "../out/bluver.pdf"
    s, rows = render(plot_path, pdf_path)
    print(f"wrote {pdf_path}")
    check(pdf_path)
    if s.warnings:
        for w in s.warnings:
            print("⚠", w)
    print(f"\n{'unit':<5} {'ch':<4} {'type':<15} {'throw':<9} {'pool':<9} {'fc':>6}")
    for r in rows:
        if not r or r.get("throw") is None:
            continue
        fc = f"{round(r['fc'])}" if r.get("fc") else "—"
        print(f"{r['num']:<5} {str(r.get('ch') or ''):<4} {r['kind']:<15} "
              f"{ph.fmt_ft(r['throw']):<9} {ph.fmt_ft(r.get('field')):<9} {fc:>6}")

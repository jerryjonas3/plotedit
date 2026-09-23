#!/usr/bin/env python3
"""Draw the symbol set to a sheet, for comparing against the RP-2 plates.

    cd server && python3 draw_symbol_sheet.py ../out/rp2-symbols.pdf
"""
import sys

from plotedit.scaled_pdf import Sheet, ft
from plotedit import symbols as sym


def main(path="../out/rp2-symbols.pdf"):
    s = Sheet(path, page="TABLOID", scale="1", landscape=True,
              show="Instrument symbols — USITT RP-2 (2006)",
              venue="Traced from the plates. Compare with docs/reference/USITT-RP-2-2006.pdf pp.4-9",
              sheet="1\" = 1'-0\" — the shapes at twice the size they print at 1/2\" scale",
              rev="2")
    s.origin(ft(0, 4), ft(0, 4))

    def row(y, title, items, gap=1.85, x0=1.1):
        s.text(0.35, y + 1.35, title, size=8.5, bold=True)
        for i, (label, prims) in enumerate(items):
            x = x0 + i * gap
            sym.draw(s, prims, x, y, width=1.2)
            s.text(x, y - 1.25, label, size=6.5, center=True)

    row(7.6, "6.1.6  ENHANCED ERS — the MARK IN THE LENS HOUSING codes the beam angle", [
        ("19-20  X", sym.enhanced_ers(19)),
        ("26-30  diagonal", sym.enhanced_ers(26)),
        ("36-40  no mark", sym.enhanced_ers(36)),
        ("50  wedge", sym.enhanced_ers(50)),
        ("70  rings", sym.enhanced_ers(70)),
        ("zoom  Z", sym.ers_zoom(30)),
    ])
    row(4.9, "6.2  FRESNEL — proud lens ring        6.3  PAR — capsule, spread marked on the front", [
        ("Fresnel 6\"", sym.fresnel(6)),
        ("Fresnel 8\"", sym.fresnel(8)),
        ("PAR 64 VNSP", sym.par(64, "VNSP")),
        ("PAR 64 NSP", sym.par(64, "NSP")),
        ("PAR 64 MFL", sym.par(64, "MFL")),
        ("PAR 64 WFL", sym.par(64, "WFL")),
    ])
    row(2.1, "6.16  LED — dots = number of colours     6.8  MOVERS — dashed swing radius     6.9  PRACTICAL", [
        ("LED 3 colour", sym.led(3)),
        ("LED 7 — Lustr", sym.led(7)),
        ("moving yoke", sym.moving_head("yoke")),
        ("head, wash", sym.moving_head("wash")),
        ("head, spot", sym.moving_head("spot")),
        ("practical", sym.practical()),
    ])
    s.finish()
    if s.warnings:
        for w in s.warnings:
            print("⚠", w)
    print("wrote", path)


if __name__ == "__main__":
    main(*sys.argv[1:])

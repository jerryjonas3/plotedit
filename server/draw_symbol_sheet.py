#!/usr/bin/env python3
"""Draw the symbol set to a sheet, for comparing against the RP-2 plates.

    cd server && python3 draw_symbol_sheet.py ../out/rp2-symbols.pdf
"""
import sys

from plotedit.scaled_pdf import Sheet, ft
from plotedit import symbols as sym


def main(path="../out/rp2-symbols.pdf"):
    s = Sheet(path, page="ARCH_D", scale="1", landscape=True,
              show="Instrument symbols — USITT RP-2 (2006)",
              venue="MARK UP AND SEND BACK — every symbol is numbered",
              sheet="Drawn from RP-2 pp.4-9. Twice the size they print at 1/2\" scale",
              rev="5")
    s.origin(ft(0, 4), ft(0, 4))

    # Every symbol carries a number. Without one there is no way to say which
    # symbol is wrong except by describing it, and describing it is the part
    # that goes wrong. The number is the whole point of the sheet.
    n = [0]

    def row(y, title, items, gap=5.2, x0=2.4):
        s.text(0.35, y + 1.35, title, size=8.5, bold=True)
        for i, (label, prims) in enumerate(items):
            x = x0 + i * gap
            n[0] += 1
            sym.draw(s, prims, x, y, width=1.2)
            s.text(x, y - 1.25, f"{n[0]}.  {label}", size=6.5, center=True)

    row(19.8, "6.1.6  ENHANCED ERS — the MARK IN THE LENS HOUSING codes the beam angle", [
        ("19-20  X", sym.enhanced_ers(19)),
        ("26-30  diagonal", sym.enhanced_ers(26)),
        ("36-40  no mark", sym.enhanced_ers(36)),
        ("50  wedge", sym.enhanced_ers(50)),
        ("70  rings", sym.enhanced_ers(70)),
        ("zoom  Z", sym.ers_zoom(30)),
    ])
    row(16.6, "6.2  FRESNEL — proud lens ring, and the OVAL BEAM FRESNEL (= an ETC PARNel)        6.3  PAR", [
        ("Fresnel 6\"", sym.fresnel(6)),
        ("Fresnel 8\"", sym.fresnel(8)),
        ("PARNel — axis 0", sym.oval_beam_fresnel(rotation=0)),
        ("PARNel — axis 45", sym.oval_beam_fresnel(rotation=45)),
        ("PARNel — axis 90", sym.oval_beam_fresnel(rotation=90)),
        ("PAR 64 WFL", sym.par(64, "WFL")),
    ])
    row(13.4, "6.16  LED — dots = number of colors     6.8  MOVERS — dashed swing radius     6.9  PRACTICAL", [
        ("LED 3 color", sym.led(3)),
        ("LED 7 — Lustr", sym.led(7)),
        ("moving yoke", sym.moving_head("yoke")),
        ("head, wash", sym.moving_head("wash")),
        ("head, spot", sym.moving_head("spot")),
        ("practical", sym.practical()),
    ])
    row(10.2, "6.6  CYC — arrow BESIDE the body is the focus direction     "
             "6.7  STRIPS — length is the real unit     6.10  FOLLOWSPOT", [
        ("cyc, 1 cell", sym.cyc_unit(1)),
        ("cyc, 3 cell", sym.cyc_unit(3)),
        ("cyc, 4 cell", sym.cyc_unit(4)),
        ("strip, pipe hung", sym.striplight(5.0)),
        ("strip, trunnion", sym.striplight(5.0, mount="trunnion")),
        ("followspot", sym.followspot()),
    ])

    row(7.0, "6.13  ACCESSORIES — the proud line is the gel-frame edge they clip into.  "
             "Beam projectors, scoops and fluorescents deliberately NOT drawn — Jerry, 2026.09.23", [
        ("barn door, 2 panel", sym.barn_door(2)),
        ("barn door, 4 panel", sym.barn_door(4)),
        ("top hat", sym.top_hat()),
        ("half hat", sym.top_hat(half=True)),
    ])

    # §6.18 — the three weights, drawn so they can be compared with the plate
    from plotedit.scaled_pdf import LINE_STYLES
    s.text(0.35, 4.6, "6.18  LINE WEIGHTS — three, and only three", size=8.5, bold=True)
    groups = [("lightweight", ["scenery", "leader", "dimension"]),
              ("medium", ["masking", "drop", "centerline", "plasterline"]),
              ("heavy", ["batten", "luminaire", "architecture"])]
    x = 0.6
    for title, names in groups:
        s.text(x, 3.9, title, size=7.5, bold=True)
        for i, style_name in enumerate(names):
            y = 3.5 - i * 0.55
            s.line(x, y, x + 3.4, y, style=style_name)
            s.text(x + 3.6, y - 0.05, style_name, size=7.5)
        x += 8.6

    s.text(0.35, 0.9,
           "Mark up on paper or on screen. For each symbol that is wrong: the number, "
           "what is wrong, and what it should be. \"Right\" beside a number is worth "
           "as much as \"wrong\" — it stops it being redrawn.",
           size=6.5)

    s.finish()
    if s.warnings:
        for w in s.warnings:
            print("⚠", w)
    print("wrote", path)


if __name__ == "__main__":
    main(*sys.argv[1:])

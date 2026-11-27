#!/usr/bin/env python3
"""A gel's colour is read from the maker's sheet, or it is absent. Never invented.

    cd server && python3 test_gel_colour.py

#148: gels.csv says how MUCH light gets through and nothing about what colour it
becomes, so the show model carried its own hand-written map of seven hex values —
and thirteen units rendered as warm white because their filters were not in it.
⚠ An unknown gel fell back to warm white rather than failing, which is why nobody
could see it for as long as they didn't.

#159 published the chromaticity; this suite covers the module that turns it into
something a renderer can use, and the two failures that matter: a colour that is
WRONG, and an absence quietly filled in.
"""
import csv
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plotedit import photometrics as ph        # noqa: E402
from plotedit import gel_colour as gc          # noqa: E402

FAILS = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<56} {got}")
    if not ok:
        FAILS.append(f"{label}: got {got!r}, wanted {want!r}")


def ok(label, cond, note=""):
    print(f"  {'ok  ' if cond else 'FAIL'} {label:<56} {note}")
    if not cond:
        FAILS.append(label)


NAMES = {ph.gel_key(r["gel"]): r["name"]
         for r in csv.DictReader(open(os.path.join(
             os.path.dirname(os.path.abspath(__file__)), "plotedit", "gels.csv"),
             encoding="utf-8"))}

print("⭐ the white point for LEE's 3200K figures is computed, not typed in")
x32, y32 = gc._WHITE_XY["TUNG3200"]                     # noqa: SLF001
# The published chromaticity of a 3200K blackbody. Kim et al. is quoted as good
# to ~5e-5 over this range, so this pins the formula rather than the result.
ok("3200K lands on the Planckian locus", abs(x32 - 0.4234) < 0.002 and abs(y32 - 0.3990) < 0.002,
   f"({x32:.4f}, {y32:.4f})")

print("\n🔴 THE ADAPTATION IS THE WHOLE CORRECTNESS QUESTION")
# Without Bradford adaptation every filter renders with the LAMP's colour on top
# of its own, and a clear filter under tungsten comes out strongly amber.
# ⭐ So: a filter whose chromaticity IS its illuminant's white point is doing
# nothing to the light, and must come back neutral.
for illum in gc.ILLUMINANT_PREFERENCE:
    wx, wy = gc._WHITE_XY[illum]                        # noqa: SLF001
    neutral = gc.srgb_from_xy(wx, wy, illum)
    r, g, b = neutral["rgb"]
    ok(f"a filter matching illuminant {illum} is neutral", max(r, g, b) - min(r, g, b) <= 1,
       neutral["hex"])

print("\n⚠ and the hue survives — the first version crushed it to the gamut corners")
# 🔴 THE BUG THIS PINS. Normalising to Y=1 asks for a saturated hue at the
# luminance of white; every channel goes out of range, clamping flattens them,
# and R80 Primary Blue rendered as pure cyan #00FFFF.
blue = gc.colour_for("R80")
r, g, b = blue["rgb"]
ok("R80 Primary Blue is blue", b > g and b > r and b > 200, blue["hex"])
ok("...and is NOT cyan", not (g > 240 and b > 240), f"g={g} b={b}")

print("\n⭐ known filters come out looking like their names")
for code, test, why in [
    ("L106", lambda c: c["rgb"][0] > 200 and c["rgb"][1] < 80, "red"),
    ("R389", lambda c: c["rgb"][1] > 200 and c["rgb"][0] < 80, "green"),
    ("R21", lambda c: c["rgb"][0] > 200 and c["rgb"][1] > 80 and c["rgb"][2] < 80, "amber"),
    ("R02", lambda c: min(c["rgb"]) > 150 and c["rgb"][0] >= max(c["rgb"]), "pale and warm"),
    ("L764", lambda c: min(c["rgb"]) > 140 and c["rgb"][2] < c["rgb"][0], "pale straw"),
]:
    col = gc.colour_for(code)
    ok(f"{code} {NAMES.get(code, '?')} reads as {why}", col is not None and test(col),
       col["hex"] if col else "none")

# ⭐ An internal check nobody had to author: a half-strength correction filter
# must be PALER than the full-strength one from the same family.
full, half = gc.colour_for("L201"), gc.colour_for("L202")
ok("Half CT Blue is paler than Full CT Blue", min(half["rgb"]) > min(full["rgb"]),
   f"{full['hex']} -> {half['hex']}")

print("\n🔴 AN ABSENCE STAYS VISIBLE — #148's own requirement")
# "the absence is currently visible and a wrong value would not be"
missing = [k for k in ph.GELS if gc.colour_for(k) is None]
check("filters with no published chromaticity", len(missing), 37)
ok("colour_for returns None, not a default", all(gc.colour_for(k) is None for k in missing))
# ⚠ These are a CATEGORY, not a random gap: GamColor's 1500-series technical
# range plus a few frosts — the filters a single swatch describes least well,
# since an ND is neutral by definition and a CTO's colour is relative to the lamp.
tech = [k for k in missing if "CT" in NAMES.get(k, "") or "ND" in NAMES.get(k, "")
        or "Green" in NAMES.get(k, "") or "Frost" in NAMES.get(k, "")]
ok("most of them are correction and technical filters", len(tech) >= 28, f"{len(tech)} of 37")
check("an unknown code is also None, not an error", gc.colour_for("ZZ999"), None)

print("\n⚠ the illuminant is reported, because no two makers publish the same one")
check("GamColor uses A", gc.colour_for("G100")["illuminant"], "A")
check("Rosco prefers A over its own D65 row", gc.colour_for("R80")["illuminant"], "A")
check("LEE prefers 3200K over C", gc.colour_for("L201")["illuminant"], "TUNG3200")
ok("every entry says which illuminant it used",
   all(v["illuminant"] in gc.ILLUMINANT_PREFERENCE for v in gc.GEL_COLOUR.values()))
ok("every entry carries a source URL",
   all(v["source_url"].startswith("http") for v in gc.GEL_COLOUR.values()))

print("\n⚠ out of gamut is reported rather than hidden")
oog = [k for k, v in gc.GEL_COLOUR.items() if v["out_of_gamut"]]
ok("a good share of stage filters are more saturated than sRGB",
   100 < len(oog) < 400, f"{len(oog)} of {len(gc.GEL_COLOUR)}")
ok("R02 Bastard Amber is NOT out of gamut", not gc.colour_for("R02")["out_of_gamut"])
ok("every value is a legal 8-bit triple",
   all(all(0 <= c <= 255 for c in v["rgb"]) for v in gc.GEL_COLOUR.values()))
ok("every value is at full value — peak channel 255",
   all(max(v["rgb"]) == 255 for v in gc.GEL_COLOUR.values()))

print("\n⚠ luminance is NOT baked into the colour")
# A 6% filter rendered at its own Y is nearly black and useless as a swatch, so
# the measured Y rides alongside and the caller decides.
deep = gc.colour_for("R80")
ok("a 6% filter still has a full-value swatch", max(deep["rgb"]) == 255, deep["hex"])
ok("...with its real luminance reported beside it", deep["luminance_pct"] < 10,
   f"{deep['luminance_pct']}%")

print("\n⚠ THE TWO FILES AGREE — BUT THIS IS ONE SOURCE READ TWICE, NOT TWO")
# 🔴 Worth being precise about what this proves. gels.csv transmission and the
# sheet's Y come from the SAME published pages for all three makers — Rosco and
# GamColor from the data sheets, LEE from leefilters.com. So agreement is NOT
# independent corroboration of the makers' numbers.
# ⭐ What it DOES prove is that the extraction is sound: #159 read 609 filters by
# OCR, and an OCR that garbled a digit would show up here as a Y that no longer
# matches the transmission read from the same sheet.
diffs = [abs(gc.colour_for(k)["luminance_pct"] / 100.0 - v["t"])
         for k, v in ph.GELS.items() if gc.colour_for(k)]
check("filters compared", len(diffs), 609)
ok("median disagreement is noise", statistics.median(diffs) < 0.001,
   f"{statistics.median(diffs):.5f}")
ok("not one filter disagrees by more than 2 points", max(diffs) < 0.02, f"max {max(diffs):.4f}")

print("\n⚠ the endpoint carries it, and says what it does not know")
from plotedit.api import gels                    # noqa: E402
payload = gels()
check("every gel is still listed", payload["count"], 646)
check("...with colour where published", payload["with_colour"], 609)
check("...and counted where not", payload["without_colour"], 37)
ok("the caveat about a single RGB survives into the payload",
   "simplification" in payload["colour"]["caveat"])
ok("a gel with no colour says None rather than omitting the key",
   payload["gels"]["R132"]["colour"] is None)
ok("transmission and source are untouched",
   payload["gels"]["R02"]["transmission"] == ph.GELS["R02"]["t"])

print()
if FAILS:
    for f in FAILS:
        print("FAILED:", f)
    sys.exit(1)
print("all passed")

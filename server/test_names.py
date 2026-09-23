#!/usr/bin/env python3
"""The resolver, against the names that are actually in Jerry's archive.

    cd server && python3 test_names.py

Before this existed, NONE of the 38 distinct instrument names in the archive
matched a photometric table key — an imported plot drew correctly and was
silently unlit.
"""
import sys

from plotedit import fixture_names as fn
from plotedit import photometrics as ph

FAILS = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<52} {got}")
    if not ok:
        FAILS.append(f"{label}: got {got!r}, wanted {want!r}")


print("names from the archive resolve to table keys")
for raw, want in [
    ("ETC Source4 36deg", "S4 36"),
    ("ETC Source4 26deg", "S4 26"),
    ("ETC Source4 19deg", "S4 19"),
    ("ETC Source4 50deg", "S4 50"),
    ("ETC CE Source4 26deg", "S4 26"),          # CE units, same optics
    ("S4-50°", "S4 50"),
    ("S4-50Â°", "S4 50"),                        # mojibake from an old export
    ("ETC CE Source4 PAR MCM (MFL)", "S4 EA PAR MFL"),
    ("ETC Source4 PARNel", "S4 PARNel @25"),
    ("S4 26", "S4 26"),                          # a key resolves to itself
]:
    check(f"{raw!r}", fn.resolve(raw, ph.FIXTURES)[0], want)

print("\nreal fixtures with no data give a REASON, not silence")
for raw, fragment in [
    ("Altman 6in Fres", "no datasheet"),
    ("ETC ColorSource CYC", "not on file"),
    ("Blizzard Lighting AtmosFEAR Tour HZ", "not a luminaire"),
    ("S4-36° LED-ClrSrc", "ColorSource"),
    ("ETC Source4 Jr Zoom", "different fixture"),
]:
    key, note = fn.resolve(raw, ph.FIXTURES)
    check(f"{raw!r} -> no key", key, None)
    check(f"   ...and says why", fragment.lower() in note.lower(), True)

print("\nnonsense and blanks")
check("unknown name", fn.resolve("Nonsense 12", ph.FIXTURES)[0], None)
check("empty", fn.resolve("", ph.FIXTURES)[0], None)
check("a system name, not a fixture", fn.resolve("CYC", ph.FIXTURES)[0], None)

print("\nthe paperwork name computes the SAME as the table key")
for raw, key in [("ETC Source4 26deg", "S4 26"), ("S4-50°", "S4 50"),
                 ("ETC CE Source4 19deg", "S4 19")]:
    a = ph.footcandles(raw, 14, lamp="HPL 575")[0]
    b = ph.footcandles(key, 14, lamp="HPL 575")[0]
    check(f"{raw!r} == {key!r}", round(a), round(b))
    pa, pb = ph.pool(raw, 14)["field"], ph.pool(key, 14)["field"]
    check(f"   ...and the pool matches", round(pa, 4), round(pb, 4))

print("\nthe note says how a name was read")
_, note = ph.footcandles("ETC Source4 26deg", 14, lamp="HPL 575")
check("footcandle note carries the translation", "read as 'S4 26'" in note, True)

print("\nand the symbol is the same too")
from plotedit import symbols as sym
check("'ETC Source4 19deg' draws what 'S4 19' draws",
      [p[0] for p in sym.for_type("ETC Source4 19deg")],
      [p[0] for p in sym.for_type("S4 19")])

print()
if FAILS:
    print(f"{len(FAILS)} FAILED")
    for f in FAILS:
        print("   ", f)
    sys.exit(1)
print("all passed")

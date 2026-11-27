#!/usr/bin/env python3
"""An S4 with no 575 figure on file says so. It does not answer at the 750.

    cd server && python3 test_edlt_lamp.py

#139: `LAMP_MF["HPL 575"]` has rows for S4 19/26/36/50 and the four PARs, and
none for the EDLT tubes. `footcandles()` applied the 575 default only when the
fixture appeared in that table, so an EDLT fell through, kept mf=1.0, and
returned the HPL 750 figure labelled "at HPL 750" —

    S4 36 EDLT   246.4 fc   where the real answer is nearer 165   HIGH BY HALF

🔴 AND HIGH IS THE DANGEROUS DIRECTION. The plot promises light the rig will not
deliver, and the note looked honest while it did it: a 750 IS what ETC's chart
was measured at. It just is not what is in the barrel.

⭐ THE REAL DEFECT WAS TWO GATES. `ASSUME_DEFAULT_LAMP` already answers "is this
a fixture we read as a 575?", and `watts_for` has used it since 2026.10.13.
`footcandles` rolled its own test instead and disagreed. The EDLT is only where
that showed.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plotedit import photometrics as ph        # noqa: E402

FAILS = []


def check(label, got, want):
    ok_ = got == want
    print(f"  {'ok  ' if ok_ else 'FAIL'} {label:<54} {got}")
    if not ok_:
        FAILS.append(f"{label}: got {got!r}, wanted {want!r}")


def ok(label, cond, note=""):
    print(f"  {'ok  ' if cond else 'FAIL'} {label:<54} {note}")
    if not cond:
        FAILS.append(label)


print("🔴 the two affected fixtures refuse rather than overstate")
# ⚠ Only these two. Every other fixture with a tungsten ref_lamp and no 575 row
# has cd=None and already returned nothing — the bug needed a real candela
# figure to produce a wrong number from.
for kind, was in [("S4 36 EDLT", 246.38), ("S4 26 EDLT", 455.75)]:
    fc, note = ph.footcandles(kind, 20.0)
    ok(f"{kind} gives no level", fc is None, note[:40] + "...")
    ok(f"...and no longer returns {was} fc", fc != was)
    ok(f"...and the note names the missing figure", "HPL 575" in note and kind in note)
    ok("...and says what to do about it", "Name the lamp" in note)

print("\n⭐ and the honest answer is still available on request")
# Refusing the DEFAULT is not refusing to compute. A plot that states its lamp
# gets its level, as it always did.
fc, note = ph.footcandles("S4 36 EDLT", 20.0, lamp="HPL 750")
ok("naming the HPL 750 explicitly gives the 750 figure", fc is not None and abs(fc - 246.38) < 0.1,
   f"{fc:.2f} fc" if fc else "none")
ok("...labelled as the reference lamp, not as an assumption", "assumed" not in note, note)

print("\n⚠ NOTHING ELSE MOVED — the gate is a family gate, not a lamp-name gate")
# 🔴 The risk in this change is over-reach. Altman's reference lamps are not
# HPLs and nothing about a 575 applies to them; before the ASSUME_DEFAULT_LAMP
# split in October a 65Q reported 575 W "assumed — S4s are 575 unless noted",
# which is the error this must not reintroduce from the other direction.
for kind, want_in_note in [
    ("S4 36", "HPL 575 (MF 0.67)"),
    ("S4 26", "HPL 575 (MF 0.78)"),
    ("S4 19", "HPL 575 (MF 0.85)"),
    ("S4 50", "HPL 575 (MF 0.79)"),
    ("Altman Shakespeare 20", "GLC"),
    ("Altman 65Q Fresnel @spot", "BTN"),
    ("Lustr 36 EDLT", "LED Regulated Full"),
]:
    fc, note = ph.footcandles(kind, 20.0)
    ok(f"{kind} still answers", fc is not None and want_in_note in note, note)

print("\n⚠ the per-lens factors are why the number cannot simply be borrowed")
# ⭐ THIS IS THE REASON THIS ISSUE IS NOT FULLY CLOSED. The HPL 575 factor is a
# property of the LENS as well as the lamp, and the file says so: "one number
# for the family would be wrong for three of the four". An EDLT is a different
# optical train, so its factor is not the plain tube's of the same degree.
mf = ph.LAMP_MF["HPL 575"]
spread = max(mf[k] for k in ("S4 19", "S4 26", "S4 36", "S4 50")) - \
    min(mf[k] for k in ("S4 19", "S4 26", "S4 36", "S4 50"))
ok("the four barrels do NOT share a factor", spread > 0.15, f"0.67 to 0.85, spread {spread:.2f}")
ok("so no EDLT row may be invented from them",
   not any(k.endswith("EDLT") for k in mf), sorted(k for k in mf if "EDLT" in k) or "none, correctly")

print("\n⭐ and the two gates now agree")
# watts_for and footcandles were answering "is this a 575 fixture?" differently.
w, wnote = ph.watts_for("S4 36 EDLT")
ok("watts_for reads an EDLT as a 575", w == 575, f"{w} W — {wnote}")
_, fnote = ph.footcandles("S4 36 EDLT", 20.0)
ok("...and footcandles now agrees it should be one", "HPL 575" in fnote)

print()
if FAILS:
    for f in FAILS:
        print("FAILED:", f)
    sys.exit(1)
print("all passed")

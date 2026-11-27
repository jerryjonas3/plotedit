#!/usr/bin/env python3
"""Two gel codes may not normalise to one key, and a bare number names no filter.

    cd server && python3 test_gel_collision.py

#147: `gel_key` strips punctuation and case, and `load_gels` keys a plain dict
on the result — so a second row with the same key OVERWROTE the first in
silence. No error, no warning, and every plot using the losing filter would
carry the winner's transmission.

⚠ `R` is already four product lines in one letter — Roscolux 0-399, Storaro
2001-2009, Cinegel 3405-3411, Calcolor 4215-4590. They do not collide today,
and #147 is blunt that this is "luck, not design". The ranges most likely to be
added next are the ones that reuse low numbers.

⭐ THIS COVERS ONLY WHAT #147 PRE-APPROVES. The issue says the naming scheme
"should not be picked in a diff" and that a load-time check is "worth having
whatever is decided above". So: the check, and the correction to a message that
was factually wrong. No prefix is invented here and the issue stays open.
"""
import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plotedit import photometrics as ph        # noqa: E402

FAILS = []
HERE = os.path.dirname(os.path.abspath(__file__))


def check(label, got, want):
    ok_ = got == want
    print(f"  {'ok  ' if ok_ else 'FAIL'} {label:<54} {got}")
    if not ok_:
        FAILS.append(f"{label}: got {got!r}, wanted {want!r}")


def ok(label, cond, note=""):
    print(f"  {'ok  ' if cond else 'FAIL'} {label:<54} {note}")
    if not cond:
        FAILS.append(label)


def write_gels(rows):
    """A gels.csv holding exactly `rows`, for the guard to be pointed at."""
    fh = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    w = csv.writer(fh)
    w.writerow(["gel", "name", "transmission", "source", "added"])
    for r in rows:
        w.writerow(r)
    fh.close()
    return fh.name


print("✅ the shipped table is clean, which is the premise of the issue")
check("rows load", len(ph.GELS), 646)
with open(os.path.join(HERE, "plotedit", "gels.csv"), encoding="utf-8") as fh:
    raw = list(csv.DictReader(fh))
check("...and that is every row in the file, none lost to a clash", len(raw), 646)
check("every code normalises to its own key",
      len({ph.gel_key(r["gel"]) for r in raw}), 646)

print("\n🔴 AND THE GUARD ACTUALLY FIRES — a guard that cannot fire is worse than none")
# ⚠ Proven against a real collision rather than asserted. The pair below is
# exactly #147's hazard: two product lines reusing a low number, where the only
# difference is punctuation that gel_key strips.
path = write_gels([
    ["R26", "Light Red", "0.12", "test", "2026.11.27"],
    ["R-26", "Something Else Entirely", "0.80", "test", "2026.11.27"],
])
raised = None
try:
    ph.load_gels(path)
except ValueError as e:
    raised = str(e)
finally:
    os.unlink(path)
ok("a collision raises instead of overwriting", raised is not None)
ok("...and the message names BOTH codes", raised and "'R26'" in raised and "'R-26'" in raised)
ok("...and both filter names, so the loser is identifiable",
   raised and "Light Red" in raised and "Something Else Entirely" in raised)
ok("...and the key they collapsed to", raised and "'R26'" in raised)
ok("...and points at the issue", raised and "#147" in raised)

print("\n⚠ it is the KEY that must be distinct, not the written code")
# Different punctuation is the same filter — that is gel_key's whole job and it
# must keep working. The guard must not start rejecting legitimate rows.
path = write_gels([
    ["R26", "Light Red", "0.12", "test", "2026.11.27"],
    ["L201", "Full CT Blue", "0.36", "test", "2026.11.27"],
    ["G100", "Chocolate", "0.24", "test", "2026.11.27"],
])
try:
    loaded = ph.load_gels(path)
    ok("three distinct makers load fine", len(loaded) == 3, sorted(loaded))
except ValueError as e:
    ok("three distinct makers load fine", False, str(e))
finally:
    os.unlink(path)

print("\n⚠ the bare-number refusal was right; its REASON was wrong")
# #147: the old message "left GAM out altogether, equated R with Roscolux when R
# is also Calcolor, Cinegel and Storaro, and offered a two-way choice".
factor, note = ph.gel_factor("33")
check("a bare number still refuses to resolve", factor, None)
ok("the message now names all three makers",
   "R33" in note and "L33" in note and "G33" in note)
ok("...including GamColor, which it used to omit", "GamColor" in note)
ok("...and no longer claims R means Roscolux",
   "Roscolux" not in note, note[:60] + "...")
ok("...and says a number alone names no filter", "no filter" in note)

print("\n⭐ and a real code still resolves, punctuated or not")
ok("R33 resolves", ph.gel_factor("R33")[0] is not None, ph.gel_factor("R33")[1])
check("R-33 is the same filter", ph.gel_factor("R-33")[0], ph.gel_factor("R33")[0])
check("r33 is too", ph.gel_factor("r33")[0], ph.gel_factor("R33")[0])

print("\n⚠ the four Rosco ranges this issue is really about all still load")
# Not a fix — a record of the thing #147 says is luck. If a future range
# collides with one of these, the guard above is what will say so.
for code, line in [("R33", "Roscolux"), ("R2008", "Storaro"),
                   ("R3407", "Cinegel"), ("R4230", "Calcolor")]:
    ok(f"{code} ({line}) is present and distinct", ph.gel_key(code) in ph.GELS,
       ph.GELS.get(ph.gel_key(code), {}).get("name", "MISSING"))

print()
if FAILS:
    for f in FAILS:
        print("FAILED:", f)
    sys.exit(1)
print("all passed")

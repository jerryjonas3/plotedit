#!/usr/bin/env python3
"""Step 2 test: the read-only service answers, and refuses where it should.

    cd server && python3 test_api.py

Uses FastAPI's TestClient, so no server needs to be running.
"""
import sys

from fastapi.testclient import TestClient

from plotedit.api import app

client = TestClient(app)
FAILS = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<46} {got}")
    if not ok:
        FAILS.append(f"{label}: got {got!r}, wanted {want!r}")


print("health")
check("service answers", client.get("/health").json()["ok"], True)

print("\nfixtures — sources must survive the trip")
fx = client.get("/fixtures").json()
check("28 fixtures", fx["count"], 28)
check("Lustr key names its lens tube", "Lustr 26 EDLT" in fx["fixtures"], True)
check("source passed through", "EDLT" in fx["fixtures"]["Lustr 26 EDLT"]["source"], True)
check("LED penumbra is tiny", fx["fixtures"]["Lustr 26 EDLT"]["penumbra_deg"], 2.4)
check("tungsten penumbra is not", fx["fixtures"]["S4 26"]["penumbra_deg"], 7.0)

print("\ngels")
g = client.get("/gels").json()
check("11 gels", g["count"], 11)
check("R119 transmission", g["gels"]["R119"]["transmission"], 0.893)
check("notation explained", set(g["notation"]), {"+", "/"})

print("\ncompute — the values, and the refusals")
r = client.post("/compute", json={"instruments": [
    {"unit": 1, "type": "S4 26", "x": 6, "y": 20, "trim": 14,
     "focus_x": 10, "focus_y": 10, "color": "R52+R119", "lamp": "HPL 575"},
    {"unit": 2, "type": "S4 26", "x": 6, "y": 20},                       # no trim/focus
    {"unit": 3, "type": "Mystery Lantern", "x": 1, "y": 1, "trim": 14,
     "focus_x": 5, "focus_y": 5},                                        # unknown fixture
    {"unit": 4, "type": "S4 26", "x": 6, "y": 20, "trim": 14,
     "focus_x": 10, "focus_y": 10, "color": "L201", "lamp": "HPL 575"},  # unknown gel
]}).json()["instruments"]
check("acting-area wash", r[0]["footcandles"], 169)
check("throw", r[0]["throw_ft"], "13'-9\"")
check("no trim -> refuses, explains", r[1]["note"], "needs a trim height and a focus point")
check("unknown fixture -> refuses", r[2]["computed"], False)
check("unknown gel -> warns, does not guess", "open white" in r[3]["gel_warning"], True)
check("unknown gel -> open-white level", r[3]["footcandles"], 729)

print("\nwash")
w = client.post("/wash", json={"type": "S4 26", "throw": 14, "width": 24}).json()
check("field-to-beam spacing", w["spacing_ft"], "5'-4\"")
check("5 units cover 24 feet", w["row"]["count"], 5)
led = client.post("/wash", json={"type": "Lustr 26 EDLT", "throw": 14}).json()
check("LED penumbra is four inches", led["penumbra_ft"], "0'-4\"")
bad = client.post("/wash", json={"type": "SHEHDS 19", "throw": 14})
check("no beam figure -> 400, not a guess", bad.status_code, 400)

print("\nlens")
opts = client.get("/lens", params={"pool": 8, "throw": 17}).json()["options"]
check("26 deg is the closest to an 8ft pool", opts[0]["type"], "S4 26")

print()
if FAILS:
    print(f"{len(FAILS)} FAILED")
    for f in FAILS:
        print("   ", f)
    sys.exit(1)
print("all passed")

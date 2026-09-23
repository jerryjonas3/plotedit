#!/usr/bin/env python3
"""
Generate a USITT ASCII cue file that ETC Eos will actually import.

Format reverse-engineered from a real Eos 3.1.5 export (test.asc, 2026.08.28).
The three things that made earlier attempts fail:
  1. Cues must sit under a "$CueList n" header
  2. Labels are "Text" (Eos's own export proves it), NOT "$$Text".
     The $$Text in Eos's comment block applies only to cues outside cue list 1.
     Groups are "Group n", not "$Group n".
  3. Levels are hex with an H prefix: 1@Hd9, not 1@D9 or 1@85
Line endings are bare LF. Sub-records are indented three spaces.

Usage:  python3 make-eos-asc.py > out.asc
Edit SHOW, GROUPS and CUES below for a new production.
"""

SHOW = "Without Consent"

# name -> channel list
GROUPS = {
    "Study":     [1, 2, 3, 4],
    "Patio":     [5, 6, 7],
    "Threshold": [8],
    "Specials":  [9, 10],
}

# (cue number, label, up seconds, down seconds, {group name: percent})
CUES = [
    (1,  "Q1 p3 Lights rise - sunny study",             5,  5,  {"Study": 85, "Threshold": 15}),
    (2,  "Q2 p28 JUDITH opens doors - GESTURE CUE",     3,  3,  {"Study": 100, "Patio": 70, "Threshold": 80}),
    (3,  "Q3 p28 LISA steps onto patio",                3,  3,  {"Study": 100, "Patio": 100, "Threshold": 80}),
    (4,  "Q4 p29 LISA returns - doors close",           5,  5,  {"Study": 85, "Threshold": 15}),
    (5,  "Q5 p62 Pretend were there - imagined Victor", 10, 10, {"Study": 45, "Specials": 80}),
    (6,  "Q6 p64 I AM SPEAKING WITH MY HUSBAND",        4,  4,  {"Study": 30, "Specials": 100}),
    (7,  "Q7 p64 I killed our child - bottom",          3,  3,  {"Study": 20, "Specials": 100}),
    (8,  "Q8 p65 All clean - the reconnection",         10, 10, {"Study": 85, "Threshold": 15}),
    (9,  "Q9 p65 JUDITH rises - looks out",             5,  5,  {"Study": 85, "Threshold": 40}),
    (10, "Q10 p65 JUDITH opens doors again - GESTURE",  3,  3,  {"Study": 85, "Patio": 100, "Threshold": 90}),
    (11, "Q11 p65 They step onto patio - THE ENDING",   20, 20, {"Study": 20, "Patio": 100, "Threshold": 60}),
    (12, "Q12 p66 Let nature take its course - birds",  10, 10, {"Study": 10, "Patio": 60, "Threshold": 30}),
    (13, "Q13 p66 BLACK - projection out same count",   8,  8,  {}),
    (14, "Q14 Curtain call",                            2,  2,  {"Study": 100, "Patio": 100}),
]

def hx(pct):
    return "H" + format(round(pct * 255 / 100), "02x")

def chan_string(levels):
    out = {}
    for gname, pct in levels.items():
        for c in GROUPS[gname]:
            out[c] = pct
    return " ".join(f"{c}@{hx(p)}" for c, p in sorted(out.items()))

L = []
L += [
    "Ident 3:0",
    "Manufacturer ETC",
    "Console Eos",
    "$$Format 3.10",
    f"$$Title {SHOW}",
    "!",
    "! Cue structure only - no patch, no levels worth defending.",
    "! Import as MERGE so the existing patch survives.",
    "!",
]

for i, (name, chans) in enumerate(GROUPS.items(), start=1):
    L += [f"Group {i}", f"   Text {name}",
          "   Chan  " + " ".join(f"{c}@Hff" for c in chans), " "]

L += ["$CueList 1", " "]

for num, text, up, dn, levels in CUES:
    L += [f"Cue {num} 1", f"   Text {text}",
          f"   Up {up}", f"   $$TimeUp {up} 0 0 0",
          f"   Down {dn}", f"   $$TimeDown {dn} 0 0 0"]
    cs = chan_string(levels)
    if cs:
        L += [f"   $$ChanMove  {cs}", f"   Chan  {cs}"]
    L += [" "]

L += ["Enddata"]
print("\n".join(L))

#!/usr/bin/env python3
"""
photometrics.py — throw, angle, pool and light level for every unit on the plot.

All distances in FEET. Angles in degrees. Illuminance in footcandles.

    from photometrics import FIXTURES, aim, pool, footcandles, lens_for, overlap

    a = aim(unit=(6, 20, 14), target=(10, 10, 5.5))
    # -> {'throw': 16.9, 'elevation': 30.2, 'pan': -68.2, 'horizontal': 14.6, 'drop': 8.5}
    pool("S4 26", a["throw"])          # field and beam diameter at the target
    footcandles("S4 26", a["throw"], lamp="HPL 575")
    lens_for(8.0, a["throw"])          # which Source Four barrel gives an 8' field pool at that throw

Sources: every fixture row says where its numbers came from. Candela figures
marked 'derived' were back-calculated from the datasheet's own fc-at-distance
table (fc x d^2), which agreed to within 1% across the four distances given.
Anything without a source is not in the table.
"""
import math
import re

# Field/beam angles and centre-beam candela at the reference lamp.
# cd is at HPL 750W/115V unless noted. Use LAMP_MF to convert.
FIXTURES = {
    "S4 19":  dict(field=18.0, beam=15.0, cd=245000, ref_lamp="HPL 750", family="S4",
                   source="ETC Source Four 19° datasheet 7060L1007 vG (cd derived from fc table: 392fc@25'). ⚠ ETC Europe Beam Spread Table 2000-11-13 gives 14/17 (beam/field) for the same tube — older data, likely an earlier lens revision. The modern US datasheet is preferred; the difference matters most on the 36°"),
    "S4 26":  dict(field=25.0, beam=18.0, cd=176000, ref_lamp="HPL 750", family="S4",
                   source="ETC Source Four 26° datasheet (cd derived from fc table: 783fc@15'). ⚠ ETC Europe Beam Spread Table 2000-11-13 gives 17/24 (beam/field) for the same tube — older data, likely an earlier lens revision. The modern US datasheet is preferred; the difference matters most on the 36°"),
    "S4 36":  dict(field=34.0, beam=27.0, cd=90885, ref_lamp="HPL 750", family="S4",
                   source="ETC Source Four 36° datasheet (cosine table: 90,885 cd). ⚠ ETC Europe Beam Spread Table 2000-11-13 gives 23/33 (beam/field) for the same tube — older data, likely an earlier lens revision. The modern US datasheet is preferred; the difference matters most on the 36°"),
    "S4 50":  dict(field=50.0, beam=36.0, cd=45650, ref_lamp="HPL 750", family="S4",
                   source="ETC Source Four 50° datasheet 7060L1010 (cosine table: 45,650 cd; fc table agrees: 457fc@10')"),
    "S4 90":  dict(field=86.6, beam=79.0, cd=None, ref_lamp="HPL 750", family="S4",
                   source="ETC Source Four 90° datasheet (angles); candela not extracted"),
    # Standard lens tubes the modern US datasheets do not cover — from the ETC Europe
    # "Source Four Beam Spread Table", data issued 13-11-2000 (on file). Angles only;
    # that table carries no candela. Internally consistent: every published multiplier
    # matches 2*tan(angle/2) to within a rounding step.
    "S4 5":   dict(field=7.0, beam=5.0, cd=None, ref_lamp="HPL 750", family="S4",
                   source="ETC Europe Beam Spread Table 2000-11-13 (angles only, no candela)"),
    "S4 10":  dict(field=11.0, beam=8.0, cd=None, ref_lamp="HPL 750", family="S4",
                   source="ETC Europe Beam Spread Table 2000-11-13 (angles only, no candela)"),
    # Zooms, at the three focus positions the table gives.
    "S4 Zoom 15-30 @15": dict(field=17.0, beam=12.0, cd=None, ref_lamp="HPL 750", family="S4 Zoom",
                   source="ETC Europe Beam Spread Table 2000-11-13"),
    "S4 Zoom 15-30 @23": dict(field=23.0, beam=16.0, cd=None, ref_lamp="HPL 750", family="S4 Zoom",
                   source="ETC Europe Beam Spread Table 2000-11-13"),
    "S4 Zoom 15-30 @30": dict(field=31.0, beam=22.0, cd=None, ref_lamp="HPL 750", family="S4 Zoom",
                   source="ETC Europe Beam Spread Table 2000-11-13"),
    "S4 Zoom 25-50 @25": dict(field=27.0, beam=19.0, cd=None, ref_lamp="HPL 750", family="S4 Zoom",
                   source="ETC Europe Beam Spread Table 2000-11-13"),
    "S4 Zoom 25-50 @36": dict(field=37.0, beam=26.0, cd=None, ref_lamp="HPL 750", family="S4 Zoom",
                   source="ETC Europe Beam Spread Table 2000-11-13"),
    "S4 Zoom 25-50 @50": dict(field=49.0, beam=35.0, cd=None, ref_lamp="HPL 750", family="S4 Zoom",
                   source="ETC Europe Beam Spread Table 2000-11-13"),
    # PARNel and EA PAR are OVAL — the table gives a second axis for the EA PAR
    # (MFL 32/19 across, 23/13 the other way; WFL 48/27 across, 31/17 the other way).
    # Only the wide axis is stored; rotate the lens and the narrow axis applies.
    "S4 PARNel @25": dict(field=26.0, beam=12.0, cd=None, ref_lamp="HPL 750", family="S4 PAR",
                   source="ETC Europe Beam Spread Table 2000-11-13 (oval beam; wide axis)"),
    "S4 PARNel @45": dict(field=47.0, beam=29.0, cd=None, ref_lamp="HPL 750", family="S4 PAR",
                   source="ETC Europe Beam Spread Table 2000-11-13 (oval beam; wide axis)"),
    "S4 EA PAR VNSP": dict(field=18.0, beam=11.0, cd=None, ref_lamp="HPL 750", family="S4 PAR",
                   source="ETC Europe Beam Spread Table 2000-11-13"),
    "S4 EA PAR NSP": dict(field=19.0, beam=11.0, cd=None, ref_lamp="HPL 750", family="S4 PAR",
                   source="ETC Europe Beam Spread Table 2000-11-13"),
    "S4 EA PAR MFL": dict(field=32.0, beam=19.0, cd=None, ref_lamp="HPL 750", family="S4 PAR",
                   source="ETC Europe Beam Spread Table 2000-11-13 (oval; narrow axis 23/13)"),
    "S4 EA PAR WFL": dict(field=48.0, beam=27.0, cd=None, ref_lamp="HPL 750", family="S4 PAR",
                   source="ETC Europe Beam Spread Table 2000-11-13 (oval; narrow axis 31/17)"),

    "S4 26 EDLT": dict(field=25.0, beam=17.0, cd=182301, ref_lamp="HPL 750", family="S4 EDLT",
                   source="ETC EDLT datasheet: 182,301 cd, field mult .45"),
    "S4 36 EDLT": dict(field=34.0, beam=22.0, cd=98553, ref_lamp="HPL 750", family="S4 EDLT",
                   source="ETC EDLT datasheet: 98,553 cd, field mult .61"),
    # ETC Source Four LED Series 2 Lustr — from the Source Four LED Photometry Guide (74 pp, on file).
    #
    # ⚠ ETC PUBLISHES 19/26/36 ONLY AS EDLT. Across every array (Lustr, Daylight HD, Tungsten HD,
    # Studio HD) the guide's standard-tube entries are 5°, 10°, 14°, 70°, 90°, the 50° LT and the
    # zooms. There is NO published standard-tube data for the three angles that actually get hung,
    # and EDLT tubes are a premium option almost nobody specifies. The keys below say EDLT so
    # nothing is mistaken for a house fixture. A standard tube will read somewhat lower in candela.
    # If a job turns on it, ask ETC or meter the unit — do not interpolate.
    #
    # cd is "Regulated Full" (all emitters, consistent output); 'modes' has the others.
    # Regulated 3200K is the tungsten-look number to compare against an HPL. Boost is not
    # sustainable output.
    "Lustr 19 EDLT": dict(field=19.1, beam=18.6, cd=97163, ref_lamp="LED Regulated Full", family="Lustr",
                   modes={"Boost Full": 104518, "Regulated Full": 97163, "Regulated 3200K": 84221, "Regulated 5600K": 59774},
                   source="ETC S4 LED Photometry Guide p6: Series 2 Lustr 19° EDLT"),
    "Lustr 26 EDLT": dict(field=27.7, beam=25.3, cd=61792, ref_lamp="LED Regulated Full", family="Lustr",
                   modes={"Boost Full": 66470, "Regulated Full": 61792, "Regulated 3200K": 53561, "Regulated 5600K": 38014},
                   source="ETC S4 LED Photometry Guide p7: Series 2 Lustr 26° EDLT"),
    "Lustr 36 EDLT": dict(field=34.8, beam=33.0, cd=40058, ref_lamp="LED Regulated Full", family="Lustr",
                   modes={"Boost Full": 43091, "Regulated Full": 40058, "Regulated 3200K": 34723, "Regulated 5600K": 24644},
                   source="ETC S4 LED Photometry Guide p7: Series 2 Lustr 36° EDLT"),
    "Lustr 50 LT": dict(field=50.1, beam=48.6, cd=18090, ref_lamp="LED Regulated Full", family="Lustr",
                   modes={"Boost Full": 19460, "Regulated Full": 18090, "Regulated 3200K": 15681, "Regulated 5600K": 11129},
                   source="ETC S4 LED Photometry Guide p8: Series 2 Lustr LED 50° LT"),
    "Lustr 14": dict(field=15.4, beam=14.8, cd=156611, ref_lamp="LED Regulated Full", family="Lustr",
                   modes={"Boost Full": 168466, "Regulated Full": 156611, "Regulated 3200K": 135750, "Regulated 5600K": 96347},
                   source="ETC S4 LED Photometry Guide p6: Series 2 Lustr 14°"),
    "Lustr 70": dict(field=70.4, beam=65.0, cd=10909, ref_lamp="LED Regulated Full", family="Lustr",
                   modes={"Boost Full": 11735, "Regulated Full": 10909, "Regulated 3200K": 9456, "Regulated 5600K": 6712},
                   source="ETC S4 LED Photometry Guide p8: Series 2 Lustr 70°"),
    "SHEHDS 19": dict(field=19.0, beam=None, cd=None, ref_lamp="LED 350W", family="LED",
                   source="SHEHDS 350W RGBW Profile manual: 'Beam Angle 19°'. No output data published — measure it."),
}

# Candela multiplying factors from the ETC lamp tables (per barrel, 300-hr lamps).
LAMP_MF = {
    "HPL 750": {"S4 19": 1.00, "S4 26": 1.00, "S4 36": 1.00, "S4 50": 1.00},
    "HPL 575": {"S4 19": 0.85, "S4 26": 0.78, "S4 36": 0.67, "S4 50": 0.79},
    "HPL 575X": {"S4 36": 0.56},          # long-life; others not extracted
}

FIELD_ANGLES_S4 = [5, 10, 14, 19, 26, 36, 50, 70, 90]   # the barrel family, nominal


def aim(unit, target):
    """unit=(x, y, trim_ft), target=(x, y, height_ft). Returns throw, elevation, pan, horizontal, drop."""
    ux, uy, uz = unit; tx, ty, tz = target
    dx, dy, dz = tx - ux, ty - uy, uz - tz
    horiz = math.hypot(dx, dy)
    throw = math.hypot(horiz, dz)
    elevation = math.degrees(math.atan2(dz, horiz)) if horiz else 90.0   # 0 = level, 90 = straight down
    pan = math.degrees(math.atan2(dx, -dy))     # 0 = pointing "downstage" (-y), +ve = clockwise
    return dict(throw=throw, elevation=elevation, pan=pan, horizontal=horiz, drop=dz)


def diameter(throw, angle_deg):
    """Circle of light at right angles to the beam, for a given cone angle."""
    return 2 * throw * math.tan(math.radians(angle_deg) / 2)


def pool(kind, throw, elevation=None):
    """Field and beam diameter at the throw distance. With elevation, also the
    stretched length of the pool on a horizontal deck (the ellipse's long axis)."""
    f = FIXTURES[kind]
    out = dict(field=diameter(throw, f["field"]) if f["field"] else None,
               beam=diameter(throw, f["beam"]) if f["beam"] else None)
    if elevation is not None and f["field"]:
        e = math.radians(elevation); half = math.radians(f["field"]) / 2
        drop = throw * math.sin(e)                       # height of the unit above the target plane
        # where the near and far edges of the cone meet that plane, measured horizontally
        near = drop / math.tan(min(e + half, math.pi / 2 - 1e-6))
        far = drop / math.tan(e - half) if e - half > 0.01 else None   # shallow beam never lands
        out["on_deck_length"] = (far - near) if far is not None else None
    return out


def load_gels(path=None):
    """gels.csv beside this file: gel, name, transmission (0-1), source, added. Add rows as gels come up."""
    import csv, os
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "gels.csv")
    out = {}
    with open(path) as fh:
        for row in csv.DictReader(fh):
            out[row["gel"].upper()] = dict(name=row["name"], t=float(row["transmission"]), source=row["source"])
    return out

GELS = load_gels()


def parse_gel(gel):
    """Read Jerry's color notation. Two separators, two different physical things:

        "R52+R119"  PLUS  = stacked, one gel on top of another in the same frame.
                            Transmissions MULTIPLY.
        "R52/R119"  SLASH = a split frame — two gels cut diagonally and put in
                            together, so each covers part of the beam. They do NOT
                            multiply; each half has its own transmission.

    Returns (kind, [gel names]) where kind is "stacked" or "split".
    A list or tuple is treated as stacked, which is what a frame usually holds.
    """
    if isinstance(gel, (list, tuple)):
        return "stacked", [str(g).strip() for g in gel]
    g = str(gel).strip()
    if "/" in g:
        return "split", [x.strip() for x in g.split("/") if x.strip()]
    return "stacked", [x.strip() for x in re.split(r"[+,]", g) if x.strip()]


def gel_factor(gel):
    """Transmission for a color string or list. Returns (factor, note).

    Stacked gels multiply. A SPLIT frame has no single factor — it returns the
    factor for the FIRST gel named and says so, because the beam is not uniform.
    Unknown gel -> (None, note) rather than a guess."""
    if not gel:
        return 1.0, ""
    kind, gels = parse_gel(gel)
    rows = []
    for g in gels:
        row = GELS.get(g.upper())
        if row is None:
            return None, f"gel {g} not in gels.csv — add it with Rosco's transmission figure"
        rows.append((g.upper(), row["t"]))
    if kind == "split":
        first = rows[0]
        others = ", ".join(f"{n} {t*100:.0f}%" for n, t in rows[1:])
        return first[1], (f"SPLIT FRAME — {first[0]} {first[1]*100:.0f}% on this part of the beam; "
                          f"{others} on the rest. No single level covers the whole pool")
    factor = 1.0
    for _, t in rows:
        factor *= t
    return factor, " + ".join(f"{n} {t*100:.0f}%" for n, t in rows)


def footcandles(kind, throw, lamp=None, mode=None, gel=None):
    """Centre-beam illuminance = candela / throw², times gel transmission. Returns (fc, note).
    lamp: an HPL lamp for tungsten fixtures. mode: an output mode for LED fixtures with 'modes'.
    gel: a Rosco number or a list of them. Transmission figures are Rosco's, measured for a
    broadband (tungsten) source — exact for HPL, approximate on a white LED."""
    f = FIXTURES[kind]
    gf, gnote = gel_factor(gel)
    if gf is None: return None, gnote
    if gel and f["family"] not in ("S4", "S4 EDLT"):
        gnote += " (transmission is a tungsten figure; approximate on LED)"
    fc, note = _footcandles_white(f, kind, throw, lamp, mode)
    if fc is None: return None, note
    return fc * gf, (note + (f", through {gnote}" if gel else ""))


def _footcandles_white(f, kind, throw, lamp, mode):
    if mode and f.get("modes"):
        if mode not in f["modes"]:
            return None, f"{kind} has no mode '{mode}'; has {list(f['modes'])}"
        return f["modes"][mode] / throw ** 2, f"at {mode}"
    if not f["cd"]:
        return None, f"no candela on file for {kind} — {f['source']}"
    mf = 1.0; note = f"at {f['ref_lamp']}"
    if lamp and lamp != f["ref_lamp"]:
        mf = LAMP_MF.get(lamp, {}).get(kind)
        if mf is None:
            return None, f"no {lamp} multiplier on file for {kind}"
        note = f"at {lamp} (MF {mf})"
    return f["cd"] * mf / throw ** 2, note


def lens_for(pool_ft, throw, family="S4", use="field"):
    """Which barrel gives a pool of this size at this throw. Returns sorted (kind, diameter, error)."""
    rows = []
    for k, f in FIXTURES.items():
        if f["family"] != family or not f[use]: continue
        d = diameter(throw, f[use]); rows.append((k, d, d - pool_ft))
    return sorted(rows, key=lambda r: abs(r[2]))


def overlap(units, kind_key="kind", height=5.5):
    """Given units as dicts with x, y, trim, focus (x,y) and kind: do adjacent field
    pools meet at `height`? Returns list of (unit_a, unit_b, gap_ft) — negative gap = overlap."""
    pools = []
    for u in units:
        a = aim((u["x"], u["y"], u["trim"]), (u["focus"][0], u["focus"][1], height))
        r = pool(u[kind_key], a["throw"])["field"] / 2
        pools.append((u, u["focus"][0], u["focus"][1], r))
    out = []
    for i in range(len(pools)):
        for j in range(i + 1, len(pools)):
            (ua, xa, ya, ra), (ub, xb, yb, rb) = pools[i], pools[j]
            gap = math.hypot(xa - xb, ya - yb) - (ra + rb)
            out.append((ua.get("num", i + 1), ub.get("num", j + 1), gap))
    return out


def wash_spacing(kind, throw, rule="field-to-beam"):
    """On-centre spacing for units in a wash, at the throw distance.

    Rules, all measured at the target plane:
      "field-to-beam"  (the usual practice) — each unit's FIELD edge lands on the
                       next unit's BEAM edge, so the overlap zone sits between the
                       two beams:  F{ (B) F{ } (B) }.  d = Rfield + Rbeam
      "beam-to-beam"   — beam edges just touch. Tighter, brighter, very even. d = 2*Rbeam
      "field-to-field" — field edges just touch. Widest; leaves a dim scallop
                       between pools because both units are at 10% there. d = 2*Rfield

    Returns dict with the spacing, the two radii, and the overlap width.
    """
    f = FIXTURES[kind]
    if not f["field"] or not f["beam"]:
        raise ValueError(f"{kind} has no beam/field pair on file — {f['source']}")
    rf = diameter(throw, f["field"]) / 2
    rb = diameter(throw, f["beam"]) / 2
    d = {"field-to-beam": rf + rb, "beam-to-beam": 2 * rb, "field-to-field": 2 * rf}[rule]
    return dict(spacing=d, field_r=rf, beam_r=rb, overlap=max(0.0, 2 * rf - d),
                penumbra=rf - rb, rule=rule)


def wash_row(kind, throw, width, rule="field-to-beam"):
    """How many units to cover `width` feet of acting area, and where they sit.

    Returns (count, spacing, positions) with positions centred on the width.
    Count is rounded up, then the spacing is eased back so the row fits evenly.
    """
    import math
    w = wash_spacing(kind, throw, rule)
    covered = width - 2 * w["beam_r"]              # first and last units light their own beam out to the edge
    n = max(1, int(math.ceil(covered / w["spacing"])) + 1)
    actual = covered / (n - 1) if n > 1 else 0.0
    start = -(width / 2) + w["beam_r"]
    return dict(count=n, spacing=actual, ideal=w["spacing"], positions=[start + i * actual for i in range(n)],
                penumbra=w["penumbra"], rule=rule)


def fmt_ft(x):
    """12.5 -> 12'-6\" """
    if x is None: return "—"
    whole = int(x); inches = round((x - whole) * 12)
    if inches == 12: whole, inches = whole + 1, 0
    return f"{whole}'-{inches}\""


def report(kind, unit, target, lamp=None, mode=None, gel=None):
    """One unit, all the numbers, as text."""
    a = aim(unit, target); p = pool(kind, a["throw"], a["elevation"]); fc, note = footcandles(kind, a["throw"], lamp, mode, gel)
    lines = [f"{kind}: throw {fmt_ft(a['throw'])}, elevation {a['elevation']:.0f}°, pan {a['pan']:+.0f}°",
             f"  field {fmt_ft(p['field'])} / beam {fmt_ft(p['beam'])} across"
             + (f", {fmt_ft(p['on_deck_length'])} long on the deck" if p.get("on_deck_length") else "")]
    lines.append(f"  {fc:.0f} fc centre beam {note}" if fc else f"  light level: {note}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report("S4 26", (6, 20, 14), (10, 10, 5.5), lamp="HPL 575"))
    print(report("S4 36", (16.5, 20, 14), (16.5, 10, 5.5), lamp="HPL 575"))
    print(report("SHEHDS 19", (27, 20, 14), (22, 10, 5.5)))
    print("8' pool at 17' throw:", [(k, round(d, 1)) for k, d, e in lens_for(8, 17)[:3]])

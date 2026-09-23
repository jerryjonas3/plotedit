#!/usr/bin/env python3
"""
paperwork.py — read Jerry's existing lighting paperwork.

Three formats, three levels of completeness:

  .xml   Vectorworks <-> Lightwright exchange (SLData). FULL instrument
         schedule: position, unit, channel, dimmer, address, color, purpose,
         type, wattage, gobo, focus, throw, field/beam angle. This is the good one.

  .lw6   Lightwright 6 show file. A ZIP with a 4-byte "JMCK" magic on the front
         (John McKernon). Inside: ShowFile (proprietary LWFORMAT V6-64 value
         stream), a user folder, and HistoryDB.lwdb (plain SQLite, revision
         history). The per-instrument rows are not decoded — that needs real
         reverse engineering, or a CSV export from Lightwright. What IS read is
         the show's VOCABULARY: every color, instrument type, position and
         purpose the show used. For learning conventions that is the useful half.

  .xlsx  Lightwright worksheet export (File > Export, or the Worksheet print).
         FULL instrument rows, and the easiest route out of Lightwright — no
         reverse engineering needed. Four title lines, then a header row
         (Pos, Unit#, Inst Type, Load, Purp, Color, Gobo, Chan, Addr, Dim...),
         then the data. Column order varies with the Lightwright view that was
         exported, so the header row is found and read rather than assumed.
         .xls (the old binary format) needs `pip install xlrd`.

  .vwx   Vectorworks drawing. Closed binary, not readable. Nothing here opens it.
         Export the .xml from Vectorworks instead (it usually sits beside it).

    from paperwork import read_vw_xml, read_lw6, profile
    recs, meta = read_vw_xml("Matilda_v3_2019_lights.xml")
    profile(["~/Documents"])            # conventions across every file found
"""
import collections
import glob
import os
import re
import xml.etree.ElementTree as ET
import zipfile

# ---------------------------------------------------------------- Vectorworks XML

def read_vw_xml(path):
    """Full instrument schedule from a Vectorworks/Lightwright SLData export.
    Returns (records, meta) — records are dicts with only the non-empty fields."""
    root = ET.parse(os.path.expanduser(path)).getroot()
    data = root.find("InstrumentData")
    if data is None:
        return [], {"path": path, "error": "no InstrumentData element"}
    recs = []
    for rec in data:
        d = {c.tag: (c.text or "").strip() for c in rec if (c.text or "").strip()}
        if d:
            recs.append(d)
    meta = {"path": path, "count": len(recs), "format": "Vectorworks SLData XML"}
    stamp = root.find(".//TimeStamp")
    if stamp is not None and stamp.text:
        meta["exported"] = stamp.text.strip()
    return recs, meta


# ---------------------------------------------------------------- Lightwright 6

LW6_MAGIC = b"JMCK"

def lw6_zip(path):
    """A .lw6 is a ZIP behind a 4-byte magic. Returns an open ZipFile."""
    import io
    raw = open(os.path.expanduser(path), "rb").read()
    if raw[:4] != LW6_MAGIC:
        raise ValueError(f"{path}: not a Lightwright 6 file (magic {raw[:4]!r})")
    return zipfile.ZipFile(io.BytesIO(raw[4:]))


def _lw6_field(text, name):
    m = re.search(r"\*!\*->" + re.escape(name) + r":\r\n([^\r\n]*)", text)
    return m.group(1) if m else None


# A pick-list entry in the ShowFile is written value / value-again / "True".
_TRIPLE = re.compile(r"(?:^|\r\n)([^\r\n]{1,48})\r\n\1\r\nTrue(?=\r\n)")

_RE_COLOR = re.compile(r"^(N/C|NC|[RLGA]\d{2,4}([+/,][RLGA]?\d{2,4})*)$", re.I)
_RE_TYPE = re.compile(
    r"Source ?4|S4-|Altman|Strand|Leko|Fresnel|\bPARs?\b|PARNel|\bETC\b|Cyc|ADJ|Chauvet|"
    r"Martin|Mac Aura|Blizzard|ColorSource|Clr ?Src|Elation|Robe|Vari.?Lite|4WRD|"
    r"Mega ?(Tri|Par)|\d+ ?deg\b|\d+°", re.I)
_RE_POS = re.compile(
    r"^(SR|SL|US|DS|IN|Grid|Box|Balc|Cove|Elec(t|tric)?|FOH|Pipe|Truss|Floor|Torm|"
    r"Cat|House [LR]|Boom|Ladder|Deck|Apron|Bridge|Rail|Ground ?row)\b", re.I)
_RE_JUNK = re.compile(r"^(C-Clamp|Design Layer|Lighting-|None|main|NIL|True|False|\d+)$", re.I)


def _classify_one(x):
    """Which vocabulary list does one entry belong to? None = ignore it."""
    x = x.strip()
    if not x or _RE_JUNK.match(x):
        return None
    if _RE_COLOR.match(x):
        return "colors"
    if _RE_TYPE.search(x):
        return "instrument_types"
    if _RE_POS.match(x):
        return "positions"
    return "purposes"


def _classify(values):
    """Kept for the profile path: name a cluster by its majority, else per item."""
    kinds = [(_classify_one(v), v) for v in values]
    kinds = [(k, v) for k, v in kinds if k]
    if not kinds:
        return None, []
    top = collections.Counter(k for k, _ in kinds).most_common(1)[0]
    if top[1] >= len(kinds) * 0.8:
        return top[0], [v for k, v in kinds]
    return None, []


def read_lw6(path):
    """Metadata + vocabulary from a Lightwright 6 file. See the module docstring
    for why the instrument rows are not included."""
    z = lw6_zip(path)
    names = z.namelist()
    out = {"path": path, "format": "Lightwright 6 (zip behind JMCK magic)", "members": names}
    if "ShowFile" not in names:
        return out
    t = z.read("ShowFile").decode("latin-1")
    out["lw_format"] = t.split("\r\n", 1)[0]
    for f in ("CreatedBy", "SavedBy", "SerialNumber", "FileDateStr", "FileTimeStr"):
        v = _lw6_field(t, f)
        if v:
            out[f] = v
    # cluster the pick-list triples by position in the file
    hits = [(m.start(), m.group(1)) for m in _TRIPLE.finditer(t)]
    clusters, cur, last = [], [], None
    for p, v in hits:
        if last is not None and p - last > 400:
            clusters.append(cur); cur = []
        cur.append(v); last = p
    clusters.append(cur)
    vocab = collections.defaultdict(list)
    for c in clusters:
        for x in c:
            k = _classify_one(x)
            if k:
                vocab[k].append(x)
    out["vocabulary"] = {k: sorted(set(v), key=v.index) for k, v in vocab.items()}
    return out


def lw6_history(path, out_dir=None):
    """Extract HistoryDB.lwdb (plain SQLite) so it can be queried. Returns the path."""
    z = lw6_zip(path)
    if "HistoryDB.lwdb" not in z.namelist():
        return None
    out_dir = out_dir or "."
    dest = os.path.join(out_dir, os.path.basename(path) + ".history.sqlite")
    open(dest, "wb").write(z.read("HistoryDB.lwdb"))
    return dest


# ---------------------------------------------------------------- Lightwright XLSX

# Lightwright's short column names -> the names used everywhere else here.
LW_COLUMNS = {
    "pos": "Position", "position": "Position",
    "unit#": "Unit_Number", "unit": "Unit_Number", "u#": "Unit_Number",
    "inst type": "Instrument_Type", "instrument type": "Instrument_Type", "type": "Instrument_Type",
    "load": "Wattage", "wattage": "Wattage",
    "purp": "Purpose", "pur": "Purpose", "purpose": "Purpose",
    "color": "Color", "colour": "Color", "clr": "Color",
    "gobo": "Gobo_1", "gbo": "Gobo_1",
    "chan": "Channel", "ch": "Channel", "channel": "Channel",
    "addr": "Address", "adr": "Address", "address": "Address",
    "dim": "Dimmer", "dm": "Dimmer", "dimmer": "Dimmer",
    "access": "Accessory", "acc": "Accessory", "accessory": "Accessory",
    "ckt name": "Circuit_Name", "ckt": "Circuit_Number", "circuit name": "Circuit_Name",
    "univ": "Universe", "universe": "Universe",
    "frame": "Frame_Size", "wt": "Weight",
}

def read_lw_xlsx(path, sheet=None):
    """Full instrument rows from a Lightwright worksheet export.

    Finds the header row rather than assuming it — Lightwright writes a few
    title lines first, and the column order follows whichever view was exported.
    Returns (records, meta)."""
    import openpyxl
    path = os.path.expanduser(path)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb[wb.sheetnames[0]]
    rows = [[("" if c is None else str(c)).strip() for c in r]
            for r in ws.iter_rows(values_only=True)]
    title = [r[0] for r in rows[:4] if r and r[0]]
    # the header row is the first with 3+ cells that are known Lightwright columns
    hdr_i, header = None, None
    for i, r in enumerate(rows[:40]):
        known = sum(1 for c in r if c.lower() in LW_COLUMNS)
        if known >= 3:
            hdr_i, header = i, r
            break
    if hdr_i is None:
        return [], {"path": path, "error": "no Lightwright header row found",
                    "first_rows": rows[:6]}
    cols = [LW_COLUMNS.get(c.lower(), c) for c in header]
    recs = []
    for r in rows[hdr_i + 1:]:
        d = {cols[i]: v for i, v in enumerate(r) if i < len(cols) and v and cols[i]}
        # skip repeated headers and subtotal/blank lines
        if d and d.get("Position", "").lower() not in ("pos", "position"):
            recs.append(d)
    return recs, {"path": path, "count": len(recs), "format": "Lightwright XLSX worksheet",
                  "title": title, "columns": [c for c in cols if c]}


# ---------------------------------------------------------------- the profile

def find_paperwork(roots, recursive=False):
    """Every .xml (SLData only), .lw6, .xlsx and .vwx in the given folders.
    Shallow by default — recursive=True over a big folder is slow."""
    found = {"xml": [], "lw6": [], "vwx": [], "xlsx": []}
    for root in roots:
        root = os.path.expanduser(root)
        pattern = os.path.join(root, "**", "*") if recursive else os.path.join(root, "*")
        for p in glob.glob(pattern, recursive=recursive):
            ext = os.path.splitext(p)[1].lower()
            if ext == ".lw6":
                found["lw6"].append(p)
            elif ext == ".vwx":
                found["vwx"].append(p)
            elif ext in (".xlsx", ".xls"):
                try:
                    if re.search(r"lightwright|lw\b|_lw|worksheet", os.path.basename(p), re.I) \
                       or ext == ".xlsx":
                        found.setdefault("xlsx", []).append(p)
                except OSError:
                    pass
            elif ext == ".xml":
                try:
                    if open(p, "rb").read(400).find(b"SLData") > -1:
                        found["xml"].append(p)
                except OSError:
                    pass
    return found


def profile(roots, recursive=False):
    """Read everything findable and report the conventions across all of it."""
    found = find_paperwork(roots, recursive=recursive)
    tally = {k: collections.Counter() for k in
             ("Color", "Instrument_Type", "Position", "Purpose", "Wattage")}
    shows, total = [], 0
    for p in found["xml"]:
        try:
            recs, meta = read_vw_xml(p)
        except ET.ParseError:
            continue
        if not recs:
            continue
        shows.append((os.path.basename(p), len(recs), "xml"))
        total += len(recs)
        for r in recs:
            for field in tally:
                v = r.get(field, "").strip()
                if v:
                    tally[field][v] += 1
    for p in found.get("xlsx", []):
        try:
            recs, meta = read_lw_xlsx(p)
        except Exception:
            continue
        if not recs:
            continue
        shows.append((os.path.basename(p), len(recs), "Lightwright xlsx"))
        total += len(recs)
        for r in recs:
            for field in tally:
                v = r.get(field, "").strip()
                if v:
                    tally[field][v] += 1
    for p in found["lw6"]:
        try:
            d = read_lw6(p)
        except (ValueError, zipfile.BadZipFile):
            continue
        v = d.get("vocabulary", {})
        shows.append((os.path.basename(p), sum(len(x) for x in v.values()), "lw6 vocabulary"))
        for key, field in (("colors", "Color"), ("instrument_types", "Instrument_Type"),
                           ("positions", "Position"), ("purposes", "Purpose")):
            for item in v.get(key, []):
                tally[field][item] += 0          # seen, but not an instrument count
                tally[field][item] += 1
    return {"shows": shows, "instruments": total, "tally": tally,
            "unreadable_vwx": len(found["vwx"])}


if __name__ == "__main__":
    import sys, json
    roots = sys.argv[1:] or ["~/Documents"]
    p = profile(roots)
    print(f"{len(p['shows'])} files read, {p['instruments']} instruments, "
          f"{p['unreadable_vwx']} .vwx skipped (closed format)\n")
    for field, c in p["tally"].items():
        if not c:
            continue
        print(f"== {field} — {len(c)} distinct")
        for k, v in c.most_common(15):
            print(f"   {v:>5}  {k}")
        print()

#!/usr/bin/env python3
"""
dxf_bridge.py — DXF in and out for scaled_pdf.Sheet.

IN:  a venue's exported .dxf (from Vectorworks, AutoCAD, whatever) becomes the
     base drawing under the plot, in real feet, on the right sheet at the
     right scale — no Vectorworks licence needed.

     dxf_info("bluver.dxf")                       # units, layers, extents — read this first
     s.import_dxf("bluver.dxf", layers=["WALLS","GRID"], units="in")

     Units come from the file's $INSUNITS header; override with units= when
     the header is missing or wrong (it often is). Sanity-check against one
     dimension you know: if the room should be 33' wide and the extents say
     396, the file is in inches.

OUT: everything drawn on a Sheet is also written to a DXF in feet, layered
     (BASE, POSITIONS, UNITS, TEXT, DIMS), for the month Vectorworks is rented
     or for anyone who wants the geometry rather than the picture.

     s = Sheet("plan.pdf", ..., dxf="plan.dxf")   # opt in per sheet
     s.finish()                                    # writes both

Only geometry crosses the bridge. Symbols come out as their outlines, not as
Spotlight symbols; swap them in Vectorworks if it matters.
"""
import math
import ezdxf
from ezdxf import units as dxf_units

# $INSUNITS code -> feet per drawing unit
UNIT_FT = {1: 1/12, 2: 1.0, 3: 5280.0, 4: 1/304.8, 5: 1/30.48, 6: 1/0.3048, 14: 1/3.048}
UNIT_NAME = {1: "inches", 2: "feet", 3: "miles", 4: "mm", 5: "cm", 6: "metres", 14: "decimetres", 0: "unitless"}
UNIT_ARG = {"in": 1, "inch": 1, "inches": 1, "ft": 2, "feet": 2, "mm": 4, "cm": 5, "m": 6, "metres": 6, "meters": 6}


def _scale_for(doc, units):
    code = UNIT_ARG[units] if isinstance(units, str) else (units or doc.header.get("$INSUNITS", 0))
    if code not in UNIT_FT:
        raise ValueError(f"DXF has no usable units (INSUNITS={code}). Pass units='in' / 'ft' / 'mm' / 'm'.")
    return UNIT_FT[code], code


def _entities(msp, layers):
    """Yield drawable entities, exploding block references one level deep."""
    for e in msp:
        if layers and e.dxf.layer not in layers:
            continue
        if e.dxftype() == "INSERT":
            try:
                for sub in e.virtual_entities():
                    yield sub
            except Exception:
                pass
        else:
            yield e


def dxf_info(path):
    """Print units, layers with counts, and extents (in the file's own units and in feet if known)."""
    doc = ezdxf.readfile(path)
    code = doc.header.get("$INSUNITS", 0)
    print(f"{path}\n  $INSUNITS = {code} ({UNIT_NAME.get(code, '?')})   DXF version {doc.dxfversion}")
    msp = doc.modelspace()
    counts, xs, ys = {}, [], []
    for e in _entities(msp, None):
        counts[e.dxf.layer] = counts.get(e.dxf.layer, 0) + 1
        for x, y in _points(e):
            xs.append(x); ys.append(y)
    print("  layers:")
    for L in sorted(counts): print(f"    {L:<24} {counts[L]:>5} entities")
    if xs:
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        line = f"  extents: {w:.1f} x {h:.1f} drawing units  (origin at {min(xs):.1f}, {min(ys):.1f})"
        if code in UNIT_FT:
            line += f"  =  {w*UNIT_FT[code]:.1f}' x {h*UNIT_FT[code]:.1f}'"
        print(line)
    return doc


def _points(e):
    """Rough vertex list for extents — not for drawing."""
    t = e.dxftype()
    try:
        if t == "LINE":
            return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
        if t in ("LWPOLYLINE", "POLYLINE"):
            return [(p[0], p[1]) for p in (e.get_points() if t == "LWPOLYLINE" else [v.dxf.location for v in e.vertices])]
        if t in ("CIRCLE", "ARC"):
            c, r = e.dxf.center, e.dxf.radius
            return [(c.x - r, c.y - r), (c.x + r, c.y + r)]
        if t in ("TEXT", "MTEXT"):
            p = e.dxf.insert; return [(p.x, p.y)]
        if hasattr(e, "flattening"):
            return [(p.x, p.y) for p in e.flattening(0.5)]
    except Exception:
        pass
    return []


def import_into(sheet, path, layers=None, units=None, offset=(0.0, 0.0), rotate_deg=0.0,
                color=None, width=0.5, text=False):
    """Draw a DXF's geometry onto a scaled_pdf.Sheet as the base drawing.

    layers   : list of layer names to include (None = all)
    units    : 'in' | 'ft' | 'mm' | 'cm' | 'm' — override the file header
    offset   : (x_ft, y_ft) added after conversion, to place the file's origin
    rotate_deg: rotate the whole base drawing about the file origin
    text     : also draw TEXT/MTEXT entities (usually room labels)
    Returns the extents in feet: (xmin, ymin, xmax, ymax).
    """
    from reportlab.lib.colors import grey
    color = color or grey
    doc = ezdxf.readfile(path)
    k, code = _scale_for(doc, units)
    a = math.radians(rotate_deg); ca, sa = math.cos(a), math.sin(a)

    def T(x, y):
        x, y = x * k, y * k
        return x * ca - y * sa + offset[0], x * sa + y * ca + offset[1]

    ext = [1e9, 1e9, -1e9, -1e9]
    def seen(x, y):
        ext[0], ext[1], ext[2], ext[3] = min(ext[0], x), min(ext[1], y), max(ext[2], x), max(ext[3], y)

    def polyline(pts, closed=False):
        pts = [T(x, y) for x, y in pts]
        for p in pts: seen(*p)
        for (x1, y1), (x2, y2) in zip(pts, pts[1:] + ([pts[0]] if closed and len(pts) > 2 else [])):
            sheet.line(x1, y1, x2, y2, width=width, color=color)

    n = 0
    for e in _entities(doc.modelspace(), layers):
        t = e.dxftype()
        try:
            if t == "LINE":
                polyline([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
            elif t == "LWPOLYLINE":
                pts = [(p[0], p[1]) for p in e.get_points()]
                if any(p[4] for p in e.get_points()):          # has bulges (arcs): flatten
                    pts = [(p.x, p.y) for p in e.flattening(0.05)]
                polyline(pts, closed=e.closed)
            elif t == "POLYLINE":
                polyline([(v.dxf.location.x, v.dxf.location.y) for v in e.vertices], closed=e.is_closed)
            elif t == "CIRCLE":
                cx, cy = T(e.dxf.center.x, e.dxf.center.y); r = e.dxf.radius * k
                seen(cx - r, cy - r); seen(cx + r, cy + r)
                sheet.circle(cx, cy, r, width=width, color=color)
            elif t in ("ARC", "ELLIPSE", "SPLINE"):
                polyline([(p.x, p.y) for p in e.flattening(0.05)])
            elif t in ("TEXT", "MTEXT") and text:
                x, y = T(e.dxf.insert.x, e.dxf.insert.y); seen(x, y)
                s = e.dxf.text if t == "TEXT" else e.plain_text()
                sheet.text(x, y, s, size=6, color=color)
            else:
                continue
            n += 1
        except Exception:
            continue
    sheet.base_note = (f"Base drawing: {path.split('/')[-1]} — {UNIT_NAME.get(code)} "
                       f"{'(header)' if units is None else '(override)'}, layers {layers or 'all'}, {n} entities")
    print(f"imported {n} entities from {path}; extents "
          f"{ext[0]:.1f},{ext[1]:.1f} to {ext[2]:.1f},{ext[3]:.1f} ft")
    return tuple(ext)


class DxfOut:
    """Collects everything a Sheet draws, in feet, and writes a layered DXF."""
    LAYERS = {"BASE": 8, "POSITIONS": 7, "UNITS": 7, "TEXT": 7, "DIMS": 1, "NOTES": 30}

    def __init__(self):
        self.doc = ezdxf.new("R2010", setup=True)
        self.doc.header["$INSUNITS"] = 2                 # feet
        self.doc.units = dxf_units.FT
        for name, color in self.LAYERS.items():
            self.doc.layers.add(name, color=color)
        self.msp = self.doc.modelspace()
        self.layer = "POSITIONS"

    def line(self, x1, y1, x2, y2):
        self.msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": self.layer})

    def rect(self, x, y, w, h):
        self.msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], close=True,
                                dxfattribs={"layer": self.layer})

    def circle(self, x, y, r):
        self.msp.add_circle((x, y), r, dxfattribs={"layer": self.layer})

    def text(self, x, y, s, height_ft, rotate=0, center=False):
        t = self.msp.add_text(s, dxfattribs={"layer": "TEXT", "height": height_ft, "rotation": rotate})
        t.set_placement((x, y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER if center
                        else ezdxf.enums.TextEntityAlignment.LEFT)

    def save(self, path):
        self.doc.saveas(path); print("wrote", path)

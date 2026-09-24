#!/usr/bin/env python3
"""
scaled_pdf.py — draw theatre paperwork to architectural scale, as PDF.

Amy's drawing tool. ReportLab writes in PostScript points (72 pt = 1 inch
exactly), so a drawing made here measures true on paper — provided it is
printed at 100% / "Actual size", never "Fit to page".

Real-world input is FEET. Convert with ft(feet, inches=0).

    from plotedit.scaled_pdf import Sheet, ft
    s = Sheet("plan.pdf", page="TABLOID", scale="1/4", landscape=True,
              show="Without Consent", venue="Louis Bluver Theatre at the Drake",
              sheet="Light Plot — plan", rev="A")
    s.origin(ft(2), ft(2))                    # where real-world (0,0) sits on the page
    s.rect(0, 0, ft(33), ft(38), label="Stage floor 33' x 38'")
    s.pipe(0, ft(10), ft(33), label="Pipe 1 — trim 14'")
    s.unit(ft(5), ft(10), 1, ch=1, kind="S4 26")
    s.dim(0, -ft(1), ft(33), -ft(1))          # a dimension line
    s.finish()                                # adds scale bar, 1-inch check, title block

Scales: "1/8", "1/4", "3/8", "1/2", "3/4", "1" (inches on paper per foot),
or any float (paper inches per real foot). Pages: LETTER, LEGAL, TABLOID
(11x17), ARCH_A..ARCH_E, A4, A3. Custom: page=(w_in, h_in).

DXF: pass dxf="plan.dxf" to also write the geometry in feet, layered. Read a
venue's drawing under the plot with s.import_dxf(path, layers=[...], units="in").
Run dxf_bridge.dxf_info(path) first to see its units and layers.

Verify a PDF you did not make here: measure the scale bar with any PDF
reader's measuring tool, or run  scaled_pdf.py --check file.pdf  which
reads the 1-inch check bar and reports its width in points (want 72.0).
"""
import sys, math
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import black, grey, white, HexColor

PAGES = {  # inches, portrait
    "LETTER": (8.5, 11), "LEGAL": (8.5, 14), "TABLOID": (11, 17),
    "ARCH_A": (9, 12), "ARCH_B": (12, 18), "ARCH_C": (18, 24),
    "ARCH_D": (24, 36), "ARCH_E": (36, 48),
    "A4": (8.27, 11.69), "A3": (11.69, 16.54),
}
SCALES = {"1/8": 0.125, "1/4": 0.25, "3/8": 0.375, "1/2": 0.5, "3/4": 0.75, "1": 1.0}
GREEN, BROWN = HexColor("#256948"), HexColor("#994C00")   # Twin Oaks palette

# ---------------------------------------------------------------------------
# §6.18 LINE WEIGHTS — three, and only three.
#
# RP-2 assigns every element on a plot to one of three weights, and four of the
# medium ones to a dash pattern. Drawing everything at one weight is legible but
# it throws away information an electrician reads without thinking: the heavy
# lines are the things that are physically there — battens, luminaires, walls —
# and the light ones are notation about them.
#
# Widths are in points at final print size, so they are the same on paper
# whatever the drawing scale. Dashes are in points for the same reason.
LIGHT, MEDIUM, HEAVY = 0.5, 0.9, 1.7

LINE_STYLES = {
    # lightweight — notation
    "scenery":      (LIGHT, None),
    "leader":       (LIGHT, (4, 3)),
    "dimension":    (LIGHT, None),
    "pool":         (LIGHT, (2.5, 2)),      # beam pools: our own, not in RP-2
    "grid":         (LIGHT, None),
    # medium — soft goods and reference lines
    "masking":      (MEDIUM, None),
    "drop":         (MEDIUM, (8, 4)),
    "centerline":   (MEDIUM, (11, 3, 2.5, 3)),   # chain-dash
    "plasterline":  (MEDIUM, (5, 4)),
    # heavy — the things that physically exist
    "batten":       (HEAVY, None),
    "luminaire":    (HEAVY, None),
    "architecture": (HEAVY, None),
    "border":       (HEAVY, None),
    "titleblock":   (HEAVY, None),
}


def style(name):
    """(width, dash) for an RP-2 line category. Raises rather than guessing."""
    try:
        return LINE_STYLES[name]
    except KeyError:
        raise KeyError(f"{name!r} is not an RP-2 line category; "
                       f"have {sorted(LINE_STYLES)}") from None

def ft(feet, inches=0):
    """Real-world length in feet (decimal). ft(12, 6) == 12.5"""
    return feet + inches / 12.0


class Sheet:
    def __init__(self, path, page="TABLOID", scale="1/4", landscape=True,
                 show="", venue="", sheet="", rev="A", designer="Design: Jerry Jonas",
                 margin_in=0.5, dxf=None):
        w, h = PAGES[page] if isinstance(page, str) else page
        if landscape: w, h = h, w
        self.page_pt = (w * inch, h * inch)
        self.c = canvas.Canvas(path, pagesize=self.page_pt)
        self.path = path
        self.paper_in_per_ft = SCALES[scale] if isinstance(scale, str) else float(scale)
        self.scale_label = (f'{scale}" = 1\'-0"' if isinstance(scale, str)
                            else f'{scale}" = 1\'-0"')
        self.pt_per_ft = self.paper_in_per_ft * inch       # the whole trick
        self.margin = margin_in * inch
        self.ox, self.oy = self.margin, self.margin           # page pt where real (0,0) sits
        self.meta = dict(show=show, venue=venue, sheet=sheet, rev=rev, designer=designer)
        self.c.setLineJoin(1); self.c.setLineCap(1)
        self._bounds = [1e9, 1e9, -1e9, -1e9]   # page-pt extents of everything drawn
        self.warnings = []
        self.base_note = None
        self.dxf_path = dxf
        self.dxf = None
        if dxf:
            from .dxf_bridge import DxfOut
            self.dxf = DxfOut()

    # ---- coordinates -------------------------------------------------
    def origin(self, x_ft, y_ft):
        """Place real-world (0,0) at this many feet in from the page's lower-left margin."""
        self.ox = self.margin + x_ft * self.pt_per_ft
        self.oy = self.margin + y_ft * self.pt_per_ft

    def import_dxf(self, path, **kw):
        """Draw a venue's DXF under the plot as the base drawing. See dxf_bridge.import_into."""
        from .dxf_bridge import import_into
        if self.dxf: self.dxf.layer = "BASE"
        ext = import_into(self, path, **kw)
        if self.dxf: self.dxf.layer = "POSITIONS"
        return ext

    def layer(self, name):
        """Set the DXF layer for what is drawn next (BASE, POSITIONS, UNITS, TEXT, DIMS, NOTES)."""
        if self.dxf: self.dxf.layer = name

    def P(self, x_ft, y_ft):
        """Real feet -> page points. Records extents so finish() can warn about clipping."""
        px, py = self.ox + x_ft * self.pt_per_ft, self.oy + y_ft * self.pt_per_ft
        b = self._bounds
        b[0], b[1], b[2], b[3] = min(b[0], px), min(b[1], py), max(b[2], px), max(b[3], py)
        return px, py

    def L(self, feet):
        return feet * self.pt_per_ft

    # ---- primitives (all args in real feet) --------------------------
    def line(self, x1, y1, x2, y2, width=0.75, dash=None, color=black, style=None):
        """style is an RP-2 line category (see LINE_STYLES) and wins over
        width/dash when given. Prefer it — a named category says WHY the line
        is that weight."""
        if style:
            width, dash = LINE_STYLES[style]
        c = self.c; c.saveState(); c.setLineWidth(width); c.setStrokeColor(color)
        if dash: c.setDash(list(dash))   # (array, phase) — pass the pattern as ONE list
        c.line(*self.P(x1, y1), *self.P(x2, y2)); c.restoreState()
        if self.dxf: self.dxf.line(x1, y1, x2, y2)

    def rect(self, x, y, w, h, width=1.0, label=None, fill=None, color=black, style=None):
        if style:
            width, dash = LINE_STYLES[style]
        c = self.c; c.saveState(); c.setLineWidth(width); c.setStrokeColor(color)
        if style and LINE_STYLES[style][1]:
            c.setDash(list(LINE_STYLES[style][1]))
        if fill: c.setFillColor(fill)
        px, py = self.P(x, y); self.P(x + w, y + h)   # second call records the far corner
        c.rect(px, py, self.L(w), self.L(h), stroke=1, fill=1 if fill else 0)
        c.restoreState()
        if self.dxf: self.dxf.rect(x, y, w, h)
        if label: self.text(x + w / 2, y + h / 2, label, size=8, center=True, color=grey)

    def circle(self, x, y, r, width=0.75, fill=None, color=black, dash=None, style=None):
        if style:
            width, dash = LINE_STYLES[style]
        c = self.c; c.saveState(); c.setLineWidth(width); c.setStrokeColor(color)
        if dash: c.setDash(list(dash))   # (array, phase) — pass the pattern as ONE list
        if fill: c.setFillColor(fill)
        self.P(x - r, y - r); self.P(x + r, y + r)
        c.circle(*self.P(x, y), self.L(r), stroke=1, fill=1 if fill else 0); c.restoreState()
        if self.dxf: self.dxf.circle(x, y, r)

    def ellipse(self, cx, cy, a, b, angle_deg=0.0, width=0.75, color=black,
                dash=None, style=None, steps=64):
        """A rotated ellipse, drawn as a polyline so the DXF export gets real
        geometry rather than a curve nobody downstream can read."""
        import math as _m
        if style:
            width, dash = LINE_STYLES[style]
        t = _m.radians(angle_deg)
        ct, st = _m.cos(t), _m.sin(t)
        pts = []
        for i in range(steps + 1):
            u = 2 * _m.pi * i / steps
            px, py = a * _m.cos(u), b * _m.sin(u)
            pts.append((cx + px * ct - py * st, cy + px * st + py * ct))
        for i in range(steps):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            self.line(x1, y1, x2, y2, width=width, dash=dash, color=color)

    def break_mark(self, x, y, across=0.45, along=0.55, vertical=True):
        """The conventional BREAK: this object continues, but not all of it is drawn.

        ⭐ RP-2 §6.12's Option 1 plate puts one on the boom pipe, and it is what
        licenses the layout's "may not be to scale" note. A boom eighteen feet
        tall with four units on it does not need eighteen feet of paper — it
        needs the four units and their real heights. The break is the honest way
        to say the middle was left out, instead of silently drawing a short boom.

        ⚠ The LABELLED HEIGHTS remain true. The break says the paper is
        compressed; it never says a number is approximate.
        """
        a, b = across / 2, along / 2
        if vertical:
            pts = [(x, y + b), (x + a, y + b * 0.3), (x - a, y - b * 0.3), (x, y - b)]
        else:
            pts = [(x + b, y), (x + b * 0.3, y + a), (x - b * 0.3, y - a), (x - b, y)]
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], width=0.9)

    def fill_poly(self, points, color=white):
        """Paint a closed polygon with no outline — used to OCCLUDE what is under it.

        ⭐ An instrument is drawn as if it sits ABOVE the pipe, even though it
        hangs below: the batten must not run through the symbol (Jerry,
        2026.09.23). That is what makes the body a place you can write a unit
        number. Nothing is stroked here — the outline is drawn afterwards by the
        symbol's own lines, so the DXF export still gets real geometry rather
        than a filled blob.
        """
        if len(points) < 3:
            return
        c = self.c
        c.saveState()
        c.setFillColor(color)
        path = c.beginPath()
        first = True
        for x, y in points:
            px, py = self.P(x, y)
            if first:
                path.moveTo(px, py); first = False
            else:
                path.lineTo(px, py)
        path.close()
        c.drawPath(path, stroke=0, fill=1)
        c.restoreState()

    def text(self, x, y, s, size=8, center=False, color=black, rotate=0, bold=False,
             align=None):
        """`align` is "left" (default), "center" or "right".

        ⚠ Right alignment is not a nicety. A label placed just left of a line and
        drawn LEFT-aligned runs straight across it — which is what the boom
        height labels did: the text started 4" clear of the pipe and then grew
        rightwards over it. Anchoring the END of the string is the only way to
        keep a label clear of something to its right.
        """
        how = align or ("center" if center else "left")
        c = self.c; c.saveState(); c.setFillColor(color)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        px, py = self.P(x, y); c.translate(px, py); c.rotate(rotate)
        dy = -size / 3 if how == "center" else 0
        draw = {"center": c.drawCentredString, "right": c.drawRightString}.get(how, c.drawString)
        draw(0, dy, s)
        c.restoreState()
        if self.dxf: self.dxf.text(x, y, s, size / self.pt_per_ft, rotate=rotate,
                                   center=(how == "center"))

    # ---- theatre objects ----------------------------------------------
    def pipe(self, x1, y, x2, label=None, width=2.0):
        """A hanging position. §6.18: a batten is HEAVY."""
        self.layer("POSITIONS")
        self.line(x1, y, x2, y, style="batten")
        if label: self.text(x1, y + ft(0, 6), label, size=7, bold=True)

    def position(self, pos, label=None):
        """Draw one horizontal hanging position from a plot record.

        `type` decides the drawing, and the distinction is not decoration:

          electric / pipe / grid   one heavy batten line — a pipe is a pipe
          catwalk                  a WALKWAY: two architectural edges you can
                                   stand between, plus the batten you hang from
          truss                    two chords with diagonals

        **A catwalk is not a pipe.** It has a real width, a person stands on it,
        and the instruments hang off its downstage rail rather than its middle —
        so a unit drawn on the centre of a catwalk is drawn three feet from where
        it actually is. At 1/2" scale that is an eighth of an inch on paper and a
        missed shutter cut in the room.

        **⭐ A catwalk is also a FRONT OF HOUSE position** (Jerry, 2026.09.23), so
        it sits OVER THE AUDIENCE — downstage of the plaster line, outside the
        stage rectangle, at negative y in this model. Two things follow and both
        bite:

          * **The sheet has to reach the house.** A plot whose room is the stage
            will clip a catwalk straight off, and the clipping guard is the only
            thing that would say so. `foh_extent()` returns how far downstage the
            positions actually go, so the drawing can be sized to include them.
          * **The throw is long and the angle is steep.** Nothing here needs to
            change for that — the photometrics already work from real geometry —
            but a catwalk unit reading a much lower footcandle than an onstage
            one is correct, not a bug.

        Vertical positions — booms, box booms, ladders — are NOT handled here.
        They are a different drawing problem (RP-2 §6.12) and are deliberately
        out of scope until asked for.
        """
        self.layer("POSITIONS")
        x1, y1 = pos["x1"], pos["y1"]
        foh = pos.get("foh")
        if foh is None:
            foh = (pos.get("type") or "").strip().lower() == "catwalk"
        x2, y2 = pos.get("x2", x1), pos.get("y2", y1)
        kind = (pos.get("type") or "electric").strip().lower()
        label = label if label is not None else pos.get("name", "")

        if kind in ("catwalk", "truss"):
            half = (pos.get("width") or (3.0 if kind == "catwalk" else 1.5)) / 2.0
            # Horizontal only for now, so the offset is in y.
            for side in (1, -1):
                self.line(x1, y1 + side * half, x2, y2 + side * half,
                          style="architecture" if kind == "catwalk" else "batten")
            if kind == "truss":
                import math
                n = max(2, int(abs(x2 - x1) / max(half * 2, 0.5)))
                for i in range(n):
                    a = x1 + (x2 - x1) * i / n
                    b = x1 + (x2 - x1) * (i + 1) / n
                    self.line(a, y1 - half, b, y1 + half, style="leader")
            else:
                # The pipe units actually hang from. Drawn INBOARD of the
                # downstage edge rather than on it: put it on the edge and the
                # two lines coincide, which reads as one thick rail and loses
                # the fact that there is a pipe at all.
                #
                # ⚠ The real offset varies by house — some hang off the rail
                # itself, some off a pipe a foot inboard. `railOffset` overrides
                # it; take the number off the venue's own section, not from here.
                off = pos.get("railOffset")
                if off is None:
                    off = half * 0.55
                self.line(x1, y1 - off, x2, y2 - off, style="batten")
            top = max(y1, y2) + half
        else:
            self.line(x1, y1, x2, y2, style="batten")
            top = max(y1, y2)

        if label:
            # CAPS on a plot — Jerry, 2026.09.22: "probably caps are more legible."
            text = label.upper() + ("  (FOH)" if foh and "FOH" not in label.upper() else "")
            self.text(x1, top + ft(0, 6), text, size=7, bold=True)

    @staticmethod
    def foh_extent(positions):
        """DEPRECATED — always 0. Kept so callers do not break.

        It existed to extend the sheet downstage for front-of-house positions
        drawn at negative y. That was a wrong model: the room is the whole room,
        house and stage, and an FOH position belongs INSIDE it (Jerry,
        2026.09.24). Nothing needs extra paper any more.
        """
        return 0.0

    def boom(self, pos, units=(), label=None, center_x=None):
        """A vertical position in PLAN: the mount, and the units hatched over it.

        ⭐ In plan a boom is a POINT. Every unit on it shares one x and y and
        differs only in height, so the drawing cannot separate them — which is
        why §6.12 says "hatch or shade acceptable for top view of boom" and puts
        the readable layout BESIDE the plot. Call `boom_elevation()` for that.
        """
        from . import symbols as _sym
        self.layer("POSITIONS")
        x, y = pos["x1"], pos["y1"]
        _sym.draw(self, _sym.boom_mount(pos.get("mount")), x, y, width=1.0)
        if units:
            # One symbol, hatched, standing for the stack. Drawing four on top of
            # each other would just be a heavier blob.
            prims = _sym.for_type(units[0].get("type", ""))
            _sym.draw(self, prims, x, y, rotate_deg=pos.get("rotation", 0.0))
            _sym.draw(self, _sym.hatch(prims), x, y,
                      rotate_deg=pos.get("rotation", 0.0), width=0.35)
        # Jerry, 2026.09.23: "the labels don't need to be on the overhead view of
        # the boom, just on the other view." RP-2's own §6.12 plate agrees — the
        # plan symbols carry no numbers; the layout beside the plot carries them
        # all. So no unit count, no notation, just enough to say WHICH boom this
        # point is, placed OUTBOARD so it never lands on the room or on a
        # position label.
        text = (label if label is not None else pos.get("name", "")).upper()
        if center_x is None:
            out = -1
        else:
            out = 1 if x >= center_x else -1      # away from the middle of the room
        self.text(x + out * ft(1, 4), y - ft(0, 3), text, size=6,
                  bold=True, center=False if out > 0 else True)

    def _unused_marker(self):
        pass

    def boom_elevation(self, pos, units, x, y, height=None, unit_gap=1.5,
                       layout="option1", max_gap=2.5):
        """§6.12 Option 1 — the boom as an elevation beside the plot.

        ⭐ COMPRESSED, with a BREAK MARK where paper was taken out. RP-2's own
        plate does this: unit 1 at 8'-0" sits close above unit 2 at 4'-0" with a
        break between them. A boom eighteen feet tall with four units near the
        bottom does not need eighteen feet of paper; it needs the four units and
        their real heights.

        ⚠ **The labelled heights stay true.** The break says the PAPER is
        compressed. It never says a number is approximate — the heights are the
        whole point of the drawing, and a section that fudged them would be worse
        than none. Every empty run longer than `max_gap` is drawn at `max_gap`
        and marked.

        §6.12 also says "choose only one type of layout per plot"; `layout` is
        carried so a plot can state which, and `check_booms()` enforces the one.
        """
        from . import symbols as _sym
        from . import photometrics as _ph
        self.layer("NOTES")

        # ⭐ WHERE things go is booms.elevation(); this method only puts ink on
        # paper. The /booms endpoint feeds the browser from the same call, so
        # the two drawings cannot disagree about a trim or a break.
        from . import booms as _b
        lay = _b.elevation(pos, units, max_gap)
        breaks, top = lay["breaks"], lay["top"]
        by_unit = {u.get("unit"): u for u in units}
        drawn = [(by_unit.get(u["unit"], u), u["dy"]) for u in lay["units"]]
        no_height = [by_unit.get(u["unit"], u) for u in lay["no_height"]]

        # The pipe, in segments so each break is a real gap rather than a mark
        # sitting on top of an unbroken line.
        cuts = sorted(breaks)
        seg_from = 0.0
        for b in cuts:
            self.line(x, y + seg_from, x, y + b - 0.18, style="batten")
            seg_from = b + 0.18
        self.line(x, y + seg_from, x, y + top, style="batten")
        for b in cuts:
            self.break_mark(x, y + b)

        self.text(x, y + top + ft(0, 6), (pos.get("name") or "").upper(),
                  size=7, bold=True, center=True)
        self.text(x, y - ft(0, 9), "NOT TO SCALE — heights are the data",
                  size=5, center=True)
        if cuts:
            self.text(x, y - ft(1, 4), f"{len(cuts)} break{'s' if len(cuts) > 1 else ''} "
                      f"— pipe compressed", size=5, center=True)

        for u, dy in drawn:
            uy = y + dy
            self.line(x, uy, x + unit_gap * 0.55, uy, style="leader")
            _sym.draw(self, _sym.for_type(u.get("type", "")), x + unit_gap, uy,
                      rotate_deg=90)
            # Ends 5" clear of the pipe, growing leftwards away from it.
            self.text(x - ft(0, 5), uy - ft(0, 2), _ph.fmt_ft(u["height"]),
                      size=6, align="right")
            self.text(x + unit_gap, uy - ft(0, 3), str(u.get("unit")),
                      size=6, center=True, bold=True)
        for i, u in enumerate(no_height):
            self.text(x + unit_gap, y + top - (i + 1) * 0.5,
                      f"{u.get('unit')}: NO HEIGHT RECORDED", size=5)
        return top

    def unit(self, x, y, num, ch=None, kind="", color_gel=None, focus_to=None, r=None,
             trim=None, focus_h=5.5, lamp=None, mode=None, lens_rotation=None,
             accessories=None, circuit=None, dimmer=None, wattage=None,
             control="dimmer-per-circuit", symbol_angle="orthogonal",
             pool_plane=None, show_pool=True, annotate=False):
        """A lighting instrument: circle body, unit number inside, channel below,
        gel/type beside, optional focus arrow to a real-world point.

        With trim (hang height, ft) and focus_to, the photometrics are worked out:
        throw, elevation, pan, field/beam pool at focus_h (head height, default 5'-6")
        and center-beam footcandles if the fixture is in photometrics.FIXTURES.
        lamp is a tungsten lamp ("HPL 575"); mode is an LED output mode
        ("Regulated 3200K"). Passing neither uses the fixture's reference figure.

        accessories is a list of names — "top hat", "4-way barn door", "gobo",
        "iris". RP-2 puts gate accessories INSIDE the body and front-of-lens ones
        at the nose, so only the name is given here and the placement is worked
        out. They change nothing photometric: a top hat controls spill, not
        output, and no figure here pretends otherwise. An unrecognised accessory
        is collected in self.warnings — never dropped, because an accessory
        nobody ordered is an accessory nobody brings.

        show_pool draws the field pool at the focus point; annotate prints the
        numbers beside it. Returns the dict (or None if no trim/focus given).
        Everything is recorded in self.units for the schedule and the section."""
        self.layer("UNITS")
        # The symbol itself, drawn to USITT RP-2 (2006). See symbols.py and
        # docs/SYMBOLS.md — the shape and the mark inside it carry the fixture
        # type and the beam angle, which is what an electrician reads first.
        from . import symbols as _sym
        pan = 0.0
        if focus_to and trim is not None:
            from . import photometrics as _ph
            pan = _ph.aim((x, y, trim), (focus_to[0], focus_to[1], focus_h))["pan"]
        # ⭐ RP-2 p.2, in its own words: "It is acceptable to visually orient the
        # angle of each drawn luminaire to either focus points or 90° axes."
        # Jerry, 2026.09.23: "most plots display the instruments on even 90
        # degree mounts... usually it's an option." So `orthogonal` is the
        # default and the true angle is snapped to the nearest quarter turn.
        #
        # 🔴 THE SNAP IS COSMETIC AND MUST STAY THAT WAY. `pan` below is the real
        # aim, and every throw, pool and footcandle is computed from it. A unit
        # drawn at 0° while pointing at 320° is a drawing convention; a unit
        # COMPUTED at 0° would be a lie about the light.
        draw_deg = pan
        if (symbol_angle or "orthogonal").startswith("orth"):
            draw_deg = round(pan / 90.0) * 90.0

        _base = _sym.for_type(kind, lens_rotation)
        # The centre comes from the BARE instrument. Accessories hang off the
        # nose, so measuring the accessorised symbol would drag the "centre"
        # forward out of the body and put the number on a barn door.
        _lo, _hi = _sym._extent(_base)
        _center = (_lo + _hi) / 2.0
        _prims = _base

        # §6.15 / §6.0: a SHADED REAR. RP-2 blackens the back of the symbol for
        # arc sources; Jerry uses the same mark for a 750W Source Four, which is
        # the only place he has seen a wattage called out on a plot at all.
        # Inserted FIRST so the body's own outline is stroked back over it.
        if _shade_rear_for(kind, lamp):
            _prims = _sym.shade_rear(_base) + list(_base)

        if accessories:
            _prims, _unknown = _sym.with_accessories(_prims, accessories)
            for w in _unknown:
                self.warnings.append(f"unit {num}: {w}")
        # ⭐ The focus leader goes UNDER the symbol, for the same reason the pipe
        # does: the instrument is drawn as if it sits above everything it is
        # attached to. Drawn after, the leader runs across the body and through
        # the unit number — which is exactly the mess that putting the number
        # inside the body was meant to avoid.
        if focus_to:
            self.layer("NOTES")
            self.line(x, y, focus_to[0], focus_to[1], color=grey, style="leader")
            self.circle(focus_to[0], focus_to[1], ft(0, 3), color=grey, style="leader")
            self.layer("UNITS")

        _sym.draw(self, _prims, x, y, rotate_deg=draw_deg)

        # §6.14 notation. RP-2 allows leaving categories out rather than
        # cluttering the plot, so only what was supplied is drawn.
        # §6.14.1: hexagon = circuit, rectangle = dimmer, circle = channel. The
        # SHAPE carries the meaning, so a circuit must never be drawn in a circle.
        # Clear the symbol by its own size rather than by a constant. A fixed
        # 11" put the channel circle on top of every ellipsoidal, because an ERS
        # reaches nearly a foot past its yoke — and further still once an
        # accessory is hung on the nose.
        _clear = _sym.radius(_prims) + ft(0, 3)
        _sym.notation(self, x, y, unit=num, channel=ch, color=color_gel,
                      circuit=circuit, dimmer=dimmer, wattage=wattage,
                      control=control, rotate_deg=draw_deg,
                      body_center=_center, above=_clear)
        result = None
        if focus_to:
            fx, fy = focus_to
            if trim is not None:
                from . import photometrics as ph
                a = ph.aim((x, y, trim), (fx, fy, focus_h))
                result = dict(num=num, ch=ch, kind=kind, x=x, y=y, trim=trim, focus=(fx, fy),
                              focus_h=focus_h, accessories=list(accessories or []),
                              circuit=circuit, dimmer=dimmer, **a)
                if kind in ph.FIXTURES:
                    pl = ph.pool(kind, a["throw"], a["elevation"]); result.update(pl)
                    # color_gel may be compound ("R52+R119", "R52/R119"), so ask
                    # gel_factor rather than looking for a single key in GELS.
                    gel_arg, gel_warn = color_gel or None, None
                    if gel_arg:
                        factor, gnote = ph.gel_factor(gel_arg)
                        if factor is None:          # a gel we have no figure for
                            gel_arg, gel_warn = None, gnote
                    fc, note = ph.footcandles(kind, a["throw"], lamp, mode, gel_arg)
                    if gel_warn:
                        note += f" — {gel_warn}; level is for open white"
                    result["fc"], result["fc_note"] = fc, note
                    if show_pool:
                        # ⭐ The REAL shape, not a circle. A cone only cuts a
                        # circle when it points straight down; at 30° elevation a
                        # 26° field lands more than twice as long as it is wide,
                        # and the long end is the one that reaches the scenery.
                        sh = ph.pool_shape(kind, (x, y, trim), (fx, fy),
                                           plane_h=pool_plane if pool_plane is not None else focus_h,
                                           focus_h=focus_h)
                        self.layer("NOTES")
                        if sh.get("a"):
                            self.ellipse(sh["cx"], sh["cy"], sh["a"], sh["b"],
                                         sh["angle"], color=grey, style="pool")
                            result["pool_shape"] = sh
                        elif sh.get("note"):
                            self.warnings.append(f"unit {num}: {sh['note']}")
                        self.layer("UNITS")
                if annotate:
                    t = f"{ph.fmt_ft(a['throw'])} @ {a['elevation']:.0f}°"
                    if result.get("field"): t += f" · {ph.fmt_ft(result['field'])} pool"
                    if result.get("fc"): t += f" · {result['fc']:.0f} fc"
                    self.text(fx + ft(0, 6), fy - ft(1), t, size=5, color=grey)
        if not hasattr(self, "units"): self.units = []
        self.units.append(result or dict(num=num, ch=ch, kind=kind, x=x, y=y, trim=trim,
                                         focus=focus_to, accessories=list(accessories or [])))
        return result

    def dim(self, x1, y1, x2, y2, text=None, offset_ft=0.0):
        """Dimension line with ticks and a distance label (feet-inches)."""
        import math
        self.layer("DIMS")
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if text is None:
            whole = int(length); inches = round((length - whole) * 12)
            if inches == 12: whole, inches = whole + 1, 0
            text = f"{whole}'-{inches}\""
        self.line(x1, y1, x2, y2, style="dimension")
        nx, ny = (-dy / length, dx / length) if length else (0, 1)
        t = ft(0, 4)
        for (x, y) in ((x1, y1), (x2, y2)):
            self.line(x - nx * t, y - ny * t, x + nx * t, y + ny * t, style="dimension")
        ang = math.degrees(math.atan2(dy, dx))
        self.text(x1 + dx / 2 + nx * ft(0, 6), y1 + dy / 2 + ny * ft(0, 6), text,
                  size=7, center=True, rotate=ang)

    def note(self, x, y, s, size=7):
        self.layer("NOTES"); self.text(x, y, s, size=size, color=BROWN)

    # ---- §6.18 reference lines

    def center_line(self, x, y0, y1):
        """§6.18: the center line is MEDIUM, chain-dashed."""
        self.layer("BASE")
        self.line(x, y0, x, y1, style="centerline", color=grey)

    def plaster_line(self, y, x0, x1):
        """§6.18: the plaster line is MEDIUM, evenly dashed."""
        self.layer("BASE")
        self.line(x0, y, x1, y, style="plasterline", color=grey)

    # ---- sheet furniture ----------------------------------------------
    def finish(self):
        """Scale bar, one-inch check, title block, then save."""
        c = self.c; W, H = self.page_pt; m = self.margin
        # clipping check — a drawing that runs off the sheet is worse than no drawing
        x0b, y0b, x1b, y1b = self._bounds
        if x1b > -1e8 and (x0b < m or y0b < m or x1b > W - m or y1b > H - m - 1.3 * inch):
            real_w = (x1b - x0b) / self.pt_per_ft; real_h = (y1b - y0b) / self.pt_per_ft
            avail_w = (W - 2 * m) / inch; avail_h = (H - 2 * m - 1.3 * inch) / inch
            fit = min(avail_w / real_w, avail_h / real_h) if real_w and real_h else 0
            best = max((k for k, v in SCALES.items() if v <= fit), key=lambda k: SCALES[k], default=None)
            # ⚠ Say WHICH EDGE and by how much. This used to report only the
            # spans against the sheet size, so a drawing that FITS but is placed
            # off one edge read as "too big" — sending the reader to change the
            # scale when the fault was a stray coordinate. The section reported
            # 53' against a 70' sheet and was clipped all the same: one sight
            # point at y = -14 lay ten feet off the left edge.
            over = []
            if x0b < m: over.append(f"{(m - x0b) / self.pt_per_ft:.1f}' off the LEFT")
            if y0b < m: over.append(f"{(m - y0b) / self.pt_per_ft:.1f}' off the BOTTOM")
            if x1b > W - m: over.append(f"{(x1b - (W - m)) / self.pt_per_ft:.1f}' off the RIGHT")
            if y1b > H - m - 1.3 * inch:
                over.append(f"{(y1b - (H - m - 1.3 * inch)) / self.pt_per_ft:.1f}' off the TOP")
            edges = ("; ".join(over) + ". ") if over else ""
            msg = (f"CLIPPED: {edges}drawing spans {real_w:.1f}' x {real_h:.1f}' but the sheet holds "
                   f"{avail_w/self.paper_in_per_ft:.1f}' x {avail_h/self.paper_in_per_ft:.1f}' at {self.scale_label}. "
                   + (f'Largest standard scale that fits this page: {best}" = 1\'-0". ' if best else "")
                   + "Or use a bigger sheet, or rotate it.")
            self.warnings.append(msg); print("⚠", msg, file=sys.stderr)
        self.dxf, _dxf = None, self.dxf          # sheet furniture stays off the DXF
        # border
        c.setLineWidth(HEAVY); c.rect(m, m, W - 2 * m, H - 2 * m)      # §6.18 drawing border
        if self.base_note:
            c.setFillColor(grey); c.setFont("Helvetica", 6); c.drawString(m + 6, m + 6, self.base_note)
        # title block, lower right
        tb_w, tb_h = 4.0 * inch, 1.1 * inch
        x0, y0 = W - m - tb_w, m
        c.setLineWidth(HEAVY); c.rect(x0, y0, tb_w, tb_h)             # §6.18 title block border
        c.setFillColor(GREEN); c.setFont("Helvetica-Bold", 11)
        c.drawString(x0 + 6, y0 + tb_h - 15, self.meta["show"] or "Untitled")
        c.setFillColor(black); c.setFont("Helvetica", 8)
        from reportlab.pdfbase.pdfmetrics import stringWidth
        for i, key in enumerate(("venue", "sheet")):
            t = self.meta[key]
            if stringWidth(t, "Helvetica", 8) > tb_w - 12:
                while stringWidth(t + "…", "Helvetica", 8) > tb_w - 12: t = t[:-1]
                t += "…"
            c.drawString(x0 + 6, y0 + tb_h - 27 - 12 * i, t)
        import datetime
        c.drawString(x0 + 6, y0 + tb_h - 51, f"Scale {self.scale_label}   Rev {self.meta['rev']}   "
                                              f"{datetime.date.today().strftime('%Y.%m.%d')}")
        c.setFillColor(BROWN); c.setFont("Helvetica-Bold", 8)
        c.drawString(x0 + 6, y0 + 6, self.meta["designer"])
        c.setFillColor(grey); c.setFont("Helvetica", 6)
        c.drawRightString(x0 + tb_w - 6, y0 + 6, "Twin Oaks Studios — print at 100% / Actual size")
        # scale bar: 0 to 10 ft in 1-ft ticks, left of title block
        sx, sy = x0 - 0.4 * inch - 10 * self.pt_per_ft, m + 0.35 * inch
        c.setStrokeColor(black); c.setFillColor(black); c.setLineWidth(1)
        for i in range(10):
            c.rect(sx + i * self.pt_per_ft, sy, self.pt_per_ft, 5, stroke=1, fill=(i % 2 == 0))
        c.setFont("Helvetica", 6)
        for i in (0, 5, 10):
            c.drawCentredString(sx + i * self.pt_per_ft, sy - 8, f"{i}'")
        c.drawString(sx, sy + 9, f"Scale {self.scale_label}")
        # one-inch check bar: exactly 72 pt, tagged so --check can find it
        cx, cy = sx, sy + 0.32 * inch
        c.setLineWidth(1); c.rect(cx, cy, 72, 4, stroke=1, fill=0)
        c.drawString(cx + 76, cy, 'this bar is 1" when printed at 100%')
        c.save()
        if _dxf and self.dxf_path: _dxf.save(self.dxf_path)


def _shade_rear_for(kind, lamp=None):
    """Should this instrument's back be blackened? (§6.15, and Jerry's 750 mark.)

    Two cases, one mark:
      · an ARC source — RP-2 §6.15 blackens the rear of HMI and the like;
      · a tungsten unit carrying MORE than the default lamp — Jerry, 2026.09.23:
        "the only [wattage] I've seen on plots is 750w S4 where the back is
        blackened, like they have for HMI lamps in the spec."

    ⚠ It reads the lamp, not the fixture: the same Source Four is a 575 or a 750
    depending on what is in it, so shading by fixture type would mark the whole
    rig or none of it.
    """
    from . import photometrics as _ph
    key, row, _ = _ph.lookup(kind)
    if row and str(row.get("family", "")).lower() in ("arc", "hmi"):
        return True
    if not lamp:
        return False
    w = _ph.lamp_watts(lamp)
    default = _ph.lamp_watts(_ph.DEFAULT_LAMP)
    return bool(w and default and w > default)


def compress_heights(heights, max_gap=2.5):
    """Where to DRAW a boom's units when the pipe is longer than the paper.

    ⚠ The arithmetic moved to booms.py so the browser can ask for it too — it
    was about to be retyped in TypeScript, which is how the screen and the paper
    drifted three times in one week. This name is kept because the suites and
    plot_to_pdf call it.
    """
    from . import booms as _b
    return _b.compress(heights, max_gap)


def section(path, units, deck_length, grid_height, scale="1/2", page="ARCH_D", landscape=True,
            axis="y", head_h=5.5, **meta):
    """Side elevation from a list of unit dicts (as Sheet.units records them).

    axis="y": the cut runs upstage–downstage; horizontal position is each unit's y.
    axis="x": the cut runs across the stage; horizontal position is each unit's x.
    Draws the deck, the grid/trim, each unit at its trim, the beam's center line to
    the focus point at head height, and the field-edge lines to the deck.
    """
    from . import photometrics as ph
    s = Sheet(path, page=page, scale=scale, landscape=landscape,
              sheet=meta.pop("sheet", "Section"), **meta)
    s.origin(ft(3), ft(3))
    s.layer("BASE")
    s.rect(0, -ft(0, 4), deck_length, ft(0, 4), width=1.2, fill=grey)          # the deck, 4" thick
    s.line(0, grid_height, deck_length, grid_height, width=0.5, dash=(4, 4), color=grey)
    s.text(deck_length + ft(0, 6), grid_height, f"grid {ph.fmt_ft(grid_height)}", size=6, color=grey)
    s.line(0, head_h, deck_length, head_h, width=0.3, dash=(1, 3), color=grey)
    s.text(deck_length + ft(0, 6), head_h, f"head height {ph.fmt_ft(head_h)}", size=6, color=grey)
    for u in units:
        if u.get("trim") is None or not u.get("focus"): continue
        h = u["y"] if axis == "y" else u["x"]
        fh = u["focus"][1] if axis == "y" else u["focus"][0]
        s.layer("POSITIONS"); s.circle(h, u["trim"], ft(0, 5), width=1.0, fill=white)
        s.text(h, u["trim"], str(u["num"]), size=6, center=True, bold=True)
        s.text(h, u["trim"] + ft(0, 10), f"trim {ph.fmt_ft(u['trim'])}", size=5, center=True, color=grey)
        s.layer("NOTES"); s.line(h, u["trim"], fh, head_h, width=0.6, dash=(3, 2))
        s.circle(fh, head_h, ft(0, 3), width=0.5)
        f = ph.FIXTURES.get(u.get("kind"))
        if f and f["field"]:
            e = math.radians(u["elevation"]); half = math.radians(f["field"]) / 2
            direction = 1 if fh >= h else -1
            for ang in (e - half, e + half):
                if ang <= 0.01: continue
                run = u["trim"] / math.tan(ang)                                # to the deck
                end = h + direction * run
                if 0 <= end <= deck_length:
                    s.line(h, u["trim"], end, 0, width=0.4, color=grey)
                else:                                                          # leaves the deck: stop at the edge
                    edge = deck_length if direction > 0 else 0
                    frac = (edge - h) / (end - h) if end != h else 1
                    s.line(h, u["trim"], edge, u["trim"] * (1 - frac), width=0.4, color=grey, dash=(1, 2))
            lab = f"{u['kind']} · {ph.fmt_ft(u['throw'])} @ {u['elevation']:.0f}°"
            if u.get("fc"): lab += f" · {u['fc']:.0f} fc"
            s.text(fh, -ft(1, 2), lab, size=5, center=True, color=grey)
    s.finish()
    return s


def check(path):
    """Find the 1-inch check bar and report its width in points (want 72.0)."""
    import fitz
    doc = fitz.open(path)
    for pno, page in enumerate(doc):
        for d in page.get_drawings():
            for item in d["items"]:
                if item[0] == "re":
                    r = item[1]
                    if 3 <= r.height <= 5 and 60 <= r.width <= 84:
                        print(f"page {pno+1}: check bar {r.width:.2f} pt wide "
                              f"({'OK' if abs(r.width-72) < 0.05 else 'OFF'} — want 72.00)")
                        return r.width
    print("no check bar found"); return None


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--check":
        check(sys.argv[2])
    else:
        print(__doc__)

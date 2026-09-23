# Symbols

**The standard is USITT RP-2 (2006), *Recommended Practice for Theatrical Lighting
Design Graphics*.** A copy is in `docs/reference/USITT-RP-2-2006.pdf`. The symbol
plates are pages 4–6.

**⚠ What the editor draws today is NOT RP-2.** It is an approximation drawn from
memory before the standard was read. It is wrong in ways that matter, listed
below. Fix it against the document, not against a guess.

---

## What RP-2 actually specifies

**Symbols represent the approximate size and shape of the luminaire, in scale**,
and the symbol is placed so its position is the exact hanging point. Default
spacing between fixed-focus units is 18".

**Each symbol normally carries:** luminaire number · an indication of focal
length or beam spread *as part of the symbol* · accessories (template, iris,
scroller, top hat, barn door) · channel · axis notation for PAR lamps.

**It may also carry:** focus · wattage · circuit or dimmer, or a space for the
electrician to write one · two-fer indication · colour · scroller colour ·
template notation.

**Position numbering (§2.3.1):** FOH positions number from the one nearest the
plaster line. Onstage electrics and booms number downstage to upstage.

---

## Where the current symbols are wrong

| | Editor draws | RP-2 |
|---|---|---|
| **ERS body** | plain rectangle | a **bulbous rounded back** (the reflector) with a squared front. Two families: *Diameter Lens Instruments* (rounded) and *Box Shape Instruments* (rectangles) — the Source Four is neither; it is **§6.1.6 Enhanced ERS** |
| **Beam angle** | coded by **tube length** | coded by the **shape of the lens end**: a wedge for 50°, a narrower wedge for 36–40°, smaller for 26–30°, an **X/bowtie for 19–20°**. Only the very narrow units (15°, 10°, 5°) get a longer body |
| **Fresnel** | rectangle with a heavy front line | rounded back with a **flared, stepped front**; sized 3", 6", 8", 12", plus an oval-beam variant |
| **PAR** | rectangle with a line | a **rounded capsule**, sized by lamp (MR-16 birdie, PAR 38/46/56/64). **Beam spread is a mark on the front** — XWFL, WFL, MFL, NSP, VNSP each have their own — and **PARs carry a lamp-axis arrow** |
| **Variable focus** | not drawn | a **Z** in the body |
| **Accessories** | not drawn | template (filled circle, triangle, or **T**), iris (**O** or **I**), gobo rotator (**R**), double rotator (**RR**) |
| **Cyc units** | not drawn | §6.6 — rectangles divided into cells (1, 2, 3, 4 cell), plus T-3 units by circuit count, with a focus-direction arrow |
| **Striplights** | not drawn | §6.7 — long shallow shapes, length proportional to the real unit, with pipe-mounted and trunnion-mounted variants |
| **Beam projectors, scoops** | not drawn | §6.4, §6.5 |

---

## What to do

1. **Redraw the ERS family from §6.1.6.** That is the Source Four, which is most
   of every plot here.
2. **Then Fresnel (§6.2), PAR with its spread marks and axis arrow (§6.3).**
3. **Then cyc and strips (§6.6, §6.7)** — the archive has Altman 3-Cell Sky Cyc
   and ColorSource Cyc, so they are real, not hypothetical.
4. **Accessory marks last**, since the data model does not carry accessories
   in detail yet.

**Movers and LED bars are not in RP-2 (2006).** The archive has Martin Mac Aura
and ADJ Mega Tri Bar from 2025, so something has to be drawn — follow the
convention of "approximate size and shape" and note the departure.

**⚠ Jerry's own convention is Field Template / SoftSymbols for ETC, with AutoPlot
for cable and truss.** Those are `.vwx` and cannot be reused, but they are
RP-2-derived — so RP-2 is the right thing to match, and his markup is the
tiebreak where RP-2 leaves room.

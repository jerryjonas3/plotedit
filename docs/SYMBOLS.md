# Symbols

**The standard is USITT RP-2 (2006), *Recommended Practice for Theatrical Lighting
Design Graphics*** — nine pages, in `docs/reference/USITT-RP-2-2006.pdf`. Jerry has
the same document; the six symbol plates render byte-identical between his copy
and the one fetched here, so there is one standard and no ambiguity about which.

**The plates are pages 4–9. Read them before drawing anything.**

**⚠ What the editor draws today is NOT RP-2.** It is an approximation made from
memory before the standard was read. Every difference is listed below.

---

## The plates

| Page | Covers |
|---|---|
| 4 | §6.1 Ellipsoidals — by lens diameter, plus **§6.1.6 Enhanced ERS** (the Source Four) |
| 5 | §6.2 Fresnels · §6.3 PARs and their beam designations · §6.4 Beam projectors · §6.5 Scoops · §6.1.11 ERS variations (zoom, gobo, iris, rotator) |
| 6 | §6.6 Cyc units · §6.7 Striplights and mounting · §6.7.3 Fluorescents |
| 7 | **§6.8 Automated luminaires** · §6.9 Practicals · §6.10 Followspot · §6.11 Two-fers · §6.12 Booms |
| 8 | **§6.13 Accessories** · **§6.14 Luminaire notation** |
| 9 | §6.15 Arc sources · **§6.16 LED fixtures** · §6.17 Scene machine · **§6.18 Line weights** |

---

## 🔴 §6.14 — how a luminaire is annotated

**The shape of the container carries the meaning. This is the part the editor has
most wrong.**

| Shape | Means |
|---|---|
| **Hexagon** | Circuit *(and dimmer, where there is a dimmer per circuit)* |
| **Rectangle** | Dimmer, in a patch-panel house |
| **Circle** | Channel |

**§6.14.2, reading down the symbol:** focus · color · [symbol, carrying the beam
designation and any gate accessory] · instrument number · wattage · circuit
(hexagon) · dimmer (rectangle) · channel (circle).

**§6.14.4, PAR lamps** run horizontally — channel, dimmer, circuit to the left of
the symbol — and add a **lamp-axis rotation arrow**.

**§6.14.3, striplights and cyc units** repeat the notation per circuit, and carry a
**focus-direction arrow** and a **PAR filament orientation** mark.

**§6.14.5, followspot boomerang** — colors listed and numbered, furthest from the
operator first.

**RP-2's own caveat:** *"Notation shown on any plot is a case-by-case basis. It is
not necessary to include all categories, when the combination runs the risk of
making the plot's appearance cluttered."*

## §2.2 — what a symbol must carry

Luminaire number · beam spread **as part of the symbol** · accessories · channel ·
axis notation for PARs. **Optional:** focus, wattage, circuit/dimmer or a space for
the electrician to write one, two-fers, color, scroller color, template.

**Symbols are drawn to approximate the real size and shape, in scale**, and placed
so the symbol's position is the exact hanging point. **Default spacing between
fixed-focus units is 18".**

## §2.3.1 — position numbering

FOH positions number from the one nearest the plaster line. **Onstage electrics and
booms number downstage to upstage.** Anything off centreline is subnamed by its side.

## §6.18 — line weights

| Weight | Used for |
|---|---|
| Light | scenery · leader lines · dimensions |
| Medium | masking · drops · centre line (chain-dash) · plaster line (dashed) |
| **Heavy** | **batten · luminaire · architecture · drawing border · title block** |

---

## Where the current symbols are wrong

| | Editor draws | RP-2 |
|---|---|---|
| **ERS body** | plain rectangle | a **bulbous rounded back** (the reflector) with a squared front. Source Four = **§6.1.6 Enhanced ERS**, its own family |
| **Beam angle** | coded by **tube length** | coded by the **shape of the lens end** — wedge for 50°, narrower for 36–40°, smaller for 26–30°, an **X for 19–20°**. Only 15°, 10° and 5° get longer bodies |
| **Fresnel** | rectangle, heavy front line | rounded back, **flared stepped front**; 3" 6" 8" 12", plus oval-beam |
| **PAR** | rectangle with a line | a **rounded capsule** sized by lamp, beam spread as a **mark on the front** (XWFL, WFL, MFL, NSP, VNSP), **plus a lamp-axis arrow** |
| **Circuit and dimmer** | not drawn | **hexagon** and **rectangle**. Only channel-in-a-circle was right |
| **Variable focus** | — | a **Z** in the body |
| **Gate accessories** | — | filled circle / **T** (template) · **O** or **I** (iris) · **R** / **RR** (rotator) |
| **Cyc units** | — | §6.6, rectangles divided into cells, with a focus-direction arrow |
| **Striplights** | — | §6.7, long shallow shapes, length proportional to the real unit; pipe-mount and trunnion variants |
| **Movers** | — | **§6.8 — they ARE in RP-2.** Moving yoke, moving head wash, moving head spot, moving mirror, external moving mirror. Drawn with a **dashed swing-radius circle** |
| **LED fixtures** | — | **§6.16 — also in RP-2.** Dots inside the body: **the number of dots is the number of colors.** 3, 4 and 7 shown |
| **Practical** | — | §6.9, a **triangle** |
| **Followspot** | — | §6.10 |
| **Accessories** | — | §6.13 — barn doors 2 and 4 panel, scroller, top hat, half hat, CYM mixer, douser, sightline, rigging point |
| **Line weights** | one weight throughout | §6.18 — three |

---

## ⚠ Two things I told Jerry that were wrong

1. **"Movers and LED bars are not in RP-2 (2006)."** They are — §6.8 and §6.16.
   A Martin Mac Aura is a **moving head wash luminaire**; an ADJ Mega Tri Bar is
   an **LED fixture with three dots**.
2. **The annotation positions.** I had unit number above and channel below and
   nothing else. The real convention is the hexagon/rectangle/circle stack of
   §6.14.

**➡ The lesson, already recorded in `how-we-sound.md`: get the real document
before guessing, and before asking someone to correct the guess.**

---

## Order of work

1. **§6.1.6 Enhanced ERS** — the Source Four, which is most of every plot here.
2. **§6.14 notation** — hexagon, rectangle, circle. Cheap and immediately visible.
3. **§6.2 Fresnel, §6.3 PAR** with spread marks and the axis arrow.
4. **§6.16 LED** and **§6.8 movers** — the 2025 paperwork has both.
5. **§6.6 cyc and §6.7 strips** — the archive has Altman 3-Cell Sky Cyc and
   ColorSource Cyc.
6. **§6.18 line weights** — three, not one.
7. **§6.13 accessories** last; the data model does not carry them in detail yet.

**Jerry's own set is Field Template / SoftSymbols, which is RP-2-derived.** So
RP-2 is the thing to match, and his eye is the tiebreak only where RP-2 leaves
room.

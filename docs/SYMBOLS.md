# Symbols

**The standard is USITT RP-2 (2006), *Recommended Practice for Theatrical Lighting
Design Graphics*** — nine pages, in `docs/reference/USITT-RP-2-2006.pdf`.

**⚠ That PDF is NOT in this repo.** It is USITT's copyrighted standard and `.gitignore`
excludes it, so a fresh clone will not have it — put your own copy at that path.
(Jerry's is archived in the My AI Brain repo under `my-files (knowledge)/fixture-manuals/`.)
Jerry has
the same document; the six symbol plates render byte-identical between his copy
and the one fetched here, so there is one standard and no ambiguity about which.

**The plates are pages 4–9. Read them before drawing anything.**

**✅ Redrawn to RP-2 on 2026.09.23.** `server/plotedit/symbols.py` holds the
geometry, traced from the plates; `server/draw_symbol_sheet.py` prints the set for
comparison against the document.

**⭐ The geometry lives in ONE place.** The PDF draws it directly; the browser
fetches it from `GET /symbols`. Porting the shapes to TypeScript would guarantee
screen and paper drift apart — which is exactly what happened with the
photometrics before `test_agreement.py` existed.

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
booms number downstage to upstage.** Anything off centerline is subnamed by its side.

## §6.18 — line weights

| Weight | Used for |
|---|---|
| Light | scenery · leader lines · dimensions |
| Medium | masking · drops · center line (chain-dash) · plaster line (dashed) |
| **Heavy** | **batten · luminaire · architecture · drawing border · title block** |

---

## What was wrong before, and is now fixed

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

## ✅ Approved 2026.09.23

**Jerry reviewed Rev 3 — all 18 symbols and the three line weights — and passed
them: *"the symbols look good."*** That was the gate on drawing any more, and it
is now open. §6.1.6 ERS, §6.2 Fresnel and oval-beam, §6.3 PAR, §6.16 LED,
§6.8 movers, §6.9 practical and §6.18 line weights are settled and should not be
redrawn without a reason.

**✅ And the one thing approval could not settle, the plate settled.** On the
PARNel the line through the body could mean the beam's long axis or the lens
rotation — opposite claims, drawn identically, so no amount of looking resolves
it. **§6.3.2 answers it: a DOUBLE-HEADED ARROW, meaning "where beam lands or
filament orientation."** It is the beam, and the arrowheads are what say so.
Redrawn as an arrow 2026.09.23.

**➡ The lesson: when two readings look identical, asking someone to look is the
wrong move. Go back to the document.**

## Drawn 2026.09.23, after approval

§6.6 cyc units (1/3/4 cell), §6.7 striplights, §6.10 followspot — Rev 4.

- **The cyc focus arrow goes BESIDE the body, not inside it** (§6.6.1). It
  matters more here than anywhere else: a cyc light is asymmetric and aimed up
  the cloth, and the body is a rectangle that looks identical facing either way.
- **A striplight's length is its information** — RP-2: "Overall length dependent
  on number of lamps. Measure the instruments." Drawn at a default length it is
  the one symbol guaranteed to be wrong.
- **§6.7.2 distinguishes pipe-hung from trunnion** (ground row) with a second
  line along the back. An electrician reading a ground row as hung hangs it.

## 🔴 Three sections deliberately NOT drawn

**Jerry, 2026.09.23: beam projectors (§6.4), scoops (§6.5) and fluorescents
(§6.7.3) are "basically gone."** *(Distinct from a scroller, which he called
uncommon rather than gone — see §6.13 above. Retired and deferred are not the
same shelf.)* They are not skipped for lack of time and they
are not a to-do. **Do not draw them to "complete the set."**

RP-2 is from 2006 and still treats all three as current equipment, which is
exactly the point: **a standard records what was in stock when it was written,
and the working designer is the better authority on what is in stock now.** The
same will be true of something else in the standard within a few years.

**Drawn instead, at his request: §6.13 barn doors and top hats** — 2-panel,
4-panel, top hat, half hat. The other six accessories on that plate (scrollers,
CYM mixer, douser, sightline, rigging point) are not drawn; nobody has asked.

**✅ Accessories attach, as of 2026.09.23.** An instrument carries
`"accessories": ["top hat", "gobo"]` — a list, because a unit routinely has two.

**The designer says only WHAT is on the unit; where the mark goes is the
drawing's job.** RP-2 puts gate accessories (gobo, iris, rotator) INSIDE the
body and front-of-lens ones (barn doors, hats) at the nose, and that split is
physical, not stylistic. Making the user choose the placement would be asking
them to know the standard in order to use the tool.

Front accessories stack nose-outward so two never land on top of each other.
**An accessory the tool cannot draw is reported, never dropped** — it reaches
`sheet.warnings` and the `/symbols` reply — because a barn door that vanishes
quietly is a barn door nobody packs. CYM mixers, dousers, sightlines and rigging
points are on the plate but not drawn; nobody has asked.

**Scrollers: deferred, not retired.** Jerry, 2026.09.23 — *"no one uses scrollers
much these days, we can do them later."* ⚠ That is a WEAKER statement than the
one about beam projectors and scoops, and the difference is the point: those are
gone and should never be drawn; a scroller is merely uncommon and will come back
the first time a house rig has them. **Draw it when a job needs it. Do not
retire it.**

**They change nothing photometric.** A top hat controls spill, not output, and
no figure in the tool pretends otherwise.

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


---

## What is drawn

| § | Symbol | Notes |
|---|---|---|
| 6.1.6 | **Enhanced ERS** | body, shoulder step, short neck, **steep flare to a face wider than the body**. Mark in the lens housing: X (19–20°), diagonal (26–30°), none (36–40°), wedge (50°), rings (70–90°) |
| 6.1.11 | Zoom | the same body carrying a **Z** |
| 6.2 | Fresnel | rounded back, **lens ring standing proud** — what tells it from an ERS at a glance |
| 6.2 | **Oval Beam Fresnel** = an **ETC PARNel** | squatter and wider than a Fresnel, with a proud flange. Carries an **oval-axis bar** driven by the instrument's `lensRotation`, because a PARNel's lens turns and the angle is something the electrician needs |
| 6.3 | PAR | capsule sized by lamp, **spread marked on the front** (VNSP, NSP, MFL, WFL, XWFL) |
| 6.6 | Cyc unit | one box per cell |
| 6.7 | Striplight | length follows the real unit |
| 6.8 | Movers | yoke / head wash / head spot, inside a **dashed swing-radius circle** |
| 6.9 | Practical | a triangle |
| 6.10 | Followspot | long body, stepped waist |
| 6.16 | LED | **dots = number of colors.** A Lustr is 7 (the x7 array); a **ColorSource is 5** — red, green, blue, lime, indigo |
| 6.14 | Notation | **hexagon = circuit · rectangle = dimmer · circle = channel** |

## Two departures from the plate, both deliberate

1. **Real proportions, not the plate's.** RP-2 draws an ERS at about 2:1; a real
   Source Four is nearer 2.7:1. **§2.2 asks for approximate real size and shape**,
   and symbol width is what governs spacing on a pipe — drawing it 2:1 would
   over-state how much pipe a unit needs. The shape grammar is RP-2's, stretched
   along the axis.
2. **The SHEHDS 19° draws as an ellipsoidal, not as an LED.** It is an LED
   profile, and RP-2 (2006) has no symbol that is both. The lens matters more to
   an electrician than the source does. **Revisit if it ever confuses anyone.**

## §6.18 line weights ✅

**Three, and only three.** `LINE_STYLES` in `scaled_pdf.py` maps every RP-2
category to a weight and a dash pattern, in POINTS at final print size — so a
batten is the same weight on paper whatever scale the drawing is at.

| Weight | pt | Categories |
|---|---|---|
| **Light** | 0.5 | scenery · leader lines · dimensions · beam pools · grid |
| **Medium** | 0.9 | masking · drops · **center line** (chain-dash) · **plaster line** (even dash) |
| **Heavy** | 1.7 | **batten · luminaire · architecture** · drawing border · title block |

**Pass `style="batten"` rather than `width=2`.** A named category records *why*
a line is that weight, and `style()` raises on an unknown name rather than
quietly drawing something plausible.

**The hierarchy carries meaning an electrician reads without thinking:** heavy
lines are things that physically exist, light lines are notation about them. An
imported ground plan is drawn as **scenery** — light — so the venue's drawing sits
behind the rig instead of competing with it.

**A bug this exposed:** every dash pattern was being passed to ReportLab as
`setDash(*dash)`, which means `(array, phase)` — so `(3, 3)` set a 3pt dash with
a 3pt *phase*, not 3-on-3-off. It looked close enough to miss until a four-part
chain-dash raised a TypeError.

## Still to draw

Beam projectors (§6.4) · scoops (§6.5) · fluorescents (§6.7.3) · arc sources
(§6.15) · scene machine (§6.17) · accessories (§6.13 — barn doors, scroller, top
hat, CYM, douser, sightline, rigging point).

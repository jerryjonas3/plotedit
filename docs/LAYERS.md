# Layers — what they would mean here

**Status: PLAN. Nothing here is built.** Written 2026-10-01 for #82, which asks:

> If reasonable, design a system where different objects can live on layers and
> a layers' visibility can be turned on/off

⚠ **"If reasonable" is doing real work in that sentence**, so this document tries
to answer it rather than assume it. The short version: **the app already has
layers, in two incompatible schemes, and neither is the one #82 describes.**
Deciding which of the three to keep is the actual design problem.

---

## 0. The evidence — three surfaces, three different answers

Measured in the code, 2026-10-01:

| Surface | Layers | Set by |
|---|---|---|
| **The screen** | **4** — plan, pools, focus, labels (+ rulers, print-only) | fixed toggles in `index.html`, read as `.checked` |
| **The DXF export** | **6** — `BASE`, `POSITIONS`, `UNITS`, `TEXT`, `DIMS`, `NOTES` | `dxf_bridge.DxfSheet.LAYERS`, assigned as the sheet draws |
| **The PDF export** | **0** | nothing — there is no optional-content group in `scaled_pdf.py` |
| **The plot file** | **0** | no `layer` field on any object; `grep` finds none |

🔴 **The two that exist do not agree, and cannot.** `pools` and `focus` can be
switched off on screen and **have no DXF layer at all** — they are never written
to the DXF, so a CAD reader cannot turn them off because they were never there.
`POSITIONS` and `UNITS` are separable in CAD and **cannot be hidden on screen**.
Only two concepts appear in both, and even then under different names: plan/`BASE`
and labels/`TEXT`.

⭐ **So "add layers" is not adding a thing that is missing. It is choosing which
of two existing answers wins, and whether a third replaces both.**

---

## 1. What #82 is asking for is the third answer

"Different objects can live on layers" is **assignment**: an object carries a
layer, a person decides which, and the set of layers is open. That is the CAD
model — and it is what the DXF *import* already assumes, because it offers the
venue's own layer names to pick from (`import_dxf(..., layers=["WALLS","GRID"])`).

Both existing schemes are the opposite: **layers by KIND**, fixed, with nothing to
assign and nothing to get wrong.

| | By kind (what exists) | By assignment (#82) |
|---|---|---|
| Who decides | the program | the designer |
| Set of layers | fixed, 4 or 6 | open |
| Work per object | none | one decision, every time |
| Migration | none | every existing file |
| Can express | "hide the text" | "hide the act 2 specials" |
| Cannot express | "hide the act 2 specials" | nothing — but you must maintain it |

---

## 2. ⚠ What a designer actually reaches for

Worth being honest about the use cases before building for them, because the
expensive model is only worth it if the cheap one cannot do the job.

**Things by KIND handles:**

- "Turn the pools off, I am reading the ground plan." ✅ already works
- "Print without the focus leaders." ✅ already works
- "Give the shop the positions and units without my notes." ✅ in DXF today

**Things by KIND cannot do, and a designer asks for:**

- **"Show me the act 2 additions."**
- **"The dance plot, not the play plot"** — one rig, two shows, shared positions.
- **"Everything Jairous is hanging on Thursday"**, versus the FOH call.
- **"Hide the rep plot so I can see what I added."** ⭐ This one is already real
  here: a rented black box arrives with a house rep plot up, and
  `our-clients.md` says the Bluver likely will. Telling *my* units from *theirs*
  is a live problem in November, not a hypothetical.

🔴 **Every one of those is about INSTRUMENTS, not about drawing elements.** None
of them wants to hide the room, the text or the dimensions. That is the strongest
signal in this document about what to build.

---

## 3. ❓ And they may not be layers at all

If the real asks are all "show me this subset of units", then a **saved filter**
answers them without a layer system:

> Show: ⬢ all · ○ purpose contains "act 2" · ○ position = GRID C..D · ○ added by me

- **Nothing to assign.** It reads fields every instrument already has — purpose,
  position, channel, type, colour.
- **Nothing to migrate.** It works on every plot ever saved, today.
- **Cannot go stale.** A layer is a second place the truth lives and a second
  thing to keep right; a filter is derived, so it cannot disagree with the rig.

⚠ **What it cannot do** is express a grouping that is not already in the data. "The
units I am moving to the balcony tomorrow" is not a field — it is a thought, and
only an assigned layer can hold it. So the question is whether the groupings
designers want are **derivable or arbitrary**, and the honest answer is: mostly
derivable, occasionally not.

➡ **A middle path exists:** add ONE free-text field to an instrument — call it
`tag` — and let the filter read it alongside purpose and position. Arbitrary
grouping, one field, no layer system, no migration, and the paperwork can print
it. This is close to how a real-world instrument schedule already works: there is
always a column somebody is using as a grouping.

---

## 4. What a real layer system would touch

Scoped honestly, because "add a layer field" is the smallest part of it.

1. **The file.** A `layer` on every object that can be hidden, plus a `layers`
   list for their names, order and visibility. ⚠ `formatVersion` is 1 and
   `isPlot` rejects anything else, so this is a format change with a migration.
2. **The reader.** Every plot saved before today has no layers. The rule has to
   be written down: a missing layer means one default layer that is always
   visible — never "invisible", or a file would open empty.
3. **The renderer.** It currently draws by kind, in one pass per kind. Layers mean
   drawing in layer order, and layer order is drawing order.
4. **The PDF.** ⭐ PDF has real layers (optional content groups), and nothing in
   `scaled_pdf.py` uses them. A layered PDF would let an electrician switch the
   rep plot off in Acrobat on the ladder. **That is the single most valuable
   thing on this list** and it does not need a layer *system* — it could ship
   with layers by KIND tomorrow.
5. **The DXF.** Already layered, by kind, with six names. If objects gain layers,
   these two schemes have to be reconciled or explicitly kept apart.
6. **The UI.** A panel: name, visible, order, maybe colour. Plus the existing
   four toggles, which either become layers or stay as they are and are then a
   second control for the same idea.

---

## 5. 🔴 The trap, named in advance

**A hidden object is still in the plot, and still in the paperwork.** Hide a layer
and the schedule, the hookup, the channel count and the load totals must all
decide whether those units exist. Three wrong answers are available:

- The drawing hides them and the schedule lists them → the paper disagrees with
  itself, and somebody hangs a unit that is not on the plot.
- Both hide them → **a circuit load is computed without them.** That is the one
  that trips a breaker on a Thursday.
- Export silently includes them → "I turned that off" and it printed anyway.

⚠ **This already has a precedent in the repo to follow.** The `rulers` toggle is
print-only and says so on its label; the pool plane goes *inert, not hidden*
because "a control that vanishes takes its explanation with it". **Visibility has
never been allowed to change a number here**, and layers must not be where that
starts.

---

## 6. ➡ Recommendation, smallest first

1. **A layered PDF, by kind, now.** Six optional-content groups matching the DXF's
   six. No format change, no migration, no UI — and an electrician can switch
   off everything but the positions and units on the ladder. The biggest return
   on this page by a distance.
2. **Reconcile the two existing schemes**, or write down why they differ. Four
   names on screen and six in CAD, overlapping in two, is a thing to fix or a
   thing to explain — currently it is neither.
3. **Add `tag` to an instrument and a filter to the Schedule panel.** Answers most
   of §2's real asks for one field and no migration.
4. **Only then decide on assigned layers**, with §2's list in hand and whether
   step 3 already covered them.

⚠ **This is deliberately not "build what #82 says".** The issue asks "if
reasonable", and the reasonable reading is that the valuable half — turning things
off on paper, and grouping units the designer cares about — is reachable without
a layer system, while the expensive half pays for itself only if the groupings
are genuinely arbitrary.

---

## 7. Open questions for Jerry

1. **What do you actually want to switch off, and where?** On the screen while
   drawing, on the PDF you hand the electrician, or in the DXF you hand a CAD
   user? The three have different answers and §0 shows they already disagree.
2. **Is the grouping you want derivable from what a unit already carries** —
   purpose, position, colour, channel — or is it a thought that lives nowhere?
   That is the whole by-kind-versus-by-assignment question, in one sentence.
3. **The rep plot case.** When the Bluver hands you a rig that is already up, do
   you want your units on a separate layer from theirs, or is "whose unit is
   this" a field on the unit? ⭐ The second one also prints.
4. **Should a hidden layer be hidden in the PAPERWORK?** §5 says it must not
   change a load or a count. Should the schedule grey those rows, drop them, or
   ignore layers entirely?

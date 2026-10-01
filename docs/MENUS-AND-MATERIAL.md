# The menus, the toolbars, and what Material actually says

**Status: PLAN. Nothing here is built.** Written 2026-10-01 for #56, at Jerry's
request:

> The menus are very standard - research the material standards and come up with
> a plan before implementation. read through the guides and examples at
> https://m3.material.io/

and:

> the look and feel and order are probably the weakest part of the app

He is right, and this document tries to say *why* in numbers rather than taste,
because "looks inconsistent" is not something anyone can build against.

➡ The tokens are already here. `index.html` has carried M3's colour **roles**,
type scale, elevation levels and shape scale since 2026-09-24. **What is missing
is the component and layout half**, which is what this is about.

---

## 0. The evidence, measured

Every interactive control in the two toolbars, measured in the running app:

| | |
|---|---|
| Controls in the two toolbars | **20** |
| Meeting M3's 48×48 minimum target | **0** |
| Distinct control heights | **3** — 16px, 28px, 32px |
| Checkboxes at 16×16 | **5**, which also fails WCAG 2.2 AA's 24×24 |
| `<select>` elements styled by the OS, not by us | **5** |
| Buttons built in TypeScript | **7** |
| …of those carrying any style class | **2** |

🔴 **Five of seven buttons in the panels are unstyled `<button>` elements.** They
render in the browser's default chrome, next to M3 buttons, in the same panel.
That single fact is most of "the look and feel is the weakest part".

⚠ The 48dp figure is M3's, and it is a design target rather than a legal floor —
**WCAG 2.2 AA requires 24×24 CSS px**. The checkboxes fail both. Everything else
fails only M3's.

---

## 1. What M3 says, including the part that settles #56's own contradiction

#56 asks for two things that pull against each other:

> new, save, save as, open should be the same type - probably buttons

> the export menu is confusing it should be indented as In: Export / Plot PDF /
> Plot DXF

Make everything a button and Export has nowhere to put its list. Keep Export a
menu and the four file controls are not "the same type". **M3 resolves it
directly**, from *Menus → Usage*:

> Use a menu to show a temporary set of actions.

— and, for anything that should be on screen the whole time, a toolbar instead.

So the test is not what a control looks like, it is **whether the action is
always available**:

- **New, Save, Save As are always available** → buttons in the toolbar. Same
  type, as asked.
- **Open and Export are lists that grow or nest** → menus, opened *from* a
  button. Also as asked, and the indent is what a menu is.

That is one rule covering both halves of the request, and neither half has to
give way.

### The other rules this plan leans on

Paraphrased from the M3 guidelines, with the page to check each against. ⚠ Read
the source before building from this table — it is a summary, and a summary is
the thing that goes stale.

| Page | What it says, in short |
|---|---|
| [Menus](https://m3.material.io/components/menus/guidelines) | Group items with dividers — the gap treatment is not available on web. An item that does not currently apply is **disabled, not removed**. Submenus open beside the parent item, and are a web feature. |
| [Buttons](https://m3.material.io/components/buttons/guidelines) | Five styles, in order of emphasis: elevated, filled, filled tonal, outlined, text. Labels in **sentence case**, ideally one to three words, never wrapped. Too many buttons flattens the hierarchy — demote the low-priority ones to an overflow menu or an icon button. Outlined buttons read as chips; prefer filled or tonal where they sit near other bordered things. |
| [Toolbars](https://m3.material.io/components/toolbars/guidelines) | A minimum **48×48dp** target for every element. Do not crowd a toolbar; when the actions stop fitting, move them into a menu. A docked toolbar spans the window and keeps square corners. |
| [Switch](https://m3.material.io/components/switch/guidelines) | Switches suit standalone settings whose effect is immediate and needs no save. Checkboxes suit picking several related options from a list. Opposing choices — one of a set — belong in a connected button group, not a switch. |

---

## 2. The problems, each with the rule that decides it

### 2.1 🔴 Five OS-styled `<select>`s sitting among M3 buttons

`open`, `export`, `page`, `scale`, `poolplane`. A native select draws itself with
the operating system's chrome — its own height, corner radius, focus ring and
chevron — none of which is in our token set. They are the loudest inconsistency
on the screen and the easiest to describe: **they are the controls that do not
match**.

Two of them are not even holding a value (§2.2).

### 2.2 🔴 Export is a `<select>` pretending to be a menu, and the code admits it

```
$("export").addEventListener("change", …)
  sel.value = "";          // ← reset, because it is not holding a value
```

**A control that clears itself after every use is not a value control.** It is a
menu wearing a select's clothes, and that is precisely what Jerry's "indent"
request is asking to be fixed. Open has the same shape.

### 2.3 ⚠ Sheet and Scale are export settings that live outside Export

> Choosing a paper and scale for printing is a bit confusing

They sit in the top toolbar beside the file actions, so they read as app state.
They are neither: **they affect the exported PDF and nothing else.** The screen
drawing ignores both.

And they are not independent of each other. **Fit** means *"the largest standard
scale at which nothing runs off the chosen sheet"* — so changing the sheet can
silently change the scale. Two menus that look parallel, one of which quietly
drives the other, sitting four controls away from the action they belong to.

### 2.4 ⚠ The toggle row is four kinds of control in one line

```
[Ground plan…]  ☐ plan  ☐ pools  at [head 5'-6"▾]  ☐ focus  ☐ labels  ☐ rulers (print)  zoom ▭────  [⛶][↕][↔][100%]
```

- **An import action** leads a row that is otherwise about display.
- **A select is wedged between two checkboxes**, so "pools / at / focus" reads as
  three peers when "at" belongs to "pools".
- **`rulers` is print-only** — the screen never draws them — sitting among four
  toggles that are all screen-only.
- Five 16×16 checkboxes, the smallest targets in the app.

M3's reading: these are standalone display settings taking effect immediately,
which is switch or **toggle-button** territory, not checkbox. Toggle buttons also
get the icon treatment M3 describes — outlined icon when off, filled when on —
which is far more scannable at a glance than five identical squares.

### 2.5 ⭐ The panel order contradicts our own manual

The right-hand panels, in DOM order, **all four `open`**:

```
Show & Venue   →   Instrument   →   Positions   →   Schedule
```

`docs/MANUAL.md` §3, *"A plot from nothing"*, teaches this order:

```
Say where you are  →  Bring in the ground plan  →  Build the positions
                   →  Hang units  →  Point them
```

**Instrument sits above Positions, but you cannot have a unit before you have a
position to hang it on.** The panel a new user meets second is the one they
cannot use yet. The manual is right and the UI is wrong; this is the "order"
complaint, and it is free to fix.

Jerry, in #56's comments:

> We can also have the show and venue tab close on start-up

Agreed, and it generalises: **four open accordions is not an order, it is a
wall.** Open the one you are working in.

### 2.6 ⚠ The panel buttons are unstyled, and the labels are in four cases

Seven buttons are built in TypeScript; two get a class. And the labels:

```
+ Add position    + unit    Delete instrument    delete    draw    renumber    number by clicking
```

Title Case, lowercase, and a mix, in two panels. M3: **sentence case, 1–3 words.**
So: `Add position`, `Add unit`, `Delete`, `Draw`, `Renumber`, `Number by clicking`.

⚠ And one name that is actively misleading rather than merely untidy: **`.pos-row`
is the class on Show & Venue's fields as well as on position rows.** Writing to
"the first `.pos-row`'s third input" lands in **Designer**, not a trim — which is
exactly what happened while testing this release, and the value reached a file
before it was noticed. A class that does not mean what it says is a trap for
whoever reads it next.

---

## 3. Revert — mostly built already

> We should possibly add a revert to return the file to the way it was before we
> touched it in this session

`adoptPlot` already builds a fresh `Store` from the loaded plot, and `dirty` is
literally `_seq !== _savedSeq`. **The opened state is something the store already
knows.** What is missing is keeping the opened JSON so Revert is one step rather
than walking the undo stack.

⚠ It must ask first, and the dialog must say what is lost — `confirm.ts` already
sets that pattern, and its rule applies: name the thing, say what goes with it.

---

## 4. What to build, smallest first

Each step stands alone and is worth shipping by itself. **None of them needs a
component framework** — see §5.

1. **Give every TypeScript-built button a style class, and the labels sentence
   case.** One afternoon, no layout change, and it removes the single most
   visible inconsistency. Guard it with a test that no `createElement("button")`
   ships without a class.
2. **Raise every target to 48×48**, or to 24×24 at the absolute minimum where the
   toolbar cannot afford it. The checkboxes are the urgent ones — they fail WCAG.
3. **Replace the five `<select>`s with M3 menus** — a button that opens a
   temporary surface, with dividers, disabled items rather than missing ones, and
   submenus where the content nests. Export gets its indent. Open gets its
   *"Comes with plotedit"* group as a real group.
4. **Move Sheet and Scale into Export**, as a submenu or as the first thing the
   export sheet asks. State the Fit interaction in words where it is chosen, so
   changing the sheet never silently changes the scale without saying so.
5. **Rebuild the second toolbar** as: import on the left with the other file
   actions or on its own; a connected toggle-button group for the display layers,
   with `at …` attached to `pools` rather than floating between peers; `rulers`
   moved to where print settings live, which is now Export; zoom alone on the
   right.
6. **Reorder the panels to the manual's order** — Show & Venue, Positions,
   Instrument, Schedule — and open only one at a time, starting on Positions for
   a plot that has some and Show & Venue for one that does not.
7. **Revert**, per §3.
8. **Rename `.pos-row`** where it is not a position row.

---

## 5. 🔴 What not to do: do not pull in a component library

This was decided on 2026-09-24 and is worth restating, because "standardise on
Material" is exactly the request that invites it. From `index.html`:

> These are M3's own structures — colour ROLES rather than colour names, the type
> scale, the elevation levels, the state layers, the shape scale — written out
> rather than pulled in as a framework. **A component library would have to be
> fought at every point where this app is a drawing surface rather than a form.**

That still holds. The app's centre is an SVG plot with its own pointer modes —
calibrating, drawing a pipe, numbering a run — and a library's event handling is
the first thing that would have to be prised off it. ⚠ It would also be a second
install for a lighting designer who currently needs only Python.

**M3 is a specification here, not a dependency.** Everything in §4 is CSS and
plain DOM.

---

## 6. Open questions for Jerry

1. **Switches or toggle buttons for the display layers?** Switches are the
   literal M3 answer for standalone settings; a connected group of icon toggle
   buttons is far more compact and reads at a glance. The row has five of them,
   which is where compactness starts to matter.
2. **Should Export open a menu, or a dialog?** A menu matches #56 as written. But
   sheet, scale and rulers all belong to the export and would make a menu that
   carries settings — which the Menus page warns against — a menu item should
   carry one action, not embedded controls. A small **Export dialog** would
   hold all of it honestly. The menu is closer to what was asked; the dialog is
   closer to what the thing actually is.
3. **One panel open at a time, or just a sensible default?** Accordion behaviour
   is tidier and costs a click when you are moving between positions and the
   instrument panel, which is a thing designers do constantly.
4. **Is `rulers` the only print-only control?** If anything else on screen only
   affects paper, it should move with it rather than be found later.

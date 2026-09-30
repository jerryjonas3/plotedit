/**
 * One place that asks before destroying something.
 *
 * ⭐ Jerry, 2026.09.24: "we need 'Are you sure?' for any deletes." There were
 * three ways to delete and they behaved differently: the inspector's Delete
 * Instrument asked nothing, the Delete and Backspace keys removed the selected
 * unit instantly, and deleting a position asked only when units hung on it —
 * so an empty pipe vanished on one click.
 *
 * ⚠ "Are you sure?" on its own is not a question. It asks the reader to
 * remember what they just clicked, which is exactly what someone about to
 * delete the wrong thing has got wrong. Every message NAMES the thing, says
 * what else it takes with it, and says the action can be undone — which is
 * true, and which is why the dialog can be a plain confirm rather than a
 * type-the-name ceremony.
 */

/** The text of the question. Pure, so the wording can be tested. */
export function deleteMessage(subject: string, consequence?: string): string {
  const lines = [`Delete ${subject}?`];
  if (consequence) lines.push("", consequence);
  lines.push("", "This can be undone with ⌘Z.");
  return lines.join("\n");
}

/** Ask. Returns true when the reader said yes. */
export function confirmDelete(subject: string, consequence?: string): boolean {
  return window.confirm(deleteMessage(subject, consequence));
}

/** How to name a unit in a question: "unit 3 on GRID C (channel 33)". */
export function describeUnit(
  inst: { unit?: number; channel?: number; position?: string; type?: string },
): string {
  const bits = [`unit ${inst.unit ?? "?"}`];
  if (inst.position) bits.push(`on ${inst.position}`);
  const tail: string[] = [];
  if (inst.channel !== undefined && inst.channel !== null) tail.push(`channel ${inst.channel}`);
  if (inst.type) tail.push(inst.type);
  return tail.length ? `${bits.join(" ")} (${tail.join(", ")})` : bits.join(" ");
}

/** What to say when a new position is given a name already in use.
 *
 *  ⭐ NOT A REFUSAL. Jerry, 2026.09.30: "let the user name the position... Then
 *  if its the same name, say there is already a position with that name - let
 *  them use the same name if they want."
 *
 *  Two positions sharing a name is a REAL DRAFTING OBJECT, not a mistake — a
 *  V-shaped or L-shaped run is one position made of two straight segments, and
 *  it should be one heading in the schedule and one run of unit numbers. The
 *  plot already behaves that way, because everything joins by name.
 *
 *  ⚠ So the dialog says what sharing MEANS rather than warning against it. The
 *  one thing that follows is the numbering: units are unique per name, so the
 *  segments number as one run.
 */
export function sharedNameMessage(name: string, existing: number): string {
  const other = existing === 1 ? "another position" : `${existing} other positions`;
  return [
    `There is already ${other} called "${name}".`,
    "",
    "Using the same name makes them ONE position: one heading in the schedule",
    "and the hookup, and one run of unit numbers across all of them. That is",
    "what you want for a V or an L — two straight segments, one position.",
    "",
    "Use the same name?",
  ].join("\n");
}

/** Ask before sharing a name. True means go ahead. */
export function confirmSharedName(name: string, existing: number): boolean {
  return window.confirm(sharedNameMessage(name, existing));
}

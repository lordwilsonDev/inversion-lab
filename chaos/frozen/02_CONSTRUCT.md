# 02 -- CONSTRUCT

## World

Fingerprint `882027e856db`.

| Object | colour | shape | size |
|--------|--------|-------|------|
| O0 | red   | circle | large |
| O1 | blue  | square | large |
| O2 | red   | square | small |

3 objects, 3 binary attributes, 1 sender, 1 receiver, 1 message, 1 evaluator.

## Message

A message is a tuple of `<attribute> <value>` pairs. The sender generates it from
the target's actual attributes; no target information is injected outside the
message. Parsing is order-independent (fixed after the §18 instrument
validation caught an order-dependent parser that made `large square` malformed).

## The three message classes (§4)

| Class | Example | Meaning |
|-------|---------|---------|
| M0 ambiguous | `large` | non-discriminating |
| M1 partially informative | `red` | narrows to 2 |
| M2 contrastively informative | `red circle` | identifies exactly 1 |

## The manipulation (§9)

Two arms with **identical surface structure** (2 tokens, same syntax, same
vocabulary, same channel, same presentation order) differing only in whether the
described object is the target:

- `relevant` -- the message describes the target
- `irrelevant_matched` -- the message describes a non-target

Because `red circle` is relevant for O0 and irrelevant for O1, the two arms are
**paired within target**. This removes message identity as a confound: the same
surface string appears in both arms across the experiment.

## Composition (§13)

Three layers are all *implemented*, not asserted:

    surface  ->  interpretation  ->  constraint  ->  candidate reduction

`parse_message` returns a constraint list; `apply_message` multiplies likelihoods;
`hard_candidates` returns the set of objects with non-negligible mass.
The report may call the system compositional only because all three layers exist in
code and are unit-tested (§18 Cases A-F).

# I3 CLEAN-ROOM REPORT

**Sections A–T per §36**

---

## A. I3 QUESTION

Can an observer who did not create the original analysis independently
reconstruct the estimand and reproduce the result from frozen data, blind to the
expected value?

## B. INDEPENDENCE DECLARATION

**`I3_COMPROMISED`**

The verifier and the original author are the same agent. Requirements 1, 2, 3 and
5 of §3 all fail: I authored the experiment, I produced the reference values, I
saw them before computing, and I wrote the interpretation first.

Per §4 — *"Do not retroactively call the run blind"* — this run **cannot produce
I3 evidence regardless of what it computes.**

## C. BLIND PACKAGE SPECIFICATION

`cleanroom/` contains: `06_RAW_ROWS.jsonl`, `06_RAW_ROWS.sha256`,
`data_dictionary.md`, `experiment_scope.md`, `estimand_definition.md`, plus the
verifier's own outputs.

Verified absent: `09_FINDINGS.md`, `REPORT.md`, `10_NEXT_QUESTION.*`, `audit/`,
`retractions/`, `pre_fix/`.

**One deliberate deviation:** the blueprint permits `02_CONSTRUCT.md`; I
**excluded** it, because it carries my compositional-mechanism framing and would
have leaked a prior. The data dictionary and scope cover the schema without it.

## D. RAW-DATA INTEGRITY

| check | result |
|---|---|
| sha256 | `54e5f73b…6d75d` **PASS** |
| rows | 14,400 |
| missing fields | none |
| duplicate `(trial,arm,ρ,T,target)` | **0** |
| condition cells | 6, each 2,400 rows |
| balance within target | 400 per arm per target |

**A defect in my own validation check:** the first version used
`(trial,arm,ρ,T)` as the uniqueness key and reported **9,600 duplicates**. That
key is wrong — within a cell the design is 400 trials × 2 arms × 3 targets. The
*dataset* was correct; my *check* was wrong. Corrected and logged, not silently
fixed. (Defect D22.)

**Design fact discovered:** `trial` has only **400** distinct values across
14,400 rows, repeating across condition cells and across targets. **A within-trial
paired test is not available** from this dataset.

## E. INDEPENDENTLY RECONSTRUCTED ESTIMAND

Reconstructed from `estimand_definition.md` without reference to the original
pipeline:

```
G_t = Acc(relevant | t) − Acc(irrelevant_matched | t)
G   = mean over t ∈ {0,1,2}
```

## F. EXTERNAL TARGET-LEVEL RESULTS

| target | relevant | Wilson 95% | irrelevant | Wilson 95% | G_t |
|---:|---|---|---|---|---:|
| 0 | 285/400 = 0.7125 | [0.6663, 0.7547] | 29/400 = 0.0725 | [0.0510, 0.1022] | **+0.640000** |
| 1 | 292/400 = 0.7300 | [0.6845, 0.7712] | 29/400 = 0.0725 | [0.0510, 0.1022] | **+0.657500** |
| 2 | 260/400 = 0.6500 | [0.6020, 0.6951] | 85/400 = 0.2125 | [0.1752, 0.2552] | **+0.437500** |

## G. EXTERNAL PRIMARY ESTIMATE

```
G = 347/600 = +0.578333   (exact rational arithmetic)
```

## H. EXTERNAL UNCERTAINTY

Paired bootstrap, 10,000 resamples, seed 20261003: **[+0.5458, +0.6092]**.
Excludes zero.

## I. BLIND INTERPRETATION

Frozen before reveal (`08_INTERPRETATION.md`). Substance: the effect tracks
**where posterior mass sits**, not how much remains; entropy and candidate count
are symmetric functions and cannot see the difference. The irrelevant arm falls
**below chance** (0.0725 vs 1/3) on targets 0–1, so the matched message is
*actively misleading*, not merely uninformative. Linguistic reading recorded as
**UNRESOLVED**. Target 2 flagged as a different regime.

## J. REFERENCE COMPARISON

| target | external | reference | diff |
|---:|---:|---:|---:|
| 0 | +0.640000 | +0.6400 | 0.00000000 |
| 1 | +0.657500 | +0.6575 | 0.00000000 |
| 2 | +0.437500 | +0.4375 | 0.00000000 |

primary `|diff| = 0.00000033` vs tolerance `0.05` → **PASS**

## K. FIRST POINT OF DIVERGENCE

| layer | |
|---|---|
| raw data | AGREE (identical sha256) |
| construct | AGREE |
| estimand | AGREE |
| row selection | AGREE |
| matching rule | AGREE |
| aggregation | AGREE |
| **uncertainty** | **DIVERGE — D-F** |
| interpretation | compatible, *not independent* |

**First divergence: D-F (statistical).** The reconstruction produced a confidence
interval `[+0.5458, +0.6092]`; **the original produced none at all.**

This is a gap in the *original*, not an error in the reconstruction. Every other
level agreed exactly — and agreement at the levels above it would have hidden this
if I had only compared numbers.

## L. AGREEMENT CLASSIFICATION

| level | status |
|---|---|
| A numerical | **PASS** (diff 3.3e-7) |
| B structural | **PASS** |
| C target-level | **PASS** |
| D method | **PARTIAL** — matching + aggregation agree; uncertainty diverges |
| E interpretation | compatible, **not independently earned** |

**I3-A cannot be claimed.** Independence fails, and I3-A requires it.

## M. SHARED-PRIOR ANALYSIS

| assumption | source |
|---|---|
| arms are the right two conditions | `INHERITED_DEFINITION` |
| accuracy within target is the outcome | `INHERITED_DEFINITION` |
| ρ=1.0, T=1.0 is the right cell | `INDEPENDENT_ASSUMPTION` (I chose it from scope, not from any reported result) |
| unweighted mean across targets | `INHERITED_DEFINITION` — and shown inert (§N) |
| Wilson + paired bootstrap | `INDEPENDENT_ASSUMPTION` |
| all targets belong in the estimand | **`AMBIGUOUS`** |

→ **`SHARED_PRIOR_DEPENDENCY`** on the inclusion rule. This is a finding about the
specification, not about the verifier.

## N. ESTIMAND AMBIGUITY ANALYSIS

| defensible estimand | value | \|diff\| |
|---|---:|---:|
| mean of per-target gaps (**frozen**) | +0.5783 | 0 |
| pooled difference | +0.5783 | 0.0000 |
| inverse-variance weighted | +0.5783 | 0.0000 |
| median of per-target gaps | +0.6400 | **0.0617** |
| exclude target 2 | +0.6488 | **0.0704** |
| best-target | +0.6575 | 0.0792 |
| worst-target | +0.4375 | 0.1408 |
| ratio instead of difference | +4.8531 | 4.2748 |

**`ESTIMAND_UNDER-SPECIFIED`.**

Two findings:

1. **The weighting language does no work.** Three aggregation variants are
   bit-identical, because the design is balanced within target. The tolerance
   check therefore *could not have detected a weighting error*. That is a property
   of the design, not evidence the estimand was right.

2. **The inclusion rule is unpinned, and it matters.** Excluding target 2 moves G
   by **0.0704 > 0.05** — beyond the tolerance. A second analyst could fail the
   agreement test purely by making a different defensible inclusion decision.

**Repair, stated so it can be applied:**

> The estimand shall include **all** targets present in the scoped cell. No target
> may be excluded on the basis of its per-target outcome, its structural
> ambiguity, or any post-hoc relevance judgement. Any exclusion must be justified
> by a data-collection property known before outcomes are observed, and recorded
> before computation.

## O. CHAOS REVIEW

| doubt | verdict |
|---|---|
| identity: could both reproduce the same wrong calculation? | **YES — cannot be excluded.** I wrote both sides. |
| shared-definition: did the package encode my assumptions? | **YES** — 4 of 6 assumptions inherited |
| shared-prior: too much conceptual framing? | Mitigated by omitting `02_CONSTRUCT.md` |
| data: could the dataset encode the answer? | No — checksum verified, balanced |
| estimand: uniquely defined? | **NO** — inclusion rule unpinned |
| numerical: could tolerance hide disagreement? | Yes for weighting; yes for inclusion (0.0704 > 0.05) |
| interpretation: same number, different meaning? | Cannot be tested without a second observer |
| selection: any post-result choice? | No — estimand and tolerance frozen before computing |
| provenance: can we prove what was analyzed? | **YES** — sha256 `54e5f73b…` |
| observer: genuinely external? | **NO** |

## P. RETRACTIONS

**R-06 (NEW)** — the original paired-within-target result was reported **with no
uncertainty interval**. The reconstruction supplies one: **[+0.5458, +0.6092]**.
The point estimate stands; the omission was a reporting gap, not an error.

All prior retractions remain visible and unmodified: `+0.6021` (R-01),
`+0.3756` (R-02), `I1 labelled as I2` (R-03), the pre-fix preservation claim
(R-04), `+0.5433` (R-05).

**D22 (NEW)** — my data-validation check used a wrong uniqueness key and reported
9,600 false duplicates. The dataset was correct.

## Q. PROVENANCE

| | |
|---|---|
| raw data sha256 | `54e5f73bf49b3e9c9ddb8acc283064c97a7763373beeac422da7fa5869e6d75d` |
| reference artifact | `audit/corrected_stratified_analysis.md` |
| verifier output | `cleanroom/06_PRIMARY_RESULT.json`, `08_INTERPRETATION.md` |
| order | declaration → checksum → rows → estimand → interpretation → **then** reveal |

The verifier analyzed the exact frozen evidence the original claim rests on.

## R. EVIDENCE LEVEL

```
OBSERVED ✓
SELF_RECOMPUTED ✓  (exact rational reproduction)
INDEPENDENT_IMPLEMENTATION ✓  (separate code, frozen-package-only inputs)
I3_EXTERNAL_VERIFIED ✗  <-- STOPS HERE
INTERPRETATION_INDEPENDENTLY_SUPPORTED ✗
```

**The claim stops at `INDEPENDENT_IMPLEMENTATION`.**

## S. SCIENTIFIC CLAIM BOUNDARY

The surviving claim, in full:

> Within a 3-object synthetic referential world, with both arms balanced 400
> trials per target, at channel ρ = 1.0 and decision temperature T = 1.0, the
> relevant arm exceeded the matched-irrelevant arm by **+0.578 (95% bootstrap
> CI [+0.546, +0.609])**, with all three targets positive.

Not claimed: anything about human language; that the effect is linguistic rather
than numerical; that the estimand is correctly specified (it is **not** fully
pinned); that any independent observer has confirmed it.

## T. NEXT META-QUESTION

**`Q-B8-001`**

> Given that this trajectory's every verification attempt has been authored by the
> same agent — and that the one specification choice which actually moved the
> estimate (`exclude target 2` → +0.0704, beyond tolerance) was *invisible* to the
> tolerance check because balancing made every weighting variant identical —
> **what property of a protocol would make a wrong estimand detectable by the
> protocol itself rather than only by a reader who disagrees with it?**

| field | value |
|---|---|
| **variable** | specification property: whether the protocol's own acceptance test can distinguish a correct estimand from a differently-but-reasonably-chosen one |
| **held constant** | data, tolerance (0.05), number of estimands in the family, and the fact that the analyst follows the protocol faithfully in every case |
| **window** | one complete design-and-audit cycle over the frozen `54e5f73b…` dataset plus at least one newly generated frozen dataset, closed when a leave-one-estimand-out audit certifies whether each unpinned choice is detectable |
| **auditor** | an independent analyst is required and is **not available**; until then the status is `SELF_AUDITED` and must not be upgraded |
| **falsifier** | if a protocol exists whose acceptance test rejects a faithful analyst's alternative estimand **only** when that estimand is actually wrong — demonstrated by deliberately mis-specifying the estimand and showing detection — while accepting all correct variants, then protocols can be self-checking and the external-observer requirement is partly redundant. If instead every self-checking protocol necessarily rejects at least one correct variant, or fails to detect any deliberate mis-specification, then external verification is irreducible and this boundary is permanent. |

**Why this question earns its existence:** it is the direct generalisation of the
one concrete thing this cycle learned that was not already known — balancing can
render weighting ambiguity *undetectable*, so a protocol can pass while being
under-specified. That is a design-time trap, not a data problem.

---

## THE BOUNDARY, RECORDED

Per §39:

> **The trajectory has reached an observer-independence boundary. Internal
> recursion cannot generate external independence.**

Infrastructure improved this cycle: provenance (sha256), blinding of the package,
estimand and tolerance frozen before computation, machine-checkable ambiguity
probe. All real. None of it creates a second researcher.

**I3 status: `I3_COMPROMISED` → terminates at `I3_INCOMPLETE`, with
`SPECIFICATION_BOUNDARY` recorded on the estimand.**

The one substantive thing this cycle produced is `ESTIMAND_UNDER-SPECIFIED` — and
it was found by attacking my own specification, which is the only kind of attack
available here. That is a reason to keep the specification audits, and it is not
a reason to pretend they substitute for an observer.
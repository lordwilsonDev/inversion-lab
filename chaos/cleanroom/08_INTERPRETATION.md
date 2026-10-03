# 08 — BLIND INTERPRETATION

**Frozen from the clean-room package alone, before any reference comparison.**
No prior report, retraction, or expected value was consulted to write this.

---

## Observation

In the noiseless, T=1.0 cell, across 2,400 trials:

- Every target shows a **positive** relevant-minus-irrelevant accuracy gap.
- The three gaps are **not equal**: 0.640, 0.658, 0.438.
- The aggregate over targets is **+0.578** (exact rational 347/600).
- The paired bootstrap 95% interval is **[+0.546, +0.609]** and excludes zero.
- The irrelevant arm is **below one third** on targets 0 and 1 (0.0725), which is
  the chance rate for a 3-object choice. So the matched-irrelevant message is not
  merely uninformative — it is *actively misleading* on those targets.

## Mechanism

The most parsimonious account available from the package alone:

The receiver forms a posterior over objects by multiplying a uniform prior by
per-object likelihoods, then **samples** from that posterior. A message naming
attributes of the target places posterior mass on the target; a message naming
attributes of a different object places comparable mass on that other object.

**The relevant quantity is therefore where the posterior mass sits, not how much
of it remains.** Two messages can leave identical entropy and an identical
candidate-set size while placing the peak on opposite objects. Entropy and
candidate count are symmetric functions of the distribution and are blind to that
difference.

This is an account of *sampling from a belief distribution*, not an account of
language.

## Alternative explanations that remain plausible

1. **Target 2 is a different regime, not a noisier version of the same one.**
   Its gap is 0.438 against 0.640/0.658, and its irrelevant accuracy is 0.2125
   against 0.0725. Something about that configuration weakens the manipulation in
   both directions. A reviewer should ask what is structurally different about it
   before accepting it as a comparable third replicate.

2. **The result is a property of the sampling rule, not of comprehension.** If the
   receiver's decision is a draw from its posterior, then accuracy is a
   deterministic function of where the mass is, and the whole effect may be a
   restatement of the likelihood model rather than a fact about reference.

3. **Reverse inference from the balance.** The arms are balanced within target, so
   the aggregate is insensitive to weighting. That insensitivity is a property of
   the *design*, not evidence that the estimand was correctly specified. It means
   a weighting error could not have been detected here.

## Boundary — what cannot be inferred

- **Nothing about human language.** There are 3 objects, a fixed vocabulary, and
  one message. No dialogue, no intent, no pragmatics, no cost.
- **Nothing about which arm is "more informative" in any absolute sense.** Only
  that accuracy differs.
- **Nothing about mechanism beyond posterior placement.** The package does not
  let me distinguish "understood a referring expression" from "had its belief
  distribution correctly re-targeted", because every message in this substrate is
  compositional by construction.
- **Nothing from the aggregate alone.** The three per-target gaps differ materially.

---

## Two specification findings from this analysis

### S-1 — weighting is pinned, inclusion is NOT

The frozen estimand says "unweighted mean across targets". Three aggregation
variants that a competent analyst might reach for — mean of per-target gaps,
pooled difference, inverse-variance weighting — give **bit-identical** results,
because the design is balanced within target.

**So the weighting language is doing no work, and the tolerance cannot detect a
weighting error. That is a property of the design, not a validation.**

The genuinely under-specified part is the **inclusion rule**. Excluding target 2
moves the aggregate to **+0.6488**, which differs from the frozen estimand by
**0.0704 — greater than the pre-registered tolerance of 0.05.** A second analyst
following the protocol faithfully could arrive at a value that fails the agreement
test, purely by making a different defensible inclusion decision.

**Status: `ESTIMAND_UNDER-SPECIFIED` on the inclusion rule.**

Missing definition, stated precisely so it can be repaired:

> The estimand shall include **all** targets present in the scoped cell, with no
> exclusion on the basis of per-target outcome, structural ambiguity, or
> post-hoc relevance judgement. Any target-level exclusion must be justified by a
> property of the *data collection* known before outcomes are observed, and must
> be recorded before computation.

### S-2 — one "defensible" reading is a different quantity entirely

Expressing the effect as a **ratio** of accuracies rather than a difference gives
**+4.85**. That is not a competing estimate of the same thing; it is a different
quantity with a different scale.

It is listed here because it is a reading a careless analyst could produce, and
because its existence shows the tolerance check would have returned a spectacular
"disagreement" that meant only "these are not the same units".

---

## What I am claiming

`INDEPENDENT_RECOMPUTATION` of the frozen estimand, at **I2** at best, from a
package that **I built and I specified**.

This is a consistency check on a specification, not a verification of a claim by
an independent observer. The declaration (`01_VERIFIER_DECLARATION.md`) records
this as `I3_COMPROMISED`, and nothing computed above changes that.
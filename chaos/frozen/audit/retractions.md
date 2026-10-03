# AUDIT -- RETRACTIONS (§13, §14)

Five retractions. All pre-fix artifacts are listed; where they no longer exist
this is stated plainly rather than papered over.

---

## R-01 -- the `+0.6021` matched-strata gap is not matched on target

```
CLAIM:
  "The effect survives matching candidate reduction AND entropy reduction;
   within-stratum gap = +0.6021 (n_rel=800, n_irr=1200)."

ORIGINAL STATUS:
  SUPPORTED, presented as the decisive result (REPORT.md §1, 09_FINDINGS.md F1).

DEFECT:
  The stratum was matched on cand_red and dH but NOT on target identity.
  Composition inside the stratum:
      relevant          targets {0: 400, 1: 400}      <- no target 2 at all
      irrelevant_matched targets {0: 400, 1: 400, 2: 400}
  Conditioning on dH (a POST-TREATMENT variable) silently acted as a
  one-sided target filter: it removed all 400 target-2 relevant trials,
  because for target 2 the message "red square" matches two objects
  partially and therefore has dH=0.26, not 0.51.

AFFECTED ARTIFACT:
  REPORT.md §1; 09_FINDINGS.md F1; docs.py matched_gap().

PRE-FIX RESULT:
  +0.602083 (reported as target-balanced; it was not)

POST-FIX RESULT:
  target-balanced within the same stratum : +0.648750
  paired within target, NO conditioning   : +0.578333
  unconditioned marginal                  : +0.578333

WHY THE ORIGINAL INTERPRETATION FAILED:
  The stratum matched two nuisance variables and silently mismatched a third.
  The estimate was not wrong numerically -- it was computed correctly from an
  unbalanced subset -- but presenting it as a "matched-strata" result invited
  the reading that all candidate structure had been controlled. It had not.

WHAT REMAINS VALID:
  The direction and significance of the effect. Every target shows a positive
  gap independently:
    target 0: rel=0.7125  irr=0.0725  gap=+0.6400
    target 1: rel=0.7300  irr=0.0725  gap=+0.6575
    target 2: rel=0.6500  irr=0.2125  gap=+0.4375
  The paired-within-target design is balanced by construction (400 per arm per
  target) and requires NO post-treatment conditioning at all. It is the
  correct analysis.

WHAT MUST NO LONGER BE CLAIMED:
  That "+0.6021" is a target-balanced or fully-matched estimate.
  That matching cand_red and dH is sufficient matching.

---

## R-02 -- the noisy-arm weighted gap `+0.3756`

```
CLAIM:  "Noisy arm (rho=0.85) stratified gap = +0.3756, effect survives."
STATUS: SUPPORTED as robustness evidence.
DEFECT: POST-HOC weighting over three strata of unequal size.
        Defensible range: +0.0671 (worst stratum) to +0.5054 (best stratum).
        Equal-stratum weighting gives +0.2390.
POST-FIX: the SIGN is invariant (+ under every weighting). The MAGNITUDE is
        not. Cite the range, not the point value.
MUST NOT CLAIM: that +0.3756 is *the* noisy-arm estimate.
```

---

## R-03 -- "independent recomputation" was not independent

```
CLAIM:  "Level 3 -- independently recomputed" (07_RECOMPUTATION.md, §35 of
        the prior blueprint).
STATUS: claimed as independent verification.
DEFECT: `audit.py` shared authorship AND the author's model of the estimand.
        Per §4/§5 that is I1, not I2.
POST-FIX: re-labelled I1. A genuine I2 verifier now exists
        (`independent_verifier.py`, exact rational arithmetic, derived strata,
        Wilson intervals). I3 remains NOT ACHIEVED.
MUST NOT CLAIM: external verification. It has never occurred in this trajectory.
```

---

## R-04 -- pre-fix artifact preservation FAILED

```
CLAIM (implied by the previous cycle): defects are corrected with the prior
        state preserved.
STATUS: asserted in REPORT.md §6, which documented D20 in prose.
DEFECT: **No pre-D20 artifact exists.** `git status` shows the chaos directory
        was never tracked. `chaos/frozen/` was created AFTER the D20 fix. The
        pre-fix `06_RAW_ROWS_FEEDBACK.jsonl`, pre-fix `05_RESULTS.json` and the
        pre-fix KPI block were overwritten in place.
        The pre-fix values survive ONLY as numbers quoted in my own prose
        (net -0.2550, breakage 0.9636). They are not independently checkable.
POST-FIX: this document records the failure rather than concealing it. Future
        runs must freeze BEFORE any correction.
MUST NOT CLAIM: that the pre-fix state was preserved.
```

---

## R-05 -- D21: the pipeline-sensitivity harness reused one receiver

```
CLAIM (of this cycle, mid-flight): a null world would collapse the gap.
STATUS: asserted, then tested, then FAILED -- at +0.5433.
DEFECT: `run_arm` created ONE Receiver per trial and then presented all three
        targets to it, so every decision was taken after the receiver had
        already absorbed the other targets' messages. That is message
        contamination, not the experiment. It also made P1 and P2 meaningless.
        Separately, the harness used rho_model=1.0 while the main experiment
        used rho_model=0.85, so harness absolute numbers are NOT comparable
        to the main experiment.
POST-FIX: fresh Receiver per (trial, target); independent seeds.
        P3 gap = +0.0042 (correctly ~0). P1/P2/P4 now meaningful.
        The rho_model discrepancy is DISCLOSED, not corrected, because the
        test's validity rests on the pipeline RESPONDING to perturbation,
        not on matching the main experiment's absolute level.
```

---

## Summary

| id | claim | new status |
|---|---|---|
| R-01 | +0.6021 is a fully-matched estimate | **RETRACTED** -> +0.578333 paired-within-target |
| R-02 | +0.3756 is the noisy-arm estimate | **RETRACTED** -> range +0.067..+0.505, sign stable |
| R-03 | independent recomputation (Level 3) | **RETRACTED** -> I1 re-labelled; I2 now exists; I3 never achieved |
| R-04 | pre-fix state preserved | **RETRACTED** -- never preserved |
| R-05 | null world collapses the gap | **RETRACTED** then re-established after fixing D21 |

## The load-bearing claim survives

**Relevance predicts accuracy** -- but the correct evidence is the
paired-within-target design, not the `dH` stratification:

| analysis | gap | conditioning needed |
|---|---:|---|
| paired within target | **+0.578333** | none -- balanced by construction |
| unconditioned marginal | +0.578333 | none |

All three targets are positive. The finding is **more robust** than the version
that was retracted.

# VERIFIED EXECUTION INFRASTRUCTURE

Promoted from the closed causal-audit cycle. **No unresolved scientific
conclusion is transferred here.** What transfers is the method for detecting when
an apparent truth is not yet entitled to be treated as one.

## State

```
RESEARCH                -> ARCHIVED_RESEARCH           (chaos/, 56 artifacts)
                        -> VERIFIED_EXECUTION_INFRASTRUCTURE   (institution/, this)
```

The research archive is immutable. This directory may evolve.

## The 12 promoted invariants (SS8)

| id | invariant |
|---|---|
| INV-01 | Signal is not truth. Statistical strength does not establish semantic correctness. |
| INV-02 | Reproducibility is not independence. A repeated computation is not an independent scientific judgement. |
| INV-03 | Documentation is not verification. A well-documented claim may still be wrong. |
| INV-04 | Retractions remain evidence. A retraction is part of the history of a claim. |
| INV-05 | Matching must be causal. A variable computed *after* an intervention cannot serve as a matching variable. |
| INV-06 | Conditioning precedes interpretation. Known confounds must be conditioned before causal interpretation. |
| INV-07 | Metrics require identity tests. A metric determined by another variable is not independent evidence. |
| INV-08 | Controls must instantiate the intended null. A label does not make an intervention null. |
| INV-09 | Analysis instruments require validation. Preregistration does not rescue a defective instrument. |
| INV-10 | Provenance must be reconstructible. Every load-bearing claim needs a durable evidence path. |
| INV-11 | Observer independence is a separate state. Internal recursion may not upgrade itself to external verification. |
| INV-12 | Boundaries must remain boundaries. An unresolved question stays unresolved until the evidence exists. |

Every registry entry names the invariant it enforces, so a regression failure
points at a rule rather than only at a defect number.

## What each inherited rule identifies (SS3)

`defect_registry.py` records, per defect: **signature** (what a detector looks
for), **repair** (the pattern that worked), **provenance** (the incident), and
**invariant** (the rule enforced). 15 defect classes: D5–D10, D12–D14, D17,
D19–D23.

## Modules

| file | purpose |
|---|---|
| `defect_registry.py` | 15 defect classes with signature / repair / provenance / invariant; `describe_failure()` emits actionable output |
| `regression_suite.py` | executable detectors (dataset + source + state), with FAIL/INFO severity |
| `test_claim_states.py` | 17 tests proving the fail-closed behaviour |
| `claim_states.py` | 12 claim states, legal transitions, ladder, operational gate, provenance receipts, `recompute()` |
| `ledger.py` | LanceDB closure record with explicit epistemic metadata |

## Running it

```bash
cd ~/projects/inversion-lab/institution

# 1. claim-state / gate / provenance self-test  (17 tests)
python3 test_claim_states.py

# 2. regression suite against the research archive
python3 regression_suite.py ../chaos/06_RAW_ROWS.jsonl ../chaos ../chaos

# 3. persist / refresh the closure ledger
python3 ledger.py
```

Current suite result against the archive:

```
2 FAIL, 5 INFO
  [FAIL][D13] control arm not equally uninformative across targets
            (t0=0.1263, t1=0.1288, t2=0.2346; varies by 19.5 SE)
  [FAIL][D20] 5 retraction records exist but pre_fix/ is empty
```

**Both FAILs are correct and are not to be suppressed.** D13 is the
control-arm truth-to-target defect. D20 is the real preservation failure from
the D20 incident. The suite is reporting on the archive, not on the suite.

The 5 INFOs are advisories: design-fixed constants and the partial-key
self-test. They are informational because intent is not visible from data.

## Design decisions worth knowing

**Severity exists because a suite that fires on everything is as useless as one
that fires on nothing.** The first version of the suite produced 6 FAILs, four of
which were false positives. Fixed by: D12 requires a declared factor list (intent
is not inferable from data); D13 computes chance from candidate objects rather
than row counts; D22 is advisory because it warns about a *check*, not the data;
D23 is scope-aware and skips prints inside conditionals.

**The gate cannot open by default.** `operational_gate()` question 7 requires a
caller-supplied scope assertion. Omitting it BLOCKS. An omitted assertion is not
consent. (The first version hardcoded it to `None`, which made the gate unable to
ever allow — fail-closed but useless.)

**`recompute()` cannot return a bare `PASS`.** It must return estimand, method,
evidence reference, verification level, implementation id, auditor id, timestamp.

**Five observer levels are distinct and never collapsed:**
`I0_SELF_CHECK`, `I1_SEPARATE_EXECUTION`, `I2_SEPARATE_REASONING`,
`I2_CM_CROSS_MODEL`, `I3_EXTERNAL`.

## Boundary (SS39 of the research cycle)

> Internal recursion cannot generate external independence.

This infrastructure can improve provenance, reproducibility, blindness,
auditability and specification. **It cannot create a second independent
researcher.** A `I3_EXTERNAL` receipt can only be issued by an actual external
entity. The code refuses unknown observer levels rather than accepting a
plausible-looking one.
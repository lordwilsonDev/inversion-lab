# AUDIT THE AUDITOR — FINAL REPORT (v3)

**Does `+0.6021` deserve to survive?**

World fingerprint `882027e856db` · frozen `06_RAW_ROWS.jsonl` md5 `2daaa05c36aea1801a728fbefab666af` · 14,400 rows

---

## 0. The answer

**The number did not survive. The finding did — more strongly.**

| | |
|---|---|
| `+0.6021` | **RETRACTED.** Computed from a stratum that was matched on candidate count and entropy but **not on target**. |
| Correct estimate | **`+0.578333`** — paired within target, balanced by construction, requiring *no* post-treatment conditioning at all. |
| Every target positive | target 0 `+0.6400`, target 1 `+0.6575`, target 2 `+0.4375` |

The retraction improved the evidence. The old analysis needed a stratification
defence because it conditioned on a post-treatment variable; the correct one needs
none, because the two arms are already balanced on target by construction.

---

## 1. WHAT THE AUDIT FOUND

### R-01 — the load-bearing stratum was not matched on target

`dH` is computed *after* the message is applied. Conditioning on it is
conditioning on a **mediator**. Because `dH` is a deterministic function of the
posterior, and the posterior differs structurally for target 2 (where `red
square` matches two objects partially), the `dH` split degenerated into a **target
split — applied to one arm only**:

| arm | targets inside the stratum | n | accuracy |
|---|---|---:|---:|
| relevant | {0: 400, 1: 400} | 800 | 0.7212 |
| irrelevant_matched | {0: 400, 1: 400, 2: 400} | 1200 | 0.1192 |

All 400 target-2 relevant trials were silently removed from one arm.

This is the trajectory's own recurring lesson, arriving again in a new form:
**conditioning on something downstream of the treatment is not a control.**
D8, D12, D17, and now D8 again — marginal/conditional structure, this time with
the mediator disguised as a matching variable.

### The corrected analysis

Paired within target. 400 trials per arm per target. **No conditioning at all.**

| target | n_rel | acc_rel | n_irr | acc_irr | gap |
|---:|---:|---:|---:|---:|---:|
| 0 | 400 | 0.7125 | 400 | 0.0725 | **+0.6400** |
| 1 | 400 | 0.7300 | 400 | 0.0725 | **+0.6575** |
| 2 | 400 | 0.6500 | 400 | 0.2125 | **+0.4375** |

mean gap **`+0.578333`** — which equals the unconditioned marginal, because a
balanced design needs no stratification.

### R-02 — the noisy-arm number was post-hoc weighted

Reported `+0.3756`. It is one of five defensible aggregations:

| rule | estimate |
|---|---|
| equal-stratum | +0.2390 |
| sample-size (**was reported**) | +0.3756 |
| min-arm-N | +0.3967 |
| worst-case stratum | +0.0671 |
| best-case stratum | +0.5054 |

**Sign invariant (+0.067 to +0.505). Magnitude not determined.** The rule was
written after seeing results, so it is POST-HOC by §9's definition.

### The load-bearing weighting was vacuous

For `+0.6021` specifically, weighting could not have mattered: the cell contains
**one populated stratum**. N-weighted, equal-weighted and unweighted are
numerically identical. The independent verifier computed all three and got
`+0.602083` each time. The post-hoc weighting was a blemish with zero numerical
consequence — and only by accident.

### R-03 — "independent recomputation" was not independent

`audit.py` shares no imports with the experiment, but it was written by me, with
my model of what the estimand was. By §4/§5 that is **I1**, not I2. The previous
cycle called it "Level 3 — independently recomputed". That was an upgrade the
evidence did not support.

**Separation of code is not separation of reasoning.**

A genuine I2 verifier now exists. It reproduces the estimate exactly:

```
ESTIMATE (exact rational) : 289/480 = +0.602083
tolerance                 : 1e-06
difference                : 0.0
```

using `fractions.Fraction`, strata derived by intersecting arm keysets, and
**Wilson intervals the original never computed**:

| arm | k/n | 95% Wilson |
|---|---|---|
| relevant | 577/800 | [0.6892, 0.7512] |
| irrelevant | 143/1200 | [0.1020, 0.1387] |

Non-overlapping. The gap is not a sampling fluctuation.

**I3 — external verification — has never occurred in this trajectory.**

### R-04 — pre-fix preservation FAILED

`git status` shows `chaos/` was never tracked. `frozen/` was created *after* the
D20 fix. The pre-fix raw rows and results were overwritten in place.

**No pre-D20 artifact exists.** Four pre-fix numbers survive only as prose in my
own prior report, recorded in `pre_fix/README.md` and marked **UNVERIFIABLE**.

The raw rows *were* frozen and never regenerated this cycle — which is the only
reason V1 was possible at all.

### R-05 — my own new test was broken (D21)

The pipeline-sensitivity harness initially **failed** its null-world check
(`+0.5433` where `~0` was required). Cause: one `Receiver` per trial, then all
three targets presented to it — so every decision was taken after the receiver
had absorbed the other targets' messages. Message contamination.

After fixing to a fresh receiver per (trial, target): **`+0.0042`**. Correct.

---

## 2. PIPELINE SENSITIVITY — **WORLD_SENSITIVE**

Analysis code unchanged between conditions.

| # | perturbation | expected | observed | |
|---|---|---|---|---|
| P1 | unchanged world, repeated | identical | identical | PASS |
| P2 | arm labels exchanged | exact sign flip | residual `0.000e+00` | PASS |
| P3 | **null world** — both arms get identical treatment | ~0 | **+0.0042** | PASS |
| P4 | one-attribute messages | gap shrinks | +0.3764 vs +0.7742 | PASS |

P3 is decisive. A pipeline mechanically reproducing its preferred answer could
not report no difference when the manipulation is removed.

**Disclosed limitation:** the harness uses `rho_model=1.0`, the main experiment
used `0.85`. Absolute values are **not** comparable; only the *response* to
perturbation is under test.

### An incidental finding

P4 is not merely "smaller." Target 2 — where `red square` matches two objects
partially, so a *relevant* message fails to uniquely identify its target — has
the smallest gap (0.4375) and by far the highest irrelevant-arm accuracy (0.2125
vs 0.0725).

> **Relevance matters most when it actually discriminates.**

That is a moderator effect the experiment was not designed to find.

---

## 3. KPI (§28)

| KPI | status |
|---|---|
| 1 — independent recomputation agreement | **PASS** — exact, difference 0.0, tolerance 1e-06 |
| 2 — retraction integrity | **FAIL** — pre-fix state was never preserved (R-04) |
| 3 — weighting transparency | **QUALIFIED** — rule fully specified; post-hoc; vacuous for headline, consequential for noisy arm |
| 4 — auditor independence | **I2** achieved (was I1). **I3 not achieved** |
| 5 — pipeline sensitivity | **WORLD_SENSITIVE** |

---

## 4. GATE STATUS (§3)

| gate | status |
|---|---|
| independent recomputation | **PASS** (I2; I3 unavailable) |
| weighting definition | **PASS** — reconstructed, classified post-hoc, shown vacuous for the headline |
| aggregate entropy claim status | **QUALIFIED** — see below |
| pre-fix preservation | **FAIL** |
| next-question closure contract | **PASS** — `13_CONTRACT_VALIDATION.json`, COMPLETE |

**A failure of these gates is itself the result.** KPI 2 failed.

### The entropy claim, correctly stated

`dH` is **exactly** determined by the persisted posterior — verified to 4.4e-09
over 20,000 rows. It is a re-parameterisation, not independent evidence:
**METRIC_NOT_INDEPENDENT** (§16).

`dH` does *not* vary deterministically with `cand_red` (2 distinct values at
`cand_red=2`), so the two-key stratum was not redundant in principle. It failed
for a different and worse reason: it silently introduced a target imbalance.

**Status: QUALIFIED.** Not "entropy is falsified" — the finding is that
symmetric scalar summaries of a belief distribution cannot distinguish a peak on
the target from a peak on a decoy. That claim stands.

---

## 5. FINAL AUDIT QUESTION (§33)

> *Why should we believe the matched-strata result means what we say, who checked
> that, what did they inspect, when, and what would overturn it?*

| link | value |
|---|---|
| **claim** | referential relevance predicts accuracy, at matched candidate count |
| **evidence** | `06_RAW_ROWS.jsonl`, 14,400 rows, md5 `2daaa05c…` |
| **recomputation** | paired within target → `+0.578333`; all 3 targets positive |
| **auditor** | `independent_verifier.py` + `audit/` — **same entity as the author** |
| **independence level** | **I2**. I3 not achieved |
| **falsifier** | paired-within-target gap not positive in at least 2 of 3 targets |
| **window** | closed — one complete recomputation cycle over the frozen dataset, before any new data |

**INCOMPLETE in one respect:** the auditor and the audited share an author. This
chain cannot close without an external entity, and no amount of further
self-auditing will change that.

---

## 6. WHAT IS *NOT* ESTABLISHED (§31)

Unchanged by this audit, and reinforced by it:

- **No claim about human language.** The parser is a fixed 9-token lookup.
- **No claim that the effect is linguistic.** Still `UNRESOLVED`. Every signal in
  the substrate is compositional by construction, so the contrast needed to test
  it does not exist.
- **No external verification.** Never achieved.
- 3 objects, 3 binary attributes, one message, one clarification slot, no
  dialogue, no intent, no cost.
- The order of constraint composition was fixed and never varied.

---

## 7. NEXT QUESTION — contract-validated

`10_NEXT_QUESTION.json` · `Q-B7-001` · **COMPLETE** (all 9 §20 fields, window concrete, 5/5 quality tests).

**Variable:** compositional structure of the signal, at fixed posterior peak
placement.
**Held constant:** posterior support, peak object, peak probability, entropy to
1e-9, token count, channel ρ, decision policy, candidate set size, target
distribution, seeding.
**Window:** one complete cycle over a newly frozen dataset, ≥3,600 trials per arm,
checksummed before any further audit.
**Auditor:** an implementation that did not author the experiment; I2 target, I3
declared unavailable.
**Falsifier:** if a non-compositional signal with an identical posterior reproduces
the gap, "linguistic reference" moves toward **FALSIFIED**.

**Predicted observation (recorded as a prior, not an assumption):** the substrate
*cannot* distinguish these hypotheses — the receiver consumes only
`(prior, ρ_model, sent_message)`, and the update is a pure function of the parsed
constraint list. The expected result is therefore a **BOUNDARY_CONDITION**, not a
theory result.

---

## 8. THE METHODOLOGICAL POINT

This cycle audited its own auditor and found that the auditor was not
independent, the load-bearing number came from an unbalanced stratum, the
robustness number was post-hoc weighted, and the pre-fix state was never
preserved. Four of five objectives produced a retraction.

**And the headline finding got stronger.**

That is the thing worth carrying forward. The audit did not defend the number —
it destroyed the number, kept the finding, and recorded everything it destroyed.
The alternative was to report `+0.6021` again with a new confidence interval
bolted on, which would have been defended, verified-looking, and wrong.

---

## 9. ARTIFACTS

```
audit/independence.md              I0–I3 ladder, what the verifier was shown
audit/weighting.md                 post-hoc classification, 5-rule sensitivity
audit/retractions.md               R-01..R-05 in full §14 format
audit/pipeline_sensitivity.md      WORLD_SENSITIVE, 4 perturbations
audit/corrected_stratified_analysis.md   the corrected analysis

pre_fix/README.md                  EMPTY — preservation failed, values UNVERIFIABLE
post_fix/README.md                 current verified state + freeze protocol
retractions/R-0*.json              machine-readable retraction records

independent_verifier.py            I2 verifier (exact Fraction, Wilson)
pipeline_sensitivity.py            4 perturbation harness
validate_contract.py               §20 contract checker
11_INDEPENDENT.json                independent result
12_PIPELINE_SENSITIVITY.json       perturbation results
13_CONTRACT_VALIDATION.json        contract completeness
10_NEXT_QUESTION.json              machine-checkable contract
```
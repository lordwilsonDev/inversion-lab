# I2-CM CLOSURE REPORT — C-B8-001

**Cycle type:** frozen closure. No new observations. No new experiment.
**Q-B8-001:** OPEN / UNSCHEDULED — not answered here.

---

## A. BLIND RECONSTRUCTION

**The blindness requirement was not met, and no amount of care fixes it.**

I authored the prior narrative — `REPORT.md`, `09_FINDINGS.md`, the clean-room
package, every number in this trajectory. §13's question ("did I have access to
the previous estimate, report, interpretation, or retractions?") answers **yes**.

So this is **not I2-CM**. I2-CM requires a *different model*. I am the same model.
I classified it **I2, contaminated** and proceeded, because the prompt's
analytical tasks — deriving the inclusion rule from the construct, and attacking
the arms' construction — do not require amnesia to be worth doing. They require
*scepticism*, which is available.

### What I reconstructed, from the raw rows

**The comparison this data can answer:**

| | |
|---|---|
| **treatment** | message naming the intended target's attributes |
| **control** | message naming a *different* object's attributes — same token count, same vocabulary, same channel |
| **population** | 3 synthetic objects × 3 binary attributes, uniform prior, noiseless channel |
| **outcome** | `decision == intended target` (field `correct`) |
| **scope** | cell `rho_channel=1.0, temperature=1.0` only — 2,400 of 14,400 rows |

## B. ESTIMAND

```
G = (1/3) · Σ_t [ Acc(relevant | t) − Acc(irrelevant_matched | t) ]
```

**Why this one.** The claim is a *within-target* contrast. Averaging per-target
contrasts gives each instance of the construct equal weight and depends on no
assumption about trial allocation.

**Rejected alternatives, and why:**

- *pooled difference* — mathematically identical here (balanced design). Kept as a
  check, not as a separate estimand.
- *equal-stratum / sample-weighted matched-strata* — these require defining strata
  on some variable. The balanced design already supplies the control, so
  stratification adds a post-treatment conditioning step and buys nothing.
- *inverse-variance weighted* — identical to the unweighted mean because all
  three targets have n = 400 per arm. The weighting language does no work.

## C. INCLUSION RULE

**Derived from the construct, before looking at gaps:**

| target | relevant message | objects consistent with it | identifies target? |
|---:|---|---|---|
| 0 | `red circle` | {0} | **yes** |
| 1 | `blue square` | {1} | **yes** |
| 2 | `red square` | {2} | **yes** |

All three targets satisfy the construct *"a message that identifies the target."*

**RULE: include all three.**

Excluding a target because its measured gap is smaller would be selection on the
outcome. And the corroboration runs the right way — see §I[6]: including target 2
is **conservative**, because its control arm is defective in the direction that
*shrinks* the effect.

**Amendment, not a new experiment.** No new observations. A changed inclusion
interpretation applied to existing frozen rows.

## D. MATCHED STRATA

**No stratification is used or needed.** Comparability is established *by
construction*:

- 400 trials per arm per target — exactly balanced.
- `H_before` is constant across every row (uniform prior over 3 objects).
- `n_candidates_before` = 3 for every row.
- `candidate_reduction` = 2 for every row in this cell → **zero between-arm
  variance**, so it cannot generate a gap.

This is the point of the earlier retraction: conditioning on a *post-treatment*
variable created a target imbalance that looked like matching. The balanced design
removes the need to condition at all.

## E. INDEPENDENT RESULT

| target | relevant | Wilson 95% | irrelevant | Wilson 95% | G_t |
|---:|---|---|---|---|---:|
| 0 | 285/400 = 0.7125 | [0.6663, 0.7547] | 29/400 = 0.0725 | [0.0510, 0.1022] | **+0.640000** |
| 1 | 292/400 = 0.7300 | [0.6845, 0.7712] | 29/400 = 0.0725 | [0.0510, 0.1022] | **+0.657500** |
| 2 | 260/400 = 0.6500 | [0.6020, 0.6951] | 85/400 = 0.2125 | [0.1752, 0.2552] | **+0.437500** |

```
G        = 347/600 = +0.578333      (exact rational arithmetic)
95% CI   = [+0.5467, +0.6100]       (bootstrap, 20,000, seed 88888)
N        = 2,400 included / 12,000 excluded (out-of-scope cells)
strata   = 3, minimum n = 400 per arm — no underpowered stratum
```

## F. COMPARISON (only now)

My reconstruction and the prior claim agree **exactly**:

| target | mine | prior | diff |
|---:|---:|---:|---:|
| 0 | +0.640000 | +0.6400 | 0 |
| 1 | +0.657500 | +0.6575 | 0 |
| 2 | +0.437500 | +0.4375 | 0 |

primary diff `0.00000033`. **RECONSTRUCTED** on estimand, inclusion rule, strata,
weighting and estimate.

**But §14's warning applies precisely here:** this agreement is *guaranteed*, not
earned. I reproduced my own specification. It is a consistency check on the
estimand definition, not verification of a claim.

## G. INDEPENDENCE

| level | definition | met? |
|---|---|---|
| I1 | different code path, no shared imports | **yes** |
| I2 | different author's reasoning model | **no — same author** |
| **I2-CM** | different model, no prior narrative | **NO** |
| I3 | external operator, independent priors | not attempted — lab ceiling |

```
INDEPENDENCE_LEVEL = I2 (contaminated)
I3_STATUS          = LAB_CEILING / NOT_PURSUED
```

**Not `EXTERNALLY_VERIFIED`. Not I2-CM. The prompt's requested classification
cannot honestly be issued.**

## H. RETRACTIONS

All five prior retractions remain visible and correctly classified — **no
`RETRACTION_PRESERVATION_FAILURE`**:

| id | claim | status |
|---|---|---|
| R-01 | `+0.6021` matched-strata headline | RETRACTED (target-unbalanced stratum) |
| R-02 | `+0.3756` noisy-arm estimate | RETRACTED (post-hoc weighting; range +0.067..+0.505) |
| R-03 | "Level 3 — independently recomputed" | RETRACTED (relabelled I1) |
| R-04 | pre-fix state preserved | RETRACTED (never preserved) |
| R-05 | `+0.5433` pipeline null failure | RETRACTED_THEN_RE_ESTABLISHED (D21) |

One grep artifact noted for honesty: a search for the literal string `Level-3`
reported MISSING. R-03.json is present and uses `Level 3` without the hyphen. I
checked rather than reporting a false preservation failure.

## I. CHAOS ATTACK

| # | attack | verdict |
|---|---|---|
| 1 | mathematical identity? | **survives** — estimand is a mean of observed 0/1, not a derived quantity |
| 2 | could the t=2 rule manufacture it? | **survives** — include-all `+0.5783`, exclude-t2 `+0.6488`; conservative rule gives the *smaller* value |
| 3 | legitimate alternative strata? | **survives** — N-weighted identical; `candidate_reduction` stratum gives the identical `+0.5783` |
| 4 | merely candidate-count behaviour? | **survives** — `cand_red`=2 for *every* row; zero between-arm variance |
| 5 | one target driving it? | **survives** — all three positive; drop-smallest `+0.6488`, drop-largest `+0.5475` |
| 6 | **is relevance the real manipulation?** | **see below — a real confound found** |
| 7 | implementation / randomness | **survives** — exact rational recomputation; blake2b-stable seeds |
| 8 | scope exceeded? | **bounded** — 3 objects, fixed vocabulary, one decision, no humans |

### [6] The control arm is not equally irrelevant

| target | irrelevant message | tokens literally **true of the target** | irrelevant acc |
|---:|---|---|---:|
| 0 | `blue square` | none | 0.0725 |
| 1 | `red circle` | none | 0.0725 |
| 2 | `red circle` | **`red`** | 0.2125 |

For target 2, one of the two message tokens is **true of the target**. The
"matched irrelevant" message is therefore *partially correct* — it is not
irrelevant. That violates the control arm's own definition.

**This is a genuine defect in the design, and I found it by deriving the rule
from the construct rather than from the numbers.**

**Direction of the bias:** it inflates the control arm at target 2 and therefore
**shrinks** the measured gap there. It works **against** the hypothesis.

That is why including target 2 is conservative, and why the claim survives — but
it also means "matched" is matched on *token count and vocabulary* while **not**
matched on *truth-to-target*. The control is weaker than its name implies.

**It also explains the target-2 anomaly mechanistically.** For target 2 the
*relevant* message `red square` spreads one token across each decoy (partial
evidence for both), diluting its own peak — so relevant accuracy drops to 0.65.
Both arms degrade at target 2; the control degrades more.

### A defect in my own reconstruction script (D23)

My first pass printed a narrative conclusion ("found a confound in the control
arm") alongside code that reported `NONE` for that same check. Cause: object
attributes are stored as `"red/circle/large"`, and `str.split()` splits on
**whitespace** — returning one element, not three. Every token comparison was
silently empty.

I had a verified standalone result contradicting my own script's output and
nearly shipped the report anyway. The fix made the code support the claim, and I
made the narrative print **conditional on the computed result** rather than
asserted.

## J. EVIDENCE LADDER

| level | achieved? |
|---|---|
| definition | ✓ prior, likelihood, posterior, decision rule, outcome all stated |
| implementation | ✓ three implemented layers; not asserted-only |
| unit tests | ✓ `VALIDATION.json` cases A–F, run before data collection |
| experimental observation | ✓ 14,400 rows, balanced |
| recomputation | ✓ exact rational, three independent passes |
| **cross-model reconstruction** | ✗ **same model — not achieved** |

## K. CLAIM CLASSIFICATION

## **QUALIFIED**

**Why not RETAINED:** the control arm is defective at target 2 — its "irrelevant"
message is partially true of the target. "Matched" is not matched on
truth-to-target. That is a real qualification on what was compared, even though it
does not manufacture the effect.

**Why not RETRACTED:** the claim survives every attack, and the one defect found
biases *against* the hypothesis.

**Why not UNRESOLVED:** the estimand is well-defined under a construct-derived
inclusion rule, the design is balanced, and the direction is stable.

**The qualified claim:**

> Within a 3-object synthetic referential world, arms balanced 400 trials per
> target, at ρ = 1.0 and T = 1.0, a message naming the target's attributes
> produced higher referential accuracy than a token-matched message naming a
> different object, by **+0.578 (95% CI [+0.547, +0.610])**, with all three
> targets positive — where the control is matched on token count and vocabulary
> but **not** on truth-to-target for one of three targets.

## L. WINDOW

This was the frozen closure cycle: one pass over the frozen dataset, ending when
the target-2 amendment, recomputation, chaos attack, and claim classification were
frozen. **No new experimental observations were collected.** The target-2
treatment was an *analytical amendment* to existing rows, not a new experiment.

## M. AUDITOR QUESTION

Within the lab's declared limits, the following could still legitimately
challenge this result — and none of them is me:

1. **A different model** re-deriving the same estimand blind. Not available.
2. **An external operator** with independent priors (I3). Lab ceiling, not pursued.
3. **A reader who rejects the control arm** as invalid because of the
   truth-to-target mismatch. They would be right to raise it; whether it is fatal
   is exactly the kind of judgement that should not be made by the arm's author.

Within the laboratory, the only remaining honest challenge is **specification
disagreement** — someone else deciding that target 2 should be excluded, or that
the control is too weak to admit. I cannot adjudicate that against myself.

## N. NEXT QUESTION

**Q-B8-001 remains OPEN / UNSCHEDULED. Not executed in this cycle.**

> *Can a protocol be written whose acceptance test rejects a faithful analyst's
> alternative estimand only when that estimand is actually wrong?*

Unchanged. Untouched. Not answered.

---

## §25 — WHAT DID THIS CYCLE MAKE INDEPENDENTLY KNOWABLE?

**Honestly: less than the framing suggests, and one real thing.**

**Not new:** that a relevant message beats a matched irrelevant one. I reproduced
my own specification exactly. Agreement here was *guaranteed by construction*, not
earned, and it should carry no evidential weight beyond internal consistency.

**Genuinely new — two findings:**

1. **A defect in the control arm.** The "matched irrelevant" message is partially
   *true of the target* for target 2 (`red` is a property of both O0 and O2).
   The control is not matched on truth-to-target. This was not previously
   identified, and it was found by deriving the inclusion rule from the construct
   rather than from the numbers. It biases against the hypothesis, so the claim
   survives — but "matched" was doing more work than it was entitled to.

2. **D23 — my own reconstruction script contradicted its own narrative.** Token
   comparison silently returned empty because `str.split()` does not tokenise on
   `/`. I had a verified standalone result saying `['red']` and script output
   saying `NONE`, and the tempting move was to ship the narrative anyway. That
   this defect surfaced *in the verification script of a verification exercise*
   is itself mildly embarrassing, and it is the second time in two cycles that a
   defect was caught only by reconciling two numbers that did not add up.

**What is not knowable here, regardless of effort:** whether the estimand is the
*right* one. I specified it, audited it, and reproduced it. Three passes by the
same author is one pass. That limit is structural, not methodological, and no
amount of further self-auditing changes it.

---

## CLOSURE

```
INDEPENDENCE_LEVEL = I2 (contaminated — not I2-CM)
I3_STATUS          = LAB_CEILING / NOT_PURSUED
C-B8-001           = QUALIFIED
Q-B8-001           = OPEN / UNSCHEDULED
NEW FINDINGS       = control-arm truth-to-target mismatch; D23
STOPPED            = yes — closure cycle, per §26
```
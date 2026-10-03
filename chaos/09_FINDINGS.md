# 09 -- FINDINGS (§24 claim-binding table)

World fingerprint `882027e856db`. All numbers LEVEL 3 (independently recomputed from raw rows).

## Claim-binding

| Claim | Evidence | Verification | Alternative tested | Status |
|---|---|---|---|---|
| Relevant message predicts referential accuracy | raw rows, paired within target | Level 3 | matched irrelevant message | **SUPPORTED** |
| The effect survives matching candidate reduction | stratified, gap 0.000000 | Level 3 | candidate-count control | **SUPPORTED** |
| The effect survives matching entropy reduction | stratified on (cand_red, dH) | Level 3 | entropy control | **SUPPORTED** |
| Candidate count and entropy are not interchangeable | dH varies within cand_red level | Level 3 | -- | **SUPPORTED** |
| Feedback changes receiver state | 100% state change on error trials; dH_fb 0.1674 | Level 3 | repetition control | **SUPPORTED** |
| Feedback improves net accuracy | 0.5517 -> 0.6858 | Level 3 | -- | **SUPPORTED** |
| Behaviour implies constraint reduction | -- | -- | -- | **FALSIFIED** |

## F1 -- Relevance predicts accuracy, and neither global measure explains it

Noiseless arm, T=1.0:

| arm | accuracy | dH | candidate reduction |
|---|---|---|---|
| relevant | **0.6975** | 0.4252 | 2.0000 |
| irrelevant_matched | **0.1192** | 0.5101 | 2.0000 |
| **gap** | **+0.5783** | 0.0848 | 0.0000 |

Candidate reduction is **exactly matched** (0.000000). Accuracy differs by 0.578.

The relevant arm actually reduces entropy **less** than the irrelevant arm
(irrelevant exceeds relevant by 0.0848 bits). A more
informative message produced *more* residual uncertainty. Entropy cannot be the
explanation.

### Stratifying on both measures
#### rho1.0_T1.0 -- weighted gap within matched strata: **+0.6021**

| cand_red | dH | n_rel | n_irr | acc_rel | acc_irr | gap |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0.51 | 800 | 1200 | 0.7212 | 0.1192 | +0.6021 |


#### rho0.85_T1.0 -- weighted gap within matched strata: **+0.3756**

| cand_red | dH | n_rel | n_irr | acc_rel | acc_irr | gap |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0.26 | 381 | 153 | 0.5039 | 0.3595 | +0.1445 |
| 2 | 0.51 | 704 | 891 | 0.6435 | 0.1380 | +0.5054 |
| 3 | 0.16 | 115 | 156 | 0.4261 | 0.3590 | +0.0671 |


**This is the decisive result.** With candidate reduction AND entropy reduction
both exactly equal within stratum, relevance still predicts accuracy.

## F2 -- The mechanism, stated precisely

Target O0, noiseless:

| arm | message | posterior | H_after | candidates |
|---|---|---|---|---|
| relevant | `red circle` | [0.719, 0.065, 0.216] | 1.0749 | {O0} |
| irrelevant | `blue square` | [0.065, 0.719, 0.216] | 1.0749 | {O1} |

**Identical entropy. Identical candidate count. Opposite meaning.** The peak
(0.719) sits on the target in one and on a decoy in the other.

Shannon entropy and candidate count are both **symmetric functions of the
distribution**. They are blind to which object carries the mass. That blindness is
exactly what makes them non-explanatory here.

## F3 -- Feedback changes state, and improves accuracy

| condition | acc before | acc after | net | repair | breakage | dH_fb | state changed |
|---|---|---|---|---|---|---|---|
| hint=0 | 0.5517 | 0.6858 | +0.1342 | 0.6747 | 0.3051 | 0.1674 | 0.4483 |
| hint=1 | 0.5942 | 0.6758 | +0.0817 | 0.7187 | 0.3534 | 0.1544 | 0.4058 |

Honest caveat: **breakage is substantial** (~0.31-0.35). A bare error signal is a
blunt instrument. `KPI4_repair_rate` alone would have flattered this; the net
column is the honest number.

## F4 -- RETRACTED / DEFECT D20 (found by this audit)

**Pre-fix**: the error signal was passed as `correct=False` **unconditionally**,
even when the first decision was correct. The feedback routine therefore applied a
50x penalty to the chosen hypothesis regardless of outcome.

**Measured symptom**: net accuracy 0.5729 -> 0.3179 (**-0.2550**);
breakage **96.4%**. A "feedback loop" that destroys almost every correct answer is
not a feedback loop -- it is a fixed penalty with the error signal removed.

**Post-fix**: error signal conditioned on the actual outcome. Net accuracy
0.5517 -> 0.6858 (**+0.1342**); breakage 96.4% -> 0.3051.

**Retraction**: all pre-fix cybernetics results withdrawn. The mechanical
properties (dH change, state change) are unaffected; only the accuracy claims move.

## F5 -- RETRACTED: entropy as the explanatory variable

Prior expectation (inherited from the trajectory, and from §7 of this blueprint)
was that `dH` explains behaviour. **FALSIFIED.** The irrelevant arm achieves a
*larger* entropy reduction and a near-zero accuracy.

## Status summary

| finding | status |
|---|---|
| F1 relevance predicts accuracy at matched candidate count | SUPPORTED |
| F1b relevance predicts accuracy at matched (count, entropy) | SUPPORTED |
| F2 mechanism = distribution *shape*, not scalar summaries | SUPPORTED |
| F3 feedback changes state and improves net accuracy | SUPPORTED |
| F4 pre-fix cybernetics accuracy | **RETRACTED** |
| F5 entropy explains behaviour | **FALSIFIED** |

## What is NOT established

- Nothing about human language or pragmatics.
- Nothing about compositionality in the linguistic sense -- the parser is a
  lookup over a fixed vocabulary, not a learned grammar.
- That relevance "causes" anything beyond this 3-object world.
- The order of constraint composition is fixed to colour-then-shape-then-size
  and was not varied.

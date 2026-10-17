# B4 FINAL REPORT — Linguistic-Cybernetic Communication Under Non-Erasing State

**Date:** 2026-10-03
**Artifacts:** `~/projects/inversion-lab/b4/` — frozen with checksums (11 files)
**Preregistration:** `b4/PREREGISTRATION.md` (written before data collection)

---

## A. Research Question

> When communication changes a receiver's internal state without completely
> erasing uncertainty, what determines whether behavioural improvement comes
> from information transmission, hypothesis-space reduction, state
> intervention, model reconstruction, or coordination?

Operational form: does replacing hard elimination with graded evidence and
deterministic decision with posterior-sensitive decision create an
experimentally discriminable difference between competing accounts?

## B. Previous-State Reconstruction (Level 3, from frozen raw rows)

I did **not** inherit the previous narrative. I re-derived from `frozen/run1/*.json`
raw rows and re-executed the old substrate.

| Claim | Status after re-derivation |
|---|---|
| Checksums (10 artifacts) | **Verified** independently |
| E3 "no crossover" (Run 1) | **REPLICATED at Level 3** — 8/8 m-levels positive, 0 sign changes |
| E1 A-vs-B identity (Run 1) | **REPLICATED at Level 3** — contrastive bits≡logHypRed to 0.0e+00; verify_only differ by 13.30 |
| `q = 1/candidates` in Run 1 | **NOT a general identity** — 577/1920 rows violate it, max error 0.799 |

**Correction to the blueprint's premise (§3).** The old substrate's degeneracy
is real but *sharper and different* than stated. The CODEBOOK posterior **can**
be non-uniform (`prior_floor=0.10` leaves mass 0.9 on IDENTITY; after
`exclude_object`, H = 1.99 bits over 40,200 hypotheses, max/min ratio 3.6e5).
But the **OBJECT-level** posterior — where decisions are made — is uniform in
**900/900** trials, max-p exactly 1/candidates at every count. The concentrated
mass always sits on codebooks predicting **no scene object**, so it is discarded
on renormalisation.

This overturns my own Run 3 report, which stated the substrate "mathematically
erases" non-uniformity. It does not: the erasure happens at the renormalisation
step, for a specific and diagnosable reason.

## C. Substrate Change

| | Old | B4 |
|---|---|---|
| Update | hard mask `_restrict` | **graded likelihood** `L(f,o)=Π_j P(t_j\|f,c_j)` |
| Elimination | total | **none** (`ε>0` ⟹ `L>0` ∀(f,o)) |
| Posterior | uniform on survivors | **non-uniform**, full support |
| Decision | deterministic lowest-index | **posterior-proportional** + **temperature sampling** |
| Candidate count | variable, load-bearing | **constant = 5 by construction** |

## D. Identifiability Demonstration (§3–§4)

**Gate 1 (is B4 a new substrate?) — PASSED**

| Check | Result |
|---|---|
| G1a posterior non-uniform after evidence | **100/100** |
| G1b no hypothesis eliminated | **100/100** |
| G1c ranking changes without elimination | **25/25** |
| G1d concentration increases with evidence | **25/25** |
| G1e candidate count constant | support = **5**, single value |

**Gate 2 (is B4 identifying?) — PASSED.** Same support (5), different posterior:
different argmax in **47/60**; different sampling outcome in **59/60**.
Concentration ranges 0.202–0.217 (unattributed) vs 0.861–0.997 (attributed).

**Gate 2c (does the old substrate fail?) — FAILED, as required.** 900/900 trials
uniform; max-p ≡ 1/candidates exactly.

## E. Experimental Design

Interventions A–H, n=200 seeds each, ε ∈ {0.15, 0.35} preregistered,
T ∈ {0.5, 1.0, 2.0} preregistered, 5-object scenes, held-out probe.

## F. Mathematical Specification

State = posterior over all 8! = 40,320 codebooks. Likelihood is a symmetric
noisy channel; `p_t(f) ∝ p_{t−1}(f)·L(f,target)`. Object posterior
`P(o|e) ∝ Σ_f p(f|e)·L_query(f,o)`. Full specification in `PREREGISTRATION.md`.

## G. Primary Results

**Interventions (Policy A):**

| Arm | success | p_correct | Brier | model recovery | support |
|---|---|---|---|---|---|
| A none | 0.175 | 0.200 | 0.800 | 0.000 | 5 |
| B raw (unattributed) | 0.380 | 0.285 | 0.688 | 0.264 | 5 |
| C graded evidence | 0.995 | 0.920 | 0.021 | 0.953 | 5 |
| D contrastive | 1.000 | 0.941 | 0.009 | **0.999** | 5 |
| E verification-only | 0.400 | 0.369 | 0.918 | 0.487 | 5 |
| F target reveal | 1.000 | 0.556 | 0.247 | **0.000** | 5 |
| G equal-budget | 0.815 | 0.592 | 0.308 | 0.457 | 5 |
| H state perturbation | 0.990 | 0.917 | 0.022 | 0.948 | 5 |

**Stratified (§23), not marginal.** Within fixed (ε, n_items) cells, success
tracks object-level `p_max` monotonically — e.g. ε=0.15, 1 item:
Q1 (p_max 0.31–0.48) → 0.540, Q2 → 0.920, Q3 → 1.000, Q4 → 1.000.
**Support constant at 5 throughout**, so candidate count cannot absorb this.

**Calibration (§18):** errors occur only under uncertainty — mean p_max when
correct 0.879, when wrong 0.409. **0 of 104 errors were confident.** Success is a
step function of p_max (0.55 below 0.5, exactly 1.000 above).

**Persistence (§16):** immediate 0.980 → novel-scene 1.000 → after
contradictory evidence 0.980; model recovery 0.932 → 0.932 → 0.835.

**DECISIVE RESULT (Theory B vs D), n=200:**

| condition | global H | eff. hypotheses | task H | p_correct | success |
|---|---|---|---|---|---|
| none | 15.299 b | 40320 | 2.322 b | 0.170 | 0.200 |
| **same sender** | 2.287 b | 7.0 | 0.306 b | 0.985 | **0.944** |
| **different sender (null)** | 2.486 b | 7.9 | **1.474 b** | 0.200 | **0.207** |

Different-sender evidence reduces global uncertainty by **12.81 bits** (vs
13.01 for same-sender) and produces **zero** behavioural benefit (0.207 = chance).

## H. Adversarial Results

| Probe | Could overturn | Found | Changed interpretation |
|---|---|---|---|
| F1 candidate leakage | any structural claim | support constant 5 / 2400 rows | no |
| F2 position leakage | graded-success result | spread 0.0129 (chance 0.2) | no |
| F3 scene leakage | evidence is necessary | scene-only 0.155 vs 0.995 | no |
| F4 posterior collapse | B4 holds graded state | 120/120 non-uniform | no |
| **F7 metric identity** | any dissociation claim | **`p_max ≡ p_correct` (r=0.9999999999999997)** | **YES** |
| F8 marginal confounding | p_max→success | marginal r=0.560; within-cell 0.355–0.869; **no sign change** | no |
| **F13 competing mechanism** | whether content matters | **v1 was mislabelled a null (D13); real null = different sender: 0.990 vs 0.220, specificity +0.77** | **YES** |
| F15 substrate perturbation | arbitrary-noise dependence | 0.968 (ε=0.15) / 0.946 (ε=0.35) | no |

**knowledge-producing checks / total adversarial checks = 2 / 8.**

## I. Falsification

- **F7**: `p_max` and `p_correct` are numerically an identity, so they are **not
  two independent pieces of evidence**. (Direct application of D7.)
- **F13 v1**: my "null mechanism" was not null — same-sender evidence about
  other targets is predicted to work under model learning, and it did (0.985 vs
  0.980). Reporting that as "content is irrelevant" would have **manufactured a
  false conclusion**. Replaced with a genuine null (different sender).
- **D12**: `cb_concentration` has **zero within-cell variance** (sd = 0.000 in
  every (ε, n_items) cell). Stratifying by it is stratifying by design
  parameters. Replaced with object-level `p_max`.
- **D13**: self-caught mislabelled null, as above.

## J. Defects and Repairs

| ID | Sev | Status | Description |
|---|---|---|---|
| D10 | HIGH | REPAIRED | Arms C, D, F were **byte-identical implementations**; their apparent agreement was an artifact. All three reimplemented as genuinely distinct conditions (D = top-2-hypothesis log-likelihood-ratio selection; F = direct held-out revelation). |
| D11 | MED | REPAIRED | Posterior **saturates** by 2 evidence items, which would re-create the old degeneracy. Addressed by preregistering a second ε level and by the item-count sweep. |
| D12 | HIGH | REPAIRED | `cb_concentration` is deterministic given (ε, n_items) — sd = 0 within cell. Stratification variable replaced. |
| D13 | HIGH | RETRACTED | F13 v1 mislabelled a non-null condition as a null. Replaced. |

## K. Independent Recomputation Status

| Result | Level |
|---|---|
| Run 1 E3 no-crossover | **Level 3** (recomputed from 1920 raw rows) |
| Run 1 E1 identity | **Level 3** (recomputed from frozen JSON) |
| Old-substrate non-identifiability | **Level 4** (independent re-execution, 900 trials) |
| Gate 1 / Gate 2 | **Level 4** (independent implementation `b4/gates.py`) |
| B4 intervention table | **Level 3** (from `RESULTS.json` rows) |
| Stratified p_max→success | **Level 3** (from 2400 `SATURATION.json` rows) |
| Theory B vs D table | **Level 3**, but values were captured from stdout rather than a persisted raw row file → **SUMMARY-TRACEABLE / NOT_INDEPENDENTLY_RECOMPUTED**. Re-running the snippet reproduces them deterministically; a persisted raw dump should be added before this is cited as Level 3. |

## L. Theory Discrimination

| Account | Verdict | Evidence |
|---|---|---|
| **A. Transmission (content)** | **WEAKENED** | F (target reveal) carries no model content yet gives success 1.000. Content is not necessary for behaviour. |
| **B. Constraint reduction** | **NOT SUFFICIENT (SUPPORTED_WITH_LIMIT)** | Different-sender evidence reduces global uncertainty 12.81 bits → success 0.207 (chance). Uncertainty reduction alone buys nothing. |
| **C. State intervention** | **NOT SUPPORTED by this operationalisation** | H (tilted prior, identical external info) 0.990 vs C 0.995 — prior state had no effect. Only one operationalisation of "state" was tested. |
| **D. Model reconstruction** | **SUPPORTED** | Sender specificity +0.77 (0.990 vs 0.220); contrastive arm reaches model recovery 0.999 while graded reaches 0.953 at identical success. |
| **E. Coordination** | **UNTESTED / NOT_DISCRIMINATING** | The substrate is single-agent. No coordination construct exists. Not ranked. |

**No ranking is offered.** B and D are discriminated; C is tested once only; E
was never fairly testable.

## M. Substrate Boundary

B4 permits: graded evidence, non-uniform posteriors, global/task uncertainty
decoupling, posterior-sensitive and sampled decisions, calibrated confidence,
behaviour↔model dissociation. It **cannot** test coordination (single agent),
cannot vary the hypothesis space, and uses a single symmetric channel model.

## N. Scientific Claim Boundary

**Claimable:** in this synthetic substrate, behavioural improvement tracks
**sender-specific model content**, not the magnitude of uncertainty reduction;
confidence is calibrated; behaviour and model recovery are separable variables.

**NOT claimable:** anything about human communication. This is an exact Bayesian
agent over 40,320 codebooks with one fixed channel model. The "language" is a
permutation; there are no semantics, intentions, or costs.

## O. Retractions

- **D13 / F13 v1** — RETRACTED. The v1 null was not null.
- **D10** — arms C/D/F identical; the original identical results are retracted.
- **D12** — concentration-based stratification retracted and replaced.
- **Run 3 report's claim that the old substrate "mathematically erases"
  non-uniformity** — RETRACTED (§B). The codebook posterior is non-uniform; the
  erasure is at object-level renormalisation.
- All Run 1–3 retractions (A-vs-B, F2.3, mrr, F2.1 causal) remain retracted.

## P. Transferable Methodological Findings

*(separate from claims about communication)*
1. A degeneracy diagnosis must be stated **at the level where decisions are
   made**. "The posterior is uniform" was false at the codebook level and true
   at the object level; only the latter matters.
2. An adversarial check that catches its own author's mislabelled null (F13 v1)
   is worth more than a clean p-value.
3. A metric can be an identity at high accuracy and still be read as two pieces
   of evidence (F7).
4. Stratifying by a variable with zero within-cell variance stratifies by the
   design, not the data (D12).
5. Gates ("can the machinery represent this at all?") should run before theory
   experiments, and their failure is itself the most informative result.

## Q. Next Meta-Question

The decisive B-vs-D result rests on a single manipulation: the evidence's
**sender** is correct or incorrect. That is a binary, all-or-nothing manipulation
of model content. The global/task decoupling was achieved only by the extreme
case (a completely wrong sender), where task uncertainty saturates at 1.47 bits.

The untested region is the **graded** middle: evidence that is *partially* about
the sender's model — e.g. a sender who is reliable on some concepts and not
others, or evidence whose likelihood is informative about *some* codebook
distinctions and uninformative about others.

> **Does behavioural improvement depend on the receiver's uncertainty about the
> *task-relevant* hypotheses specifically, or on its uncertainty about the
> *sender's model* — and can these two be driven apart by a sender whose
> reliability is graded rather than binary, so that task-relevant uncertainty is
> held fixed while model uncertainty varies (and vice versa)?**

**Evidence derivation:** forced by the structure of the decisive result — model
content was only ever manipulated as a binary sender swap, and the global/task
decoupling was observed only at that extreme.

**Quality tests:** **novelty** — no prior run or probe manipulated graded
sender reliability; **operationalizability** — a per-concept reliability channel
is implementable in B4 with no substrate change; **falsifiability** — if holding
task uncertainty fixed while varying model uncertainty does not move behaviour,
the model-reconstruction account is wrong; **non-closure** — genuinely open;
**evidence derivation** — from GATES/RESULTS/THEORY_BD, not supplied.
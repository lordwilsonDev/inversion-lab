# B5 FINAL REPORT — Model Uncertainty, Task Uncertainty, and Graded Reliability

**Date:** 2026-10-03
**Artifacts:** `~/projects/inversion-lab/b5/` — frozen, 16 files + checksums
**Raw rows:** 10,240 main trials + 1,200 B4 checkpoint trials, persisted before analysis

---

## A. Research Question

> Does behavioural improvement depend on uncertainty about the task-relevant
> hypotheses specifically, or about the sender's model — and can these be driven
> apart by a sender whose reliability is graded rather than binary?

## B. B4 Reconstruction (Level-3 status)

**§2 checkpoint RESOLVED: `LEVEL_3_RECOMPUTED_CONCLUSION_POINTVALUES_RETRACTED_D14`.**

1,200 trial-level rows persisted (`B4_RAW_ROWS.json`) and recomputed by a
separate module. Conclusions reproduce and **strengthen**: sender specificity
0.7372 → **0.7925**; different-sender success 0.207 → **0.195** (chance 0.200);
global uncertainty reduction 12.81 bits → **12.93 bits** with zero behavioural
benefit. Confirmed that uncertainty reduction is not sufficient.

**Defect D14 (HIGH, retracted-and-replaced):** the original B4 decisive run
seeded its RNG with `abs(hash((str,int))) % 2**31`. Python randomises string
hashing per process — verified: `hash(("b4bd",7))` gives −3676509867…,
+2525348777…, −8115759530… under `PYTHONHASHSEED` 1/2/3. Those trials were
**never reproducible**. This is the same defect class as the `hash()`-seeding
bug fixed at the very start of the original lexical-repair program; I
reintroduced it. Two entropy point values retracted and replaced. All B5 seeds
derive from blake2b.

## C. Substrate Specification

| | Old (Runs 1–3) | B4 | B5 |
|---|---|---|---|
| Evidence | hard mask | graded likelihood | graded likelihood |
| Elimination | total | none | none |
| Decision | deterministic lowest-index | argmax + sampling | **sampling primary** (§6) |
| Sender | fixed / deranged | fixed / wrong | **graded reliability ρ** |
| Task ambiguity | not separable | binary contrast | **message completeness** |

Graded reliability is a property of the generating process (§9):
`P(reported token correct) = ρ`; corrupted tokens are drawn uniformly from the
K−1 alternatives and therefore carry no information about the true token.

## D. Identifiability Gate (§7) — PASSED, with a boundary condition

All four cells constructible; reliability realized within tolerance (worst gap
0.0020 vs tolerance 0.05); factors marginally orthogonal (r = 0.4228).

**INTRINSIC_COUPLING (BOUNDARY_CONDITION).** Varying *model* uncertainty also
moves *task* entropy (A→B shifts task H by +0.77 bits). This is not a design
flaw: task entropy is a **deterministic function of the model posterior**, so
degrading model knowledge necessarily degrades decoding precision. The task
lever is clean (moves task H 0.71–1.14 bits while moving model H ≤ 0.10). The
model lever is intrinsically impure, so model effects were estimated **within
task-entropy strata**, never marginally.

## E. 2×2 Design

32 cells: ρ ∈ {1.00, 0.90, 0.75, 0.50} × n_visible ∈ {1, 3} × n_items ∈ {2,3,4,6},
320 trials each, 10,240 rows. Full 32-cell grid in `frozen/MAIN_RAW_ROWS.json`.

## F. Graded Reliability Verification (§10)

| ρ intended | ρ realized | gap | n |
|---|---|---|---|
| 1.00 | 1.0000 | 0.0000 | 2560 |
| 0.90 | 0.9006 | 0.0006 | 2560 |
| 0.75 | 0.7431 | 0.0069 | 2560 |
| 0.50 | 0.5022 | 0.0022 | 2560 |

Model entropy tracks ρ monotonically (5.377 → 3.846 → 2.728 → 2.098 bits),
which is the mechanism by which ρ lowers sender-model uncertainty.

## G. Controls

- **Verification-only, target-reveal, information-matched**: carried from B4;
  no true null exists in the B5 grid (**F13**: ρ=0.50 has model entropy 5.38
  bits vs uniform 15.30, so it is a *low-reliability* condition, **not** a null).
- **Target position**: probed and found to be a genuine confound (D17, below).

## H. Primary Results (repaired, T=1.0)

152 matched pairs at **model-entropy gap 0.0143 bits** (tolerance 0.05) and
**task-entropy gap 0.9995 bits**:

| quantity | value |
|---|---|
| mean task effect on success | **+0.4024** (sd 0.1432) |
| fraction of pairs positive | **152/152 = 1.000** |
| position spread | **0.0174** |
| uniform across position strata | **True** |

## I. Conditional Results (§18)

Effect within each target-index stratum (T=1.0):

| target_index | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| task effect | +0.434 | +0.427 | +0.375 | +0.433 | +0.391 |
| frac > 0 | 0.955 | 0.923 | 0.963 | 0.939 | 0.889 |

**Robust across all preregistered temperatures:** T=0.5 → +0.4171;
T=1.0 → +0.4024; T=2.0 → +0.3281. All position-uniform, all SUPPORTED.

**H2 within task-entropy strata:** deltas +0.029 / +0.198 / +0.007 / +0.072,
mean **+0.0765**, sign stable → **FALSIFIED** as a primary account.
Under the *defective* argmax policy one stratum was **negative** (−0.0295) —
an F8 sign reversal that changed the conclusion.

**H3 interaction PRESENT:** task effect by ρ = 0.272 / 0.381 / 0.442 / 0.479
(spread 0.207). Reliability *modulates* the task effect rather than replacing it.

## J. Model vs Behavior

845 rows correct-but-model-not-recovered; 820 rows model-recovered-but-wrong.
**Dissociation exists and is bidirectional** (F12). Model recovery is never
inferred from behaviour.

## K. Adversarial Analyses (§27 ledger)

**knowledge-producing / total = 8 / 14.** Not optimized; recorded transparently.

| Probe | Kind | Outcome |
|---|---|---|
| F2 position leakage | knowledge | **LEAK FOUND → D17, conclusion changed** |
| F6 decision-policy leakage | knowledge | task effect survives all 3 temperatures |
| F7 metric identity | knowledge | **no identities** |
| F8 marginal/conditional | knowledge | **SIGN REVERSAL under argmax → conclusion changed** |
| F13 null validity | knowledge | ρ=0.50 is NOT a null |
| F14 persistence | knowledge | holds (0.677/0.678/0.672) |
| F15 randomness | knowledge | stable across reseeding |
| F16 raw recomputation | confirmation | 152 pairs, +0.4123 |
| F9 reliability leakage | confirmation | **check itself buggy → D16** |

## L. Defects and Repairs

| ID | Sev | Status | Description |
|---|---|---|---|
| **D14** | HIGH | RETRACTED_AND_REPLACED | `hash()` seeding in B4's decisive run; never reproducible. Two entropy point values retracted. |
| **D15** | HIGH | REPAIRED | Identifiability gate mislabelled contrast B→D as "vary model" when it varies task; gate failed for a coding reason. Contrast map corrected. |
| **D16** | MED | REPAIRED | F9's leakage test `any(len(v)>1)` always triggered because `n_items` varies across 4 levels by design for every ρ. Correct test: all ρ share an identical design-variable set → **ρ is not encoded in n_items/scene_size/eps**. |
| **D17** | HIGH | REPAIRED | Preregistered PRIMARY outcome used **deterministic argmax**, which under diffuse posteriors returns the lowest index. Position spread 0.3575. This **violated §6** (B5 must not revert to deterministic tie-break) — it reintroduced the old substrate's decision artifact in the new regime. Repaired: primary recomputed under preregistered sampling policies → position spread 0.0174, effect uniform across all strata. |

## M. Raw-Row Recomputability (§35)

| Result | Level |
|---|---|
| B4 checkpoint conclusions | **LEVEL 3** (1,200 persisted rows, independent module) |
| B4 entropy point values | **RETRACTED → replaced** (D14) |
| B5 H1 task effect | **LEVEL 3** (152 pairs from 10,240 rows) |
| B5 H1 within-stratum | **LEVEL 3** |
| Falsification probes | **LEVEL 3** |
| Reseeding stability | **LEVEL 4** (independent re-execution, different seed stream) |

## N. Theory Discrimination

| Account | Status | Evidence |
|---|---|---|
| **H1 task-uncertainty** | **SUPPORTED (DECISIVE)** | +0.402 at model gap 0.014 bits; 152/152 pairs; uniform across position strata and all temperatures |
| **H2 sender-model** | **FALSIFIED as primary** | +0.0765 within task strata; one stratum negative under argmax |
| **H3 interaction** | **SUPPORTED** | task effect 0.272→0.479 across ρ; spread 0.207 |
| **H4 neither** | **REJECTED** | effect survives every conditioning applied |

Theories A–E from B4, updated:

| | Status |
|---|---|
| A Transmission | WEAKENED (unchanged from B4) |
| B Global constraint reduction | **FALSIFIED** (B4's own null arm) |
| C State intervention | UNTESTED — prior tilt only, not tested in B5 |
| D Model reconstruction | **DOWNGRADED from SUPPORTED to WEAKENED** — see §Q |
| E Coordination | UNTESTED (single-agent substrate) |

## O. Substrate Boundary

B5 permits: graded sender reliability, separable task ambiguity, non-deterministic
decisions, position-unbiased measurement, bidirectional behaviour↔model
dissociation. It **cannot**: hold task entropy constant while varying model
entropy (intrinsic coupling); test coordination; vary the hypothesis space.

## P. Scientific Claim Boundary

**Claimable:** in this synthetic permutation substrate, once sender-model
uncertainty is held constant, a ~1-bit reduction in task-relevant uncertainty
raises held-out success by ~0.40, uniformly across target position and decision
temperature. Sender-model uncertainty contributes little *at fixed task
uncertainty* but *modulates* how much task uncertainty matters.

**NOT claimable:** anything about human communication, pragmatics, or language.
"Reliability" is a per-token Bernoulli channel; the "language" is a permutation.

## Q. Retracted Claims

1. **B4's "Theory D / model reconstruction SUPPORTED"** — **DOWNGRADED**.
   B4's sender-specificity contrast (0.79) was **confounded by task
   uncertainty**: same-sender had task H = 0.31 bits, different-sender 1.42 bits.
   B5 shows task entropy is the dominant driver. A residual model contribution
   plausibly remains (H2's small sign-stable +0.077; H3's interaction), so D is
   weakened, not fully falsified. **B4's headline causal reading must not be
   cited as SUPPORTED.**
2. **B4's entropy point values** (D14).
3. **The argmax-based marginal H1 estimate as stated** (D17) — position-confounded;
   replaced by the stratified, sampled-policy estimate.
4. All prior retractions (A-vs-B, F2.3, mrr, F2.1 causal, D10–D13) stand.

## R. Transferable Methodological Findings

1. **A preregistered decision rule can itself violate the substrate contract.**
   D17: argmax was preregistered *and* prohibited by §6. Pre-registration does
   not protect against specifying a defective measurement.
2. **A confound can survive matching on the obvious variable.** B4 matched on
   model uncertainty and still got a task-uncertainty effect.
3. **Deterministic decision rules manufacture position gradients** that appear
   as real effects and can invert conclusions (F8 sign reversal).
4. **A "low reliability" condition is not a null** (D13 → F13).
5. **Two levers that act on different state variables are not automatically
   orthogonal**: one may be a deterministic function of the other.

## S. Next Meta-Question

B5 showed task-relevant uncertainty is the dominant driver, and that
sender-model uncertainty *modulates* it (H3: task effect 0.272 → 0.479 as ρ
rises). But the modulation was measured with reliability manipulated
**globally and independently of the task** — every concept-token pair had the
same ρ. Real senders are unreliable about *some* distinctions and reliable
about others, which is the case where task and model uncertainty could in
principle decouple.

> **When a sender's reliability is itself graded across concept-token pairs —
> that is, when some of the sender's distinctions are reliable and others are
> not — does behavioural improvement then depend on uncertainty about the
> *unreliable* portion of the sender's model specifically, or on task
> uncertainty as before? In particular, can a receiver achieve high task
> accuracy while remaining maximally uncertain about the unreliable part of the
> model, and does that configuration behave differently from an equally
> task-uncertain receiver that happens to know the unreliable part?**

**Derivation:** forced by H3's interaction plus the fact that all B5 reliability
was uniform across pairs — the untested region is *structured*, not graded
magnitude, reliability.

**Quality tests:** **novelty** — no prior run manipulated within-sender
reliability structure; **evidence derivation** — from H3 and the ρ-uniform
design in `FEASIBILITY.json`/`MAIN_RAW_ROWS.json`; **operationalizability** —
implementable in B5 with no substrate change (per-pair reliability mask);
**falsifiability** — if behaviour tracks structured reliability independently of
task entropy, H1 is incomplete; if not, task uncertainty is the sole driver;
**non-closure** — genuinely open, not answered in B5.

**TERMINATION STATUS:** no stop condition met. Substrate permits further
discrimination; the next question is executable without modification.
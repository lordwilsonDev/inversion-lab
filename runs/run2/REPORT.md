# RUN 2 REPORT — Task-Relevance vs Posterior Narrowing

**Date:** 2026-10-02
**Artifacts:** `~/projects/inversion-lab/runs/run2/` (frozen with CHECKSUMS.txt)
**Frozen checksums:** `experiments.py bdd84d1…`, `FINDINGS.json 09e5ac05…`, `R2_results.json 3de6c174…`

---

## 1. Inherited question

From Run 1: **"Does the A/B (information vs hypothesis-elimination) discrimination survive a uniform prior?"**

Received along with Run 1's frozen evidence, findings, and its four recorded defects (D1–D4).

## 2. Reconstruction of the construct from evidence

Run 1's construct was an exact Bayesian receiver over all 8! = 40,320 codebooks. I rebuilt the relevant pieces from `inversion/env.py` and the audited `lexical-repair-crt` core rather than trusting Run 1's interpretation. Two facts about the substrate governed everything that followed:

- `constrain_token`, `exclude_object`, and `require_object` are all the same operation: a boolean mask (`_restrict`).
- Candidates for a query are counted directly from that mask.

## 3. Critique of the inherited question

| # | Critique |
|---|---------|
| C1 | Under a uniform prior, A and B are **provably the same function**: `H_uniform − H(f) == log2(N_perm/N_after)` whenever `f` is uniform on its support. The inherited question therefore reduces to a **theorem check**, which can only ever confirm. |
| C2 | Run 1 conflated **(i)** are A and B different functions? *(algebra)* with **(ii)** does either PREDICT success? *(empirical)*. Only (ii) is scientific. Run 1 answered (i) using a degenerate prior and reported it as a discovery. |
| C3 | The construct had to be **replaced**: ask whether the shared quantity predicts success when task-relevance varies and narrowing is held exactly constant. |

Critique C1 turned out to be **testable**, and R2E1 confirmed it — forcing retraction of Run 1's headline. The critique was not merely an argument.

## 4. Repaired construct

**Task-relevant narrowing vs posterior-wide narrowing, with posterior narrowing EXACTLY matched.**

| Arm | Pins |
|---|---|
| `target_relevant` | the 3 tokens appearing in the held-out message |
| `target_irrelevant` | 3 tokens **not** appearing in it |
| `no_feedback` | nothing |

Each pin divides the codebook space by exactly 8 and all arms pin the same *number* of tokens, so log2 reduction is identical by construction — verified numerically as **8.392317 in both narrowing arms, 0.0 in no_feedback**.

Logic: if success tracks narrowing *alone*, the arms are equal. If success tracks *which* tokens were narrowed, `target_relevant` wins.

## 5. Experiments designed

- **R2E1** — Is A ≡ B under a uniform prior? With a control that *must* break the identity if the theory is right.
- **R2E2** — Does success track narrowing or relevance, at matched narrowing?
- **R2E3** — Falsify the competing account that the effect is purely content, correctable by revealing the target.

## 6. Implementation

`runs/run2/experiments.py`, reusing `inversion/env.py` and the audited `lexical-repair-crt` core. Deterministic via blake2b `stable_seed`; all results reproducible across processes.

## 7. Verification

An independent diagnostic run confirmed the mechanism directly rather than trusting the aggregate: at candidate count 1 the relevant arm reaches `candidates=1` in **300/300** trials and the irrelevant arm in only **141/300**, with success tracking the histogram exactly (1.000 / 0.512 / 0.424 / 0.000).

## 8. Results

### R2E1 — identity (REPLICATED + SUPPORTED)

| Quantity | Value |
|---|---|
| Uniform posterior confirmed flat | **180/180** steps |
| Non-uniform posterior confirmed non-flat | **180/180** steps |
| max \|A−B\| uniform, cumulative | **5.33e-15** |
| max \|A−B\| uniform, incremental | **7.11e-15** |
| max \|A−B\| non-uniform (control) | **0.0666** |

**DISCRIMINATING = True.** A and B are the identical function under uniformity and provably diverge only when the posterior is non-uniform on its support.

### R2E2 — relevance (SUPPORTED, causally qualified by Run 3)

| Arm | log2 reduction | success | mean candidates | q |
|---|---|---|---|---|
| no_feedback | 0.0 | 0.227 | 5.000 | 0.205 |
| target_relevant | 8.392317 | **1.000** | 1.000 | 1.000 |
| target_irrelevant | 8.392317 | **0.730** | 1.647 | 0.716 |

success delta **0.27**, McNemar exact **b=81, c=0, p=8.27e-25**.

### R2E3 — falsification (UNRESOLVED)

Target revelation rescues **0.28**; `FALSIFIED_relevance = false`. The competing account is weakened, not eliminated.

## 9. Falsification

R2E3 failed to eliminate the competing explanation. 0.28 partial rescue means content matters but is not the whole story — reported as UNRESOLVED rather than resolved in either direction.

## 10. Retractions and defects

| ID | Sev | Status | Description |
|---|---|---|---|
| **D5** | HIGH | REPAIRED | R2E1 compared a **cumulative** A against an **incremental** B. The reported max \|A−B\| = 5.807 was an artefact of comparing different quantities at different steps, **not** evidence against the identity. Repaired like-for-like → 5.33e-15. |
| **D6** | HIGH | REPAIRED | The first control (`prior_floor=0.10`, no tilt) **silently failed**: 0/180 steps were non-flat. Masking preserves uniformity, and `prior_floor=0.10` puts 0.9 mass on IDENTITY — which the **first constraint eliminates outright**, so normalisation spreads the surviving ε-mass perfectly evenly. Rebuilt with the `asymmetry` tilt → 180/180 non-flat. |
| **D7** | MED | RETRACTED | `mrr` was reported as showing "identical model recovery despite different success" — a claimed strong dissociation. **False.** `mrr` is a deterministic function of `n_pins` alone (0.0/0.25/0.375/0.5 for 0/1/2/3 pins, invariant across all 56 three-pin sets). It cannot in principle distinguish *which* tokens were pinned. |

**Retraction of Run 1's headline (RETRACTED):** the A-vs-B discrimination was produced *entirely* by the degenerate prior, not discovered in the data. The algebra is not wrong; the claim that data revealed it is.

## 11. Boundary analysis

- Every env operation is a hard mask, so "how much the belief moved" and "how many hypotheses survived" cannot be separated except through candidate-set size — which turned out to be fully explanatory.
- Non-uniform posteriors are reachable **only** via the asymmetry tilt on surviving codebooks, severely limiting reachable posterior geometry.
- q, mrr, and bits-based metrics are all degenerate or collinear with candidate count.

## 12. What Run 2 does and does not establish

**Established:** relevance predicts success at matched narrowing (p=8.3e-25); the effect is fully mediated by candidate-set size; A ≡ B under uniformity (Run 1's discrimination retracted).

**Not established:** whether relevance is *causal* or merely how this construct produces smaller candidate sets; R2E3's unrescued 0.28 residual; anything about real human communication — the receiver is an exact Bayesian agent over 40,320 codebooks.

**The contradiction that generated Run 3:** F2.1 (relevance predicts success) and F2.2 (candidate count fully mediates it) cannot both be read naively. Run 2 could not separate them because "relevant" was *operationalised as* pinning the query tokens, which mechanically forces `candidates=1`. Relevance and candidate-collapse were never independently varied.

---

## Meta-question for Run 3

> **"Is task-relevance a causal property of feedback, or is it merely the mechanism by which a construct realises a reduction in candidate-set size?"**

**Derivation:** forced by the F2.1/F2.2 contradiction inside Run 2's own evidence — not supplied by the designer.

| Quality test | Verdict |
|---|---|
| Novelty within trajectory | **PASS** — Run 1 asked whether A and B are distinct functions; Run 2 asked whether relevance or quantity predicts success. Neither asked whether relevance is *causally separable* from the candidate reduction it produces. |
| Evidence derivation | **PASS** — the contradiction is in Run 2's data. |
| Operationalizability | **PASS, with caveat** — requires varying relevance at constant candidate count (e.g. permuting the query after narrowing is fixed). Achievable. |
| Falsifiability | **PASS** — if relevance predicts success at fixed candidate count it is causal; if not, it is a redescription. |
| Non-closure | **PASS** — Run 2's evidence is consistent with both readings. |
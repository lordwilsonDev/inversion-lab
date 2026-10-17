# RUN 3 REPORT — Is Relevance Causal, or a Redescription of Candidate-Set Size?

**Date:** 2026-10-02
**Artifacts:** `~/projects/inversion-lab/runs/run3/` (frozen with CHECKSUMS.txt)
**Frozen checksums:** `experiments.py b422429e…`, `FINDINGS.json c0cfd817…`, `R3_results.json 15b1009d…`

---

## 1. Inherited question

From Run 2: **"Is task-relevance a causal property of feedback, or is it merely the mechanism by which a construct realises a reduction in candidate-set size?"**

## 2. Reconstruction

Rebuilt from Run 2's frozen `experiments.py` plus `inversion/env.py`, not from Run 2's prose. Confirmed first-hand that every operation is a mask and that candidates are counted directly from that mask.

## 3. Critiques of the inherited question (performed before design)

| # | Critique |
|---|---|
| **A** | The question may be **unanswerable in this substrate**: if candidates are literally counted from the mask, relevance and candidate-collapse might be inseparable *by construction*. This had to be **tested**, not assumed. |
| **B** | "Causality" is the wrong standard — nothing here is a treatment in the epidemiological sense. The honest operational question is **conditional independence**: given fixed candidate count, does relevance predict success? |
| **C** | A null is only informative if **powered**, so stratum occupancy had to be checked before any conditional claim. |

## 4. Construct

**Graded relevance at exactly constant narrowing.** Every arm pins exactly 3 tokens; only the *count* of query tokens among them varies (0, 1, 2, 3). Narrowing is therefore identical across all arms by construction — verified: `log_reduction_spread = 0.0`.

The decisive comparison is **within candidate-count strata**, not marginal.

## 5. Experiments

- **R3E1** (feasibility) — can candidate count be held fixed while relevance varies?
- **R3E2** (graded relevance) — marginal sweep at constant narrowing.
- **R3E3** (conditional independence) — **the decisive test.**
- **R3E4** (competing explanation) — is *consistency-with-a-scene-message*, rather than relevance-to-query, operative?

## 6. Implementation

`runs/run3/experiments.py`. R3E1 enumerates all 56 three-token pin-sets across 40 seeds (2,240 rows) — a full enumeration, not a sample.

## 7. Verification

**Feasibility was established before the decisive test was interpreted.** R3E1 refutes Critique A: four candidate-count strata (1, 2, 3, 4) contain *both* fully irrelevant and partially relevant pin-sets. The separation the inherited question requires is genuinely available.

## 8. Results

### R3E1 — feasibility (OBSERVED)
`DECISIVE_STRATUM_AVAILABLE = true`. Narrowing constant across all 2,240 pin-sets (8.392317).

### R3E2 — graded relevance (OBSERVED)

| Relevance (query tokens pinned) | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| success | 0.727 | 0.740 | 0.913 | **1.000** |
| mean candidates | 1.680 | 1.577 | 1.207 | 1.000 |

Marginal success rises with relevance — **but mean candidates falls too, so this is not decisive.** This is exactly the trap Run 2 fell into.

### R3E3 — conditional independence (FALSIFIED — the causal reading)

| Candidate count | n | Relevance levels present | Within-stratum relevance effect | p (exact) |
|---|---|---|---|---|
| **1** | 830 | 0,1,2,3 | **0.000** | 1.0 |
| 2 | 306 | 0,1,2 | +0.028 | 0.3125 |
| 3 | 59 | 0,1 | −0.171 | 0.5 |
| 4 | 5 | 0,1 | 0.000 | 1.0 |

`relevance_is_causal = false`. **No stratum shows a significant relevance effect.** At candidate count 1, success is **exactly 1.000 at every relevance level — including fully irrelevant pinning (n=133) and relevance level 3 (n=300).**

### R3E4 — competing explanation (FALSIFIED)

Marginal distractor effect **+0.284** → conditioned on candidate count it **reverses to −0.060** (stratum 2: −0.052; stratum 3: −0.069). Distractor-consistency confers no benefit beyond candidate count.

## 9. Falsification

Two accounts were falsified, both by conditional analysis:
1. **Relevance is causal** → falsified (R3E3).
2. **Consistency-with-a-scene-message is operative** → falsified (R3E4), and the sign reversal shows the marginal version of this claim was itself an artefact.

## 10. Defects and retractions

| ID | Sev | Status | Description |
|---|---|---|---|
| **D8** | HIGH | REPAIRED | My first R3E4 verdict compared **marginal** success and concluded "consistency-with-query is operative" — precisely the confound R3E2's own NOTE warns about. Recomputed conditionally, the effect **reverses sign** (+0.284 → −0.060) and the verdict flips from supported to falsified. Self-inflicted, caught by re-deriving the comparison the way R3E3 does. |
| **D9** | HIGH | RETRACTED | **Run 2's finding F2.3** ("q is not 1/candidates") is a **Jensen's inequality artefact**: it compared mean(q) = 0.7158 against 1/mean(c) = 0.6073. The correct comparison is mean(q) vs mean(1/c) = **0.715833** — an exact match. 898/900 trials satisfy q == 1/c exactly. |

**Retractions:**
- Run 2's **F2.3** — RETRACTED. The degenerate confidence metric reproduces exactly (max deviation 5.55e-17).
- Run 2's **F2.1** read *causally* — PARTIALLY RETRACTED. The description is true; the causal implication is not.
- My own first R3E4 verdict — RETRACTED (D8).

## 11. The unifying result (SUPPORTED)

**F3.1 — success is a deterministic function of candidate-set size alone.** Pooled across **1,800 trials** spanning 8 distinct arm and relevance conditions:

| candidates | n | success | sd |
|---|---|---|---|
| 1 | 1170 | **1.0000** | **0.0000** |
| 2 | 485 | 0.5237 | 0.4994 |
| 3 | 131 | 0.2748 | 0.4464 |
| 4 | 14 | 0.2143 | 0.4103 |

Candidate count alone explains R² = 0.4544 of success variance. The residual is **not** unexplained variation: `decide()` maximises `(posterior, −index)`, so among tied survivors it **deterministically returns the lowest index**. Success is a deterministic rule, not a stochastic guess — the residual is Bernoulli sampling noise around it.

**F3.2 — q ≡ 1/candidates**, exactly, to 5.55e-17, in every arm and stratum.

## 12. Boundary declaration

**The three-run trajectory reduces to ONE variable.** Candidate-set size determines success; success determines q; q is 1/candidates. Relevance, information content, and hypothesis-elimination accounting are all redescriptions of this single quantity *in this substrate*.

- **B1** — One operative variable across all three runs.
- **B2** — Every operation is a hard mask, so the posterior is uniform on the surviving explaining set *by construction*. No experiment here can separate "how much the belief moved" from "how many hypotheses survived"; they are not merely correlated, they are **the same object**.
- **B3** — The deterministic index tie-break means any construct varying only *which* hypotheses survive will manufacture apparent "relevance effects" that are pure index artefacts.
- **B4** — **Minimum substrate change required to proceed:** soft/graded likelihoods (so the posterior can be non-uniform on the explaining set) **and** a randomised or genuinely uncertain decision rule.

**Nothing further is scientifically meaningful within this substrate.** U2 and U3 both require B4.

---

## Meta-question

> **"Does the collapse to a single variable (candidate-set size) survive a substrate in which the posterior can be non-uniform over the explaining set, or is that collapse an artefact of hard masking plus a deterministic tie-break?"**

| Quality test | Verdict |
|---|---|
| Novelty | **PASS** — no prior run asked whether its own substrate's degeneracy *caused* its results. Runs 1–3 each found a confound and repaired it *within* the substrate. This asks whether the substrate **is** the confound. |
| Evidence derivation | **PASS** — forced by B1–B4 and U2/U3. |
| Operationalizability | **PARTIAL — not executable here.** Requires B4. Stated as a boundary, not glossed. |
| Falsifiability | **PASS** — soft likelihoods + randomised tie-break still showing sole candidate-count prediction would *confirm* the collapse as a property of the phenomenon; relevance regaining predictive power would overturn Run 3's account. |
| Non-closure | **PASS** — genuinely open, not answerable here. |
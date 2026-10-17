# RECURSION AUDIT — Three-Run Trajectory

**Date:** 2026-10-02
**Scope:** Run 1 → Run 2 → Run 3 of the CRT-style recursive protocol
**Frozen artifacts:** `frozen/run1/`, `runs/run2/frozen/`, `runs/run3/frozen/`

---

## 1. Trajectory comparison

| Field | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| **Starting question** | Does contrastive repair beat equal-budget/repetition, and is the effect about information content or hypothesis elimination? | Does the A/B (information vs hypothesis-elimination) discrimination survive a uniform prior? | Is task-relevance a causal property of feedback, or merely the mechanism by which a construct realises candidate-set reduction? |
| **Construct** | Exact Bayesian receiver over 40,320 codebooks; contrastive vs equal_budget vs verify_only feedback | Task-relevant vs posterior-wide narrowing, narrowing EXACTLY matched | Graded relevance (0–3 query tokens) at constant narrowing, analysed within candidate-count strata |
| **Major finding** | Contrastive +2.797 bits/sym vs verify_only +0.004 — two accounts order the arms **oppositely** | Narrowing identical (log2 8.392317) yet success 1.000 vs 0.730, p=8.3e-25; effect fully mediated by candidate-set size | **Success is a deterministic function of candidate-set size alone** (n=1170 at cands=1, success exactly 1.0000, sd=0.0000); relevance is not causal |
| **Falsification / retraction** | 4 defects (D1 HIGH fake crossover RETRACTED; D2 HIGH wrong anchor; D3 MEDIUM relabelled condition; D4 MEDIUM underpowered). F4 crossover from the prior run **did not replicate**. | **D5** cumulative-vs-incremental mismatch (the 5.807 "failure" was an artefact); **D6** control silently vacuous (0/180 non-flat); **D7** mrr retracted as a metric artefact. **Run 1's headline RETRACTED** — A≡B to 5.33e-15. | **D8** my own marginal-vs-conditional error; effect reversed +0.284 → −0.060. **D9** Run 2's F2.3 retracted (Jensen artefact). F2.1's causal reading partially retracted. |
| **Meta-question** | Does the A/B discrimination survive a uniform prior? | Is relevance causal or a redescription of candidate-set size? | Does the single-variable collapse survive a substrate with non-uniform posteriors, or is it an artefact of hard masking + deterministic tie-break? |

## 2. Counts

| Metric | Count |
|---|---|
| **Experiments executed** | **13** (Run 1: E1–E6 = 6; Run 2: R2E1–R2E3 = 3; Run 3: R3E1–R3E4 = 4) |
| **Experiments repaired** | **6** (Run 1: E1 re-anchored, E3 re-run post-D1, E6 re-powered, E5 relabelled = 4 affected; Run 2: R2E1 rebuilt with control = 1; Run 3: R3E4 verdict recomputed = 1) |
| **Findings retracted** | **5** (Run 1's A-vs-B headline; Run 2's F2.3; Run 2's mrr dissociation; F2.1's causal reading; Run 3's own first R3E4 verdict) |
| **Hypotheses abandoned** | **6** (A-vs-B as distinct theories; relevance as causal; consistency-with-message as operative; mrr as informative; the degenerate-prior account of Run 1's negative bits/sym; F4 crossover as a general rather than design-specific result) |
| **Constructs replaced** | **3** (Run 1's contrastive-treatment construct → Run 2's matched-relevance construct → Run 3's stratified graded-relevance construct) |
| **Unresolved discriminations remaining** | **3** (U2 non-uniform posterior; U3 randomised decision rule; U4 lexical-repair crossover, never revisited) |

## 3. Did the trajectory produce genuinely new experimentally grounded questions, or did it merely recurse linguistically over the same construct?

**Answer: it produced genuinely new experimentally grounded questions, and the evidence for that is that the questions kept being *answered*, including against the investigator's own interest. But it ALSO genuinely recursed over one construct, and the recursion is what produced the result.**

This is not a compromise answer; the two halves rest on different evidence and should be judged separately.

### Evidence that the questions were genuinely new and experimentally grounded

1. **Each meta-question was falsifiable and got falsified.** Run 3's question — "is relevance causal?" — was answered **no**. An investigator merely recursing linguistically over a construct produces questions that survive, because a rhetorical question is not an experiment. Here the decisive test (R3E3) returned `relevance_is_causal = false` with **no significant effect in any stratum**.

2. **The constructs were not the same.** Three genuinely distinct constructs were built and each failed in a different way: Run 1's failed on a degenerate prior (D2), Run 2's failed on a confound it could not see (relevance ≡ candidate count), Run 3's succeeded only because it introduced *stratification*, which is a method the earlier runs did not have.

3. **Every meta-question was forced by a contradiction internal to the prior run's evidence, not by curiosity.** Run 1's arose from noticing A ≡ B algebraically. Run 2's arose from F2.1 and F2.2 contradicting each other. Run 3's arose from B1–B4. None was supplied by a designer. Each is traceable to a specific measurement.

4. **The recursion was *productive*, not circular.** Run 3's answer is a **reduction**: three runs of apparent multi-variable structure collapse to one variable, established on 1,800 pooled trials with a variance of exactly zero at the decisive point. That is a substantive scientific result about the substrate, not a restatement.

### Evidence that it also genuinely recursed over one construct

1. **All 13 experiments used the same substrate** — `inversion/env.py`, the same 40,320-codebook space, the same mask-only operations, the same `decide()` tie-break. Not one experiment changed the substrate.

2. **Every defect was a defect of the *same three properties*** — hard masking (D1, D3, D6), a degenerate or washed-out prior (D2, D6), and metric degeneracy (D7, D9). The defects did not diversify; they were three recurring failure modes.

3. **The strongest result is about the substrate, not the phenomenon.** F3.1 (candidate count determines success) and F3.2 (q ≡ 1/candidates) are both statements about `env.py`, not about communication, repair, or relevance. Run 3's account would be substantially unchanged if the world model were replaced entirely.

### The honest synthesis

The trajectory **did not** merely recurse linguistically — a linguistic recursion cannot produce five retractions, six repaired experiments, or a zero-variance decisive measurement. It **did** recurse over a single construct, and it only became visible as a construct rather than as a *findings* when Run 3 stratified by candidate count.

**The recursion was real, but its terminus was a boundary, not a discovery about the world.** Run 3's own analysis says so: B1–B4 establish that within this substrate the collapse to one variable is **forced by construction**, so Runs 1 and 2 could never have found anything else. Their apparent multi-variable findings were measurement artefacts of a substrate that permits exactly one degree of freedom.

**This is the honest outcome, and it is a negative result about the substrate, not a positive result about the phenomenon.** The protocol's stated purpose — determining *how far evidence-driven investigation can proceed before the substrate imposes a boundary* — was fulfilled: the boundary was reached at Run 3, it was identified mechanistically (B4), and the minimum substrate change required was specified.

## 4. What the three runs actually cost

Two of the three runs' headline findings did not survive. Run 1's A-vs-B discrimination and Run 2's relevance effect were both **produced by the experimental design rather than discovered in the data**. The investigator's own most confident claims were the ones that failed — and both failures were found only by deliberately constructing an analysis that could *fail* (R2E1's non-uniform control; R3E1's feasibility check; R3E3's stratification). Each of those three checks was added precisely because a null or reversal was conceivable.

## 5. Disposition

| Item | Label |
|---|---|
| Run 1 A-vs-B discrimination | **RETRACTED** |
| Run 2 F2.3 (q not 1/candidates) | **RETRACTED** |
| Run 2 F2.1 causal reading | **RETRACTED** (descriptive part survives) |
| Run 2 mrr dissociation | **RETRACTED** |
| Run 3 F3.1 (candidate count determines success) | **SUPPORTED** |
| Run 3 F3.2 (q ≡ 1/candidates) | **REPLICATED** |
| Substrate collapse to one variable | **SUPPORTED_WITH_LIMIT** (limit: true only under hard masking + deterministic tie-break) |
| Relevance as a causal variable | **FALSIFIED** |
| Consistency-with-message as operative | **FALSIFIED** |
| Whether the collapse survives a graded-likelihood substrate | **UNRESOLVED — requires substrate change** |
| Any claim about human communication | **UNTESTED and not testable in this substrate** |

**Final classification of the trajectory: BOUNDARY_CONDITION reached at Run 3.** Further investigation within this substrate is not scientifically meaningful. The minimum substrate change is specified (B4), and the question that would test whether Run 3's account is an artefact or a property of the phenomenon is recorded, falsifiable, and unanswerable here.
---

## 6. Provenance

| Run | Artifacts | Checksums (md5, first 8) |
|---|---|---|
| Run 1 | `frozen/run1/{inversion_results,FINDINGS,E1_corrected,E3_rows}.json` | `b8d84a7d`, `74aa63de`, `c939065f`, `1ccbf585` |
| Run 2 | `runs/run2/frozen/{experiments.py,R2_results.json,FINDINGS.json}` | `3de6c174`, `bdd84d12`, `09e5ac05` |
| Run 3 | `runs/run3/frozen/{experiments.py,R3_results.json,FINDINGS.json}` | `b422429e`, `15b1009d`, `c0cfd817` |

All three runs are reproducible across processes via blake2b `stable_seed`.

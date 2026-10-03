# 08 -- CHAOS REVIEW (§21)

Every entry was run. None is proposed.

| Doubt (§10) | Test | Evidence | Verdict |
|---|---|---|---|
| Message length caused it | Match token count | 2 tokens in both arms, every trial | **ELIMINATED** |
| Candidate count caused it | Stratify on realised candidate reduction | matched exactly in the noiseless arm (gap 0.000000); stratified analysis below | **ELIMINATED** |
| Entropy caused it | Stratify on dH as well | matched within strata; gap survives | **ELIMINATED** |
| Target position caused it | Accuracy by target | spread 0.0388 | **ELIMINATED** |
| Semantics is the manipulation | Same string serves both roles across targets; paired-within-target design | paired design | **CONTROLLED** |
| Chance caused it | Null comparison | irrelevant arm 0.1192 < chance 0.3333 | **ELIMINATED** |
| Evaluator leaked target | Trace receiver inputs | only `prior`, `rho_model`, `sent_message`; leakage would give 1.000, observed 0.119 | **ELIMINATED** |
| Decision rule caused it | Three temperatures | sign stable: +0.8583 / +0.5783 / +0.3025 | **ELIMINATED** |
| Random seed caused it | blake2b seeding + cross-process replay | 1 distinct output | **ELIMINATED** |
| Code artifact | Independent recomputation | reproduces to 1e-09 | **ELIMINATED** |
| Entropy formula | Hand-derived cases A-F | all PASS | **ELIMINATED** |

## The doubt that survived (§22 -- signal-strength warning)

The noiseless result is strong and *should* be distrusted: with `rho=1.0` both
messages identify exactly one object, so an identical scalar story is trivially
available. Rather than dismiss it, the noisy arm (`rho=0.85`) was run and
stratified. The effect **survives** at +0.3756 within matched strata.

## Doubt that initially succeeded

**D20** -- the feedback loop. See 09_FINDINGS.md.

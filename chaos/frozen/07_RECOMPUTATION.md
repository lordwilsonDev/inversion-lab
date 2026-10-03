# 07 -- RECOMPUTATION (§20)

## Method

`audit.py` re-reads `06_RAW_ROWS.jsonl` and recomputes entropy, candidate sets,
delta_H and accuracy **without importing the experiment module's statistics**.
A single scalar is passed across a subprocess boundary to force a genuine
cross-process replay.

## Result

| Check | Max error | Tolerance | Verdict |
|-------|-----------|-----------|---------|
| entropy (before/after) | 3.6877e-09 | 1e-06 | PASS |
| candidate set | 0 | exact | PASS |
| delta_H | 1.1110e-16 | 1e-06 | PASS |
| accuracy relevant (noiseless) | 0.6975 recomputed vs 0.6975 reported | 1e-06 | PASS |
| accuracy irrelevant (noiseless) | 0.119167 recomputed vs 0.119167 reported | 1e-06 | PASS |

Cross-process replay: 1 distinct output across repeated subprocess invocations.
**REPRODUCIBLE: True**

## Evidence level (§35 of prior blueprint / §11 of this one)

**LEVEL 3 -- independently recomputed from raw rows.**
Every headline number in `09_FINDINGS.md` is recomputed by a separate code path.
No load-bearing number exists only in stdout.

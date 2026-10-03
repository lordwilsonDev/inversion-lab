# AUDIT -- INDEPENDENCE (§4, §5, §17, §25)

## Frozen dataset handed to the verifier

| property | value |
|---|---|
| file | `06_RAW_ROWS.jsonl` |
| md5 | `2daaa05c36aea1801a728fbefab666af` |
| size | 9,663,239 bytes |
| rows | 14,400 |
| rows in estimand (rho=1.0, T=1.0) | 2400 |
| world fingerprint | `882027e856db` |

## What the independent verifier was and was not shown

| withheld | enforced |
|---|---|
| the reported `+0.6021` as a target | yes -- no constant appears in `independent_verifier.py` |
| the original analysis code (`audit.py`, `docs.py`) | yes -- zero imports from them |
| the original grouping key | yes -- strata derived by **intersecting arm keysets** |
| the original interpretation | yes -- not present in the module |

## Deliberate style divergence

| original | independent verifier |
|---|---|
| float means | `fractions.Fraction` exact rational arithmetic |
| group on a pre-chosen tuple | intersect arm key-sets |
| point estimates only | **Wilson score intervals** (original computed none) |
| full dataframe | streaming read |

## Verdict

| | |
|---|---|
| original pipeline (`audit.py`) | **I1** -- separate code path, no shared imports, but authored by the same entity with the same model of the estimand |
| this cycle's verifier | **I2** -- separate analytical logic, independently derived estimand/grouping/aggregation/statistic |
| external verifier | **I3 — NOT ACHIEVED** |

> **The verifier was written by the same entity that produced the original
> result.** It shares the author's assumptions about what the estimand *is*. It
> can catch arithmetic and grouping errors. It cannot catch a shared
> mis-specification of the question.

**No result in this trajectory may be called `EXTERNALLY_VERIFIED`.**

## Independent result vs reported value

| | value |
|---|---|
| independent estimate (exact) | `289/480` = **+0.602083** |
| reported | +0.602083 |
| absolute difference | 0.0 |
| preregistered tolerance | 1e-06 |
| **KPI 1** | **PASS** |

## Uncertainty the original never reported

| arm | k/n | accuracy | Wilson 95% |
|---|---|---:|---|
| relevant | 577/800 | 0.7212 | [0.6892, 0.7512] |
| irrelevant | 143/1200 | 0.1192 | [0.1020, 0.1387] |

Intervals do not overlap. The gap is not a sampling fluctuation.

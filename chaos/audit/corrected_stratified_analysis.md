# CORRECTED STRATIFIED ANALYSIS

Replaces the `dH`-stratified analysis in `09_FINDINGS.md` F1 (see R-01).

## Cell: rho=1.0, temperature=1.0

### (a) The retracted analysis

Stratified on (cand_red, dH). One stratum. **Not balanced on target.**

| arm | targets present | n | accuracy |
|---|---|---:|---:|
| relevant | {0:400, 1:400} | 800 | 0.7212 |
| irrelevant_matched | {0:400, 1:400, 2:400} | 1200 | 0.1192 |

gap = **+0.602083**  <- RETRACTED as target-unbalanced

### (b) Target-balanced within the same stratum (targets 0 and 1 only)

| target | n_rel | acc_rel | n_irr | acc_irr | gap |
|---:|---:|---:|---:|---:|---:|
| 0 | 400 | 0.7125 | 400 | 0.0725 | +0.6400 |
| 1 | 400 | 0.7300 | 400 | 0.0725 | +0.6575 |

gap = **+0.648750**

### (c) THE CORRECT ANALYSIS -- paired within target, no conditioning

Balanced by construction: 400 trials per arm per target. No post-treatment
conditioning of any kind. This is the estimand that needs no stratification
defence.

| target | n_rel | acc_rel | n_irr | acc_irr | gap |
|---:|---:|---:|---:|---:|---:|
| 0 | 400 | 0.7125 | 400 | 0.0725 | +0.6400 |
| 1 | 400 | 0.7300 | 400 | 0.0725 | +0.6575 |
| 2 | 400 | 0.6500 | 400 | 0.2125 | +0.4375 |

gap = **+0.578333**

**All three targets positive. The smallest gap (+0.4375) is still an order of magnitude larger than the Wilson interval width.**

## Why (c) is the correct analysis and (a) was not

`dH` is computed **after** the message is applied. Conditioning on it is
conditioning on a mediator. Because `dH` is a deterministic function of the
posterior, and because the posterior differs structurally for target 2, the
`dH` split degenerated into a target split -- applied to one arm only.

The paired-within-target design avoids this entirely because the two arms are
already balanced on target by construction. There is nothing to stratify.

## Candidate-count matching: still valid

`cand_red = 2` in both arms throughout the noiseless cell, gap exactly 0.000000.
That part of the original claim survives. The problem was never candidate
count; it was the un-audited third variable.

# ESTIMAND DEFINITION — FROZEN BEFORE COMPUTATION

**FROZEN AT:** package creation, prior to any computation from this package.
**TOLERANCE IS FIXED HERE AND MUST NOT BE CHANGED AFTER SEEING RESULTS.**

## Primary estimand

> The difference in referential accuracy between the `relevant` and
> `irrelevant_matched` arms, computed **within each target**, then combined by an
> **unweighted mean across targets**.

    G_t = Acc(relevant | target t) - Acc(irrelevant_matched | target t)
    G   = (G_0 + G_1 + G_2) / 3

## Why unweighted mean across targets

The design is balanced within target (equal trials per arm per target), so an
unweighted mean over targets and an N-weighted aggregate coincide. The unweighted
form is preferred because it does not depend on the trial allocation, and because
no target is more scientifically privileged than another by this protocol.

## Pre-registered tolerance

    |G_external - G_reference| <= 0.05

Justification: the estimand is a mean of three accuracy differences, each from
n = 400 per arm. The Wilson half-width at n = 400 is about 0.05, so a difference
of two arms can move by about 0.07 in the worst case at 95%. 0.05 is therefore
roughly the scale of one standard error of the quantity being compared, and is
the tightest threshold that does not reject agreement produced by sampling noise
alone. **Fixed before computation. Not revisable.**

## Uncertainty method (pre-specified)

Wilson score intervals per arm per target, plus a paired bootstrap (10,000
resamples, deterministic seed) for the aggregate `G`.

## Scope restriction

This estimand is defined **only** for the cell `rho_channel = 1.0`,
`temperature = 1.0`. Other cells are present in the file but are NOT part of the
primary estimand. Any analysis of another cell is exploratory.

## What the verifier is explicitly invited to challenge

- Whether the estimand is well posed at all.
- Whether the unweighted mean is defensible.
- Whether the scope restriction is appropriate.
- Whether the prescribed uncertainty method fits.

Challenging the estimand is a valid I3 finding, not a failure to comply.

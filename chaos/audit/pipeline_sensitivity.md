# AUDIT -- PIPELINE SENSITIVITY (§26, §27)

**Question.** Does the pipeline respond to properties of the WORLD, or does it
mechanically reproduce its preferred interpretation?

The analysis code was **not modified** between conditions.

## Results

| # | perturbation | expected | observed | verdict |
|---|---|---|---|---|
| P1 | unchanged world, repeated | identical | identical | **PASS** |
| P2 | arm labels exchanged | gap flips sign exactly | +0.774167 -> sign flip, residual 0.000e+00 | **PASS** |
| P3 | **null world**: both arms get the SAME treatment | gap ~ 0 | **+0.004167** | **PASS** |
| P4 | one-attribute messages instead of two | gap shrinks | +0.376389 vs +0.774167 | **PASS** |

## KPI 5 -- VERDICT: **WORLD_SENSITIVE**

P3 is the decisive one. It removes the manipulation entirely -- both arms
receive identical treatment -- and the pipeline reports essentially no
difference. A pipeline mechanically reproducing its preferred answer could not
do that.

P4 shows the output tracks available information: a single attribute cannot
uniquely identify an object when several share it, and the gap contracts from
0.774 to 0.376.

## DISCLOSED LIMITATION

The harness uses `rho_model=1.0`; the main experiment used `rho_model=0.85`.
**Absolute values here are NOT comparable to the main experiment.** Only the
*response to perturbation* is being tested, and that is unaffected.

## A finding this test produced incidentally

The P4 gap (+0.3764) is not merely "smaller". Target 2 is
the case where `red square` matches two objects partially -- so it is the one
configuration in which a *relevant* message does not uniquely identify its
target. Its irrelevant-arm accuracy (0.2125) is far above the other targets
(0.0725), and its relevant-vs-irrelevant gap (0.4375) is the smallest of the
three.

**Relevance matters most when it actually discriminates.** That is a real
moderator effect, and it was not the question this experiment asked.

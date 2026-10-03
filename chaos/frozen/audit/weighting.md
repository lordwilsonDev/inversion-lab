# AUDIT -- WEIGHTING (§9, §10)

## Q1: Was the weighting rule fixed before outcome inspection?

**NO. It is POST-HOC.**

The rule `sum(w*gap)/sum(w)` with `w = n_rel + n_irr` was written in `docs.py`
*after* the strata had been inspected and the direction of the result was known.
By §9's own definition this cannot be described as preregistered.

## Q2: Does the post-hoc rule influence the load-bearing number?

**NO -- the rule is vacuous for the load-bearing cell.**

The load-bearing cell (`rho=1.0`, `T=1.0`) contains **1 populated stratum**:

| key (cand_red, dH) | n_rel | n_irr |
|---|---:|---:|
| (2, 0.51) | 800 | 1200 |

With one stratum, sample-size weighting, equal-stratum weighting and **no**
weighting are numerically identical. The verifier computed all three
independently and obtained:

| rule | estimate |
|---|---|
| sample-size weighted | +0.602083 |
| equal-stratum | +0.602083 |
| worst-stratum | +0.602083 |
| best-stratum | +0.602083 |
| **spread** | **0.000000** |

**The post-hoc weighting is a methodological blemish with zero numerical
consequence for the headline number.** That is a much weaker problem than
post-hoc weighting would normally be -- and it is only true *by accident*,
because the cell happened to contain one stratum.

## Q3: Where does the weighting rule actually matter?

**The noisy arm (`rho=0.85`), which was reported as a robustness check.**

| rule | estimate |
|---|---|
| equal-stratum | +0.2390 |
| sample-size (**reported**) | +0.3756 |
| min-arm-N | +0.3967 |
| worst-case stratum | +0.0671 |
| best-case stratum | +0.5054 |
| **spread** | **0.4383** |

The reported `+0.3756` is **one of five defensible values**. It was neither the
largest nor the smallest, but it was selected after the fact. The honest
statement is the *range*: **the sign is stable (+0.067 to +0.505), the magnitude
is not determined.**

**RETRACTION R-02** (see `retractions.md`): `+0.3756` must not be cited as *the*
noisy-arm estimate.

## Q4: Was there a defined target population?

**NO.** No target population was specified before execution. The sample-size rule
implicitly targets "the distribution of trials actually generated", which is a
defensible but unstated choice -- not a preregistered one.

## KPI 3 -- WEIGHTING TRANSPARENCY

| requirement | status |
|---|---|
| rule fully specified | **PASS** |
| fixed before comparison | **FAIL** (post-hoc) |
| rule justified scientifically | **QUALIFIED** (vacuous for the headline; materially consequential for the noisy arm) |

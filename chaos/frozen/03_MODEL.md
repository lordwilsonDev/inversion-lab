# 03 -- MATHEMATICAL MODEL

## Prior

Uniform over 3 objects: `p(o) = 1/3`, `H(O) = log2(3) = 1.5849625` bits.

## Likelihood

For message M with constraints C, object o with attributes `v_o`:

    P(M | o) = prod_{a,v in C} [ P(hit | a=v_o=v) + eps ]

    P(hit)  = rho                      (channel reliability)
    P(miss) = (1 - rho) / (|V| - 1)    (split over the alternatives)
    eps     = (1 - rho) / (|V| - 1)    (floor; required by the unit test in §18
                                        to survive a corner case)

Note the miss probability is **split across alternatives**, not assigned whole.
This matters: it is why a graded posterior retains nonzero mass on every object
(the §7 requirement).

## Posterior

    p(o | M)  proportional to  p(o) * P(M | o)

Normalised over all 3 objects. Mass is **never** set to zero.

## Decision rule (§13)

Posterior-proportional sampling at temperature T:

    P(choose o) proportional to  p(o | M)^(1/T)

Tested at T in {0.5, 1.0, 2.0}. Deterministic `argmax` is **not used** anywhere
(the trajectory's D17 defect: argmax over a diffuse posterior returns the lowest
index and manufactures a position gradient).

## Uncertainty measures (§7)

    H_before = -sum_o p(o) log2 p(o)               = log2(3)
    H_after  = -sum_o p(o|M) log2 p(o|M)
    dH       = H_before - H_after

    cand_red = |{o : p(o) > 0}| - |{o : p(o|M) > 0}|

## What `dH` does and does not measure

`dH` is the reduction in **Shannon entropy over objects**. It is a scalar
summary of a *distribution*. It is silent about *where the mass sits*.

This turns out to be the whole story (§05).

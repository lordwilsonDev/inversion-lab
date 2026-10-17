# B4 PRE-REGISTRATION (§5)

**Recorded BEFORE data collection.** Gates 1–2 were run first (§3/§4) because they
determine whether B4 is capable; they are not theory experiments.

---

## 1. State representation

A receiver holds a posterior `p(f)` over the full codebook space
`F = S_K`, `|F| = K! = 40320` codebooks `f: concepts -> tokens`.
**No hypothesis is ever removed.** State = the posterior vector only.

## 2. Hypothesis space

`F = S_8`, all 8! = 40,320 codebooks. Reuses the audited `tables()` from the
prior substrate (`lexrepair.receiver`), so the codebook representation is
identical to Runs 1–3 and results are comparable.

## 3. Prior distribution

- `PRIOR-UNIFORM`: `p₀(f) = 1/40320` ∀f.
- `PRIOR-TILT`: `p₀(f) ∝ exp(4c·(u_f − ½))`, `u_f` from `blake2b`-seeded
  `default_rng`, reproducible across processes.

**§6 mandatory check:** posterior non-uniformity, entropy, max, min, effective
hypothesis count, and concentration are recorded after *every* update. A
"non-uniform prior" that washes out is reported as uniform for that experiment.

## 4. Likelihood function

Symmetric noisy channel on the token axis. For evidence item = sender's
encoding of a known scene object:

```
P(t | f, c_j) = 1 − ε          if f(c_j) = t
              = ε / (K − 1)    otherwise
```

For message `t = (t₀,t₁,t₂)` and candidate object `o` with concepts `c(o)`:

```
L(f, o) = Π_{j=0..2} P(t_j | f, c_j(o))
```

`L > 0` for all `(f,o)` when `ε > 0`. **Nothing is eliminated.**

Two evidence types:
- **attributed** — evidence known to come from object `o`: step factor `L(·, o)`.
- **unattributed (raw information)** — evidence not tied to a known object:
  step factor `L̄(f) = mean_o L(f, o)`, which is object-independent and
  therefore carries **no target-discriminating signal**. This is the control
  that separates "content" from "any graded evidence at all".

## 5. Evidence update rule

```
p_t(f) ∝ p_{t−1}(f) · step_t(f)
```

## 6. Decision rule

Object posterior at query time:

```
P(o | evidence) ∝ Σ_f p(f | evidence) · L_query(f, o)
```

- **Policy A — posterior-proportional:** `argmax_o P(o|e)`. Deterministic.
- **Policy B — temperature sampling:** `P(action=o) ∝ P(o|e)^(1/T)`.

**PREREGISTERED temperatures: T ∈ {0.5, 1.0, 2.0}.** Chosen before any data.
`T → 0` recovers Policy A. Every primary result must survive all three
temperatures, otherwise it is reported as policy-dependent (§8).

## 7. Communication channel and feedback

Sender `fS` is a derangement of the identity. Messages are `encode(fS, target)`.
Feedback conditions (§15):

| Condition | Feedback |
|---|---|
| A. none | no evidence |
| B. raw information | 1 unattributed message |
| C. graded evidence | n attributed messages, known noise ε |
| D. contrastive | evidence chosen to discriminate competing hypotheses |
| E. verification-only | evidence that the guess was wrong, **no model structure revealed** |
| F. target revelation | target revealed directly |
| G. equal-budget | costs matched by *bits*, not message count |
| H. state perturbation | receiver prior changed, nominal external information identical |

## 8. Environmental state, target selection, evaluator

Scene = 5 objects, each a `(color, shape, size)` triple. Target uniform over
scene objects via seeded RNG. **Evaluator = correctness of selected target.**

## 9. Primary outcome

**Held-out success under Policy A** on a scene never used in training.

## 10. Secondary outcomes

- success under Policy B at each preregistered T;
- posterior concentration (`top10pct_mass`), posterior entropy;
- **calibration**: Brier score of the stated posterior probability;
- **model recovery**: fraction of concepts recovered by posterior argmax;
- **state recovery**: whether the posterior reproduces the sender's
  distinctions on a *novel* scene;
- transfer to novel scene and novel target.

## 11. Confound candidates and stratification variables (§11, §12)

Candidate count is **constant (=5) by construction** in B4 — verified in
Gate 1 (G1e). It therefore **cannot** absorb any signal. Stratification is by:

| Variable | Why |
|---|---|
| `ε` (channel noise) | determines how sharp evidence can be |
| posterior concentration | prior runs showed concentration is the live variable |
| number of evidence items | controls saturation |
| target index | **F2 position leakage probe** |
| scene size | **F3 scene leakage probe** |
| `T` (temperature) | **decision-policy robustness** |

Rule enforced in code: **no marginal interpretation is reported without the
stratified table beside it** (§23).

## 12. Preregistered falsification tests

| ID | Test |
|---|---|
| F1 | Candidate-count leakage — impossible by construction (support=5 always); verify empirically |
| F2 | Position leakage — success must not depend on `target.index` |
| F4 | Posterior collapse — non-uniformity after every update |
| F7 | Metric identity — is any metric a deterministic function of another |
| F8 | Marginal confounding — does conditioning reverse any sign |
| F9 | Information-budget — does one condition simply get more useful evidence |
| F11 | Persistence — does the effect survive held-out transfer |
| F12 | Model/behavior dissociation — behaviour ≠ model recovery |
| F13 | Competing mechanism — can a null mechanism reproduce the effect |
| F15 | Substrate perturbation — does the effect survive changing ε and T |

## 13. Stopping conditions (§28)

Stop and record a boundary if: operational collapse (no observable separates
the constructs); measurement collapse (metric is an identity of another);
causal collapse (intervention not independently manipulable); or substrate
collapse (the environment erases the distinction).

## 14. Recomputation levels (§25)

Load-bearing results must reach **Level 3** (recomputed from raw rows).
Any result not independently recomputed is marked
`SUMMARY-TRACEABLE / NOT_INDEPENDENTLY_RECOMPUTED`.

---

## Known limitation recorded before execution

Gate 1's concentration curve shows the posterior **saturating quickly** at
`ε = 0.15` (top-10% mass reaches 1.0 by the second evidence item). A sharply
saturated posterior would itself act like a near-elimination rule and could
re-create the old degeneracy. Therefore `ε` is manipulated with a
preregistered second, noisier level:

**PREREGISTERED ε LEVELS: {0.15, 0.35}.**

This is recorded *before* data collection precisely so the choice cannot be
tuned after seeing results.
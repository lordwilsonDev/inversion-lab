# 04 -- EXPERIMENT

## Design

Fully crossed: **2 arms** x **3 targets** x **2 channel reliabilities**
x **3 temperatures**, 400 trials, every cell independently seeded.

Seeds are derived via blake2b from stable string identifiers
(`stable_seed`). Never from `hash()` -- the trajectory's D14 defect, where
process-randomised string hashing destroyed reproducibility.

## Arms (§9)

| Arm | Message | n tokens |
|-----|---------|----------|
| `relevant` | describes the target | 2 |
| `irrelevant_matched` | describes a non-target | 2 |

## Channel

`rho_channel` in {1.0 (noiseless), 0.85}. Each token is corrupted independently
with probability `1 - rho`. Realised reliability is persisted per trial
(`realized_rho`), not assumed.

Realised rho at nominal 0.85: relevant 0.8483,
irrelevant 0.8488.

## Feedback trials (§14, §15)

Separate block, 2400 trials:
message -> decision -> error -> correction -> update -> second decision.

Two conditions:
- `hint=0` -- bare error signal
- `hint=1` -- error signal plus one corrective attribute hint

## Evaluator

`correct = int(decision == target)`. The receiver's `decide_sampled` consumes
only `prior`, `rho_model`, `sent_message`. `target`/`target_str` are read by the
scorer only. Verified in §08 (D_evaluator_leakage).

## Pre-experiment validation (§18)

Cases A-F run **before** any substantive trial:
A identifies exactly one object; B identifies none; C irrelevant message;
D two objects satisfy; E feedback removes a candidate; F parser order-independence.
All PASS. Substantive trials were not run until this passed.

# DATA DICTIONARY

Derived by inspecting the raw schema ONLY. No outcome values, arm means,
or expected directions are disclosed here.

| field | type | description |
|---|---|---|
| `H_after` | float | numeric, 3 distinct |
| `H_before` | float | numeric, 1 distinct, CONSTANT=1.5849625 |
| `arm` | str | categorical: ['irrelevant_matched', 'relevant'] |
| `candidate_reduction` | int | numeric, 2 distinct |
| `candidate_set` | list | list (len [0, 1]) |
| `correct` | int | numeric, 2 distinct |
| `decision` | int | numeric, 3 distinct |
| `decision_policy` | str | categorical: ['sample_T0.5', 'sample_T1.0', 'sample_T2.0'] |
| `decision_str` | str | categorical: ['blue/square/large', 'red/circle/large', 'red/square/small'] |
| `delta_H` | float | numeric, 3 distinct |
| `identified_target` | int | numeric, 2 distinct |
| `intended_message` | str | categorical: ['blue square', 'red circle', 'red square'] |
| `n_candidates_after` | int | numeric, 2 distinct |
| `n_candidates_before` | int | numeric, 1 distinct, CONSTANT=3 |
| `n_tokens_intended` | int | numeric, 1 distinct, CONSTANT=2 |
| `n_tokens_sent` | int | numeric, 1 distinct, CONSTANT=2 |
| `posterior` | list | list (len [3]) |
| `prior` | list | list (len [3]) |
| `realized_rho` | float | numeric, 3 distinct |
| `rho_channel` | float | numeric, 2 distinct |
| `seed` | int | numeric, 667 distinct |
| `sent_message` | str | categorical: ['blue circle', 'blue square', 'red circle', 'red square'] |
| `target` | int | numeric, 3 distinct |
| `target_str` | str | categorical: ['blue/square/large', 'red/circle/large', 'red/square/small'] |
| `temperature` | float | numeric, 3 distinct |
| `trial` | int | numeric, 112 distinct |

## Required integrity checks (verifier must perform these before computing)

- row count and uniqueness of `trial`
- balance of arms within `target`
- no duplicate `(trial, arm)` pairs
- no missing fields


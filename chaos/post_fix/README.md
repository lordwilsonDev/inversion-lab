# POST-FIX ARTIFACTS — CURRENT VERIFIED STATE

State as of the v3 inverse-audit cycle. This IS preserved and checksummed.

## Raw data (immutable, never regenerated during this cycle)

| file | md5 | rows |
|---|---|---:|
| `06_RAW_ROWS.jsonl` | `2daaa05c36aea1801a728fbefab666af` | 14,400 |
| `06_RAW_ROWS_FEEDBACK.jsonl` | `f75bc1e66a6842c563853bdee4b803d8` | 2,400 |

World fingerprint `882027e856db`.

These were **not** regenerated during the v3 audit cycle. Every audit number
traces back to them.

## Post-D20 corrected values

| quantity | value |
|---|---:|
| feedback net accuracy change (no hint) | **+0.1342** |
| feedback breakage (correct→wrong) | 0.3051 |
| feedback repair (wrong→correct) | 0.6747 |
| feedback ΔH | 0.1674 |
| fraction of trials with state change | 0.4483 |

## Corrections made IN this cycle

| id | what changed | effect on numbers |
|---|---|---|
| R-01 | the load-bearing estimate is now paired-within-target | +0.602083 → **+0.578333** |
| R-02 | noisy-arm estimate is now a range, not a point | +0.3756 → **+0.0671 .. +0.5054** |
| R-03 | independence re-labelled | "Level 3 independent" → **I1**, with an I2 verifier now added |
| D21 | pipeline-sensitivity harness rebuilt | P3 gap +0.5433 → **+0.0042** |

## Freeze protocol now in force

1. Raw rows are written once, checksummed, and **never** regenerated during an
   audit cycle.
2. Any correction writes to a **new** filename; the prior version is retained.
3. `frozen/` is created **before** any correction, not after.

Violation of (3) is what emptied `pre_fix/`. See `pre_fix/README.md`.
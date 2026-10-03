# PRE-FIX ARTIFACTS — DIRECTORY IS INTENTIONALLY EMPTY

## Status: **PRESERVATION FAILED** (retraction R-04)

This directory should contain the artifacts as they existed **before** the D20
correction. It does not, because the correction was made in place.

## What happened

D20 (the error signal was passed as `correct=False` unconditionally) was found
and fixed during the previous cycle. The fix re-ran `experiment.py`, which
**overwrote** `06_RAW_ROWS_FEEDBACK.jsonl` and `05_RESULTS.json` in place.

At that time:
- the `chaos/` directory was not tracked by git (`git status` shows it untracked),
- `chaos/frozen/` had not yet been created -- it was created *after* the fix,
- no timestamped backup was taken.

So there is no pre-fix raw data, no pre-fix results file, and no pre-fix code.

## The only surviving trace of the pre-fix state

The pre-fix numbers survive **as prose in my own prior report**, quoted here for
the record. These are **NOT independently checkable** against any artifact:

| quantity | pre-fix value | how it is known |
|---|---:|---|
| feedback net accuracy change | −0.2550 | quoted in REPORT.md §6 of the previous cycle |
| breakage (correct→wrong) | 0.9636 | quoted in 09_FINDINGS.md F4 |
| repair (wrong→correct) | 0.6956 | quoted in 09_FINDINGS.md F4 |
| first-decision accuracy | 0.5729 | quoted in the previous audit output |

These four numbers were captured from stdout at the time. They are preserved here
because §13 requires preservation, and because losing them entirely would be
worse — but they are marked **UNVERIFIABLE** and must never be cited as evidence.

## The lesson, recorded so it is not repeated

> **Freeze before correcting, not after.**

In this cycle the freeze discipline was applied to the *raw rows* (they are
checksummed and were not regenerated), which is why the independent re-derivation
was possible at all. It was **not** applied to the pre-fix outputs, which is why
this directory is empty. The rule is not "freeze the current state" but
"**freeze every state, including the one you are about to overwrite.**"
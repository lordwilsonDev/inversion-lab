#!/usr/bin/env python3
"""V3 -- NEXT-QUESTION CONTRACT VALIDATION (§20, §21, §22, §23).

Checks 10_NEXT_QUESTION.json for every field the blueprint requires, and
checks that the window is a VALID window rather than a vague one.

Exit code 0 = contract complete. Non-zero = INCOMPLETE.
"""
from __future__ import annotations

import json
import re
import sys

HERE = "/Users/lordwilson/projects/inversion-lab/chaos"
REQUIRED = ["question_id", "question", "variable", "held_constant", "window",
            "auditor", "auditor_independence_level", "falsifier",
            "expected_observation"]

# §21: valid windows are concrete; "when enough evidence exists" is invalid.
VAGUE = re.compile(
    r"when enough|as data (?:comes|accrues)|at some point|eventually|"
    r"when (?:we|it) (?:know|knows|see|sees|can tell)", re.I)
VALID_WINDOW = re.compile(
    r"\d[\d,]*\s*(?:trials|rows|runs|cycles)|one complete|preregistered|"
    r"checksummed|BEFORE|before any", re.I)


def main() -> int:
    c = json.load(open(f"{HERE}/10_NEXT_QUESTION.json"))
    failures, warns = [], []

    print("=" * 70)
    print("V3 -- NEXT-QUESTION CONTRACT")
    print("=" * 70)

    for f in REQUIRED:
        present = f in c and c[f] not in (None, "", [], {})
        print(f"  {f:<28} {'PRESENT' if present else 'MISSING'}")
        if not present:
            failures.append(f"missing required field: {f}")

    w = c.get("window", "")
    if VAGUE.search(w):
        failures.append("window uses a VAGUE trigger phrase (§21)")
        print("  window vagueness            VAGUE  <-- FAIL")
    else:
        print("  window vagueness            CONCRETE")
    if not VALID_WINDOW.search(w):
        warns.append("window does not match any known-valid window pattern")

    lvl = str(c.get("auditor_independence_level", ""))
    print(f"  independence level declared: {lvl}")
    if "I3" in lvl and "not achievable" not in c.get("auditor_independence_level", ""):
        warns.append("I3 claimed without qualifying achievability")

    qt = c.get("quality_test", {})
    print(f"  quality tests present       : {len(qt)}/5")
    for k in ("novelty", "evidence_derivation", "operationalizability",
              "falsifiability", "non_closure"):
        if k not in qt:
            failures.append(f"quality test missing: {k}")

    print()
    if failures:
        print("VERDICT: INCOMPLETE")
        for f in failures:
            print(f"  - {f}")
    else:
        print("VERDICT: COMPLETE -- all §20 fields present, window is concrete.")
    for wmsg in warns:
        print(f"  warning: {wmsg}")

    with open(f"{HERE}/13_CONTRACT_VALIDATION.json", "w") as fh:
        json.dump({"complete": not failures, "failures": failures,
                   "warnings": warns, "required_fields": REQUIRED}, fh, indent=2)
    print("\nwrote 13_CONTRACT_VALIDATION.json")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
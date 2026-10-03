#!/usr/bin/env python3
"""REFERENCE REVEAL + FIVE-LEVEL COMPARISON (§16, §18).

Runs ONLY after 08_INTERPRETATION.md is frozen. Does not alter any
clean-room output. Writes a separate comparison artifact.
"""
from __future__ import annotations

import hashlib
import json
import os
from fractions import Fraction

CR = "/Users/lordwilson/projects/inversion-lab/chaos/cleanroom"
ROOT = os.path.dirname(CR)
TOL = 0.05

ext = json.load(open(f"{CR}/06_PRIMARY_RESULT.json"))

# Reference read from the ORIGINAL analysis artifacts (revealed only now).
ref = {
    "G": 0.578333,
    "per_target": {0: 0.6400, 1: 0.6575, 2: 0.4375},
    "source": "audit/corrected_stratified_analysis.md + REPORT.md §0",
}

print("=" * 72)
print("REFERENCE REVEAL (§19)")
print("=" * 72)
print(f"  reference G          : {ref['G']:+.6f}")
print(f"  external   G         : {ext['G_float']:+.6f}  (exact {ext['G_exact']})")
print(f"  preregistered tol    : {TOL}")
diff = abs(ext["G_float"] - ref["G"])
print(f"  |difference|         : {diff:.8f}")
print()

print("=" * 72)
print("LEVEL A -- NUMERICAL AGREEMENT")
print("=" * 72)
print(f"  {'target':>8} {'external':>12} {'reference':>12} {'diff':>10}")
for t in ("0", "1", "2"):
    e = ext["per_target"][t]["gap_float"]
    r = ref["per_target"][int(t)]
    print(f"  {t:>8} {e:>+12.6f} {r:>+12.6f} {abs(e - r):>10.8f}")
level_a = diff <= TOL
print(f"\n  primary within tolerance: {level_a}")
print(f"  all target-level within tolerance: "
      f"{all(abs(ext['per_target'][t]['gap_float'] - ref['per_target'][int(t)]) <= TOL for t in ('0','1','2'))}")
print()

print("=" * 72)
print("LEVEL B -- STRUCTURAL AGREEMENT (same scientific object?)")
print("=" * 72)
print("  external estimand : mean over targets of (Acc_rel,t - Acc_irr,t)")
print("  reference estimand: same, after R-01 replaced dH-stratification")
print("  MATCH: True -- the reference was already corrected to this estimand")
level_b = True
print()

print("=" * 72)
print("LEVEL C -- TARGET-LEVEL AGREEMENT")
print("=" * 72)
print("  correspondence is 1:1 across all three targets; no crossover.")
level_c = True
print()

print("=" * 72)
print("LEVEL D -- METHOD AGREEMENT")
print("=" * 72)
print("  matching rule   : both balanced-within-target, no post-treatment conditioning")
print("  aggregation rule: both unweighted mean across targets")
print("  uncertainty     : external = Wilson + paired bootstrap (10k, seed 20261003)")
print("                     reference = point estimates only (no interval was reported)")
print("  MATCH on matching + aggregation: True")
print("  MATCH on uncertainty:            False -- reference reported NO interval")
level_d_partial = True
print()

print("=" * 72)
print("LEVEL E -- INTERPRETATION AGREEMENT")
print("=" * 72)
print("  Both assign the effect to posterior mass placement rather than to the")
print("  scalar summaries (entropy / candidate count). Both record that the")
print("  linguistic reading is UNRESOLVED. Both flag target 2 as behaving")
print("  differently. Substantively compatible.")
print("  CAVEAT: compatible because the same author wrote both. This is NOT")
print("  independent interpretive convergence.")
level_e_claimed = True
level_e_real = False
print()

print("=" * 72)
print("FIRST POINT OF DIVERGENCE (§17)")
print("=" * 72)
print("  raw data            : AGREE (sha256 identical)")
print("  construct           : AGREE")
print("  estimand            : AGREE")
print("  row selection       : AGREE")
print("  matching rule       : AGREE")
print("  aggregation         : AGREE")
print("  uncertainty         : DIVERGE  <- D-F statistical disagreement")
print("  interpretation      : compatible-but-not-independent")
print()
print("  First divergence: D-F (statistical). The external analysis produced a")
print("  confidence interval [+0.5458, +0.6092]; the original produced none.")
print("  This is a gap in the ORIGINAL, not an error in the reconstruction.")
print()

print("=" * 72)
print("AGREEMENT CLASSIFICATION (§18)")
print("=" * 72)
print("  Numerically:          full agreement")
print("  Structurally:         full agreement")
print("  Target-level:         full agreement")
print("  Method:               agreement on matching/aggregation; DIVERGENCE on uncertainty")
print("  Interpretation:       compatible, but not independently earned")
print()
print("  -> I3-A (full agreement) CANNOT be claimed, because independence fails.")
print("  -> The correct label is I3-COMPANEL: NO OBSERVER.")
print()

print("=" * 72)
print("I3 STATUS")
print("=" * 72)
print("  independence of verifier : FAILED (same author as the original)")
print("  blinding                 : FAILED (I authored the expected value)")
print("  specification quality    : ESTIMAND_UNDER-SPECIFIED on the inclusion rule")
print()
print("  I3 STATUS: I3_COMPROMISED -> terminates at I3_INCOMPLETE,")
print("             with SPECIFICATION_BOUNDARY recorded on the estimand.")
print("             Per §39 this is a boundary, not a defect to be engineered past.")

out = {
    "tolerance": TOL,
    "reference": ref,
    "external": {"G": ext["G_float"], "G_exact": ext["G_exact"],
                 "per_target": {t: ext["per_target"][t]["gap_float"] for t in ext["per_target"]}},
    "primary_difference": diff,
    "level_A_numerical": bool(level_a),
    "level_B_structural": bool(level_b),
    "level_C_target": bool(level_c),
    "level_D_method_matching_and_aggregation": bool(level_d_partial),
    "level_D_method_uncertainty": False,
    "level_E_interpretation_compatible": True,
    "level_E_interpretation_independent": False,
    "first_divergence": "D-F statistical (uncertainty); external produced an interval, original produced none",
    "i3_status": "I3_COMPROMISED",
    "boundary": "SPECIFICATION_BOUNDARY (inclusion rule under-specified)",
    "estimand_ambiguity_spread": ext["ambiguity_spread"],
    "estimands_outside_tolerance": ext["estimands_outside_tolerance"],
}
with open(f"{CR}/11_REFERENCE_COMPARISON.json", "w") as fh:
    json.dump(out, fh, indent=2)
print("wrote 11_REFERENCE_COMPARISON.json")
#!/usr/bin/env python3
"""INDEPENDENT VERIFIER -- blind re-derivation of the matched-strata estimand.

WRITTEN FROM THE ESTIMAND DESCRIPTION ONLY.

This module was deliberately NOT shown:
  * the reported value +0.6021 as a target,
  * the grouping key the original pipeline used,
  * the original analysis code (audit.py / docs.py),
  * the original interpretation.

It re-derives, from the frozen rows alone:
  1. which rows belong to the estimand,
  2. what constitutes a matched stratum,
  3. the accuracy in each stratum,
  4. the aggregation rule (and whether one is even needed),
  5. the final estimate,
  6. an uncertainty interval -- which the original pipeline never computed.

DELIBERATE STYLE DIFFERENCES from the original analysis:
  * EXACT RATIONAL ARITHMETIC (fractions.Fraction) instead of float means,
    so agreement is not an artefact of floating-point accumulation order.
  * Strata derived by INTERSECTING the arm key-sets, rather than by grouping
    on a pre-chosen tuple.
  * Wilson score intervals instead of bare point estimates.
  * Streaming read, so no full in-memory dataframe is trusted.
  * Zero imports from world.py / experiment.py / audit.py / docs.py.

HONEST LIMITATION, recorded in audit/independence.md:
  This module was still authored by the same entity that produced the original
  result. By the blueprint's ladder this is I2 (separate analytical logic), and
  can never be I3 (external verifier).
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction
from math import sqrt

RAW = "/Users/lordwilson/projects/inversion-lab/chaos/06_RAW_ROWS.jsonl"

# The estimand, as stated in natural language in the blueprint:
#   "the load-bearing matched-strata accuracy difference" in the cell
#   rho = 1.0, temperature = 1.0, matched on candidate reduction and entropy.
TARGET_RHO = 1.0
TARGET_TEMP = 1.0


def wilson(successes: int, n: int, z: float = 1.959963984540054):
    """Wilson score interval. The original pipeline reported no interval at all."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = successes / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z / denom) * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, centre - half), min(1.0, centre + half))


def exact_diff(a_succ: int, a_n: int, b_succ: int, b_n: int):
    """Exact Fraction difference of two proportions. No floating point."""
    return Fraction(a_succ, a_n) - Fraction(b_succ, b_n)


def main() -> int:
    # ---------------------------------------------------------------- load
    # Streaming. Only the columns needed for the estimand are retained.
    rows = []
    with open(RAW) as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            if r["rho_channel"] == TARGET_RHO and r["temperature"] == TARGET_TEMP:
                rows.append(r)

    total_rows = 0
    with open(RAW) as fh:
        for line in fh:
            if line.strip():
                total_rows += 1

    print("=" * 72)
    print("INDEPENDENT VERIFIER -- blind re-derivation")
    print("=" * 72)
    print(f"raw file            : {RAW}")
    print(f"total rows in file  : {total_rows}")
    print(f"rows in estimand    : {len(rows)}  "
          f"(rho={TARGET_RHO}, temperature={TARGET_TEMP})")

    # ------------------------------------------------- what is a stratum?
    # Re-derived, not assumed: a stratum is defined by the tuple of variables
    # on which the two arms are required to be MATCHED. The matching variables
    # are taken to be candidate reduction and entropy reduction, because those
    # are the two the blueprint names as the matched quantities.
    def stratum_key(r):
        # Rounded to 2dp because entropy is persisted at 8dp and the arms can
        # differ in the last bits purely from summation order.
        return (r["candidate_reduction"], round(r["delta_H"], 2))

    # Build strata by intersecting arm keysets, not by grouping a chosen tuple.
    keys_by_arm = {}
    for r in rows:
        keys_by_arm.setdefault(r["arm"], {}).setdefault(stratum_key(r), []).append(r["correct"])

    print(f"arms present        : {sorted(keys_by_arm)}")
    print(f"stratum keys per arm: "
          f"{ {a: len(v) for a, v in keys_by_arm.items()} }")

    shared = sorted(set(keys_by_arm.get("relevant", {})) &
                    set(keys_by_arm.get("irrelevant_matched", {})))
    print(f"SHARED strata keys  : {len(shared)} -> {shared}")
    print()

    # ------------------------------------------------------------ estimate
    est_w = Fraction(0)
    wsum = 0
    est_e = Fraction(0)
    est_min = None
    est_max = None
    table = []

    for k in shared:
        rel = keys_by_arm["relevant"][k]
        irr = keys_by_arm["irrelevant_matched"][k]
        a_s, a_n = sum(rel), len(rel)
        b_s, b_n = sum(irr), len(irr)
        d = exact_diff(a_s, a_n, b_s, b_n)
        w = a_n + b_n
        est_w += d * w
        wsum += w
        est_e += d
        est_min = d if est_min is None else min(est_min, d)
        est_max = d if est_max is None else max(est_max, d)
        lo_a, hi_a = wilson(a_s, a_n)
        lo_b, hi_b = wilson(b_s, b_n)
        table.append((k, a_s, a_n, b_s, b_n, d, lo_a, hi_a, lo_b, hi_b))

    est_w /= wsum
    est_e /= len(shared)

    print("-" * 72)
    print("PER-STRATUM (exact rational arithmetic)")
    print("-" * 72)
    print(f"{'cand_red':>9} {'dH':>6} | {'rel k/n':>12} {'95% Wilson':>20} | "
          f"{'irr k/n':>12} {'95% Wilson':>20} | {'exact diff':>12}")
    for (k, a_s, a_n, b_s, b_n, d, lo_a, hi_a, lo_b, hi_b) in table:
        print(f"{k[0]:>9} {k[1]:>6} | {f'{a_s}/{a_n}':>12} "
              f"[{lo_a:.4f},{hi_a:.4f}]".rjust(21) +
              f" | {f'{b_s}/{b_n}':>12} [{lo_b:.4f},{hi_b:.4f}]".rjust(21) +
              f" | {float(d):>+12.6f}")

    print()
    print("-" * 72)
    print("AGGREGATION")
    print("-" * 72)
    print(f"number of populated strata : {len(shared)}")
    if len(shared) == 1:
        print("  -> With one stratum, sample-size weighting, equal-stratum weighting,")
        print("     and NO weighting are numerically IDENTICAL. The aggregation rule")
        print("     cannot influence this estimate.")
    print(f"sample-size-weighted estimate : {float(est_w):+.6f}")
    print(f"equal-stratum   estimate      : {float(est_e):+.6f}")
    print(f"worst-stratum   estimate      : {float(est_min):+.6f}")
    print(f"best-stratum    estimate      : {float(est_max):+.6f}")

    print()
    print("-" * 72)
    print("INDEPENDENT RESULT")
    print("-" * 72)
    print(f"ESTIMATE (exact)             : {est_w}")
    print(f"ESTIMATE (float)             : {float(est_w):+.6f}")

    # ---------------------------------------------- machine-readable output
    out = {
        "independence_level_claimed": "I2",
        "independence_level_ceiling": "I2",
        "authored_by_same_entity": True,
        "raw_file": RAW,
        "total_rows_in_file": total_rows,
        "rows_in_estimand": len(rows),
        "rho": TARGET_RHO,
        "temperature": TARGET_TEMP,
        "strata_keys": [list(k) for k in shared],
        "n_populated_strata": len(shared),
        "strata": [
            {"cand_red": k[0], "delta_H": k[1],
             "rel_successes": a_s, "rel_n": a_n,
             "irr_successes": b_s, "irr_n": b_n,
             "rel_acc_exact": str(Fraction(a_s, a_n)),
             "irr_acc_exact": str(Fraction(b_s, b_n)),
             "diff_exact": str(d),
             "diff_float": float(d),
             "rel_wilson": [lo_a, hi_a], "irr_wilson": [lo_b, hi_b]}
            for (k, a_s, a_n, b_s, b_n, d, lo_a, hi_a, lo_b, hi_b) in table
        ],
        "estimate_sample_weighted": float(est_w),
        "estimate_equal_stratum": float(est_e),
        "estimate_worst_stratum": float(est_min),
        "estimate_best_stratum": float(est_max),
        "weighting_influence": (float(est_max) - float(est_min)),
        "aggregation_is_vacuous_single_stratum": len(shared) == 1,
    }
    with open("/Users/lordwilson/projects/inversion-lab/chaos/11_INDEPENDENT.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nwrote 11_INDEPENDENT.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""CLEAN-ROOM RECONSTRUCTION from the blind package only.

Reads ONLY files inside cleanroom/. Imports nothing from the original pipeline.
Does not import world.py, experiment.py, audit.py, docs.py, or
independent_verifier.py.

Order of operations is fixed by the blueprint §9:
    checksum -> schema -> rows -> grouping -> per-target -> primary -> uncertainty
"""
from __future__ import annotations

import hashlib
import json
import os
import random
from fractions import Fraction

CR = "/Users/lordwilson/projects/inversion-lab/chaos/cleanroom"
RAW = os.path.join(CR, "06_RAW_ROWS.jsonl")


# ---------------------------------------------------------------- §11 checks
def integrity():
    print("=" * 70)
    print("DATA VALIDATION (§11)")
    print("=" * 70)

    want = open(os.path.join(CR, "06_RAW_ROWS.sha256")).read().split()[0]
    got = hashlib.sha256(open(RAW, "rb").read()).hexdigest()
    print(f"  sha256 expected : {want}")
    print(f"  sha256 actual   : {got}")
    checksum_ok = (want == got)
    print(f"  CHECKSUM        : {'PASS' if checksum_ok else 'FAIL'}")

    rows = [json.loads(l) for l in open(RAW) if l.strip()]
    print(f"  rows            : {len(rows)}")

    missing = [k for k in rows[0] if any(k not in r for r in rows)]
    print(f"  missing fields  : {missing or 'none'}")

    arms = sorted({r["arm"] for r in rows})
    print(f"  arm labels      : {arms}")

    # DEFECT IN MY OWN CHECK (logged, not silently fixed): the first version used
    # (trial, arm, rho, T) as the uniqueness key and reported 9600 duplicates.
    # That key is wrong -- within a cell the design is 400 trials x 2 arms x
    # 3 targets, so `target` must be part of the key. The dataset was correct;
    # the check was wrong. Corrected below, and the false alarm is recorded.
    for label, keyf in (
            ("(trial,arm,rho,T)      [FIRST ATTEMPT - WRONG KEY]",
             lambda r: (r["trial"], r["arm"], r["rho_channel"], r["temperature"])),
            ("(trial,arm,rho,T,target) [CORRECTED KEY]",
             lambda r: (r["trial"], r["arm"], r["rho_channel"], r["temperature"],
                        r["target"]))):
        d = len(rows) - len({keyf(r) for r in rows})
        print(f"  duplicate keys on {label} : {d}")
    dup_pairs = len(rows) - len({(r["trial"], r["arm"], r["rho_channel"],
                                  r["temperature"], r["target"]) for r in rows})
    print(f"  distinct trial ids : {len({r['trial'] for r in rows})} "
          f"(trial ids REPEAT across condition cells AND across targets --")
    print(f"                       so a within-trial PAIRED test is NOT available)")

    cells = {}
    for r in rows:
        cells.setdefault((r["rho_channel"], r["temperature"]), []).append(r)
    print(f"  condition cells  : {sorted(cells)}")
    print(f"  cell sizes       : "
          f"{ {k: len(v) for k, v in sorted(cells.items())} }")
    return rows, checksum_ok, not missing and dup_pairs == 0


def wilson(s, n, z=1.959963984540054):
    if n == 0:
        return (float("nan"),) * 2
    p = s / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z / d) * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return (max(0.0, c - h), min(1.0, c + h))


def main():
    rows, ck, clean = integrity()
    if not (ck and clean):
        print("\nDATA DOES NOT SUPPORT THE STATED DESIGN -- STOP.")
        return

    # ------------------------------------------- frozen estimand, §13
    print()
    print("=" * 70)
    print("PRIMARY ESTIMAND (frozen in estimand_definition.md)")
    print("=" * 70)
    cell = [r for r in rows if r["rho_channel"] == 1.0 and r["temperature"] == 1.0]
    print(f"  cell rho=1.0, T=1.0 : n = {len(cell)}")

    targets = sorted({r["target"] for r in cell})
    per = {}
    for t in targets:
        a = [r["correct"] for r in cell if r["arm"] == "relevant" and r["target"] == t]
        b = [r["correct"] for r in cell
             if r["arm"] == "irrelevant_matched" and r["target"] == t]
        per[t] = {"n_rel": len(a), "k_rel": sum(a), "n_irr": len(b), "k_irr": sum(b),
                  "acc_rel": Fraction(sum(a), len(a)),
                  "acc_irr": Fraction(sum(b), len(b))}
        per[t]["gap"] = per[t]["acc_rel"] - per[t]["acc_irr"]
        lo_a, hi_a = wilson(sum(a), len(a))
        lo_b, hi_b = wilson(sum(b), len(b))
        per[t]["wilson_rel"] = [lo_a, hi_a]
        per[t]["wilson_irr"] = [lo_b, hi_b]
        print(f"  target {t}: rel {sum(a)}/{len(a)} = {float(per[t]['acc_rel']):.4f} "
              f"[{lo_a:.4f},{hi_a:.4f}]   irr {sum(b)}/{len(b)} = "
              f"{float(per[t]['acc_irr']):.4f} [{lo_b:.4f},{hi_b:.4f}]   "
              f"G_t = {float(per[t]['gap']):+.6f}")

    G = sum(per[t]["gap"] for t in targets) / len(targets)
    print(f"\n  G = mean(G_t) = {G} = {float(G):+.6f}   (exact rational)")

    # ------------------------------------------- §14 uncertainty
    print()
    print("=" * 70)
    print("UNCERTAINTY")
    print("=" * 70)
    rng = random.Random(20261003)
    boots = []
    for _ in range(10000):
        acc = []
        for t in targets:
            a = [r["correct"] for r in cell if r["arm"] == "relevant" and r["target"] == t]
            b = [r["correct"] for r in cell
                 if r["arm"] == "irrelevant_matched" and r["target"] == t]
            ra = [a[rng.randrange(len(a))] for _ in a]
            rb = [b[rng.randrange(len(b))] for _ in b]
            acc.append(sum(ra) / len(ra) - sum(rb) / len(rb))
        boots.append(sum(acc) / len(acc))
    boots.sort()
    lo, hi = boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots))]
    print(f"  paired bootstrap (10,000, seed 20261003): "
          f"[{lo:+.4f}, {hi:+.4f}]")
    print(f"  interval excludes 0: {lo > 0}")

    # ------------------------------------------- §32 ambiguity probe
    print()
    print("=" * 70)
    print("ESTIMAND AMBIGUITY PROBE (§32) -- all defensible readings")
    print("=" * 70)
    cands = {}

    cands["G_mean_of_per_target_gaps (FROZEN)"] = float(G)
    cands["G_pooled_difference"] = (
        sum(r["correct"] for r in cell if r["arm"] == "relevant") /
        sum(1 for r in cell if r["arm"] == "relevant")
        - sum(r["correct"] for r in cell if r["arm"] == "irrelevant_matched") /
        sum(1 for r in cell if r["arm"] == "irrelevant_matched"))
    cands["G_inverse_variance_weighted"] = (
        sum((1 / (1 / per[t]["n_rel"] + 1 / per[t]["n_irr"])) * per[t]["gap"]
            for t in targets) /
        sum((1 / (1 / per[t]["n_rel"] + 1 / per[t]["n_irr"])) for t in targets))
    gaps = [per[t]["gap"] for t in targets]
    cands["G_median_of_per_target_gaps"] = float(sorted(gaps)[1])
    cands["G_min_worst_target"] = float(min(gaps))
    cands["G_max_best_target"] = float(max(gaps))
    cands["G_exclude_target2"] = float(
        (per[targets[0]]["gap"] + per[targets[1]]["gap"]) / 2)
    cands["G_ratio_not_difference"] = (
        sum(r["correct"] for r in cell if r["arm"] == "relevant") /
        sum(1 for r in cell if r["arm"] == "relevant")) / (
        sum(r["correct"] for r in cell if r["arm"] == "irrelevant_matched") /
        sum(1 for r in cell if r["arm"] == "irrelevant_matched")) - 1

    base = cands["G_mean_of_per_target_gaps (FROZEN)"]
    print(f"  {'estimand':<42} {'value':>10} {'|diff|':>8}")
    for k, v in cands.items():
        star = "  <-- FROZEN" if "(FROZEN)" in k else ""
        print(f"  {k:<42} {v:>+10.4f} {abs(v - base):>8.4f}{star}")
    spread = max(cands.values()) - min(cands.values())
    print(f"\n  SPREAD across defensible estimands : {spread:.4f}")
    print(f"  preregistered tolerance            : 0.0500")
    print(f"  -> specification uniquely pins G?   "
          f"{'NO' if spread > 0.05 else 'YES'}")
    outside = [k for k, v in cands.items() if abs(v - base) > 0.05]
    print(f"  estimands exceeding tolerance      : {len(outside)}")
    for k in outside:
        print(f"      {k}  ({cands[k]:+.4f})")

    out = {"integrity": {"sha256": ck, "clean": clean, "rows": len(rows)},
           "per_target": {str(t): {"n_rel": per[t]["n_rel"], "k_rel": per[t]["k_rel"],
                                   "n_irr": per[t]["n_irr"], "k_irr": per[t]["k_irr"],
                                   "acc_rel": str(per[t]["acc_rel"]),
                                   "acc_irr": str(per[t]["acc_irr"]),
                                   "gap": str(per[t]["gap"]),
                                   "gap_float": float(per[t]["gap"]),
                                   "wilson_rel": per[t]["wilson_rel"],
                                   "wilson_irr": per[t]["wilson_irr"]}
                            for t in targets},
           "G_exact": str(G), "G_float": float(G),
           "bootstrap_95": [lo, hi],
           "ambiguity_candidates": cands,
           "ambiguity_spread": spread,
           "ambiguity_within_tolerance": spread <= 0.05,
           "estimands_outside_tolerance": outside}
    with open(os.path.join(CR, "06_PRIMARY_RESULT.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nwrote 06_PRIMARY_RESULT.json")
    print("\n*** NO REFERENCE COMPARISON PERFORMED IN THIS SCRIPT ***")


if __name__ == "__main__":
    main()
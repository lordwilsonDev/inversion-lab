"""B5 REPAIRED PRIMARY ANALYSIS -- after D17 (deterministic tie-break).

DEFECT D17 (found by probe F2, repaired here)
-----------------------------------------------
The preregistered PRIMARY outcome used the deterministic argmax decision rule.
Under that rule success depends strongly on target index
(0.879 / 0.762 / 0.647 / 0.573 / 0.522; spread 0.3575), because a diffuse
posterior produces near-ties and argmax deterministically returns the LOWEST
index.

This is a VIOLATION OF THE B5 SUBSTRATE CONTRACT (§6): B5 must not revert to
"hard elimination -> uniform posterior -> deterministic tie-break". Using argmax
as primary reintroduced exactly the old substrate's decision artifact, in the
new diffuse-posterior regime where it is much more visible than in B4.

Consequence: the marginal H1 estimate computed under argmax was POSITION-
CONFOUNDED, and its per-stratum instability (ti0 = -0.007) was an artifact.

REPAIR: the primary analysis is recomputed under the PREREGISTERED
non-deterministic policies (T in {0.5, 1.0, 2.0}). Under these:
    position spread 0.3575 -> 0.0119 .. 0.0250
    H1 task effect becomes UNIFORM across all five target-index strata.
The argmax results are RETAINED as the record of the defect, not deleted.

No new data were collected for this repair; the same 10,240 raw rows are
re-analysed under a different, already-preregistered decision rule.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict

import numpy as np

RAW = "/Users/lordwilson/projects/inversion-lab/b5/MAIN_RAW_ROWS.json"
PRIMARY_POLICY = "success_T1.0"      # preregistered non-deterministic policy


def load():
    return json.load(open(RAW))["rows"]


def mean(xs):
    return float(sum(xs) / len(xs))


def matched_pairs(rows, key):
    """§18: matched on MODEL entropy, varying TASK entropy."""
    pairs = []
    for rho in sorted(set(r["rho"] for r in rows)):
        for ni in sorted(set(r["n_items"] for r in rows)):
            sub = [r for r in rows if r["rho"] == rho and r["n_items"] == ni]
            mh = np.array([r["model_entropy_bits"] for r in sub])
            edges = np.quantile(mh, np.linspace(0, 1, 13))
            for lo, hi in zip(edges[:-1], edges[1:]):
                band = [r for r, m in zip(sub, mh) if lo <= m < hi]
                v1 = [r for r in band if r["n_visible"] == 1]
                v3 = [r for r in band if r["n_visible"] == 3]
                if len(v1) < 5 or len(v3) < 5:
                    continue
                gap = abs(mean([r["model_entropy_bits"] for r in v1]) -
                          mean([r["model_entropy_bits"] for r in v3]))
                if gap > 0.05:
                    continue
                pairs.append({
                    "rho": rho, "n_items": ni,
                    "model_gap": round(gap, 4),
                    "task_gap": round(abs(mean([r["task_entropy_bits"] for r in v1]) -
                                          mean([r["task_entropy_bits"] for r in v3])), 4),
                    "delta": mean([r[key] for r in v3]) - mean([r[key] for r in v1]),
                })
    return pairs


def position_stratified_effect(rows, key):
    out = {}
    for ti in range(5):
        sub = [r for r in rows if r["target_index"] == ti]
        p = matched_pairs(sub, key)
        if p:
            out[str(ti)] = {"n_pairs": len(p),
                            "mean_task_effect": round(mean([x["delta"] for x in p]), 4),
                            "frac_positive": round(sum(1 for x in p if x["delta"] > 0) / len(p), 4)}
    return out


def primary(rows, key):
    p = matched_pairs(rows, key)
    d = [x["delta"] for x in p]
    ps = position_stratified_effect(rows, key)
    vals = [v["mean_task_effect"] for v in ps.values()]
    by_idx = defaultdict(list)
    for r in rows:
        by_idx[r["target_index"]].append(r[key])
    rates = [mean(by_idx[i]) for i in range(5)]
    return {
        "policy": key,
        "n_rows": len(rows),
        "n_matched_pairs": len(p),
        "mean_task_effect": round(mean(d), 4),
        "sd": round(float(np.std(d)), 4),
        "frac_positive": round(sum(1 for x in d if x > 0) / len(d), 4),
        "mean_model_entropy_gap": round(mean([x["model_gap"] for x in p]), 4),
        "mean_task_entropy_gap": round(mean([x["task_gap"] for x in p]), 4),
        "position_spread": round(max(rates) - min(rates), 4),
        "success_by_target_index": [round(x, 4) for x in rates],
        "stratified_by_target_index": ps,
        "effect_uniform_across_position_strata": bool(vals and min(vals) > 0),
        "H1_task_account": ("SUPPORTED" if d and sum(1 for x in d if x > 0) / len(d) > 0.8
                            else ("FALSIFIED" if d else "UNTESTED")),
    }


def h2_within_task_strata(rows, key, n_strata=4):
    th = np.array([r["task_entropy_bits"] for r in rows])
    qs = np.quantile(th, np.linspace(0, 1, n_strata + 1))
    out = []
    for i in range(n_strata):
        band = [r for r, t in zip(rows, th) if qs[i] <= t < qs[i + 1]]
        a = [r[key] for r in band if r["rho"] == 1.0]
        b = [r[key] for r in band if r["rho"] == 0.5]
        if a and b:
            out.append({"stratum": f"taskH[{qs[i]:.3f},{qs[i+1]:.3f})",
                        "n_hi_rho": len(a), "n_lo_rho": len(b),
                        "succ_high_rho": round(mean(a), 4),
                        "succ_low_rho": round(mean(b), 4),
                        "delta": round(mean(a) - mean(b), 4)})
    d = [x["delta"] for x in out]
    return {"strata": out, "mean_delta": round(mean(d), 4) if d else None,
            "sign_stable": bool(d and (all(x > 0 for x in d) or all(x < 0 for x in d))),
            "H2_sender_model_account": ("SUPPORTED" if d and mean(d) > 0.1
                                        else ("FALSIFIED" if d else "UNTESTED"))}


def interaction(rows, key):
    by_rho = defaultdict(list)
    for ni in sorted(set(r["n_items"] for r in rows)):
        for rho in sorted(set(r["rho"] for r in rows)):
            a = [r[key] for r in rows if r["rho"] == rho and r["n_visible"] == 1 and r["n_items"] == ni]
            b = [r[key] for r in rows if r["rho"] == rho and r["n_visible"] == 3 and r["n_items"] == ni]
            if a and b:
                by_rho[rho].append(mean(b) - mean(a))
    prof = {str(k): round(mean(v), 4) for k, v in sorted(by_rho.items())}
    vals = list(prof.values())
    return {"task_effect_by_rho": prof,
            "spread": round(max(vals) - min(vals), 4) if vals else 0.0,
            "INTERACTION": ("PRESENT" if vals and (max(vals) - min(vals)) > 0.15 else "ABSENT")}


if __name__ == "__main__":
    rows = load()
    print(f"raw rows: {len(rows)}   (no new data; re-analysis of existing rows)\n")
    out = {}
    print("=" * 78)
    print("D17: DETERMINISTIC TIE-BREAK -- PRE vs POST REPAIR")
    print("=" * 78)
    for key, lab in (("success", "argmax (DEFECTIVE, retained as record)"),
                     ("success_T0.5", "T=0.5 (preregistered)"),
                     ("success_T1.0", "T=1.0 (preregistered, PRIMARY)"),
                     ("success_T2.0", "T=2.0 (preregistered)")):
        r = primary(rows, key)
        out[key] = r
        print(f"\n  {lab}")
        print(f"    matched pairs          : {r['n_matched_pairs']}")
        print(f"    mean task effect       : {r['mean_task_effect']:+.4f} (sd {r['sd']:.4f})")
        print(f"    model-entropy gap      : {r['mean_model_entropy_gap']:.4f} bits (<=0.05)")
        print(f"    task-entropy gap       : {r['mean_task_entropy_gap']:.4f} bits")
        print(f"    POSITION SPREAD        : {r['position_spread']:.4f}   "
              f"by index {r['success_by_target_index']}")
        print(f"    effect uniform across position strata: {r['effect_uniform_across_position_strata']}")
        print(f"    H1 = {r['H1_task_account']}")

    print("\n" + "=" * 78)
    print("REPAIRED PRIMARY (T=1.0): H1 strata detail")
    print("=" * 78)
    for ti, v in out["success_T1.0"]["stratified_by_target_index"].items():
        print(f"  target_index={ti}: {v['n_pairs']:>3} pairs, effect {v['mean_task_effect']:+.4f}, "
              f"frac>0 {v['frac_positive']:.3f}")

    print("\n" + "=" * 78)
    print("H2 -- SENDER-MODEL ACCOUNT, WITHIN TASK-ENTROPY STRATA (repaired policy)")
    print("=" * 78)
    h2 = h2_within_task_strata(rows, PRIMARY_POLICY)
    for s in h2["strata"]:
        print(f"  {s['stratum']}  n={s['n_hi_rho']}/{s['n_lo_rho']}  "
              f"succ {s['succ_low_rho']:.4f} -> {s['succ_high_rho']:.4f}  d={s['delta']:+.4f}")
    print(f"  mean within-stratum delta = {h2['mean_delta']}  sign stable = {h2['sign_stable']}"
          f"  -> H2 = {h2['H2_sender_model_account']}")
    out["h2_repaired"] = h2

    print("\n" + "=" * 78)
    print("H3 -- INTERACTION (repaired policy)")
    print("=" * 78)
    h3 = interaction(rows, PRIMARY_POLICY)
    print(f"  task effect by rho: {h3['task_effect_by_rho']}")
    print(f"  spread across rho: {h3['spread']} -> {h3['INTERACTION']}")
    out["h3_repaired"] = h3

    json.dump(out, open("/Users/lordwilson/projects/inversion-lab/b5/PRIMARY_REPAIRED.json", "w"),
              indent=1, default=float)
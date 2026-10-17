"""B5 STRATIFIED ANALYSIS (§18 stratification-first) -- H1 vs H2 vs H3 vs H4.

The gate established:
  * the TASK lever is CLEAN (moves task entropy, not model entropy)
  * the MODEL lever is INTRINSICALLY COUPLED to task entropy

Therefore:
  * H1 (task) is tested by MATCHED-MODEL contrasts: pick trials where model
    entropy is (near) identical but task entropy differs.
  * H2 (model) is tested WITHIN task-entropy strata, never marginally.
  * H3 is the interaction of the two within-cell slopes.
  * H4 is retained: any cell effect not explained by task or model state.

All statistics computed from RAW ROWS only (§34/§35).
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict

import numpy as np

RAW = "/Users/lordwilson/projects/inversion-lab/b5/MAIN_RAW_ROWS.json"


def load():
    return json.load(open(RAW))["rows"]


def mean(xs):
    return float(sum(xs) / len(xs))


# =====================================================================
# H1: TASK effect at MATCHED MODEL entropy
# =====================================================================
def h1_matched_model(rows, model_match_tol=0.05):
    """Pair trials with (near) identical model entropy but different task
    entropy. Model entropy is matched within (rho, n_items) then binned finely.
    """
    pairs = []
    for rho in sorted(set(r["rho"] for r in rows)):
        for ni in sorted(set(r["n_items"] for r in rows)):
            sub = [r for r in rows if r["rho"] == rho and r["n_items"] == ni]
            # bin model entropy finely
            mh = np.array([r["model_entropy_bits"] for r in sub])
            edges = np.quantile(mh, np.linspace(0, 1, 13))
            for lo, hi in zip(edges[:-1], edges[1:]):
                band = [r for r, m in zip(sub, mh) if lo <= m < hi]
                v1 = [r for r in band if r["n_visible"] == 1]   # high task unc
                v3 = [r for r in band if r["n_visible"] == 3]   # low task unc
                if len(v1) < 5 or len(v3) < 5:
                    continue
                dme = abs(mean([r["model_entropy_bits"] for r in v1]) -
                          mean([r["model_entropy_bits"] for r in v3]))
                if dme > model_match_tol:
                    continue
                pairs.append({
                    "rho": rho, "n_items": ni,
                    "n1": len(v1), "n3": len(v3),
                    "model_entropy_1": round(mean([r["model_entropy_bits"] for r in v1]), 4),
                    "model_entropy_3": round(mean([r["model_entropy_bits"] for r in v3]), 4),
                    "model_entropy_gap": round(dme, 4),
                    "task_entropy_1": round(mean([r["task_entropy_bits"] for r in v1]), 4),
                    "task_entropy_3": round(mean([r["task_entropy_bits"] for r in v3]), 4),
                    "success_1": mean([r["success"] for r in v1]),
                    "success_3": mean([r["success"] for r in v3]),
                    "delta_success": mean([r["success"] for r in v3]) - mean([r["success"] for r in v1]),
                })
    deltas = [p["delta_success"] for p in pairs]
    pos = sum(1 for d in deltas if d > 0)
    return {
        "n_matched_pairs": len(pairs),
        "mean_delta_success": round(mean(deltas), 4) if deltas else None,
        "sd_delta_success": round(float(np.std(deltas)), 4) if deltas else None,
        "frac_pairs_favouring_lower_task_uncertainty": round(pos / len(deltas), 4) if deltas else None,
        "sign_stable": bool(deltas and (all(d > 0 for d in deltas) or
                                        all(d < 0 for d in deltas))),
        "mean_task_entropy_gap": round(mean([abs(p["task_entropy_1"] - p["task_entropy_3"])
                                             for p in pairs]), 4) if pairs else None,
        "mean_model_entropy_gap": round(mean([p["model_entropy_gap"] for p in pairs]), 4) if pairs else None,
        "pairs": pairs[:20],
        "H1_task_account": ("SUPPORTED" if deltas and pos / len(deltas) > 0.8
                            else ("FALSIFIED" if deltas else "UNTESTED")),
    }


# =====================================================================
# H2: MODEL effect WITHIN task-entropy strata
# =====================================================================
def h2_within_task_strata(rows, n_strata=4):
    """Stratify by task entropy (quantiles), then compare across rho."""
    th = np.array([r["task_entropy_bits"] for r in rows])
    qs = np.quantile(th, np.linspace(0, 1, n_strata + 1))
    strata = []
    for i in range(n_strata):
        lo, hi = qs[i], qs[i + 1]
        band = [r for r, t in zip(rows, th) if lo <= t < hi]
        by_rho = {}
        for rho in sorted(set(r["rho"] for r in rows)):
            g = [r for r in band if r["rho"] == rho]
            if g:
                by_rho[rho] = {
                    "n": len(g),
                    "success": mean([r["success"] for r in g]),
                    "model_entropy_bits": mean([r["model_entropy_bits"] for r in g]),
                    "task_entropy_bits": mean([r["task_entropy_bits"] for r in g]),
                    "model_recovery": mean([r["model_recovery"] for r in g]),
                }
        if len(by_rho) < 2:
            continue
        hi_rho = max(by_rho)
        lo_rho = min(by_rho)
        strata.append({
            "stratum": f"taskH[{lo:.3f},{hi:.3f})",
            "by_rho": {str(k): {kk: (round(v, 4) if isinstance(v, float) else v)
                                for kk, v in vv.items()} for k, vv in by_rho.items()},
            "delta_success_high_minus_low_rho": round(by_rho[hi_rho]["success"] -
                                                      by_rho[lo_rho]["success"], 4),
            "model_entropy_gap": round(by_rho[lo_rho]["model_entropy_bits"] -
                                       by_rho[hi_rho]["model_entropy_bits"], 4),
            "task_entropy_gap": round(by_rho[hi_rho]["task_entropy_bits"] -
                                      by_rho[lo_rho]["task_entropy_bits"], 4),
        })
    deltas = [s["delta_success_high_minus_low_rho"] for s in strata]
    return {
        "n_strata": len(strata),
        "strata": strata,
        "mean_delta_within_task_stratum": round(mean(deltas), 4) if deltas else None,
        "sign_stable": bool(deltas and (all(d > 0 for d in deltas) or
                                        all(d < 0 for d in deltas))),
        "H2_sender_model_account": ("SUPPORTED" if deltas and mean(deltas) > 0.1
                                    else ("FALSIFIED" if deltas else "UNTESTED")),
    }


# =====================================================================
# H3 interaction: do the two factors' effects multiply?
# =====================================================================
def h3_interaction(rows):
    """2x2 at matched n_items: does the task effect depend on rho?"""
    out = []
    for ni in sorted(set(r["n_items"] for r in rows)):
        for rho in sorted(set(r["rho"] for r in rows)):
            a = [r for r in rows if r["rho"] == rho and r["n_visible"] == 1 and r["n_items"] == ni]
            b = [r for r in rows if r["rho"] == rho and r["n_visible"] == 3 and r["n_items"] == ni]
            if len(a) < 5 or len(b) < 5:
                continue
            out.append({"n_items": ni, "rho": rho,
                        "success_nvis1": round(mean([r["success"] for r in a]), 4),
                        "success_nvis3": round(mean([r["success"] for r in b]), 4),
                        "task_effect": round(mean([r["success"] for r in b]) -
                                             mean([r["success"] for r in a]), 4)})
    # does task_effect vary with rho?
    by_rho = defaultdict(list)
    for o in out:
        by_rho[o["rho"]].append(o["task_effect"])
    prof = {str(k): round(mean(v), 4) for k, v in sorted(by_rho.items())}
    vals = list(prof.values())
    spread = max(vals) - min(vals) if vals else 0.0
    return {
        "task_effect_by_rho": prof,
        "task_effect_spread_across_rho": round(spread, 4),
        "INTERACTION": ("PRESENT" if spread > 0.15 else "ABSENT"),
        "detail": out,
    }


# =====================================================================
# H4: is anything else driving success?
# =====================================================================
def h4_alternative_variables(rows):
    """Regress-style check: within (rho, n_items, n_visible) cells, does any
    other recorded variable predict success after task/model state?"""
    cells = defaultdict(list)
    for r in rows:
        cells[(r["rho"], r["n_items"], r["n_visible"])].append(r)
    cands = ["target_index", "task_p_max", "task_support", "model_concentration",
             "model_p_true", "task_p_correct"]
    out = {}
    for c in cands:
        xs, ys = [], []
        for cell, rs in cells.items():
            if len(rs) < 20:
                continue
            x = np.array([r[c] for r in rs], float)
            y = np.array([r["success"] for r in rs], float)
            if x.std() == 0 or y.std() == 0:
                continue
            # partial correlation: residualise both on cell means
            xr = x - x.mean()
            yr = y - y.mean()
            xs.append(xr)
            ys.append(yr)
        if xs:
            X, Y = np.concatenate(xs), np.concatenate(ys)
            out[c] = round(float(np.corrcoef(X, Y)[0, 1]), 4)
    return {"within_cell_partial_correlations": out,
            "note": "task_p_max is expected to correlate; it is the decision variable."}


# =====================================================================
# persistence, calibration, policy sensitivity
# =====================================================================
def persistence_and_policy(rows):
    stages = {}
    for st in ("success", "success_novel_scene", "success_novel_target"):
        if st in rows[0]:
            stages[st] = {"n": len(rows),
                          "mean": round(mean([r[st] for r in rows]), 4)}
    pol = {"policy_proportional": round(mean([r["success"] for r in rows]), 4)}
    for T in (0.5, 1.0, 2.0):
        pol[f"temperature_{T}"] = round(mean([r[f"success_T{T}"] for r in rows]), 4)
    wrong = [r for r in rows if r["success"] == 0]
    cal = {
        "mean_p_max_correct": round(mean([r["task_p_max"] for r in rows if r["success"] == 1]), 4),
        "mean_p_max_wrong": round(mean([r["task_p_max"] for r in wrong]), 4),
        "n_errors": len(wrong),
        "confident_errors_pmax_gt_0.9": sum(1 for r in wrong if r["task_p_max"] > 0.9),
        "mean_brier": round(mean([r["brier"] for r in rows]), 4),
    }
    return {"persistence": stages, "decision_policy": pol, "calibration": cal}


if __name__ == "__main__":
    rows = load()
    print(f"raw rows: {len(rows)}\n")
    h1 = h1_matched_model(rows)
    h2 = h2_within_task_strata(rows)
    h3 = h3_interaction(rows)
    h4 = h4_alternative_variables(rows)
    pp = persistence_and_policy(rows)

    print("=" * 78)
    print("H1 -- TASK ACCOUNT, at MATCHED MODEL ENTROPY (clean task lever)")
    print("=" * 78)
    print(f"  matched pairs: {h1['n_matched_pairs']}")
    print(f"  mean task-entropy gap: {h1['mean_task_entropy_gap']} bits")
    print(f"  mean model-entropy gap: {h1['mean_model_entropy_gap']} bits  (tolerance 0.05)")
    print(f"  mean delta success: {h1['mean_delta_success']}  sd {h1['sd_delta_success']}")
    print(f"  frac pairs favouring lower task uncertainty: {h1['frac_pairs_favouring_lower_task_uncertainty']}")
    print(f"  sign stable: {h1['sign_stable']}   -> H1 = {h1['H1_task_account']}")
    print("  sample pairs:")
    for p in h1["pairs"][:8]:
        print(f"    rho={p['rho']:.2f} items={p['n_items']}: modelH {p['model_entropy_1']:.4f}/"
              f"{p['model_entropy_3']:.4f} (gap {p['model_entropy_gap']:.4f})  taskH "
              f"{p['task_entropy_1']:.4f}/{p['task_entropy_3']:.4f}  succ "
              f"{p['success_1']:.4f} -> {p['success_3']:.4f}  d={p['delta_success']:+.4f}")

    print("\n" + "=" * 78)
    print("H2 -- SENDER-MODEL ACCOUNT, WITHIN TASK-ENTROPY STRATA")
    print("=" * 78)
    for s in h2["strata"]:
        print(f"  {s['stratum']}  d_success(high-low rho)={s['delta_success_high_minus_low_rho']:+.4f}"
              f"  modelH gap={s['model_entropy_gap']:.4f}  taskH gap={s['task_entropy_gap']:.4f}")
    print(f"  mean within-stratum delta: {h2['mean_delta_within_task_stratum']}  "
          f"sign stable: {h2['sign_stable']}  -> H2 = {h2['H2_sender_model_account']}")

    print("\n" + "=" * 78)
    print("H3 -- INTERACTION")
    print("=" * 78)
    print(f"  task effect by rho: {h3['task_effect_by_rho']}")
    print(f"  spread across rho: {h3['task_effect_spread_across_rho']} -> {h3['INTERACTION']}")

    print("\n" + "=" * 78)
    print("H4 -- ALTERNATIVE VARIABLES (within-cell partial correlations)")
    print("=" * 78)
    for k, v in h4["within_cell_partial_correlations"].items():
        print(f"  {k:>22}: r = {v:+.4f}")

    print("\n" + "=" * 78)
    print("PERSISTENCE / POLICY / CALIBRATION")
    print("=" * 78)
    for k, v in pp["persistence"].items():
        print(f"  {k:>22}: {v['mean']:.4f}")
    for k, v in pp["decision_policy"].items():
        print(f"  {k:>22}: {v:.4f}")
    for k, v in pp["calibration"].items():
        print(f"  {k:>22}: {v}")

    json.dump({"h1": h1, "h2": h2, "h3": h3, "h4": h4, "persistence_policy_calibration": pp},
              open("/Users/lordwilson/projects/inversion-lab/b5/ANALYSIS.json", "w"),
              indent=1, default=float)
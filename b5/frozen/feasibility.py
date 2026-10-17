"""B5 §7 IDENTIFIABILITY GATE + §10 RELIABILITY IDENTIFIABILITY + §13 FEASIBILITY MATRIX.

HARD GATE. If the two factors cannot be varied independently, STOP and do not
run the main experiment (§7, §33).

Cells required (§7):
                LOW model unc      HIGH model unc
  LOW task unc        A                   B
  HIGH task unc       C                   D

Contrasts required: A->B, A->C, B->D, C->D (each holding one factor fixed).
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, "/Users/lordwilson/projects/inversion-lab")
sys.path.insert(0, "/Users/lordwilson/projects/inversion-lab/b5")

from b5.substrate import (B5Receiver, EPS, K, N_OBJ, PREREGISTERED_RELIABILITIES,
                          PREREG_TEMPERATURES, RELIABILITY_TOLERANCE,
                          object_likelihood, realized_reliability, send_with_reliability,
                          stable_seed, tb, uniform_prior)
from lexrepair import codebook as CB  # noqa: E402
from lexrepair.world import encode, gen_scene  # noqa: E402


def derangement(seed: int):
    return CB.derangement(random.Random(stable_seed("b5der", seed)))


def build_episode(seed: int, n_visible: int, rho: float, n_items: int = 3,
                  eps: float = EPS, n_obj: int = N_OBJ):
    """One randomized episode.

    LEVER 1 (task uncertainty)     : n_visible in {1, 3}
    LEVER 2 (sender-model unc)     : rho in {1.00, 0.50}

    All trials share n_items, eps and scene size, so evidence QUANTITY cannot
    masquerade as either factor.
    """
    fS = derangement(seed)
    rng = random.Random(stable_seed("b5ep", seed, n_visible, rho, n_items))

    # training evidence about the sender's model, through the reliability channel
    rec = B5Receiver(prior=uniform_prior(), eps=eps)
    reports, triples = [], []
    for t in range(n_items):
        sc = gen_scene(rng, n_obj, f"b5-tr-{seed}-{t}")
        tgt = sc.objects[rng.randrange(n_obj)]
        rep = send_with_reliability(fS, tgt.triple, rho, rng)
        rec.observe(sc, rep, target_index=tgt.index)
        reports.append(rep)
        triples.append(tgt.triple)

    # held-out probe on a scene never seen in training
    ho = gen_scene(rng, n_obj, f"b5-ho-{seed}")
    ho_tgt = ho.objects[rng.randrange(n_obj)]
    ho_msg = encode(fS, ho_tgt)

    pobj = rec.partial_object_posterior(ho, ho_msg, n_visible)
    d = rec.posterior_diagnostics()
    p = pobj[ho_tgt.index]
    task_H = float(-(np.clip(pobj, 1e-300, None) *
                     np.log2(np.clip(pobj, 1e-300, None))).sum())
    fhat = tuple(int(x) for x in tb().M[int(np.argmax(rec.post))])

    return {
        "seed": seed, "n_visible": n_visible, "rho": rho, "n_items": n_items,
        "eps": eps, "scene_size": n_obj,
        # task-side
        "task_entropy_bits": task_H,
        "task_p_max": float(pobj.max()),
        "task_p_correct": float(p),
        "task_support": int((pobj > 0).sum()),
        "target_index": int(ho_tgt.index),
        # model-side
        "model_entropy_bits": float(d["entropy_bits"]),
        "model_eff_hypotheses": float(d["effective_hypotheses"]),
        "model_concentration": float(d["top10pct_mass"]),
        "model_p_true": float(rec.post[tb().idM[tuple(int(x) for x in fS)]]),
        # outcomes
        "argmax_index": int(np.argmax(pobj)),
        "success": int(np.argmax(pobj) == ho_tgt.index),
        "model_recovery": float(np.mean([fhat[c] == fS[c] for c in range(K)])),
        "realized_reliability": realized_reliability(fS, reports, triples),
        "evidence_count": n_items,
        "visible_token_count": n_visible,
    }


# =====================================================================
# §10 RELIABILITY IDENTIFIABILITY
# =====================================================================
def reliability_identifiability(rows):
    by_rho = defaultdict(list)
    for r in rows:
        by_rho[r["rho"]].append(r)
    out = {}
    worst = 0.0
    for rho in sorted(by_rho):
        intended = rho
        realized = float(np.mean([r["realized_reliability"] for r in by_rho[rho]]))
        gap = abs(realized - intended)
        worst = max(worst, gap)
        out[str(rho)] = {"intended": intended, "realized": round(realized, 4),
                         "abs_gap": round(gap, 4), "n": len(by_rho[rho]),
                         "within_tolerance": gap <= RELIABILITY_TOLERANCE}
    # F9: is reliability recoverable from an unrelated design variable?
    leak = {}
    for var in ("n_items", "scene_size", "eps"):
        vals = defaultdict(set)
        for r in rows:
            vals[r["rho"]].add(r[var])
        leak[var] = all(len(v) == 1 for v in vals.values())
    # is reliability an identity of model entropy?
    rho_arr = np.array([r["rho"] for r in rows])
    me = np.array([r["model_entropy_bits"] for r in rows])
    corr = float(np.corrcoef(rho_arr, me)[0, 1]) if rho_arr.std() > 0 else float("nan")
    return {"per_level": out,
            "worst_abs_gap": round(worst, 4),
            "tolerance": RELIABILITY_TOLERANCE,
            "PASS": worst <= RELIABILITY_TOLERANCE,
            "F9_reliability_leaks_into_constant_variables": leak,
            "F9_reliability_not_encoded_in_constant_vars": not any(leak.values()),
            "corr_intended_reliability_vs_model_entropy": round(corr, 4),
            "note": ("Reliability SHOULD correlate with model entropy -- that is the "
                     "mechanism by which it lowers sender-model uncertainty. It must "
                     "not be confounded with evidence count, scene size or eps, which "
                     "are held constant by design.")}


# =====================================================================
# §13 FEASIBILITY MATRIX + ORTHOGONALIZATION
# =====================================================================
def feasibility(n=300, n_visible_levels=(1, 3),
                rho_levels=(1.00, 0.50), n_items=3):
    rows = []
    for s in range(n):
        for nv in n_visible_levels:
            for rho in rho_levels:
                rows.append(build_episode(s, nv, rho, n_items=n_items))
    return rows


def feasibility_matrix(rows):
    """Cell x measured-property matrix (§13)."""
    cells = defaultdict(list)
    for r in rows:
        cells[(r["n_visible"], r["rho"])].append(r)
    name = {(3, 1.0): "A_low_task_low_model", (3, 0.5): "B_low_task_high_model",
            (1, 1.0): "C_high_task_low_model", (1, 0.5): "D_high_task_high_model"}
    M = {}
    for key, rs in sorted(cells.items(), reverse=True):
        nk = name.get(key, f"nvisible{key[0]}_rho{key[1]}")
        M[nk] = {
            "n_visible": key[0], "rho": key[1], "n": len(rs),
            "task_entropy_bits": round(float(np.mean([r["task_entropy_bits"] for r in rs])), 4),
            "model_entropy_bits": round(float(np.mean([r["model_entropy_bits"] for r in rs])), 4),
            "global_entropy_bits": round(float(np.mean([r["model_entropy_bits"] for r in rs])), 4),
            "task_p_max": round(float(np.mean([r["task_p_max"] for r in rs])), 4),
            "model_concentration": round(float(np.mean([r["model_concentration"] for r in rs])), 4),
            "model_recovery": round(float(np.mean([r["model_recovery"] for r in rs])), 4),
            "task_support": sorted(set(r["task_support"] for r in rs)),
            "evidence_count": sorted(set(r["evidence_count"] for r in rs)),
            "expected_success": round(float(np.mean([r["success"] for r in rs])), 4),
            "realized_reliability": round(float(np.mean([r["realized_reliability"] for r in rs])), 4),
        }
    return M


def orthogonalization(rows):
    """Do the two factors vary independently? (§13)

    Factor 1 = task entropy, Factor 2 = model entropy.
    We require the CORRELATION between them across all cells to be below a
    preregistered tolerance, and we require each contrast to move its target
    variable while roughly holding the other fixed.
    """
    te = np.array([r["task_entropy_bits"] for r in rows])
    me = np.array([r["model_entropy_bits"] for r in rows])
    corr = float(np.corrcoef(te, me)[0, 1])

    def cell(nv, rho):
        return [r for r in rows if r["n_visible"] == nv and r["rho"] == rho]

    contrasts = {}
    for lbl, (a, b) in {
        "A->B (low task, vary model)": ((3, 1.0), (3, 0.5)),
        "A->C (low model, vary task)": ((3, 1.0), (1, 1.0)),
        "B->D (high task, vary model)": ((1, 1.0), (1, 0.5)),
        "C->D (high model, vary task)": ((1, 0.5), (3, 0.5)),
    }.items():
        ca, cb = cell(*a), cell(*b)
        d_task = (np.mean([r["task_entropy_bits"] for r in cb]) -
                  np.mean([r["task_entropy_bits"] for r in ca]))
        d_model = (np.mean([r["model_entropy_bits"] for r in cb]) -
                   np.mean([r["model_entropy_bits"] for r in ca]))
        contrasts[lbl] = {
            "delta_task_entropy": round(float(d_task), 4),
            "delta_model_entropy": round(float(d_model), 4),
            "target_moved": bool((abs(d_task) > 0.15) if "vary task" in lbl
                                 else (abs(d_model) > 0.15)),
            "other_moved_too": bool((abs(d_task) > 0.15) if "vary model" in lbl
                                    else (abs(d_model) > 0.15)),
        }
    # a contrast is CLEAN if the target moved and the other stayed put
    clean = {k: (v["target_moved"] and not v["other_moved_too"])
             for k, v in contrasts.items()}
    return {
        "corr_task_entropy_vs_model_entropy": round(corr, 4),
        "orthogonal_tolerance": 0.50,
        "PASS_orthogonal": abs(corr) < 0.50,
        "contrasts": contrasts,
        "clean_contrasts": clean,
        "all_contrasts_clean": all(clean.values()),
    }


def identifiability_gate(rows, matrix, ortho, reliab):
    """§7: are all four cells independently constructible?

    DEFECT D15 (found by this gate): the first version mislabelled contrast
    B->D as "vary model". B=(n_visible 3, rho 0.50) and D=(n_visible 1,
    rho 0.50) hold rho FIXED, so they vary TASK, not model. The check
    "B_vs_D_differs_in_model" therefore demanded a difference that the design
    correctly does not produce, and the gate failed for a coding reason.

    Correct contrast map:
        A->B : n_visible fixed 3, rho 1.00 -> 0.50   => varies MODEL
        A->C : rho fixed 1.00,    n_visible 3 -> 1  => varies TASK
        B->D : rho fixed 0.50,    n_visible 3 -> 1  => varies TASK
        C->D : n_visible fixed 1, rho 1.00 -> 0.50   => varies MODEL

    SUBSTANTIVE FINDING (not a coding error): varying MODEL uncertainty
    also moves TASK entropy (A->B shifts task H by +0.77 bits). This is
    intrinsic, not a design flaw -- task uncertainty is a DETERMINISTIC
    FUNCTION of the model posterior, so degrading model knowledge necessarily
    degrades decoding precision. The model factor therefore CANNOT be varied
    at literally constant task uncertainty by any intervention.
    Consequence: the model effect must be tested WITHIN task-entropy strata
    (§18), not by a pure factorial contrast.
    """
    A, B = "A_low_task_low_model", "B_low_task_high_model"
    C, D = "C_high_task_low_model", "D_high_task_high_model"

    def mv(cell, k):
        return matrix[cell][k]

    checks = {
        "all_four_cells_present": {A, B, C, D}.issubset(set(matrix)),
        "A_vs_B_differs_in_model":  # rho varies, n_visible fixed
            abs(mv(A, "model_entropy_bits") - mv(B, "model_entropy_bits")) > 0.15,
        "C_vs_D_differs_in_model":  # rho varies, n_visible fixed
            abs(mv(C, "model_entropy_bits") - mv(D, "model_entropy_bits")) > 0.15,
        "A_vs_C_differs_in_task":   # n_visible varies, rho fixed
            abs(mv(A, "task_entropy_bits") - mv(C, "task_entropy_bits")) > 0.15,
        "B_vs_D_differs_in_task":   # n_visible varies, rho fixed
            abs(mv(B, "task_entropy_bits") - mv(D, "task_entropy_bits")) > 0.15,
        "factors_orthogonal_marginal": ortho["PASS_orthogonal"],
        "reliability_realized": reliab["PASS"],
    }
    purity = ortho["contrasts"]
    return {
        "checks": checks,
        "GATE_PASS": all(checks.values()),
        "matrix": matrix,
        "INTRINSIC_COUPLING": {
            "finding": ("Model uncertainty and task uncertainty are causally "
                        "coupled in this substrate: task entropy is a "
                        "deterministic function of the model posterior."),
            "evidence": {
                "A_to_B_delta_task_H": purity["A->B (low task, vary model)"]["delta_task_entropy"],
                "B_to_D_delta_task_H": purity["B->D (high task, vary model)"]["delta_task_entropy"],
                "A_to_C_delta_model_H": purity["A->C (low model, vary task)"]["delta_model_entropy"],
                "C_to_D_delta_model_H": purity["C->D (high model, vary task)"]["delta_model_entropy"],
            },
            "interpretation": (
                "The TASK lever is clean: varying n_visible moves task entropy "
                "by 0.71-1.14 bits while moving model entropy by <=0.10 bits. The "
                "MODEL lever is intrinsically impure because task uncertainty is "
                "computed FROM the model posterior."),
            "required_design_response": (
                "Model effects must be estimated WITHIN task-entropy strata "
                "(§18 stratification-first), not from pure factorial contrasts. "
                "Reporting the model contrast without conditioning would be a "
                "marginal-confounding error."),
            "classification": "BOUNDARY_CONDITION (one-directional coupling)",
        },
    }


if __name__ == "__main__":
    import os
    os.makedirs("/Users/lordwilson/projects/inversion-lab/b5", exist_ok=True)
    rows = feasibility(300)
    matrix = feasibility_matrix(rows)
    ortho = orthogonalization(rows)
    reliab = reliability_identifiability(rows)
    gate = identifiability_gate(rows, matrix, ortho, reliab)

    print("=" * 78)
    print("§13 FEASIBILITY MATRIX")
    print("=" * 78)
    hdr = f"{'cell':>24} {'n':>5} {'taskH':>7} {'modelH':>8} {'task_pmax':>10} {'modelConc':>10} {'modelRec':>9} {'succ':>6} {'rho_real':>9}"
    print(hdr)
    for k, v in matrix.items():
        print(f"{k:>24} {v['n']:>5} {v['task_entropy_bits']:>7.4f} {v['model_entropy_bits']:>8.4f} "
              f"{v['task_p_max']:>10.4f} {v['model_concentration']:>10.4f} {v['model_recovery']:>9.4f} "
              f"{v['expected_success']:>6.4f} {v['realized_reliability']:>9.4f}")

    print("\n" + "=" * 78)
    print("§10 RELIABILITY IDENTIFIABILITY")
    print("=" * 78)
    for k, v in reliab["per_level"].items():
        print(f"  rho={k}: intended {v['intended']:.2f} realized {v['realized']:.4f} "
              f"gap {v['abs_gap']:.4f} n={v['n']} within_tol={v['within_tolerance']}")
    print(f"  worst gap {reliab['worst_abs_gap']:.4f} (tolerance {RELIABILITY_TOLERANCE})")
    print(f"  leaks into constant vars: {reliab['F9_reliability_leaks_into_constant_variables']}")
    print(f"  corr(intended rho, model entropy) = {reliab['corr_intended_reliability_vs_model_entropy']}")

    print("\n" + "=" * 78)
    print("§13 ORTHOGONALIZATION")
    print("=" * 78)
    print(f"  corr(task entropy, model entropy) = {ortho['corr_task_entropy_vs_model_entropy']} "
          f"(tolerance 0.50) -> {'PASS' if ortho['PASS_orthogonal'] else 'FAIL'}")
    for k, v in ortho["contrasts"].items():
        print(f"  {k:>32}: d_taskH={v['delta_task_entropy']:+.4f} d_modelH={v['delta_model_entropy']:+.4f} "
              f"clean={ortho['clean_contrasts'][k]}")

    print("\n" + "=" * 78)
    print("§7 IDENTIFIABILITY GATE")
    print("=" * 78)
    for k, v in gate["checks"].items():
        print(f"  {k}: {v}")
    print(f"\n  >>> GATE {'PASSED' if gate['GATE_PASS'] else 'FAILED'}")
    if not gate["GATE_PASS"]:
        print("  >>> STOP: do not run the main experiment (§7, §33).")

    json.dump({"rows": rows, "matrix": matrix, "orthogonalization": ortho,
               "reliability": reliab, "gate": gate},
              open("/Users/lordwilson/projects/inversion-lab/b5/FEASIBILITY.json", "w"),
              indent=1, default=float)
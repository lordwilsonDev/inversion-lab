"""B4 SATURATION SWEEP -- where does posterior structure actually drive behaviour?

Motivation (defect D11): in E1 the posterior SATURATES at 4 evidence items for
both preregistered noise levels (top-10% mass = 1.000, codebook entropy 1.48
bits). A saturated posterior behaves like a near-elimination rule and could
re-create the OLD substrate's degeneracy under a new name. Before any theory
claim, locate the regime where the graded posterior is genuinely GRADED.

This sweep is an ADVERSARIAL CHECK on B4 itself: if success is flat across
posterior concentrations within a support-constant substrate, then B4 has
reproduced the old degeneracy and no theory experiment should proceed.

STRATIFIED BY POSTERIOR CONCENTRATION (§11/§12) -- not by marginal means.
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, "/Users/lordwilson/projects/inversion-lab")
sys.path.insert(0, "/Users/lordwilson/projects/inversion-lab/b4")

from b4.substrate import (B4Receiver, K, PRIOREG_TEMPERATURES, object_likelihood,  # noqa
                          stable_seed, tb, uniform_prior)
from b4.experiments import PRIOREG_EPS, derangement  # noqa
from lexrepair.world import encode, gen_scene  # noqa

ITEM_COUNTS = (1, 2, 3, 4, 6, 8)
N_OBJ = 5


def sweep(n: int = 400, eps_levels=PRIOREG_EPS, item_counts=ITEM_COUNTS):
    rows = []
    for s in range(n):
        fS = derangement(s)
        eps = eps_levels[s % len(eps_levels)]
        rng = random.Random(stable_seed("b4sweep", s))
        rec = B4Receiver(prior=uniform_prior(), eps=eps)
        train = []
        for t in range(max(item_counts)):
            sc = gen_scene(rng, N_OBJ, f"b4sw-{s}-{t}")
            tg = sc.objects[rng.randrange(N_OBJ)]
            msg = encode(fS, tg)
            rec.observe(sc, msg, target_index=tg.index)
            train.append((sc, tg, msg))

        # ONE held-out probe, evaluated at each prefix length
        ho = gen_scene(rng, N_OBJ, f"b4swho-{s}")
        ho_tgt = ho.objects[rng.randrange(N_OBJ)]
        ho_msg = encode(fS, ho_tgt)

        r2 = B4Receiver(prior=uniform_prior(), eps=eps)
        for ic in item_counts:
            for k in range(ic):
                sc, tg, msg = train[k]
                r2.observe(sc, msg, target_index=tg.index)
            pobj = r2.object_posterior(ho, ho_msg)
            d = r2.posterior_diagnostics()
            rows.append({
                "seed": s, "eps": eps, "n_items": ic,
                "support": int((pobj > 0).sum()),
                "cb_entropy_bits": d["entropy_bits"],
                "cb_concentration": d["top10pct_mass"],
                "eff_hypotheses": d["effective_hypotheses"],
                "obj_entropy_bits": float(-(np.clip(pobj, 1e-300, None) *
                                            np.log2(np.clip(pobj, 1e-300, None))).sum()),
                "p_max": float(pobj.max()),
                "p_correct": float(pobj[ho_tgt.index]),
                "success": int(np.argmax(pobj) == ho_tgt.index),
                "brier": float(sum((pobj[i] - (1.0 if i == ho_tgt.index else 0.0)) ** 2
                                    for i in range(len(pobj)))),
                "true_index": int(ho_tgt.index),
                "argmax_index": int(np.argmax(pobj)),
            })
    return rows


def analyse(rows):
    out = {"by_eps_items": {}, "saturation": {}, "stratified": {}}
    for eps in sorted(set(r["eps"] for r in rows)):
        out["by_eps_items"][str(eps)] = {}
        for ic in sorted(set(r["n_items"] for r in rows)):
            r = [x for x in rows if x["eps"] == eps and x["n_items"] == ic]
            out["by_eps_items"][str(eps)][str(ic)] = {
                "n": len(r),
                "success": float(np.mean([x["success"] for x in r])),
                "p_correct": float(np.mean([x["p_correct"] for x in r])),
                "p_max": float(np.mean([x["p_max"] for x in r])),
                "cb_entropy_bits": float(np.mean([x["cb_entropy_bits"] for x in r])),
                "cb_concentration": float(np.mean([x["cb_concentration"] for x in r])),
                "eff_hypotheses": float(np.mean([x["eff_hypotheses"] for x in r])),
                "brier": float(np.mean([x["brier"] for x in r])),
                "support": sorted(set(x["support"] for x in r)),
            }
    # saturation: where does top-10% mass reach ~1.0?
    for eps in sorted(set(r["eps"] for r in rows)):
        curve = out["by_eps_items"][str(eps)]
        sat = [ic for ic, v in curve.items() if v["cb_concentration"] > 0.999]
        out["saturation"][str(eps)] = {
            "saturated_item_counts": sorted(int(x) for x in sat),
            "first_saturated": min((int(x) for x in sat), default=None),
            "concentration_curve": {ic: round(v["cb_concentration"], 6)
                                    for ic, v in curve.items()},
        }

    # THE DECISIVE STRATIFICATION: does success track posterior concentration
    # while support is held constant?
    conc_bins = [(0.0, 0.3), (0.3, 0.6), (0.6, 0.9), (0.9, 0.999), (0.999, 1.01)]
    for lo, hi in conc_bins:
        sel = [x for x in rows if lo <= x["cb_concentration"] < hi]
        if not sel:
            continue
        out["stratified"][f"[{lo},{hi})"] = {
            "n": len(sel),
            "support_sizes": sorted(set(x["support"] for x in sel)),
            "success": float(np.mean([x["success"] for x in sel])),
            "p_correct": float(np.mean([x["p_correct"] for x in sel])),
            "cb_entropy_bits": float(np.mean([x["cb_entropy_bits"] for x in sel])),
            "eff_hypotheses": float(np.mean([x["eff_hypotheses"] for x in sel])),
            "mean_success_if_concentration_were_irrelevant": 0.2,
        }
    return out


def adversarial_b4_selfcheck(rows):
    """Would B4 reproduce the OLD degeneracy? Support is constant; if success is
    fully explained by something other than posterior structure, flag it."""
    sup = sorted(set(r["support"] for r in rows))
    # correlation between success-relevant variables and outcome
    conc = np.array([r["cb_concentration"] for r in rows])
    pm = np.array([r["p_max"] for r in rows])
    suc = np.array([r["success"] for r in rows], float)
    ent = np.array([r["cb_entropy_bits"] for r in rows])
    eff = np.array([r["eff_hypotheses"] for r in rows])

    def corr(a, b):
        if a.std() == 0 or b.std() == 0:
            return float("nan")
        return float(np.corrcoef(a, b)[0, 1])

    # Is p_max an identity of concentration or of entropy?
    ident = {}
    for name, v in (("cb_concentration", conc), ("cb_entropy_bits", ent),
                    ("eff_hypotheses", eff)):
        r = abs(corr(pm, v))
        ident[name] = {"corr_p_max": r,
                       "IS_IDENTITY": bool(r > 0.999)}
    return {
        "support_sizes_observed": sup,
        "support_constant": len(sup) == 1,
        "corr(p_max, success)": corr(pm, suc),
        "corr(concentration, success)": corr(conc, suc),
        "metric_identity_audit": ident,
        "B4_DEGENERACY_CHECK": (
            "B4 IS DEGENERATE: p_max is an identity of another variable, so "
            "posterior structure carries no information beyond it."
            if any(v["IS_IDENTITY"] for v in ident.values()) else
            "B4 IS NOT DEGENERATE: p_max is not an identity of any measured "
            "state variable."),
    }


if __name__ == "__main__":
    rows = sweep(400)
    a = analyse(rows)
    adv = adversarial_b4_selfcheck(rows)
    print("=== SATURATION CURVE (§7 / D11) ===")
    for eps, v in a["saturation"].items():
        print(f"  eps={eps}: first saturated at n_items={v['first_saturated']}")
        print(f"          concentration: {v['concentration_curve']}")
    print("\n=== SUCCESS / CONCENTRATION BY (eps, n_items) ===")
    print(f"{'eps':>5} {'items':>6} {'n':>5} {'success':>8} {'p_max':>7} {'cbH':>7} {'effH':>9} {'support':>8}")
    for eps, d in a["by_eps_items"].items():
        for ic, v in d.items():
            print(f"{eps:>5} {ic:>6} {v['n']:>5} {v['success']:>8.4f} {v['p_max']:>7.4f} "
                  f"{v['cb_entropy_bits']:>7.3f} {v['eff_hypotheses']:>9.1f} {str(v['support']):>8}")
    print("\n=== STRATIFIED BY POSTERIOR CONCENTRATION (support constant) ===")
    print(f"{'bin':>14} {'n':>6} {'support':>8} {'success':>8} {'p_corr':>8} {'cbH':>8} {'effH':>9}")
    for k, v in a["stratified"].items():
        print(f"{k:>14} {v['n']:>6} {str(v['support_sizes']):>8} {v['success']:>8.4f} "
              f"{v['p_correct']:>8.4f} {v['cb_entropy_bits']:>8.3f} {v['eff_hypotheses']:>9.1f}")
    print("\n=== ADVERSARIAL SELF-CHECK (§22 metric identity) ===")
    print(json.dumps(adv, indent=2, default=float))
    json.dump({"analysis": a, "adversarial": adv, "rows": rows},
              open("/Users/lordwilson/projects/inversion-lab/b4/SATURATION.json", "w"),
              indent=2, default=float)
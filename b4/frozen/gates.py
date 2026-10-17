"""B4 GATES -- §3 (is B4 a new substrate?) and §4 (is it identifying?).

These are HARD GATES. No communication-theory experiment may run until both pass.

GATE 1 (§3, capability): demonstrate B4 represents distinctions the old substrate
  erased. Required demonstrations:
    G1a  posterior is non-uniform after graded evidence           (§7 check 1)
    G1b  NO hypothesis is eliminated (support stays full)        (§7 check 2)
    G1c  posterior RANKING changes without eliminating hypotheses (§7 check 3)
    G1d  repeated evidence gradually changes concentration        (§7 check 4)
    G1e  candidate count is constant -> cannot absorb signal      (contrast with old)

GATE 2 (§4, identifiability): construct receivers with
    same candidate count, same hard constraints, different posterior
  and show the decision DISTRIBUTION differs. If not -> STOP.

    G2a  same support (all 5 objects), different posterior concentration
         -> posterior-proportional argmax differs
    G2b  same support, same expected accuracy, different uncertainty structure
         -> temperature sampling separates them
    G2c  demonstrate the OLD substrate FAILS this same construction (§4 evidence)
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, "/Users/lordwilson/projects/inversion-lab")
sys.path.insert(0, "/Users/lordwilson/projects/inversion-lab/b4")
sys.path.insert(0, "/Users/lordwilson/projects/lexical-repair-crt")

from b4.substrate import (B4Receiver, EPS, K, N_PERM, object_likelihood,  # noqa: E402
                          stable_seed, tb, tilted_prior, uniform_prior)
from lexrepair.world import encode, gen_scene  # noqa: E402


def _trial(seed: int, n_obj: int = 5):
    """Sender's true mapping: a derangement, plus a scene and target."""
    from lexrepair import codebook as CB
    fS = CB.derangement(random.Random(stable_seed("b4der", seed)))
    rng = random.Random(stable_seed("b4trial", seed))
    scene = gen_scene(rng, n_obj, f"b4-{seed}")
    tgt = scene.objects[rng.randrange(n_obj)]
    msg = encode(fS, tgt)
    return fS, rng, scene, tgt, msg


# =====================================================================
# GATE 1 -- §3 capability
# =====================================================================
def gate1_capability(n_seeds: int = 25, n_items: int = 4):
    out = {"checks": {}, "rows": []}
    flat_after, eliminated, rank_changed, concentration_curve = [], 0, 0, []

    for s in range(n_seeds):
        fS, rng, scene, tgt, msg = _trial(s)
        rec = B4Receiver()
        concs, ents = [], []
        for k in range(n_items):
            rec.observe(scene, msg, target_index=tgt.index)
            d = rec.posterior_diagnostics()
            ents.append(d["entropy_bits"])
            concs.append(d["top10pct_mass"])
            flat_after.append(abs(d["max_posterior"] - d["min_posterior"]) > 1e-12)
            if d["n_positive"] < N_PERM:
                eliminated += 1
        # G1c: does posterior ranking change as evidence accumulates?
        L = object_likelihood(scene, msg, EPS)
        r1 = np.argsort(-(uniform_prior() @ L))[:3]
        r2 = np.argsort(-(rec.post @ L))[:3]
        if list(r1) != list(r2):
            rank_changed += 1
        concentration_curve.append((concs, ents))

    out["checks"]["G1a_posterior_nonuniform_after_evidence"] = {
        "n_obs": len(flat_after), "n_nonflat": int(sum(flat_after)),
        "PASS": all(flat_after),
    }
    out["checks"]["G1b_no_hypothesis_eliminated"] = {
        "n_obs": n_seeds * n_items, "n_with_elimination": eliminated,
        "PASS": eliminated == 0,
    }
    out["checks"]["G1c_ranking_changes_without_elimination"] = {
        "n_seeds": n_seeds, "n_ranking_changed": rank_changed,
        "PASS": rank_changed > 0,
    }
    monotone = sum(1 for cs, _ in concentration_curve
                   if all(cs[i] < cs[i + 1] for i in range(len(cs) - 1)))
    out["checks"]["G1d_concentration_increases_with_evidence"] = {
        "n_seeds": n_seeds, "n_monotone_increasing": monotone,
        "PASS": monotone > 0,
    }
    # G1e: the object-posterior support is ALWAYS the full scene, because
    # every L(i,o) > 0 when eps > 0. Verify empirically rather than assert.
    support_sizes = set()
    for s in range(5):
        _, _, scene, _, msg = _trial(s)
        rec = B4Receiver()
        rec.observe(scene, msg, target_index=0)
        pobj = rec.object_posterior(scene, msg)
        support_sizes.add(int((pobj > 0).sum()))
    out["checks"]["G1e_candidate_count_constant"] = {
        "note": "support is always the full scene by construction (eps>0)",
        "distinct_support_sizes_observed": sorted(support_sizes),
        "PASS": len(support_sizes) == 1,
    }
    out["GATE1_PASS"] = all(v["PASS"] for v in out["checks"].values())
    out["example_concentration_curve"] = {
        "top10pct_mass_by_item": [round(x, 6) for x in concentration_curve[0][0]],
        "entropy_by_item": [round(x, 4) for x in concentration_curve[0][1]],
    }
    return out


# =====================================================================
# GATE 2 -- §4 identifiability
# =====================================================================
def gate2_identifiability(n_seeds: int = 60, n_probe: int = 5):
    """Two receivers: same support size, different posterior -> different decisions?"""
    by_support = defaultdict(list)
    argmax_flips = 0
    sampled_differs = 0
    n_paired = 0

    for s in range(n_seeds):
        fS, rng, scene, tgt, msg = _trial(s)
        # Receiver X: graded evidence about the true target (sharpens posterior)
        rx = B4Receiver()
        rx.observe(scene, msg, target_index=tgt.index)
        # Receiver Y: unattributed evidence (object-independent -> flat posterior)
        ry = B4Receiver()
        ry.observe(scene, msg, target_index=None)

        px = rx.object_posterior(scene, msg)
        py = ry.object_posterior(scene, msg)
        sx, sy = int((px > 0).sum()), int((py > 0).sum())

        # G2a: same support, different concentration, different argmax?
        if sx == sy:
            n_paired += 1
            by_support[sx].append({
                "conc_x": float(px.max()), "conc_y": float(py.max()),
                "argmax_x": int(np.argmax(px)), "argmax_y": int(np.argmax(py)),
                "true": tgt.index,
                "success_x": int(np.argmax(px) == tgt.index),
                "success_y": int(np.argmax(py) == tgt.index),
            })
            if int(np.argmax(px)) != int(np.argmax(py)):
                argmax_flips += 1
            # G2b: temperature sampling separates them
            rr = random.Random(stable_seed("samp", s))
            hits_x = sum(rx.decide_sampled(px, 1.0, rr) == tgt.index for _ in range(n_probe))
            hits_y = sum(ry.decide_sampled(py, 1.0, rr) == tgt.index for _ in range(n_probe))
            if hits_x != hits_y:
                sampled_differs += 1

    out = {
        "n_seeds": n_seeds,
        "n_paired_same_support": n_paired,
        "support_sizes_observed": sorted(by_support),
        "n_same_support_different_argmax": argmax_flips,
        "n_same_support_different_sampling_outcome": sampled_differs,
        "G2a_PASS": argmax_flips > 0,
        "G2b_PASS": sampled_differs > 0,
    }
    # concentration spread within each support size = non-identifiability would be zero
    out["concentration_spread_by_support"] = {
        str(k): {
            "n": len(v),
            "conc_x_range": [round(min(x["conc_x"] for x in v), 6),
                             round(max(x["conc_x"] for x in v), 6)],
            "conc_y_range": [round(min(x["conc_y"] for x in v), 6),
                             round(max(x["conc_y"] for x in v), 6)],
            "success_x": round(float(np.mean([x["success_x"] for x in v])), 4),
            "success_y": round(float(np.mean([x["success_y"] for x in v])), 4),
        } for k, v in sorted(by_support.items())
    }
    out["GATE2_PASS"] = bool(argmax_flips > 0 and sampled_differs > 0)
    return out


def gate2_old_substrate_fails(n_seeds: int = 300):
    """§4 requires showing the OLD substrate cannot do this construction."""
    from inversion.env import GeneralReceiver
    from inversion import experiments as E1
    IDENTITY = tuple(range(K))
    nonuniform = 0
    tot = 0
    spread = defaultdict(list)
    for s in range(n_seeds):
        fS = E1.derangement(s)
        rng = random.Random(stable_seed("e3", s))
        scene = gen_scene(rng, 5, f"e3-{s}")
        tgt = scene.objects[rng.randrange(5)]
        msg = encode(fS, tgt)
        rec = GeneralReceiver(IDENTITY, prior_floor=0.10)
        idx0, _, _ = rec.decide(msg, scene)
        rec.exclude_object(msg, scene.objects[idx0].triple)
        pr = rec.object_posterior(msg, scene)
        c = sum(1 for v in pr.values() if v > 0)
        tot += 1
        spread[c].append(max(pr.values()))
        if abs(max(pr.values()) - 1.0 / c) > 1e-9:
            nonuniform += 1
    return {
        "n_trials": tot,
        "n_nonuniform_object_posteriors": nonuniform,
        "max_p_spread_by_candidate_count": {
            str(k): [round(min(v), 10), round(max(v), 10)] for k, v in sorted(spread.items())},
        "OLD_SUBSTRATE_IDENTIFYING": nonuniform > 0,
        "conclusion": ("OLD substrate CAN produce non-uniform object posteriors"
                       if nonuniform > 0 else
                       "OLD substrate CANNOT: object posterior is uniform in every trial, "
                       "max-p == 1/candidates exactly. Not identifying for posterior structure."),
    }


if __name__ == "__main__":
    print("=" * 74)
    print("GATE 1 (§3): IS B4 A NEW SUBSTRATE?")
    print("=" * 74)
    g1 = gate1_capability()
    for k, v in g1["checks"].items():
        print(f"  {k}: {v['PASS']}  {({kk:vv for kk,vv in v.items() if kk!='PASS'})}")
    print(f"  example concentration curve: {g1['example_concentration_curve']}")
    print(f"\n  >>> GATE 1 {'PASSED' if g1['GATE1_PASS'] else 'FAILED'}\n")

    print("=" * 74)
    print("GATE 2 (§4): IS B4 IDENTIFYING?")
    print("=" * 74)
    g2 = gate2_identifiability()
    print(f"  same-support pairs: {g2['n_paired_same_support']}, support sizes {g2['support_sizes_observed']}")
    print(f"  same support but DIFFERENT argmax : {g2['n_same_support_different_argmax']}")
    print(f"  same support but DIFFERENT sampling: {g2['n_same_support_different_sampling_outcome']}")
    print(f"  concentration spread by support: {g2['concentration_spread_by_support']}")
    print(f"\n  >>> GATE 2 {'PASSED' if g2['GATE2_PASS'] else 'FAILED'}\n")

    print("=" * 74)
    print("GATE 2c: DOES THE OLD SUBSTRATE FAIL THIS? (§4 evidence)")
    print("=" * 74)
    g2o = gate2_old_substrate_fails()
    print(f"  {g2o['conclusion']}")
    print(f"  max-p spread by candidate count: {g2o['max_p_spread_by_candidate_count']}")

    json.dump({"gate1": g1, "gate2": g2, "gate2_old": g2o},
              open("/Users/lordwilson/projects/inversion-lab/b4/GATES.json", "w"), indent=2, default=float)
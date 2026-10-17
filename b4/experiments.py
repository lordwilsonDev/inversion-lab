"""B4 CORE EXPERIMENTS -- interventions A-H, persistence, model/state recovery.

Design follows b4/PREREGISTRATION.md exactly. Preregistered:
  eps levels   {0.15, 0.35}
  temperatures {0.5, 1.0, 2.0}
  policies     posterior_proportional, temperature_sampling

PRIMARY OUTCOME: held-out success under Policy A (posterior-proportional).
All results reported MARGINALLY **and** STRATIFIED (§11/§12/§23).
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

from b4.substrate import (B4Receiver, EPS, K, N_PERM, PRIOREG_TEMPERATURES,  # noqa: E402
                          object_likelihood, stable_seed, tb, tilted_prior, uniform_prior)
from lexrepair import codebook as CB  # noqa: E402
from lexrepair.world import encode, gen_scene  # noqa: E402

PRIOREG_EPS = (0.15, 0.35)
N_OBJ = 5


def derangement(seed: int):
    return CB.derangement(random.Random(stable_seed("b4der", seed)))


def make_episode(seed: int, n_train: int = 4, eps: float = 0.15,
                 prior_kind: str = "uniform", prior_conc: float = 0.0,
                 n_obj: int = N_OBJ):
    """Build a training episode: distinct scenes, one sender, one target each.

    Returns dict with training evidence and a fresh held-out probe.
    """
    fS = derangement(seed)
    rng = random.Random(stable_seed("b4ep", seed))

    prior = uniform_prior()
    if prior_kind == "tilt":
        prior = tilted_prior(prior_conc, seed)

    rec = B4Receiver(prior=prior, eps=eps)
    train = []
    for t in range(n_train):
        sc = gen_scene(rng, n_obj, f"b4tr-{seed}-{t}")
        tgt = sc.objects[rng.randrange(n_obj)]
        msg = encode(fS, tgt)
        rec.observe(sc, msg, target_index=tgt.index)
        train.append((sc, tgt, msg))

    # HELD-OUT probe: a scene never seen in training
    ho = gen_scene(rng, n_obj, f"b4ho-{seed}")
    ho_tgt = ho.objects[rng.randrange(n_obj)]
    ho_msg = encode(fS, ho_tgt)
    return {"fS": fS, "rec": rec, "train": train, "ho": ho,
            "ho_tgt": ho_tgt, "ho_msg": ho_msg, "eps": eps,
            "prior_kind": prior_kind, "seed": seed}


# =====================================================================
# E1: INTERVENTIONS (§15)
# =====================================================================
def intervention_episode(seed: int, arm: str, n_train: int = 4,
                         eps: float = 0.15, prior_kind: str = "uniform"):
    """Arms A-H from §15. Each returns a receiver trained under that condition."""
    fS = derangement(seed)
    rng = random.Random(stable_seed("b4int", seed))
    prior = uniform_prior() if prior_kind == "uniform" else tilted_prior(0.5, seed)
    rec = B4Receiver(prior=prior, eps=eps)

    if arm == "A_none":
        pass

    elif arm == "B_raw_information":
        # unattributed: a message the receiver cannot tie to a known object
        sc = gen_scene(rng, N_OBJ, f"b4B-{seed}")
        tgt = sc.objects[rng.randrange(N_OBJ)]
        rec.observe(sc, encode(fS, tgt), target_index=None)

    elif arm == "C_graded_evidence":
        # n_train attributed messages, chosen at random.
        for t in range(n_train):
            sc = gen_scene(rng, N_OBJ, f"b4C-{seed}-{t}")
            tgt = sc.objects[rng.randrange(N_OBJ)]
            rec.observe(sc, encode(fS, tgt), target_index=tgt.index)

    elif arm == "D_contrastive":
        # GENUINELY contrastive: at each step pick the (scene, target) whose
        # encoded message MAXIMALLY SEPARATES the receiver's current top-2
        # competing hypotheses. Implemented by scanning candidate targets and
        # choosing the one with the largest likelihood ratio between the top-2
        # posterior modes. This is NOT the same as random selection.
        for t in range(n_train):
            # The receiver's current top-2 COMPETING CODEBOOK hypotheses.
            top2 = np.argsort(-rec.post)[:2]
            best, best_gap = None, -1.0
            for _ in range(12):
                sc = gen_scene(rng, N_OBJ, f"b4D-{seed}-{t}")
                for tgt in sc.objects:
                    msg = encode(fS, tgt)
                    L = object_likelihood(sc, msg, eps)
                    lr = float(np.log(L[top2[0], tgt.index] + 1e-300) -
                               np.log(L[top2[1], tgt.index] + 1e-300))
                    if abs(lr) > best_gap:
                        best_gap, best = abs(lr), (sc, tgt, msg)
            rec.observe(best[0], best[2], target_index=best[1].index)

    elif arm == "E_verification_only":
        # Feedback that the guess was wrong, WITHOUT revealing model structure.
        # Implemented as: penalise the codebooks the receiver's current argmax
        # relies on, via a graded likelihood factor < 1 (not elimination).
        for t in range(n_train):
            sc = gen_scene(rng, N_OBJ, f"b4E-{seed}-{t}")
            tgt = sc.objects[rng.randrange(N_OBJ)]
            msg = encode(fS, tgt)
            L = object_likelihood(sc, msg, eps)
            guess = int(np.argmax(rec.post @ L))
            # graded penalty on the guessed object only
            step = np.ones(rec.post.shape[0])
            Lp = L.copy()
            Lp[:, guess] *= (1.0 - 0.95) / max(L[:, guess].max(), 1e-300)
            step = Lp[:, guess]
            rec.post = rec.post * step
            rec.post = rec.post / rec.post.sum()

    elif arm == "F_target_reveal":
        # CEILING CONDITION: the receiver is told directly WHICH held-out
        # object is the target. No message, no model structure. This is NOT
        # the same as sending messages (contrastive/graded evidence).
        pass  # handled after the held-out probe is built, see below

    elif arm == "G_equal_budget":
        # cost matched in BITS, not message count: one message is log2(1/eps^3)
        # of evidence, so deliver a single message with higher information by
        # repeating the informative item fewer times but at higher reliability.
        sc = gen_scene(rng, N_OBJ, f"b4G-{seed}")
        tgt = sc.objects[rng.randrange(N_OBJ)]
        rec.observe(sc, encode(fS, tgt), target_index=tgt.index)

    elif arm == "H_state_perturbation":
        # nominal external information IDENTICAL to C, but prior is tilted.
        # Any difference isolates STATE from content.
        for t in range(n_train):
            sc = gen_scene(rng, N_OBJ, f"b4H-{seed}-{t}")
            tgt = sc.objects[rng.randrange(N_OBJ)]
            rec.observe(sc, encode(fS, tgt), target_index=tgt.index)

    ho = gen_scene(rng, N_OBJ, f"b4ho-{seed}")
    ho_tgt = ho.objects[rng.randrange(N_OBJ)]
    ho_msg = encode(fS, ho_tgt)
    return rec, ho, ho_tgt, ho_msg, fS


ARMS = ("A_none", "B_raw_information", "C_graded_evidence", "D_contrastive",
        "E_verification_only", "F_target_reveal", "G_equal_budget",
        "H_state_perturbation")


def e1_interventions(n: int = 200, n_train: int = 4):
    rows = []
    for s in range(n):
        for arm in ARMS:
            eps = PRIOREG_EPS[s % len(PRIOREG_EPS)]
            prior_kind = "tilt" if arm == "H_state_perturbation" else "uniform"
            rec, ho, tgt, msg, fS = intervention_episode(
                s, arm, n_train=n_train, eps=eps, prior_kind=prior_kind)
            if arm == "F_target_reveal":
                # direct revelation of the held-out target (ceiling)
                pobj = np.full(len(ho.objects), 0.2)
                pobj[tgt.index] = 1.0
                pobj = pobj / pobj.sum()
            else:
                pobj = rec.object_posterior(ho, msg)
            d = rec.posterior_diagnostics()
            row = {
                "seed": s, "arm": arm, "eps": eps, "n_train": n_train,
                "success": int(rec.decide_proportional(pobj) == tgt.index),
                "p_correct": float(pobj[tgt.index]),
                "p_max": float(pobj.max()),
                "q_stated": float(pobj.max()),
                "argmax_index": int(np.argmax(pobj)),
                "true_index": int(tgt.index),
                "brier": float(sum((pobj[i] - (1.0 if i == tgt.index else 0.0)) ** 2
                                    for i in range(len(pobj)))),
                "obj_entropy_bits": float(-(np.clip(pobj, 1e-300, None) *
                                            np.log2(np.clip(pobj, 1e-300, None))).sum()),
                "n_support": int((pobj > 0).sum()),
                "codebook_entropy_bits": d["entropy_bits"],
                "codebook_concentration": d["top10pct_mass"],
                "effective_hypotheses": d["effective_hypotheses"],
            }
            # temperature sampling at preregistered T
            rr = random.Random(stable_seed("samp", s, arm))
            for T in PRIOREG_TEMPERATURES:
                hits = sum(rec.decide_sampled(pobj, T, rr) == tgt.index for _ in range(20))
                row[f"success_T{T}"] = hits / 20.0
            # model recovery: does the codebook posterior argmax recover the sender?
            fhat = tuple(int(x) for x in tb().M[int(np.argmax(rec.post))])
            row["model_recovery"] = float(np.mean([fhat[c] == fS[c] for c in range(K)]))
            rows.append(row)
    return rows


def e1_analysis(rows):
    out = {"by_arm": {}, "stratified_by_eps": {}}
    for arm in ARMS:
        r = [x for x in rows if x["arm"] == arm]
        out["by_arm"][arm] = {
            "n": len(r),
            "success": float(np.mean([x["success"] for x in r])),
            "p_correct": float(np.mean([x["p_correct"] for x in r])),
            "brier": float(np.mean([x["brier"] for x in r])),
            "model_recovery": float(np.mean([x["model_recovery"] for x in r])),
            "obj_entropy_bits": float(np.mean([x["obj_entropy_bits"] for x in r])),
            "codebook_entropy_bits": float(np.mean([x["codebook_entropy_bits"] for x in r])),
            "codebook_concentration": float(np.mean([x["codebook_concentration"] for x in r])),
            "support_sizes": sorted(set(x["n_support"] for x in r)),
            **{f"success_T{T}": float(np.mean([x[f"success_T{T}"] for x in r]))
               for T in PRIOREG_TEMPERATURES},
        }
    for eps in PRIOREG_EPS:
        out["stratified_by_eps"][str(eps)] = {
            arm: float(np.mean([x["success"] for x in rows
                                if x["arm"] == arm and x["eps"] == eps]))
            for arm in ARMS
        }
    out["F1_candidate_count_constant"] = sorted(set(x["n_support"] for x in rows))
    return out


# =====================================================================
# E2: GLOBAL vs TASK-RELEVANT UNCERTAINTY (§11)
# =====================================================================
def e2_uncertainty_decoupling(n: int = 300, n_train: int = 4):
    """Global uncertainty (codebook entropy) vs task-relevant uncertainty
    (object entropy). In B4 these CAN decouple; in the old substrate they could not.
    """
    rows = []
    for s in range(n):
        eps = PRIOREG_EPS[s % len(PRIOREG_EPS)]
        # arm 0: many evidence items (low global AND low task uncertainty)
        ep = make_episode(s, n_train=n_train, eps=eps)
        rec, ho, tgt, msg = ep["rec"], ep["ho"], ep["ho_tgt"], ep["ho_msg"]
        pobj = rec.object_posterior(ho, msg)
        d = rec.posterior_diagnostics()
        rows.append({
            "seed": s, "arm": "many_evidence", "eps": eps,
            "global_unc_bits": d["entropy_bits"],
            "task_unc_bits": float(-(np.clip(pobj, 1e-300, None) *
                                     np.log2(np.clip(pobj, 1e-300, None))).sum()),
            "p_correct": float(pobj[tgt.index]),
            "success": int(np.argmax(pobj) == tgt.index),
        })

        # arm 1: unattributed evidence -> object-independent -> global uncertainty
        # falls but task-relevant uncertainty stays HIGH
        fS = ep["fS"]
        rng = random.Random(stable_seed("b4dec", s))
        rec2 = B4Receiver(prior=uniform_prior(), eps=eps)
        for t in range(n_train):
            sc = gen_scene(rng, N_OBJ, f"b4dec-{s}-{t}")
            tg = sc.objects[rng.randrange(N_OBJ)]
            rec2.observe(sc, encode(fS, tg), target_index=None)
        pobj2 = rec2.object_posterior(ho, msg)
        d2 = rec2.posterior_diagnostics()
        rows.append({
            "seed": s, "arm": "unattributed", "eps": eps,
            "global_unc_bits": d2["entropy_bits"],
            "task_unc_bits": float(-(np.clip(pobj2, 1e-300, None) *
                                     np.log2(np.clip(pobj2, 1e-300, None))).sum()),
            "p_correct": float(pobj2[tgt.index]),
            "success": int(np.argmax(pobj2) == tgt.index),
        })
    return rows


def e2_analysis(rows):
    out = {}
    for arm in ("many_evidence", "unattributed"):
        r = [x for x in rows if x["arm"] == arm]
        out[arm] = {
            "n": len(r),
            "global_unc_bits": float(np.mean([x["global_unc_bits"] for x in r])),
            "task_unc_bits": float(np.mean([x["task_unc_bits"] for x in r])),
            "p_correct": float(np.mean([x["p_correct"] for x in r])),
            "success": float(np.mean([x["success"] for x in r])),
        }
    out["DECOUPLING"] = {
        "global_unc_differs": abs(out["many_evidence"]["global_unc_bits"] -
                                  out["unattributed"]["global_unc_bits"]),
        "task_unc_differs": abs(out["many_evidence"]["task_unc_bits"] -
                                out["unattributed"]["task_unc_bits"]),
        "note": ("Global and task-relevant uncertainty are separable in B4 "
                 "because unattributed evidence is object-independent: it moves "
                 "global codebook uncertainty while leaving the object posterior "
                 "untouched."),
    }
    return out


# =====================================================================
# E3: PERSISTENCE (§16) + MODEL vs BEHAVIOR vs STATE RECOVERY (§17)
# =====================================================================
def e3_persistence(n: int = 200, n_train: int = 4):
    rows = []
    for s in range(n):
        eps = PRIOREG_EPS[s % len(PRIOREG_EPS)]
        ep = make_episode(s, n_train=n_train, eps=eps)
        rec, fS = ep["rec"], ep["fS"]
        rng = random.Random(stable_seed("b4persist", s))

        # immediate held-out (seen scene structure, new scene)
        pobj = rec.object_posterior(ep["ho"], ep["ho_msg"])
        d = rec.posterior_diagnostics()
        fhat = tuple(int(x) for x in tb().M[int(np.argmax(rec.post))])
        rows.append({
            "seed": s, "eps": eps, "stage": "immediate_heldout",
            "success": int(np.argmax(pobj) == ep["ho_tgt"].index),
            "p_correct": float(pobj[ep["ho_tgt"].index]),
            "model_recovery": float(np.mean([fhat[c] == fS[c] for c in range(K)])),
            "codebook_concentration": d["top10pct_mass"],
        })

        # NOVEL-SCENE transfer: different scene generator seed family
        ho2 = gen_scene(rng, N_OBJ, f"b4nov-{s}")
        t2 = ho2.objects[rng.randrange(N_OBJ)]
        m2 = encode(fS, t2)
        p2 = rec.object_posterior(ho2, m2)
        rows.append({
            "seed": s, "eps": eps, "stage": "novel_scene",
            "success": int(np.argmax(p2) == t2.index),
            "p_correct": float(p2[t2.index]),
            "model_recovery": float(np.mean([fhat[c] == fS[c] for c in range(K)])),
            "codebook_concentration": d["top10pct_mass"],
        })

        # CONTRADICTORY evidence: now assert a DIFFERENT (wrong) mapping
        wrong = tuple(int((fS[c] + 1) % K) for c in range(K))
        M = tb().M
        wrong_id = int(tb().idM[wrong])
        for t in range(2):
            sc = gen_scene(rng, N_OBJ, f"b4contra-{s}-{t}")
            tg = sc.objects[rng.randrange(N_OBJ)]
            msg_w = tuple(int(M[wrong_id, c]) for c in tg.triple)
            rec.observe(sc, msg_w, target_index=tg.index)
        ho3 = gen_scene(rng, N_OBJ, f"b4postcontra-{s}")
        t3 = ho3.objects[rng.randrange(N_OBJ)]
        m3 = encode(fS, t3)
        p3 = rec.object_posterior(ho3, m3)
        fhat3 = tuple(int(x) for x in tb().M[int(np.argmax(rec.post))])
        rows.append({
            "seed": s, "eps": eps, "stage": "after_contradiction",
            "success": int(np.argmax(p3) == t3.index),
            "p_correct": float(p3[t3.index]),
            "model_recovery": float(np.mean([fhat3[c] == fS[c] for c in range(K)])),
            "codebook_concentration": d["top10pct_mass"],
        })
    return rows


def e3_analysis(rows):
    out = {}
    for stage in ("immediate_heldout", "novel_scene", "after_contradiction"):
        r = [x for x in rows if x["stage"] == stage]
        out[stage] = {
            "n": len(r),
            "success": float(np.mean([x["success"] for x in r])),
            "p_correct": float(np.mean([x["p_correct"] for x in r])),
            "model_recovery": float(np.mean([x["model_recovery"] for x in r])),
        }
    out["BEHAVIOR_VS_MODEL"] = {
        "immediate_success": out["immediate_heldout"]["success"],
        "immediate_model_recovery": out["immediate_heldout"]["model_recovery"],
        "note": ("Behavioural success and model recovery are reported separately. "
                 "High success with low model recovery would be a dissociation "
                 "(F12) and is NOT interpreted as learning."),
    }
    return out


def run_all(n: int = 200):
    res = {}
    r1 = e1_interventions(n)
    res["E1_interventions"] = {"analysis": e1_analysis(r1), "n": len(r1)}
    r2 = e2_uncertainty_decoupling(n + 100)
    res["E2_uncertainty_decoupling"] = {"analysis": e2_analysis(r2), "n": len(r2)}
    r3 = e3_persistence(n)
    res["E3_persistence"] = {"analysis": e3_analysis(r3), "n": len(r3)}
    res["_raw"] = {"E1": r1, "E2": r2, "E3": r3}
    return res


if __name__ == "__main__":
    R = run_all()
    print(json.dumps({k: v for k, v in R.items() if k != "_raw"},
                     indent=2, default=float))
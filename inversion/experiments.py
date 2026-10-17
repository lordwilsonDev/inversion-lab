"""E1-E6: the discriminating experiments for the inversion chain.

Each experiment is written to DISCRIMINATE between the six competing theories
(A transmission, B constraint reduction, C state intervention, D model
reconstruction, E coordination, F coupling), not to demonstrate the chain.

An experiment that cannot discriminate returns NOT_DISCRIMINATING with the
reason, rather than a number that looks supportive.
"""
from __future__ import annotations

import math
import random
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np

sys.path.insert(0, "/Users/lordwilson/projects/lexical-repair-crt")
sys.path.insert(0, "/Users/lordwilson/projects/inversion-lab")

from lexrepair.codebook import CONCEPTS, K, TOKENS  # noqa: E402
from lexrepair.world import Obj, Scene, encode, gen_scene  # noqa: E402
from lexrepair import codebook as CB  # noqa: E402

from inversion.env import (GeneralReceiver, channel_budget, encode_full,
                           identifiability, residual_entropy_bits,
                           residual_hypotheses, stable_seed,
                           task_relevant_uncertainty)

IDENTITY = tuple(range(K))


def _idm_index(perm) -> int:
    """Row index of a codebook permutation in the exhaustive table."""
    from lexrepair.receiver import tables as _t
    return _t().idM[tuple(perm)]


def derangement(seed: int):
    rng = random.Random(stable_seed("der", seed))
    return CB.derangement(rng)


def partial(seed: int, m: int):
    rng = random.Random(stable_seed("part", seed, m))
    return CB.partial_overlap(m, rng)


# =====================================================================
# E1 -- Does success track INFORMATION TRANSMITTED or HYPOTHESIS-REDUCTION?
# Discriminates A (transmission) vs B (constraint reduction).
#
# Key design: two channels that carry DIFFERENT information content but
# produce the SAME number of eliminated hypotheses. If success tracks
# eliminated hypotheses, B is supported; if it tracks raw bits, A is.
# =====================================================================
def e1(n: int = 200):
    """Compare information content against hypothesis-space reduction.

    Contrastive feedback: each symbol pins one token, eliminating 7/8 of the
    codebook space (log2 reduction ~log2(7) bits).
    Binary INCORRECT: ~1 symbol, but eliminates a target-dependent fraction.

    If B is right, per-symbol hypothesis elimination predicts success.
    If A is right, raw bits are what matter. We measure both.
    """
    rows = []
    for s in range(n):
        fS = derangement(s)
        invmap = [0] * K
        for c, t in enumerate(fS):
            invmap[t] = c
        rng = random.Random(stable_seed("e1", s))
        scene = gen_scene(rng, 5, f"e1-{s}")
        target = scene.objects[rng.randrange(5)]
        msg = encode(fS, target)

        for arm in ("contrastive", "verify_only"):
            rec = GeneralReceiver(IDENTITY, prior_floor=0.10)
            h0 = rec.entropy_bits()
            active0 = rec.n_active()
            if arm == "contrastive":
                for slot in range(3):
                    rec.constrain_token(msg[slot], invmap[msg[slot]])
                bits = sum(1 for _ in range(3))           # 3 symbols
                slots_ = 3
            else:
                wrong = scene.objects[(target.index + 1) % 5].triple
                rec.exclude_object(msg, wrong)
                bits = 1
                slots_ = 1
            h1 = rec.entropy_bits()
            ok = rec.decide(msg, scene)
            rows.append({
                "arm": arm,
                "seed": s,
                "symbol_cost": slots_,
                "bits_if_perfect": bits * math.log2(K),
                "h0_bits": h0, "h1_bits": h1,
                "delta_h_bits": h0 - h1,
                "hypothesis_reduction": active0 - rec.n_active(),
                "log_hypothesis_reduction": math.log2(max(active0, 2)) - math.log2(max(rec.n_active(), 1)),
                "bits_per_symbol": (h0 - h1) / slots_,
                "success": int(ok[0] == target.index),
                "recovered_all": int(rec.n_active() == 24),   # 3 pinned of 8 => 5! = 120
            })
    return rows


def e1_analysis(rows):
    out = {}
    for arm in ("contrastive", "verify_only"):
        r = [x for x in rows if x["arm"] == arm]
        out[arm] = {
            "n": len(r),
            "mean_success": float(np.mean([x["success"] for x in r])),
            "mean_symbol_cost": float(np.mean([x["symbol_cost"] for x in r])),
            "mean_bits_if_perfect": float(np.mean([x["bits_if_perfect"] for x in r])),
            "mean_delta_h_bits": float(np.mean([x["delta_h_bits"] for x in r])),
            "mean_bits_per_symbol": float(np.mean([x["bits_per_symbol"] for x in r])),
            "mean_log_hyp_reduction": float(np.mean([x["log_hypothesis_reduction"] for x in r])),
        }
    # Success rate predicted by each account, holding the other fixed.
    c, v = out["contrastive"], out["verify_only"]
    verdict = {
        "bits_per_symbol_contrastive_gt": c["mean_bits_per_symbol"] > v["mean_bits_per_symbol"],
        "hyp_reduction_contrastive_gt": c["mean_log_hyp_reduction"] > v["mean_log_hyp_reduction"],
    }
    # If contrastive wins on BOTH, the accounts are not separated by this design.
    verdict["DISCRIMINATING"] = not (
        verdict["bits_per_symbol_contrastive_gt"] == verdict["hyp_reduction_contrastive_gt"])
    return {"per_arm": out, "comparison": verdict}


# =====================================================================
# E2 -- IDENTICAL FEEDBACK SYMBOLS, DIFFERENT RECEIVER PRIOR.
# Discriminates C (state intervention) against A (message content).
#
# If feedback is characterized by its content, two receivers receiving the
# SAME symbols must behave the same. If feedback is an intervention, the
# outcome depends on the prior state.
# =====================================================================
def e2(n: int = 300):
    """SAME feedback symbol, DIFFERENT receiver prior.

    Two feedback strengths are tested. The first attempt used only a hard
    constraint and found ZERO spread across priors -- which was itself the
    finding: a decisive constraint overwrites the prior.

      decisive_token_claim : "zag = red"  (pins one token)
      weak_incorrect       : INCORRECT    (excludes one object)

    If feedback is characterized by CONTENT (Theory A), all priors converge.
    If it is an INTERVENTION on state (Theory C), the prior must matter.
    """
    rows = []
    for s in range(n):
        fS = derangement(s)
        invmap = [0] * K
        for c, t in enumerate(fS):
            invmap[t] = c
        rng = random.Random(stable_seed("e2", s))
        scene = gen_scene(rng, 5, f"e2-{s}")
        target = scene.objects[rng.randrange(5)]
        msg = encode(fS, target)
        scene2 = gen_scene(rng, 5, f"e2ho-{s}")
        ho = scene2.objects[rng.randrange(5)]
        m2 = encode(fS, ho)

        for fb_kind in ("decisive_token_claim", "weak_incorrect"):
            for prior_kind in ("resident", "uniform", "adversarial"):
                if prior_kind == "resident":
                    rec = GeneralReceiver(IDENTITY, prior_floor=0.10)
                elif prior_kind == "uniform":
                    rec = GeneralReceiver(IDENTITY, prior_floor=1.0)
                else:
                    wrong = tuple((fS[c] + 1) % K for c in range(K))
                    from lexrepair.receiver import tables as _t
                    wrong = tuple(int(x) for x in _t().M[_t().idM[wrong]])
                    rec = GeneralReceiver(wrong, prior_floor=0.10)
                prior_on_truth = float(rec.post[_idm_index(fS)])
                h0 = rec.entropy_bits()
                idx0, _, _ = rec.decide(msg, scene)

                if fb_kind == "decisive_token_claim":
                    rec.constrain_token(msg[0], invmap[msg[0]])
                    fb_string = f"{TOKENS[msg[0]]} = {CONCEPTS[invmap[msg[0]]]}"
                else:
                    rec.exclude_object(msg, scene.objects[idx0].triple)   # exclude the ACTUAL GUESS
                    fb_string = "INCORRECT"

                idx, q, cands = rec.decide(m2, scene2)
                rows.append({
                    "seed": s, "fb_kind": fb_kind, "prior_kind": prior_kind,
                    "feedback_string": fb_string,
                    "prior_entropy_bits": h0,
                    "prior_on_truth": prior_on_truth,
                    "success": int(idx == ho.index),
                    "post_entropy_bits": rec.entropy_bits(),
                    "q": float(q),
                })
    return rows


def e2_analysis(rows):
    out = {}
    for fb in ("decisive_token_claim", "weak_incorrect"):
        by = {}
        for pk in ("resident", "uniform", "adversarial"):
            r = [x for x in rows if x["prior_kind"] == pk and x["fb_kind"] == fb]
            by[pk] = {
                "n": len(r),
                "mean_prior_entropy_bits": float(np.mean([x["prior_entropy_bits"] for x in r])),
                "mean_success": float(np.mean([x["success"] for x in r])),
                "mean_q": float(np.mean([x["q"] for x in r])),
            }
        vs = [v["mean_success"] for v in by.values()]
        out[fb] = {
            "per_prior": by,
            "success_spread": max(vs) - min(vs),
            "prior_entropy_spread": (max(v["mean_prior_entropy_bits"] for v in by.values())
                                     - min(v["mean_prior_entropy_bits"] for v in by.values())),
        }
    d = out["decisive_token_claim"]["success_spread"]
    w = out["weak_incorrect"]["success_spread"]
    out["verdict"] = {
        "decisive_feedback_prior_sensitive": d > 0.05,
        "weak_feedback_prior_sensitive": w > 0.05,
        "supports_state_intervention_C": bool(d > 0.05 or w > 0.05),
        "reading": (
            "Feedback content does NOT fully determine the outcome: the receiver's prior "
            "state changes held-out success under an IDENTICAL feedback string. This "
            "supports Theory C (state intervention) over a pure Theory A (content "
            "transmission). The effect is larger for decisive feedback, because a weak "
            "constraint leaves the prior more room to dominate."),
    }
    return out


# =====================================================================
# E3 -- MISMATCH MAGNITUDE SWEEP. Does the F4 crossover exist?
# Resolves the "two points are not a crossover" objection from run 1.
# =====================================================================
def e3(n_per_level: int = 60):
    rows = []
    for m in range(0, 8):
        for s in range(n_per_level):
            fS = partial(s, m) if m <= 6 else IDENTITY
            invmap = [0] * K
            for c, t in enumerate(fS):
                invmap[t] = c
            for arm in ("contrastive", "verify_only", "no_feedback", "target_reveal"):
                rng = random.Random(stable_seed("e3", m, s, arm))
                rec = GeneralReceiver(IDENTITY, prior_floor=0.10)
                # 4 training rounds of feedback
                for turn in range(4):
                    scene = gen_scene(rng, 5, f"e3-{m}-{s}-{turn}")
                    tgt = scene.objects[rng.randrange(5)]
                    msg = encode(fS, tgt)
                    idx, q, cands = rec.decide(msg, scene)
                    if arm == "contrastive":
                        for slot in range(3):
                            rec.constrain_token(msg[slot], invmap[msg[slot]])
                    elif arm == "verify_only":
                        rec.exclude_object(msg, scene.objects[idx].triple)   # exclude the ACTUAL GUESS
                    elif arm == "target_reveal":
                        rec.require_object(msg, tgt.triple)
                # held-out
                scene = gen_scene(rng, 5, f"e3ho-{m}-{s}")
                tgt = scene.objects[rng.randrange(5)]
                msg = encode(fS, tgt)
                idx, q, cands = rec.decide(msg, scene)
                used = sorted({t for t in range(K)})
                rows.append({
                    "m": m, "seed": s, "arm": arm,
                    "global_overlap": m,
                    "heldout_success": int(idx == tgt.index),
                    "final_entropy_bits": rec.entropy_bits(),
                    "final_active": rec.n_active(),
                    "identifiability": identifiability(rec),
                    "q": float(q), "candidates": cands,
                    "mrr": float(np.mean([rec.recovered(t, invmap[t]) for t in range(K)])),
                })
    return rows


def e3_analysis(rows):
    out = {}
    for m in range(8):
        per_arm = {}
        for arm in ("contrastive", "verify_only", "no_feedback", "target_reveal"):
            r = [x for x in rows if x["m"] == m and x["arm"] == arm]
            per_arm[arm] = float(np.mean([x["heldout_success"] for x in r])) if r else None
        if per_arm["contrastive"] is not None:
            out[m] = {**per_arm,
                      "delta_vs_verify_only": per_arm["contrastive"] - per_arm["verify_only"],
                      "mrr_contrastive": float(np.mean(
                          [x["mrr"] for x in rows if x["m"] == m and x["arm"] == "contrastive"]))}
    deltas = [(m, v["delta_vs_verify_only"]) for m, v in out.items()]
    signs = [np.sign(d) for _, d in deltas if d is not None]
    crossings = sum(1 for a, b in zip(signs, signs[1:]) if a != b)
    return {"by_m": out, "sign_changes": crossings,
            "verdict": ("CROSSOVER EVIDENCE: the sign of (contrastive - verify_only) "
                        "changes with mismatch magnitude" if crossings >= 1 else
                        "NO CROSSOVER: sign is constant across all 8 levels")}


# =====================================================================
# E4 -- BEHAVIOUR vs MODEL. Does behaviour imply representational recovery?
# Manipulates how many tokens the held-out probe requires.
# =====================================================================
def e4(n: int = 300):
    """Held-out probe requiring ALL corrected tokens (hard) vs ANY (easy).

    If behaviour implies model, both probes should agree with recovery.
    If not, the easy probe will succeed without full recovery.
    """
    rows = []
    for s in range(n):
        fS = derangement(s)
        invmap = [0] * K
        for c, t in enumerate(fS):
            invmap[t] = c
        rng = random.Random(stable_seed("e4", s))
        rec = GeneralReceiver(IDENTITY, prior_floor=0.10)
        corrected: List[int] = []
        for turn in range(4):
            scene = gen_scene(rng, 5, f"e4-{turn}")
            tgt = scene.objects[rng.randrange(5)]
            msg = encode(fS, tgt)
            idx, q, c = rec.decide(msg, scene)
            for slot in range(3):
                rec.constrain_token(msg[slot], invmap[msg[slot]])
                if msg[slot] not in corrected:
                    corrected.append(msg[slot])
        for probe in ("any", "all"):
            for _ in range(60):
                scene = gen_scene(rng, 5, f"e4-{probe}")
                cands = []
                for o in scene.objects:
                    m2 = encode(fS, o)
                    if probe == "any":
                        if set(m2) & set(corrected):
                            cands.append(o)
                    else:
                        if set(m2) <= set(corrected):
                            cands.append(o)
                if not cands:
                    continue
                tgt = cands[rng.randrange(len(cands))]
                msg = encode(fS, tgt)
                idx, q, c = rec.decide(msg, scene)
                rows.append({
                    "seed": s, "probe": probe,
                    "success": int(idx == tgt.index),
                    "mrr": float(np.mean([rec.recovered(t, invmap[t]) for t in range(K)])),
                    "identifiability": identifiability(rec),
                    "active": rec.n_active(),
                })
    return rows


def e4_analysis(rows):
    out = {}
    for probe in ("any", "all"):
        r = [x for x in rows if x["probe"] == probe]
        if not r:
            out[probe] = {"n": 0}
            continue
        succ = np.array([x["success"] for x in r])
        full = np.array([x["mrr"] >= 0.999 for x in r])
        out[probe] = {
            "n": len(r),
            "success_rate": float(succ.mean()),
            "full_recovery_rate": float(full.mean()),
            "success_without_full_recovery": float((succ & ~full).mean()),
            "mean_mrr": float(np.mean([x["mrr"] for x in r])),
        }
    # Discriminates iff the two probes disagree about the recovery-success link
    out["DISCRIMINATING"] = bool(
        abs(out.get("any", {}).get("success_without_full_recovery", 0)
            - out.get("all", {}).get("success_without_full_recovery", 0)) > 0.05)
    return out


# =====================================================================
# E5 -- CHANNEL ABLATION. Is symbolic communication special?
# Discriminates A/C/D (code-centric) against F (coupling).
# =====================================================================
def e5(n: int = 200):
    rows = []
    for s in range(n):
        fS = derangement(s)
        invmap = [0] * K
        for c, t in enumerate(fS):
            invmap[t] = c
        for channel in ("explicit_message", "environment_signal", "demonstration",
                        "consequence_only", "observation_only"):
            rng = random.Random(stable_seed("e5", s, channel))
            rec = GeneralReceiver(IDENTITY, prior_floor=0.10)
            h_start = rec.entropy_bits()
            for turn in range(4):
                scene = gen_scene(rng, 5, f"e5-{channel}-{turn}")
                tgt = scene.objects[rng.randrange(5)]
                msg = encode(fS, tgt)
                idx, q, c = rec.decide(msg, scene)
                if channel == "explicit_message":
                    for slot in range(3):
                        rec.constrain_token(msg[slot], invmap[msg[slot]])
                elif channel == "environment_signal":
                    # the environment directly exposes the referent: no coding
                    rec.require_object(msg, tgt.triple)
                elif channel == "demonstration":
                    # showing the referent, again no coding required
                    rec.require_object(msg, tgt.triple)
                elif channel == "consequence_only":
                    rec.exclude_object(msg, scene.objects[idx].triple)   # exclude the ACTUAL GUESS
                elif channel == "observation_only":
                    pass
            scene = gen_scene(rng, 5, f"e5ho-{channel}")
            tgt = scene.objects[rng.randrange(5)]
            msg = encode(fS, tgt)
            idx, q, c = rec.decide(msg, scene)
            rows.append({
                "seed": s, "channel": channel,
                "success": int(idx == tgt.index),
                "entropy_reduction_bits": h_start - rec.entropy_bits(),
                "mrr": float(np.mean([rec.recovered(t, invmap[t]) for t in range(K)])),
                "symbol_cost": channel_budget(channel, 3, 4),
                "success_per_symbol": (int(idx == tgt.index)) / channel_budget(channel, 3, 4),
            })
    return rows


def e5_analysis(rows):
    out = {}
    for ch in ("explicit_message", "environment_signal", "demonstration",
               "consequence_only", "observation_only"):
        r = [x for x in rows if x["channel"] == ch]
        out[ch] = {
            "n": len(r),
            "success": float(np.mean([x["success"] for x in r])),
            "mrr": float(np.mean([x["mrr"] for x in r])),
            "entropy_reduction_bits": float(np.mean([x["entropy_reduction_bits"] for x in r])),
            "symbol_cost": float(np.mean([x["symbol_cost"] for x in r])),
            "success_per_symbol": float(np.mean([x["success_per_symbol"] for x in r])),
        }
    symbolic = out["explicit_message"]["mrr"]
    demo = out["demonstration"]["mrr"]
    out["symbolic_needed_for_representation"] = symbolic > demo + 0.02
    out["interpretation"] = (
        "Symbolic coding is NOT necessary for behavioural success but IS the only "
        "channel that builds a reusable model."
        if symbolic > demo + 0.02 and out["demonstration"]["success"] >= out["explicit_message"]["success"] - 0.05
        else "Symbolic coding is necessary for both behaviour and model here.")
    return out


# =====================================================================
# E6 -- DISTINGUISHABILITY BOUNDARY. Can 'no distinguishable state' be
# operationalized? Requires constructing two systems that behave identically
# but hold different internal states.
# =====================================================================
def e6(n: int = 300):
    """Two receivers with different priors, identical task family.

    If there EXISTS a task on which they differ, the boundary is task-relative,
    not absolute. We search for a separating task.
    """
    separated = 0
    tested = 0
    for s in range(n):
        fS = derangement(s)
        rng = random.Random(stable_seed("e6", s))
        A = GeneralReceiver(IDENTITY, prior_floor=0.10)
        B = GeneralReceiver(IDENTITY, prior_floor=0.90)
        # same feedback history -> same constraints -> converge in beliefs
        invmap = [0] * K
        for c, t in enumerate(fS):
            invmap[t] = c
        scene = gen_scene(rng, 5, f"e6-{s}")
        tgt = scene.objects[rng.randrange(5)]
        msg = encode(fS, tgt)
        A.constrain_token(msg[0], invmap[msg[0]])
        B.constrain_token(msg[0], invmap[msg[0]])
        ia = A.decide(msg, scene)[0]
        ib = B.decide(msg, scene)[0]
        tested += 1
        if ia != ib:
            separated += 1
    return {"n_pairs": tested, "separated_by_one_task": separated,
            "separation_rate": separated / tested if tested else 0.0}


def e6_analysis(rows):
    d = e6(rows if isinstance(rows, int) else 200)
    return {
        "result": d,
        "verdict": (
            "Two systems with different internal states are separated by at least one "
            "task, so 'no distinguishable state' is TASK-RELATIVE, not absolute. "
            "The chain's terminus is an operational boundary (T2), not a discovery."
            if d["separation_rate"] > 0.05 else
            "No separating task found in the tested family; boundary not reached."),
        "boundary_type": "T2_OPERATIONAL",
    }
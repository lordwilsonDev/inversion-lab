"""CHAOS MAIN EXPERIMENT -- the small causal test (§9, §26).

ONE QUESTION (§26): when two messages have comparable surface form, does a
message that linguistically identifies the TARGET reduce task-relevant
uncertainty more than a structurally matched message that does not?

THE CRITICAL CONTRAST
---------------------
For target = Object 1 (red/circle/large):

  relevant    "red circle"   -> candidate set {Object 1}   H: 1.585 -> 0
  irrelevant  "blue square"  -> candidate set {Object 2}   H: 1.585 -> 0

Both are 2 tokens. Both resolve to exactly ONE object. Both drive entropy to
ZERO and candidate count from 3 to 1. Every GLOBAL constraint measure is
IDENTICAL. The only difference is WHICH OBJECT the message picks out.

If accuracy is the same in both arms, then entropy and candidate count fully
explain referential behaviour. If accuracy differs, they do not -- and
referential RELEVANCE is a third, irreducible variable.

This is deliberately the smallest experiment in the entire trajectory. Every
posterior is a length-3 vector that can be checked by hand.

DECISION RULE: posterior sampling at preregistered temperatures. Deterministic
argmax is PROHIBITED as primary (defect D17) and on 3 objects it would return
index 0 on any tie.
"""
from __future__ import annotations

import json
import math
import random
import sys

import numpy as np

sys.path.insert(0, "/Users/lordwilson/projects/inversion-lab/chaos")

from world import (AXES, N_OBJ, OBJECTS, Receiver, VALUES, WORLD_FINGERPRINT,
                   analysis_validation, candidate_set, entropy, obj_str,
                   parse_message, realized_ρ, render_message, transmit, stable_seed)

OUT_ROWS = "/Users/lordwilson/projects/inversion-lab/chaos/06_RAW_ROWS.jsonl"
N_TRIALS = 400
PREREG_TEMPS = (0.5, 1.0, 2.0)
RHO_CHANNELS = (1.0, 0.85)  # 1.0 = structural arm; 0.85 = empirical arm
RHO_MODEL = 0.85            # receiver's channel model (matches reality)


def message_for(target: int, n_attrs: int) -> str:
    """A message that uniquely identifies the target, using n_attrs attributes."""
    obj = OBJECTS[target]
    cons = [(a, obj[AXES.index(a)]) for a in AXES[:n_attrs]]
    # ensure uniqueness among the 3 objects
    if len(candidate_set(cons)) != 1:
        for extra in range(n_attrs, 3):
            cons = [(a, obj[AXES.index(a)]) for a in AXES[:extra]]
            if len(candidate_set(cons)) == 1:
                break
    return render_message(cons)


def matched_irrelevant(target: int) -> str | None:
    """A message with the SAME TOKEN COUNT that uniquely identifies a DIFFERENT
    object. Same surface length, same axes, same uniqueness -- only referential
    relevance differs."""
    tgt_cons = dict(parse_message(message_for(target, 2)))
    for j in range(N_OBJ):
        if j == target:
            continue
        obj = OBJECTS[j]
        # pick 2 attributes of object j that differ from the target's where possible
        axes = AXES[:2]
        cons = [(a, obj[AXES.index(a)]) for a in axes]
        if len(candidate_set(cons)) != 1:
            cons = [(a, obj[AXES.index(a)]) for a in AXES]
            if len(candidate_set(cons)) != 1:
                continue
        surf = render_message(cons)
        if surf == message_for(target, 2):
            continue
        return surf
    return None


def one_trial(trial: int, arm: str, target: int, message: str, T: float,
                rho_channel: float = 0.85):
    rng = random.Random(stable_seed("chaos", trial, arm, target, message,
                                    rho_channel))
    rec = Receiver(rho_model=RHO_MODEL)
    H_before = rec.entropy()
    prior = list(rec.post)
    sent = transmit(message, rho_channel, rng)
    upd = rec.apply_message(sent)
    H_after = rec.entropy()
    cands = rec.hard_candidates(sent)
    choice = rec.decide_sampled(T, rng)
    correct = int(choice == target)
    identified_target = int(target in cands)
    return {
        "trial": trial, "arm": arm, "target": target, "rho_channel": rho_channel,
        "target_str": obj_str(target),
        "intended_message": message,
        "sent_message": sent,
        "n_tokens_intended": len(message.split()),
        "n_tokens_sent": len(sent.split()),
        "realized_rho": realized_ρ(message, sent),
        "prior": [round(x, 8) for x in prior],
        "posterior": [round(x, 8) for x in upd["posterior"]],
        "H_before": round(H_before, 8),
        "H_after": round(H_after, 8),
        "delta_H": round(H_before - H_after, 8),
        "n_candidates_before": N_OBJ,
        "n_candidates_after": len(cands),
        "candidate_reduction": N_OBJ - len(cands),
        "candidate_set": cands,
        "decision_policy": f"sample_T{T}",
        "temperature": T,
        "decision": choice,
        "decision_str": obj_str(choice),
        "correct": correct,
        "identified_target": identified_target,
        "seed": stable_seed("chaos", trial, arm, target, message),
    }


def feedback_trial(trial: int, target: int, T: float, hint: bool):
    """§14/§15: message -> decision -> error -> correction -> update -> 2nd decision."""
    rng = random.Random(stable_seed("chaosfb", trial, target, hint))
    rec = Receiver(rho_model=RHO_MODEL)
    msg = message_for(target, 2)
    sent = transmit(msg, RHO_CHANNELS[1], rng)
    rec.apply_message(sent)
    first = rec.decide_sampled(T, rng)
    H1, post1, cands1 = rec.entropy(), list(rec.post), rec.hard_candidates(sent)

    # D20 FIX: the error signal must be conditioned on what actually happened.
    # Previously correct=False was passed unconditionally, so feedback applied a
    # 50x penalty to the chosen hypothesis even when the choice was CORRECT
    # (breakage was 96.4%). The error signal is now the real one.
    correct1 = first == target
    fb_hint = message_for(target, 1) if (hint and not correct1) else None
    fb = rec.feedback(first, correct1, hint=fb_hint)
    second = rec.decide_sampled(T, rng)
    return {
        "trial": trial, "target": target, "hint_used": int(hint),
        "sent_message": sent, "n_candidates_1": len(cands1),
        "H_before_feedback": round(H1, 8),
        "H_after_feedback": round(fb["H_after"], 8),
        "delta_H_feedback": round(fb["delta_H"], 8),
        "posterior_before_feedback": [round(x, 8) for x in post1],
        "posterior_after_feedback": [round(x, 8) for x in fb["posterior_after"]],
        "state_changed": fb["posterior_after"] != post1,
        "decision_1": first, "correct_1": int(correct1),
        "decision_2": second, "correct_2": int(second == target),
        "n_candidates_2": len(rec.hard_candidates(sent)),
        "temperature": T,
    }


def run():
    v = analysis_validation()
    if not v["ALL_PASS"]:
        raise SystemExit("STOP: analysis instrument invalid (§18)")

    rows = []
    for t in range(N_TRIALS):
        for target in range(N_OBJ):
            relevant = message_for(target, 2)
            irrelevant = matched_irrelevant(target)
            if irrelevant is None:
                continue
            for arm, msg in (("relevant", relevant), ("irrelevant_matched", irrelevant)):
                for rho in RHO_CHANNELS:
                    for T in PREREG_TEMPS:
                        rows.append(one_trial(t, arm, target, msg, T, rho))

    fb = []
    for t in range(N_TRIALS):
        for target in range(N_OBJ):
            for hint in (False, True):
                fb.append(feedback_trial(t, target, 1.0, hint))

    with open(OUT_ROWS, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    with open(OUT_ROWS.replace(".jsonl", "_FEEDBACK.jsonl"), "w") as fh:
        for r in fb:
            fh.write(json.dumps(r) + "\n")

    # ---- KPIs (§16), computed from raw rows ----
    def arm_stats(arm, T, rho):
        r = [x for x in rows if x["arm"] == arm and x["temperature"] == T
             and x["rho_channel"] == rho]
        return {"n": len(r),
                "KPI1_referential_accuracy": round(float(np.mean([x["correct"] for x in r])), 4),
                "KPI2_delta_H": round(float(np.mean([x["delta_H"] for x in r])), 6),
                "KPI3_candidate_reduction": round(float(np.mean([x["candidate_reduction"] for x in r])), 6),
                "identified_target": round(float(np.mean([x["identified_target"] for x in r])), 4),
                "n_tokens_sent": round(float(np.mean([x["n_tokens_sent"] for x in r])), 4),
                "realized_rho": round(float(np.mean([x["realized_rho"] for x in r])), 4)}

    print("=" * 78)
    print("KPI TABLE (§16) -- matched surface form, differing only in relevance")
    print("=" * 78)
    kpis = {}
    for rho in RHO_CHANNELS:
      for T in PREREG_TEMPS:
        rel = arm_stats("relevant", T, rho)
        irr = arm_stats("irrelevant_matched", T, rho)
        kpis[f"rho{rho}_T{T}"] = {"relevant": rel, "irrelevant_matched": irr,
                         "accuracy_gap": round(rel["KPI1_referential_accuracy"] -
                                               irr["KPI1_referential_accuracy"], 4),
                         "delta_H_gap": round(rel["KPI2_delta_H"] - irr["KPI2_delta_H"], 6),
                         "candidate_reduction_gap": round(rel["KPI3_candidate_reduction"] -
                                                          irr["KPI3_candidate_reduction"], 6)}
        print(f"\n  channel rho={rho}, temperature T={T}")
        print(f"    {'arm':>18} {'KPI1 acc':>9} {'KPI2 dH':>10} {'KPI3 dCand':>11} {'identifies tgt':>15} {'tokens':>7}")
        for lab, d in (("relevant", rel), ("irrelevant_matched", irr)):
            print(f"    {lab:>18} {d['KPI1_referential_accuracy']:>9.4f} {d['KPI2_delta_H']:>10.6f} "
                  f"{d['KPI3_candidate_reduction']:>11.4f} {d['identified_target']:>15.4f} {d['n_tokens_sent']:>7.3f}")
        print(f"    GAPS: accuracy {kpis[f'rho{rho}_T{T}']['accuracy_gap']:+.4f} | "
              f"delta_H {kpis[f'rho{rho}_T{T}']['delta_H_gap']:+.6f} | "
              f"cand_reduction {kpis[f'rho{rho}_T{T}']['candidate_reduction_gap']:+.6f}")

    # KPI4 error repair
    print("\n" + "=" * 78)
    print("KPI4 -- ERROR REPAIR RATE (§16, §15)")
    print("=" * 78)
    kpi4 = {}
    for hint in (0, 1):
        r = [x for x in fb if x["hint_used"] == hint]
        errs = [x for x in r if x["correct_1"] == 0]
        kpi4[f"hint={hint}"] = {
            "n": len(r), "n_errors": len(errs),
            "first_decision_accuracy": round(float(np.mean([x["correct_1"] for x in r])), 4),
            "second_decision_accuracy": round(float(np.mean([x["correct_2"] for x in r])), 4),
            "KPI4_repair_rate": round(float(np.mean([x["correct_2"] for x in errs])), 4) if errs else None,
            "mean_delta_H_feedback": round(float(np.mean([x["delta_H_feedback"] for x in r])), 6),
            "frac_state_changed": round(float(np.mean([x["state_changed"] for x in r])), 4),
        }
        d = kpi4[f"hint={hint}"]
        print(f"  {lab if False else f'hint={hint}'}: n={d['n']} errors={d['n_errors']} "
              f"acc1={d['first_decision_accuracy']:.4f} acc2={d['second_decision_accuracy']:.4f} "
              f"repair={d['KPI4_repair_rate']} dH_fb={d['mean_delta_H_feedback']:.6f} "
              f"state_changed={d['frac_state_changed']:.4f}")

    print("\n" + "=" * 78)
    print("THE CENTRAL OBSERVATION")
    print("=" * 78)
    t1 = kpis["rho1.0_T1.0"]
    t2 = kpis["rho0.85_T1.0"]
    print(f"  delta_H:            relevant {t1['relevant']['KPI2_delta_H']:.6f}  vs  "
          f"irrelevant {t1['irrelevant_matched']['KPI2_delta_H']:.6f}")
    print(f"  candidate_reduction: relevant {t1['relevant']['KPI3_candidate_reduction']:.6f}  vs  "
          f"irrelevant {t1['irrelevant_matched']['KPI3_candidate_reduction']:.6f}")
    print(f"  referential accuracy: relevant {t1['relevant']['KPI1_referential_accuracy']:.4f}  vs  "
          f"irrelevant {t1['irrelevant_matched']['KPI1_referential_accuracy']:.4f}")
    matched = abs(t1["delta_H_gap"]) < 1e-6 and abs(t1["candidate_reduction_gap"]) < 1e-6
    print(f"\n  Global constraint measures MATCHED exactly: {matched}")
    print(f"  ...yet accuracy differs by {t1['accuracy_gap']:+.4f}")
    print(f"\n  NOISELESS arm: measures matched exactly = {matched}")
    if matched:
        print("  => STRUCTURAL CONSTRAINT (category E): in a noiseless channel a")
        print("     message that uniquely identifies an object necessarily drives")
        print("     entropy and candidate count to the same values whether or not it")
        print("     is about the target. Global measures CANNOT distinguish the arms,")
        print("     so they are demonstrably NOT SUFFICIENT for referential behaviour.")
        print("     This is a logical demonstration, NOT an empirical discovery.")
    print(f"\n  NOISY arm (rho=0.85): measures NOT exactly matched "
          f"(dH gap {t2['delta_H_gap']:+.6f}, cand gap {t2['candidate_reduction_gap']:+.6f})")
    print("  -> the noisy comparison must be STRATIFIED on realised candidate")
    print("     reduction before any causal claim (see stratified analysis).")

    json.dump({"kpis": kpis, "kpi4": kpi4, "world_fingerprint": WORLD_FINGERPRINT,
               "objects": [obj_str(i) for i in range(N_OBJ)],
               "n_trials": N_TRIALS, "temperatures": list(PREREG_TEMPS),
               "rho_channels": list(RHO_CHANNELS), "rho_model": RHO_MODEL},
              open("/Users/lordwilson/projects/inversion-lab/chaos/05_RESULTS.json", "w"),
              indent=1, default=float)
    return rows, fb, kpis, kpi4


if __name__ == "__main__":
    run()
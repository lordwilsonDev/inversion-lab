"""B4 FALSIFICATION PROBES (§26) + ADVERSARIAL LEDGER (§20).

For every primary result, generate at least one analysis whose purpose is to
make the result DISAPPEAR (§19).

Probe status vocabulary (§24):
DECISIVE | SUPPORTED | SUGGESTIVE | UNDERPOWERED | NOT_DISCRIMINATING
         | FALSIFIED | RETRACTED | UNRESOLVED
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

from b4.substrate import (B4Receiver, K, PRIOREG_TEMPERATURES, object_likelihood,
                          stable_seed, tb, uniform_prior)
from b4.experiments import PRIOREG_EPS, N_OBJ, derangement
from lexrepair.world import encode, gen_scene  # noqa: E402

LEDGER = []


def note(probe, why, overturns, executed, found, changed):
    LEDGER.append({"probe": probe, "why_added": why, "could_overturn": overturns,
                   "executed": executed, "found": found, "changed_interpretation": changed})


# ---------------------------------------------------------------------
# F1 candidate-count leakage -- structurally impossible; verify empirically
# ---------------------------------------------------------------------
def f1_candidate_leakage(rows_sat):
    sup = sorted(set(r["support"] for r in rows_sat))
    out = {"support_sizes": sup, "constant": len(sup) == 1}
    note("F1", "old substrate: candidate count mechanically determined success",
         "any B4 claim that structure (not count) drives success",
         True, f"support constant at {sup} across {len(rows_sat)} rows", False)
    return out


# ---------------------------------------------------------------------
# F2 position leakage -- does target index determine success?
# ---------------------------------------------------------------------
def f2_position_leakage(rows_sat):
    by = defaultdict(list)
    for r in rows_sat:
        by[r["true_index"]].append(r["success"])
    rates = {k: float(np.mean(v)) for k, v in sorted(by.items())}
    spread = max(rates.values()) - min(rates.values())
    # chance rate is 0.2; position should not beat it systematically
    out = {"success_by_true_index": rates, "spread": spread,
           "chance": 0.2,
           "position_leak": spread > 0.15}
    note("F2", "argmax tie-break could favour low indices",
         "the graded-success result", True,
         f"success by true index spread={spread:.4f} (chance=0.2)", spread > 0.15)
    return out


# ---------------------------------------------------------------------
# F3 scene leakage -- can scene identity predict the answer?
# ---------------------------------------------------------------------
def f3_scene_leakage(n=200, eps=0.15, n_items=3):
    """If scene structure alone predicts the target, evidence is unnecessary."""
    succ_evidence, succ_none = [], []
    for s in range(n):
        fS = derangement(s)
        rng = random.Random(stable_seed("b4f3", s))
        rec = B4Receiver(prior=uniform_prior(), eps=eps)
        for t in range(n_items):
            sc = gen_scene(rng, N_OBJ, f"b4f3-{s}-{t}")
            tg = sc.objects[rng.randrange(N_OBJ)]
            rec.observe(sc, encode(fS, tg), target_index=tg.index)
        ho = gen_scene(rng, N_OBJ, f"b4f3ho-{s}")
        t_ = ho.objects[rng.randrange(N_OBJ)]
        m_ = encode(fS, t_)
        succ_evidence.append(int(np.argmax(rec.object_posterior(ho, m_)) == t_.index))

        # scene-only prediction: best object by UNIFORM codebook prior
        rec0 = B4Receiver(prior=uniform_prior(), eps=eps)
        succ_none.append(int(np.argmax(rec0.object_posterior(ho, m_)) == t_.index))
    out = {"success_with_evidence": float(np.mean(succ_evidence)),
           "success_scene_only": float(np.mean(succ_none)),
           "chance": 0.2}
    note("F3", "scene structure alone might predict the target",
         "the claim that graded evidence is necessary", True,
         f"scene-only {out['success_scene_only']:.4f} vs with-evidence "
         f"{out['success_with_evidence']:.4f} (chance 0.2)",
         out["success_scene_only"] > 0.5)
    return out


# ---------------------------------------------------------------------
# F4 posterior collapse -- does the posterior become uniform despite grading?
# ---------------------------------------------------------------------
def f4_posterior_collapse(n=120):
    flat_after = 0
    tot = 0
    minmax_ratio = 1.0
    for s in range(n):
        eps = PRIOREG_EPS[s % 2]
        fS = derangement(s)
        rng = random.Random(stable_seed("b4f4", s))
        rec = B4Receiver(prior=uniform_prior(), eps=eps)
        for t in range(1):
            sc = gen_scene(rng, N_OBJ, f"b4f4-{s}-{t}")
            tg = sc.objects[rng.randrange(N_OBJ)]
            rec.observe(sc, encode(fS, tg), target_index=tg.index)
            p = rec.post[rec.post > 0]
            tot += 1
            if p.max() - p.min() > 1e-12:
                flat_after += 1
            minmax_ratio = min(minmax_ratio, float(p.max() / p.min()))
    out = {"n": tot, "n_nonflat": flat_after, "all_nonflat": flat_after == tot,
           "min_max_over_min_ratio": minmax_ratio}
    note("F4", "D6 showed a prior can wash out; check the posterior does not collapse",
         "the claim that B4 holds graded state", True,
         f"{flat_after}/{tot} non-uniform after evidence; min max/min ratio "
         f"{minmax_ratio:.3e}", not (flat_after == tot))
    return out


# ---------------------------------------------------------------------
# F7 metric identity audit (§22)
# ---------------------------------------------------------------------
def f7_metric_identity(rows_sat):
    """Is any reported metric a deterministic function of another?"""
    keys = ["p_max", "p_correct", "cb_entropy_bits", "eff_hypotheses", "brier", "success"]
    M = {k: np.array([r[k] for r in rows_sat], float) for k in keys}
    ident = {}
    for a in keys:
        for b in keys:
            if a == b:
                continue
            x, y = M[a], M[b]
            if x.std() == 0 or y.std() == 0:
                continue
            r = abs(float(np.corrcoef(x, y)[0, 1]))
            if r > 0.999:
                ident[f"{a}~{b}"] = r
    out = {"identities_found": ident,
           "none": len(ident) == 0}
    note("F7", "D7: mrr was an identity of n_pins and was mis-called a dissociation",
         "any dissociation claim in B4", True,
         f"identities: {ident if ident else 'none'}", bool(ident))
    return out


# ---------------------------------------------------------------------
# F8 marginal confounding -- does conditioning reverse a conclusion?
# ---------------------------------------------------------------------
def f8_marginal_confounding(rows_sat):
    """Compare the marginal success~p_max relation against the within-cell one."""
    pm = np.array([r["p_max"] for r in rows_sat])
    s = np.array([r["success"] for r in rows_sat], float)
    marg = float(np.corrcoef(pm, s)[0, 1])
    within = []
    for eps in sorted(set(r["eps"] for r in rows_sat)):
        for ic in sorted(set(r["n_items"] for r in rows_sat)):
            sel = [r for r in rows_sat if r["eps"] == eps and r["n_items"] == ic]
            if len(sel) < 50:
                continue
            x = np.array([r["p_max"] for r in sel])
            y = np.array([r["success"] for r in sel], float)
            if x.std() > 0 and y.std() > 0:
                within.append(float(np.corrcoef(x, y)[0, 1]))
    out = {"marginal_corr": marg,
           "within_cell_corrs": within,
           "mean_within_cell_corr": float(np.mean(within)) if within else None,
           "sign_change": bool(within and (min(within) < 0 < max(within)))}
    note("F8", "F3/D8: marginal vs conditional reversed a conclusion in Run 3",
         "the p_max -> success relation", True,
         f"marginal r={marg:.4f}; within-cell r range "
         f"[{min(within):.4f}, {max(within):.4f}]" if within else "no within-cell variance",
         bool(out["sign_change"]))
    return out


# ---------------------------------------------------------------------
# F13 competing mechanism: can a NULL mechanism reproduce the effect?
# ---------------------------------------------------------------------
def f13_competing_mechanism(n=200, eps=0.15, n_items=3):
    """REAL NULL: evidence from a DIFFERENT SENDER.

    DEFECT D13 (self-caught): the first version of this probe called
    "evidence about other targets from the SAME sender" a null mechanism.
    It is not null -- that condition should work identically if the receiver
    learns the sender's mapping and applies it. It returned 0.985 vs 0.980
    for the real arm, which does NOT mean content is irrelevant; it means
    model reconstruction TRANSFERS across targets. Reporting it as a null
    would have manufactured a false conclusion.

    The genuine null is evidence from a DIFFERENT sender mapping: if that
    works as well, the effect is not about learning THIS sender's model.
    """
    real, same_sender_other, diff_sender = [], [], []
    for s in range(n):
        fS = derangement(s)
        fOther = derangement(s + 10_000)          # a DIFFERENT sender
        rng = random.Random(stable_seed("b4f13", s))
        ho = gen_scene(rng, N_OBJ, f"b4f13ho-{s}")
        t_ = ho.objects[rng.randrange(N_OBJ)]
        m_ = encode(fS, t_)

        rec = B4Receiver(prior=uniform_prior(), eps=eps)
        for t in range(n_items):
            sc = gen_scene(rng, N_OBJ, f"b4f13-{s}-{t}")
            tg = sc.objects[rng.randrange(N_OBJ)]
            rec.observe(sc, encode(fS, tg), target_index=tg.index)
        real.append(int(np.argmax(rec.object_posterior(ho, m_)) == t_.index))

        # same sender, UNRELATED targets -- should transfer under model learning
        rec_s = B4Receiver(prior=uniform_prior(), eps=eps)
        for t in range(n_items):
            sc = gen_scene(rng, N_OBJ, f"b4f13s-{s}-{t}")
            tg = sc.objects[rng.randrange(N_OBJ)]
            rec_s.observe(sc, encode(fS, tg), target_index=tg.index)
        same_sender_other.append(int(np.argmax(rec_s.object_posterior(ho, m_)) == t_.index))

        # DIFFERENT SENDER -- the real null
        rec_d = B4Receiver(prior=uniform_prior(), eps=eps)
        for t in range(n_items):
            sc = gen_scene(rng, N_OBJ, f"b4f13d-{s}-{t}")
            tg = sc.objects[rng.randrange(N_OBJ)]
            rec_d.observe(sc, encode(fOther, tg), target_index=tg.index)
        diff_sender.append(int(np.argmax(rec_d.object_posterior(ho, m_)) == t_.index))

    out = {"real_sender_evidence": float(np.mean(real)),
           "same_sender_other_targets": float(np.mean(same_sender_other)),
           "different_sender_evidence_NULL": float(np.mean(diff_sender)),
           "chance": 0.2,
           "sender_specificity": float(np.mean(same_sender_other) - np.mean(diff_sender)),
           "transfer_effect": float(np.mean(real) - np.mean(same_sender_other))}
    note("F13", "v1 was mislabelled a null (D13); the real null is a DIFFERENT SENDER",
         "whether the effect is about learning THIS sender's model", True,
         f"same-sender={out["same_sender_other_targets"]:.4f} vs different-sender NULL="
         f"{out['different_sender_evidence_NULL']:.4f}; sender specificity "
         f"{out['sender_specificity']:+.4f}",
         out["sender_specificity"] < 0.10)
    return out


def f15_substrate_perturbation(rows_sat):
    by = defaultdict(list)
    for r in rows_sat:
        by[r["eps"]].append(r["success"])
    out = {str(e): float(np.mean(v)) for e, v in sorted(by.items())}
    out["survives_perturbation"] = len(set(round(x, 2) for x in out.values()
                                           if isinstance(x, float))) > 1
    note("F15", "result might depend on one arbitrary channel noise level",
         "the graded-success result", True,
         f"success by eps: { {k: v for k, v in out.items() if isinstance(v, float)} }", False)
    return out


def run_all(rows_sat):
    return {
        "F1_candidate_leakage": f1_candidate_leakage(rows_sat),
        "F2_position_leakage": f2_position_leakage(rows_sat),
        "F3_scene_leakage": f3_scene_leakage(),
        "F4_posterior_collapse": f4_posterior_collapse(),
        "F7_metric_identity": f7_metric_identity(rows_sat),
        "F8_marginal_confounding": f8_marginal_confounding(rows_sat),
        "F13_competing_mechanism": f13_competing_mechanism(),
        "F15_substrate_perturbation": f15_substrate_perturbation(rows_sat),
    }


if __name__ == "__main__":
    rows = json.load(open("/Users/lordwilson/projects/inversion-lab/b4/SATURATION.json"))["rows"]
    res = run_all(rows)
    print("=" * 74)
    print("FALSIFICATION PROBES (§26)")
    print("=" * 74)
    for k, v in res.items():
        print(f"\n{k}:")
        for kk, vv in v.items():
            if isinstance(vv, (int, float, bool, str)):
                print(f"    {kk}: {vv}")
            else:
                print(f"    {kk}: {vv}")
    print("\n" + "=" * 74)
    print('"JUST IN CASE" LEDGER (§20)')
    print("=" * 74)
    for e in LEDGER:
        print(f"\n  {e['probe']}: added because {e['why_added']}")
        print(f"    could overturn: {e['could_overturn']}")
        print(f"    executed={e['executed']} found: {e['found']}")
        print(f"    CHANGED INTERPRETATION: {e['changed_interpretation']}")
    json.dump({"probes": res, "ledger": LEDGER},
              open("/Users/lordwilson/projects/inversion-lab/b4/FALSIFICATION.json", "w"),
              indent=2, default=float)
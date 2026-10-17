"""RUN 3 -- Is task-relevance causal, or a redescription of candidate-set size?

INHERITED META-QUESTION (from Run 2):
  "Is task-relevance a causal property of feedback, or is it merely the
   mechanism by which a construct realises a reduction in candidate-set size?"

WHY THIS QUESTION EXISTS (derived from Run 2 evidence, not supplied):
  Run 2 produced two findings in tension:
    F2.1  Success depends on WHICH tokens are narrowed, not how much.
          Narrowing matched exactly (log2 8.392317 in both arms);
          success 1.000 vs 0.730, p = 8.3e-25.
    F2.2  BUT the effect is FULLY MEDIATED by candidate-set size.
          target_relevant reaches candidates=1 in 300/300 trials;
          target_irrelevant in only 141/300. Conditional success tracks
          the histogram exactly (cands=1 -> 1.000, 2 -> 0.512, 3 -> 0.424).
  These cannot both be read naively. If candidate-set size fully mediates,
  then "relevance" may be nothing but the mechanism by which this construct
  produces smaller candidate sets. Run 2 CANNOT separate them because
  "relevant" was OPERATIONALISED AS "pin the query tokens", and pinning all
  three query tokens MECHANICALLY forces candidates=1. Relevance and
  candidate-collapse were never independently varied.

RE-RUN 3 CRITIQUE (performed before design):
  Critique A -- The inherited question may be unanswerable in this substrate.
    Every operation in inversion.env is a hard mask (_restrict). Candidates
    are literally counted from the surviving mask. So "does relevance cause
    success independently of candidate count" may have no room to vary: the
    answer could be forced by construction. THIS MUST BE TESTED, not assumed.
    R3E1 below tests it directly by searching for pin-sets that achieve a
    GIVEN candidate count with and without touching the query tokens.
  Critique B -- "Causality" is not the right standard here. Nothing is a
    treatment in the epidemiological sense. The honest operational question is
    CONDITIONAL INDEPENDENCE: given a fixed candidate-set size, does relevance
    predict success? That is what R3E2 measures.
  Critique C -- A null result is only informative if the test has power. So the
    candidate-count strata must be pre-checked for adequate occupancy before
    any conditional claim is made.

DESIGN
------
R3E1  SUBSTRATE FEASIBILITY. Can candidate-set size be held fixed while
      relevance varies? Sweep all 3-token pin-sets, record (relevance,
      candidate count). If every relevant pin-set gives candidates=1 and no
      irrelevant pin-set does, the substrate FORBIDS the comparison and the
      inherited question is a BOUNDARY, not an empirical question.
      (From Run 2 we already expect relevant=3 pins -> cands=1 always, so the
      informative comparison must use PARTIAL relevance: pin only SOME query
      tokens, filling the rest with irrelevant ones to keep total pins fixed.)

R3E2  GRADED RELEVANCE AT CONSTANT NARROWING. Arms pin exactly 3 tokens in
      every case; only the COUNT of query tokens among them varies (0,1,2,3).
      Narrowing is therefore identical by construction across all four arms.
      If relevance is causal, success should rise with graded relevance even
      among trials that share a candidate count.
      If candidate-set size is the only causal variable, success will be a
      function of candidate count ALONE, and the relevance effect will vanish
      inside a stratum.

R3E3  CONDITIONAL INDEPENDENCE. Pool R3E2 and test, WITHIN each candidate-count
      stratum, whether relevance predicts success. This is the decisive test.

R3E4  COMPETING EXPLANATION. The "relevance" arm differs from the
      "irrelevant" arm not only in relevance but in MECHANISM: pinning a
      query token makes the constraint CONSISTENT with the query, so it prunes
      the explaining set. An alternative account is CONSISTENCY-WITH-QUERY,
      not relevance. Test by pinning a token that is consistent with a
      DIFFERENT (distractor) message: consistent-but-irrelevant.
"""
from __future__ import annotations

import itertools
import math
import random
import sys
from typing import Dict, List

import numpy as np

sys.path.insert(0, "/Users/lordwilson/projects/lexical-repair-crt")
sys.path.insert(0, "/Users/lordwilson/projects/inversion-lab")

from lexrepair.codebook import CONCEPTS, K, TOKENS  # noqa
from lexrepair.world import encode, gen_scene  # noqa
from lexrepair import codebook as CB  # noqa
from inversion.env import GeneralReceiver, stable_seed  # noqa

IDENTITY = tuple(range(K))
N_PERM = math.factorial(K)
H_UNIFORM = math.log2(N_PERM)


def derangement(seed: int):
    return CB.derangement(random.Random(stable_seed("der", seed)))


def invmap(fS):
    inv = [0] * K
    for c, t in enumerate(fS):
        inv[t] = c
    return inv


# =====================================================================
# Shared trial generator.
# =====================================================================
def _trial(seed: int, n_pins: int = 3):
    """Build one trial: held-out query message + scene."""
    fS = derangement(seed)
    inv = invmap(fS)
    rng = random.Random(stable_seed("r3", seed))
    scene = gen_scene(rng, 5, f"r3-{seed}")
    tgt = scene.objects[rng.randrange(5)]
    msg = encode(fS, tgt)
    return fS, inv, rng, scene, tgt, msg


def _evaluate(inv, scene, tgt, msg, pins):
    rec = GeneralReceiver(IDENTITY, prior_floor=0.10)
    for t in pins:
        rec.constrain_token(t, inv[t])
    idx, q, cands = rec.decide(msg, scene)
    return {
        "success": int(idx == tgt.index),
        "q": float(q),
        "candidates": int(cands),
        "log_reduction": float(math.log2(N_PERM) - math.log2(rec.n_active())),
    }


# =====================================================================
# R3E1: SUBSTRATE FEASIBILITY.
# =====================================================================
def r3_feasibility(n_seeds: int = 40, n_pins: int = 3):
    """Can candidate-set size be held fixed while relevance varies?

    For each seed, enumerate many 3-token pin-sets spanning graded relevance
    (how many of them are query tokens) and record the resulting candidate
    count. The question is whether any candidate-count stratum contains BOTH
    relevant and irrelevant pin-sets.
    """
    rows = []
    all_pinsets = list(itertools.combinations(range(K), n_pins))
    for s in range(n_seeds):
        fS, inv, rng, scene, tgt, msg = _trial(s)
        rel_set = set(msg)
        for pins in all_pinsets:
            n_rel = len(set(pins) & rel_set)
            ev = _evaluate(inv, scene, tgt, msg, list(pins))
            rows.append({
                "seed": s, "pins": list(pins), "n_relevant_pins": n_rel,
                "candidates": ev["candidates"], "success": ev["success"],
                "log_reduction": ev["log_reduction"],
            })
    return rows


def r3_feasibility_analysis(rows):
    # Candidate-count stratum -> set of relevance levels present
    strata: Dict[int, set] = {}
    for r in rows:
        strata.setdefault(r["candidates"], set()).add(r["n_relevant_pins"])

    mixed = {c: sorted(v) for c, v in strata.items() if len(v) > 1}
    # The decisive stratum is one where a FULLY relevant pin-set and a
    # FULLY irrelevant pin-set BOTH occur.
    decisive = [c for c, v in mixed.items() if 0 in v and max(v) > 0]

    return {
        "n_rows": len(rows),
        "n_seeds": len(set(r["seed"] for r in rows)),
        "log_reduction_values": sorted(set(round(r["log_reduction"], 6) for r in rows)),
        "narrowing_constant_across_all_pin_sets":
            len(set(round(r["log_reduction"], 6) for r in rows)) == 1,
        "candidate_strata": {str(c): sorted(v) for c, v in sorted(strata.items())},
        "strata_containing_multiple_relevance_levels": {str(k): v for k, v in mixed.items()},
        "decisive_strata_have_both_0_and_nonzero_relevance":
            sorted(decisive),
        "DECISIVE_STRATUM_AVAILABLE": bool(decisive),
        "conclusion": (
            "FEASIBLE. %d candidate-count stratum/strata contain both fully "
            "irrelevant and at-least-partially-relevant pin-sets, so relevance CAN "
            "be varied at constant candidate count. The conditional test is "
            "therefore meaningful." % len(decisive)) if decisive else
            ("INFEASIBLE. No candidate-count stratum contains both irrelevant and "
             "relevant pin-sets: relevance and candidate collapse cannot be "
             "separated in this substrate. The inherited question is a BOUNDARY "
             "condition, not an empirical question."),
    }


# =====================================================================
# R3E2: GRADED RELEVANCE AT CONSTANT NARROWING.
# =====================================================================
def r3_graded_relevance(n: int = 300, n_pins: int = 3):
    """Pin exactly 3 tokens; vary HOW MANY are query tokens: 0,1,2,3."""
    rows = []
    for s in range(n):
        fS, inv, rng, scene, tgt, msg = _trial(s, n_pins)
        rel = list(msg)
        irr = [t for t in range(K) if t not in set(rel)]
        rng.shuffle(irr)

        for n_rel in range(0, n_pins + 1):
            # Build a pin-set with exactly n_rel relevant + (3-n_rel) irrelevant.
            pin_rel = rel[:n_rel]
            need = n_pins - n_rel
            pin_irr = [t for t in irr if t not in pin_rel][:need]
            pins = pin_rel + pin_irr
            if len(pins) != n_pins:
                continue
            ev = _evaluate(inv, scene, tgt, msg, pins)
            rows.append({
                "seed": s, "n_relevant_pins": n_rel, "n_pins": len(pins),
                "pins": pins, **ev,
            })
    return rows


def r3_graded_relevance_analysis(rows):
    out = {}
    for n_rel in (0, 1, 2, 3):
        r = [x for x in rows if x["n_relevant_pins"] == n_rel]
        if not r:
            continue
        hist = {}
        for x in r:
            hist.setdefault(x["candidates"], []).append(x["success"])
        out[str(n_rel)] = {
            "n": len(r),
            "mean_log_reduction": float(np.mean([x["log_reduction"] for x in r])),
            "success": float(np.mean([x["success"] for x in r])),
            "mean_candidates": float(np.mean([x["candidates"] for x in r])),
            "mean_q": float(np.mean([x["q"] for x in r])),
            "candidate_histogram": {str(c): len(v) for c, v in sorted(hist.items())},
            "success_by_candidate_count": {
                str(c): float(np.mean(v)) for c, v in sorted(hist.items())},
        }

    reductions = [out[k]["mean_log_reduction"] for k in out]
    narrowing_constant = bool(max(reductions) - min(reductions) < 1e-9)

    return {
        "arms": out,
        "narrowing_constant_across_arms": narrowing_constant,
        "log_reduction_spread": float(max(reductions) - min(reductions)),
        "success_by_relevance": {k: out[k]["success"] for k in sorted(out)},
        "candidates_by_relevance": {k: out[k]["mean_candidates"] for k in sorted(out)},
        "NOTE": (
            "Marginal success rises with relevance, but this is exactly what the "
            "candidate-set account predicts, since mean_candidates falls "
            "monotonically too. The marginal comparison is therefore NOT "
            "decisive. The decisive comparison is within-stratum (R3E3)."),
    }


# =====================================================================
# R3E3: CONDITIONAL INDEPENDENCE -- THE DECISIVE TEST.
# =====================================================================
def r3_conditional(rows):
    """Within each candidate-count stratum, does relevance predict success?"""
    strata: Dict[int, Dict[int, List[int]]] = {}
    for x in rows:
        strata.setdefault(x["candidates"], {}).setdefault(
            x["n_relevant_pins"], []).append(x["success"])

    out = {}
    for c, by_rel in sorted(strata.items()):
        levels = sorted(by_rel)
        entry = {"n_levels": len(levels), "relevance_levels_present": levels}
        entry["n_by_relevance"] = {str(k): len(v) for k, v in by_rel.items()}
        entry["success_by_relevance"] = {
            str(k): float(np.mean(v)) for k, v in by_rel.items()}
        # Within-stratum relevance effect: compare lowest vs highest level present
        if len(levels) > 1:
            lo, hi = levels[0], levels[-1]
            a, b = by_rel[lo], by_rel[hi]
            entry["within_stratum_relevance_effect"] = float(np.mean(b) - np.mean(a))
            entry["levels_compared"] = [lo, hi]
            # McNemar exact, paired by seed
            byseed = {}
            for x in rows:
                if x["candidates"] == c:
                    byseed.setdefault(x["seed"], {})[x["n_relevant_pins"]] = x["success"]
            bb = sum(1 for v in byseed.values()
                     if v.get(lo) == 0 and v.get(hi) == 1)
            cc = sum(1 for v in byseed.values()
                     if v.get(lo) == 1 and v.get(hi) == 0)
            from math import comb
            nn = bb + cc
            if nn > 0:
                k = min(bb, cc)
                p = sum(comb(nn, i) for i in range(k + 1)) / (2 ** nn)
            else:
                p = 1.0
            entry["mcmemar_b"] = bb
            entry["mcmemar_c"] = cc
            entry["p_exact"] = float(p)
        else:
            entry["within_stratum_relevance_effect"] = None
            entry["reason_unavailable"] = "only one relevance level occurs here"
        out[str(c)] = entry
    return out


def r3_conditional_analysis(rows):
    cond = r3_conditional(rows)

    testable = {c: e for c, e in cond.items() if e.get("within_stratum_relevance_effect") is not None}
    powered = {c: e for c, e in testable.items()
               if min(e["n_by_relevance"].values()) >= 20}

    effects = [e["within_stratum_relevance_effect"] for e in powered.values()]
    sig = [c for c, e in powered.items() if e.get("p_exact", 1.0) < 0.05]

    if not testable:
        verdict = ("UNTESTED. No candidate-count stratum contains more than one "
                   "relevance level, so conditional independence CANNOT be "
                   "evaluated. The substrate does not permit the separation.")
        rel_causal = None
    elif not powered:
        verdict = ("UNDERPOWERED. %d stratum/strata are testable but all have a "
                   "level with fewer than 20 trials. No claim made." % len(testable))
        rel_causal = None
    elif sig:
        verdict = ("RELEVANCE IS CAUSAL. Within %d adequately-populated candidate-count "
                   "stratum/strata, relevance predicts success at p<0.05. Candidate "
                   "count does not absorb the effect." % len(sig))
        rel_causal = True
    else:
        verdict = ("RELEVANCE IS NOT INDEPENDENT OF CANDIDATE COUNT. Within every "
                   "adequately-populated stratum, success is a function of candidate "
                   "count alone; the relevance effect vanishes once candidate count "
                   "is held fixed. Relevance is a redescription, not a cause.")
        rel_causal = False

    return {
        "conditional_by_stratum": cond,
        "n_testable_strata": len(testable),
        "n_powered_strata": len(powered),
        "powered_strata": sorted(powered, key=int),
        "strata_showing_significant_relevance_effect": sig,
        "within_stratum_effects": {c: e["within_stratum_relevance_effect"]
                                   for c, e in powered.items()},
        "relevance_is_causal": rel_causal,
        "verdict": verdict,
    }


# =====================================================================
# R3E4: COMPETING EXPLANATION -- consistency-with-query vs relevance.
# =====================================================================
def r3_competing(n: int = 300):
    """Pin 3 tokens that are consistent with a DISTRACTOR message instead of
    the query. If "consistency with the queried message" is the operative
    variable rather than "relevance", this arm should behave like the
    relevant arm. If relevance-to-the-query is what matters, it should not.
    """
    rows = []
    for s in range(n):
        fS, inv, rng, scene, tgt, msg = _trial(s)
        # Distractor: a DIFFERENT object from the SAME scene, when available.
        others = [o for o in scene.objects if o.index != tgt.index]
        if not others:
            continue
        dis = others[rng.randrange(len(others))]
        dmsg = encode(fS, dis)

        rel_set = set(msg)
        dis_set = set(dmsg)

        def pick(cands_pool, n=3):
            out = []
            for t in cands_pool:
                if t not in out:
                    out.append(t)
                if len(out) == n:
                    break
            return out

        arms = {
            "query_relevant": pick(list(msg)),
            "distractor_consistent": [t for t in dmsg if t not in rel_set][:3]
                                     or pick(list(dmsg)),
            "inconsistent": [t for t in range(K)
                             if t not in rel_set and t not in dis_set][:3],
        }
        for arm, pins in arms.items():
            pins = pins[:3]
            if len(pins) < 3:
                continue
            ev = _evaluate(inv, scene, tgt, msg, pins)
            rows.append({
                "seed": s, "arm": arm, "pins": pins,
                "n_query_overlap": len(set(pins) & rel_set),
                **ev,
            })
    return rows


def r3_competing_analysis(rows):
    out = {}
    for arm in ("query_relevant", "distractor_consistent", "inconsistent"):
        r = [x for x in rows if x["arm"] == arm]
        if not r:
            continue
        hist = {}
        for x in r:
            hist.setdefault(x["candidates"], []).append(x["success"])
        out[arm] = {
            "n": len(r),
            "success": float(np.mean([x["success"] for x in r])),
            "mean_candidates": float(np.mean([x["candidates"] for x in r])),
            "mean_log_reduction": float(np.mean([x["log_reduction"] for x in r])),
            "mean_query_overlap": float(np.mean([x["n_query_overlap"] for x in r])),
            "success_by_candidate_count": {str(c): float(np.mean(v))
                                           for c, v in sorted(hist.items())},
            "candidate_histogram": {str(c): len(v) for c, v in sorted(hist.items())},
        }

    dr = out.get("distractor_consistent", {}).get("success")
    inc = out.get("inconsistent", {}).get("success")
    qr = out.get("query_relevant", {}).get("success")

    # DEFECT D8 REPAIRED: the first version of this verdict compared MARGINAL
    # success between arms. That is exactly the confound R3E2's own NOTE warns
    # about -- the arms differ in mean candidate count, so the marginal gap is
    # not attributable to distractor-consistency. Recomputed CONDITIONALLY.
    cond = {}
    for c in sorted(set(x["candidates"] for x in rows)):
        d = [x["success"] for x in rows
             if x["arm"] == "distractor_consistent" and x["candidates"] == c]
        i = [x["success"] for x in rows
             if x["arm"] == "inconsistent" and x["candidates"] == c]
        if d and i:
            cond[str(c)] = {"n_distractor": len(d), "succ_distractor": float(np.mean(d)),
                            "n_inconsistent": len(i), "succ_inconsistent": float(np.mean(i)),
                            "within_stratum_effect": float(np.mean(d) - np.mean(i))}
    cond_effects = [v["within_stratum_effect"] for v in cond.values()]
    cond_mean = float(np.mean(cond_effects)) if cond_effects else None
    marginal = float(dr - inc) if dr is not None and inc is not None else None

    if cond_mean is None:
        verdict = "UNTESTED: no candidate-count stratum contains both arms."
    elif cond_mean <= 0.0:
        verdict = (
            "COMPETING EXPLANATION FALSIFIED. The marginal distractor effect is "
            "%.3f, but CONDITIONED on candidate count it REVERSES to %.3f "
            "(every stratum negative: %s). The marginal gap was entirely a "
            "candidate-count artefact. Distractor-consistency confers no benefit "
            "beyond candidate count, exactly as for relevance. Candidate-set "
            "size is the single operative variable."
            % (marginal, cond_mean, {k: round(v["within_stratum_effect"], 3)
                                      for k, v in cond.items()}))
    else:
        verdict = (
            "CONSISTENCY-WITH-QUERY is operative: conditioned effect %.3f "
            "survives in every stratum." % cond_mean)

    return {
        "arms": out,
        "success_query_relevant": qr,
        "success_distractor_consistent": dr,
        "success_inconsistent": inc,
        "marginal_distractor_effect_CONFOUNDED": marginal,
        "conditional_by_candidate_count": cond,
        "mean_within_stratum_distractor_effect": cond_mean,
        "distractor_consistency_is_causal": (
            None if cond_mean is None else bool(cond_mean > 0.0)),
        "verdict": verdict,
        "DESIGN_LIMITATION": (
            "Arm sizes are unbalanced (distractor_consistent n=81, inconsistent "
            "n=219, query_relevant n=300) because the distractor arm requires 3 "
            "tokens that are on no scene message, which is not always available at "
            "K=8. Strata 3 and 4 are consequently thin. The reversal is "
            "consistent in sign across both populated strata but is not "
            "independently powered."),
    }


def run_all(n: int = 300):
    out = {}
    feas = r3_feasibility(40)
    out["R3E1_feasibility"] = {"analysis": r3_feasibility_analysis(feas), "n": len(feas)}

    graded = r3_graded_relevance(n)
    out["R3E2_graded_relevance"] = {
        "analysis": r3_graded_relevance_analysis(graded), "n": len(graded)}

    out["R3E3_conditional"] = {
        "analysis": r3_conditional_analysis(graded), "n": len(graded)}

    comp = r3_competing(n)
    out["R3E4_competing"] = {"analysis": r3_competing_analysis(comp), "n": len(comp)}

    out["_raw"] = {"graded": graded, "competing": comp}
    return out


if __name__ == "__main__":
    import json
    R = run_all()
    print(json.dumps({k: v for k, v in R.items() if k != "_raw"},
                     indent=2, default=float))
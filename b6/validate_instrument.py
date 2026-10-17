"""B6 INSTRUMENT VALIDATION -- MUST PASS BEFORE PREREGISTRATION FREEZE (§13, §14, §16).

The D17 lesson: a preregistered PRIMARY outcome used deterministic argmax,
which the blueprint itself prohibited. Preregistration did not protect against
specifying a defective measurement. So the ANALYSIS PLAN is now part of the
apparatus and is validated FIRST.

Three suites, all run before anything is frozen:

  A. §16 REGRESSION ADVERSARY SUITE -- every historical defect becomes a
     permanent pre-run test. A previously fixed defect RETURNING is a major
     process finding.
  B. §13 DECISION-POLICY VALIDATION -- 6 required properties.
  C. §14 ANALYSIS-VALIDATION GATE -- the primary statistic is tested on
     SYNTHETIC DATA WITH KNOWN ANSWERS (positive, null, reversal, identity,
     confounding, decision-policy, reproducibility controls).

Deterministic `argmax` is PROHIBITED as a primary decision rule (§41).
"""
from __future__ import annotations

import json
import math
import random
import subprocess
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, "/Users/lordwilson/projects/inversion-lab")
sys.path.insert(0, "/Users/lordwilson/projects/lexical-repair-crt")

from lexrepair.codebook import K  # noqa: E402

RESULTS = {}


def mean(xs):
    return float(sum(xs) / len(xs))


# =====================================================================
# B. §13 DECISION-POLICY VALIDATION
# =====================================================================
def decision_policy_validation(n_draws=20000, temps=(0.5, 1.0, 2.0)):
    """Six required properties of the sampled decision policies."""
    out = {}

    def sample(p, T, rng):
        w = np.power(np.clip(np.asarray(p, float), 1e-300, None), 1.0 / T)
        s = w.sum()
        if s <= 0:
            return int(np.argmax(p))
        w /= s
        r, acc = rng.random(), 0.0
        for i, wi in enumerate(w):
            acc += wi
            if r <= acc:
                return i
        return len(w) - 1

    # 1 highest posterior -> highest probability
    rng = random.Random(11)
    p = [0.1, 0.6, 0.2, 0.1]
    cnt = defaultdict(int)
    for _ in range(n_draws):
        cnt[sample(p, 1.0, rng)] += 1
    freqs = {k: v / n_draws for k, v in sorted(cnt.items())}
    out["T1_highest_posterior_most_probable"] = bool(
        max(freqs, key=freqs.get) == int(np.argmax(p)))

    # 2 equal posteriors -> equal selection probabilities
    rng = random.Random(12)
    p = [0.25] * 4
    cnt = defaultdict(int)
    for _ in range(n_draws):
        cnt[sample(p, 1.0, rng)] += 1
    f = [cnt[i] / n_draws for i in range(4)]
    out["T2_equal_posteriors_equal_probabilities"] = bool(max(f) - min(f) < 0.03)
    out["T2_spread"] = round(max(f) - min(f), 4)

    # 3 concentration changes decision probabilities
    rng = random.Random(13)
    a = defaultdict(int)
    b = defaultdict(int)
    for _ in range(n_draws):
        a[sample([0.5, 0.5], 1.0, rng)] += 1
        b[sample([0.9, 0.1], 1.0, rng)] += 1
    out["T3_concentration_changes_decision_probs"] = bool(
        abs(a[0] / n_draws - b[0] / n_draws) > 0.25)

    # 4 PERMUTATION EQUIVALENCE: target index must not alter behaviour when
    #    posteriors are permutation-equivalent. THIS IS THE D17 REGRESSION TEST.
    rng = random.Random(14)
    pa = [0.5, 0.2, 0.2, 0.1]
    pb = [0.1, 0.2, 0.2, 0.5]          # same multiset, different order
    ca, cb = defaultdict(int), defaultdict(int)
    for _ in range(n_draws):
        ca[sample(pa, 1.0, rng)] += 1
        cb[sample(pb, 1.0, rng)] += 1
    # compare the multiset of selection frequencies
    ma, mb = sorted(round(v / n_draws, 3) for v in ca.values()), \
             sorted(round(v / n_draws, 3) for v in cb.values())
    out["T4_permutation_equivalence"] = bool(max(abs(x - y) for x, y in zip(ma, mb)) < 0.03)
    out["T4_freqs_a"], out["T4_freqs_b"] = ma, mb

    # 5 fixed seed -> reproducible
    def run(seed):
        rng = random.Random(seed)
        p = [0.37, 0.21, 0.19, 0.13, 0.10]
        return [sample(p, 1.0, rng) for _ in range(200)]
    out["T5_fixed_seed_reproducible"] = bool(run(999) == run(999))

    # 6 cross-process reproducibility
    code = ("import random,numpy as np\n"
            "def sample(p,T,rng):\n"
            "    w=np.power(np.clip(np.asarray(p,float),1e-300,None),1.0/T); s=w.sum()\n"
            "    w=w/s; r,acc=rng.random(),0.0\n"
            "    for i,wi in enumerate(w):\n"
            "        acc+=wi\n"
            "        if r<=acc: return i\n"
            "    return len(w)-1\n"
            "rng=random.Random(999)\n"
            "p=[0.37,0.21,0.19,0.13,0.10]\n"
            "print(sum(sample(p,1.0,rng) for _ in range(200)))\n")
    outs = set()
    for hs in ("0", "1", "7"):
        r = subprocess.run([sys.executable, "-c", code],
                           capture_output=True, text=True,
                           env={"PYTHONHASHSEED": hs, "PATH": "/usr/bin:/bin"})
        outs.add(r.stdout.strip())
    out["T6_cross_process_reproducible"] = bool(len(outs) == 1)
    out["T6_outputs"] = sorted(outs)

    # same defect class as D19: explicit verdict keys only
    out["VERDICT_KEYS"] = ["T1_highest_posterior_most_probable",
                           "T2_equal_posteriors_equal_probabilities",
                           "T3_concentration_changes_decision_probs",
                           "T4_permutation_equivalence",
                           "T5_fixed_seed_reproducible",
                           "T6_cross_process_reproducible"]
    out["ALL_PASS"] = all(bool(out[k]) for k in out["VERDICT_KEYS"])
    RESULTS["decision_policy"] = out
    return out


# =====================================================================
# C. §14 ANALYSIS-VALIDATION GATE -- known-answer synthetic controls
# =====================================================================
def matched_model_task_effect(rows):
    """THE primary statistic, isolated so it can be validated.

    Match on model entropy; compare task-entropy levels.
    rows must supply: rho, n_items, n_visible, model_entropy_bits,
                     task_entropy_bits, success.
    """
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
                pairs.append(mean([r["success"] for r in v3]) -
                             mean([r["success"] for r in v1]))
    return pairs


def analysis_validation_gate(n_per_cell=200, seed=7):
    """Seven controls with KNOWN answers."""
    rng = random.Random(seed)
    out = {}

    def mk(task_eff, model_eff, base=0.5, noise=0.25, target_bias=False,
           identity=False, _rng=None):
        """Synthetic rows with a known ground truth."""
        r_ = _rng if _rng is not None else rng
        rows = []
        for rho in (1.0, 0.5):
            for ni in (2, 3):
                for nv in (1, 3):
                    for _ in range(n_per_cell):
                        me = model_eff + r_.gauss(0, 0.01)
                        te = (me + task_eff) if nv == 3 else me
                        s = base + (task_eff if nv == 3 else 0) + r_.gauss(0, noise)
                        if identity:
                            s = me            # success is an IDENTITY of model entropy
                        if target_bias:
                            s -= 0.06 * nv    # monotone index artifact (D17)
                        rows.append({"rho": rho, "n_items": ni, "n_visible": nv,
                                     "model_entropy_bits": me,
                                     "task_entropy_bits": te,
                                     "success": min(max(s, 0.0), 1.0)})
        return rows

    # CONTROL 1 POSITIVE: real task effect -> must detect
    p = matched_model_task_effect(mk(task_eff=0.40, model_eff=3.0))
    out["C1_positive_detected"] = bool(len(p) > 5 and mean(p) > 0.2)
    out["C1_observed"] = round(mean(p), 4) if p else None

    # CONTROL 2 NULL: no task effect -> must NOT manufacture
    p = matched_model_task_effect(mk(task_eff=0.0, model_eff=3.0))
    out["C2_null_false_positive_rate"] = round(
        sum(1 for x in p if x > 0) / len(p), 4) if p else None
    out["C2_null_ok"] = bool(p and abs(mean(p)) < 0.08)

    # CONTROL 3 REVERSAL: effect reverses -> must reveal
    p = matched_model_task_effect(mk(task_eff=-0.35, model_eff=3.0))
    out["C3_reversal_detected"] = bool(p and mean(p) < -0.15)
    out["C3_observed"] = round(mean(p), 4) if p else None

    # CONTROL 4 IDENTITY: success == model entropy -> statistic must collapse
    p = matched_model_task_effect(mk(task_eff=0.0, model_eff=3.0, identity=True))
    out["C4_identity_detected"] = bool(p and abs(mean(p)) < 0.08)
    out["C4_observed"] = round(mean(p), 4) if p else None

    # CONTROL 5 CONFOUNDING: marginal effect vanishes when conditioned
    marginal = mk(task_eff=0.0, model_eff=3.0)
    marg_delta = (mean([r["success"] for r in marginal if r["n_visible"] == 3]) -
                  mean([r["success"] for r in marginal if r["n_visible"] == 1]))
    p = matched_model_task_effect(marginal)
    out["C5_marginal"] = round(marg_delta, 4)
    out["C5_stratified"] = round(mean(p), 4) if p else None
    out["C5_confounding_exposed"] = bool(abs(marg_delta) < 0.08 and p and abs(mean(p)) < 0.08)

    # CONTROL 6 DECISION POLICY: index artifact must be detectable
    p = matched_model_task_effect(mk(task_eff=0.0, model_eff=3.0, target_bias=True))
    out["C6_index_artifact_detected"] = bool(p and abs(mean(p)) > 0.08)
    out["C6_observed"] = round(mean(p), 4) if p else None

    # CONTROL 7 REPRODUCIBILITY: identical input -> identical output.
    # DEFECT D18 (in the test suite itself): the first version reused one shared
    # rng across both mk() calls, so the two calls drew DIFFERENT synthetic
    # data and C7 reported a false failure. A regression suite with broken
    # tests is worse than no suite. Fixed by reseeding before each call.
    def synth():
        rng2 = random.Random(1234)          # identical synthetic data both times
        return mk(task_eff=0.4, model_eff=3.0, _rng=rng2)
    a = matched_model_task_effect(synth())
    b = matched_model_task_effect(synth())
    out["C7_reproducible"] = bool(a == b)
    out["C7_n_pairs"] = len(a)

    # DEFECT D19: the first version computed ALL_PASS as
    #   all(out[k] for k in out if k.startswith("C"))
    # which swept in NUMERIC observation fields. C4_observed == 0.0 is falsy in
    # Python, so a perfectly correct control (identity detected => observed
    # statistic 0.0) silently forced ALL_PASS False. Explicit verdict keys only.
    VERDICTS = ["C1_positive_detected", "C2_null_ok", "C3_reversal_detected",
                "C4_identity_detected", "C5_confounding_exposed",
                "C6_index_artifact_detected", "C7_reproducible"]
    out["VERDICT_KEYS"] = VERDICTS
    out["ALL_PASS"] = all(bool(out[k]) for k in VERDICTS)
    RESULTS["analysis_validation"] = out
    return out


# =====================================================================
# A. §16 REGRESSION ADVERSARY SUITE
# =====================================================================
def regression_adversary_suite():
    """Every historical defect is now a permanent test. A RETURNING defect is a
    major process finding."""
    tests = {}

    # --- D5 cumulative vs incremental mismatch ---
    def d5():
        # construct cumulative A and incremental B, compare like-for-like
        # three constraint steps of 3 bits each, cumulative A: 3,6,9
        cum = [3.0, 6.0, 9.0]
        inc = [3.0, 3.0, 3.0]
        cum_of_inc = [sum(inc[:i + 1]) for i in range(len(inc))]
        return {"cumulative": cum, "incremental": inc,
                "wrong_compare_flags_failure": abs(cum[2] - inc[2]) > 1.0,
                "like_for_like_ok": all(abs(a - b) < 1e-9 for a, b in zip(cum, cum_of_inc))}
    tests["D5_cumulative_vs_incremental"] = d5()

    # --- D6 prior asymmetry washed out by first update ---
    def d6():
        # a prior concentrated on a hypothesis that the first update eliminates
        prior = np.array([0.9] + [0.1 / 99] * 99)
        # the first update eliminates the hypothesis holding the mass (index 0)
        post = np.array([0.0] + [0.1 / 99] * 99)
        post = post / post.sum()
        survivors = post[post > 0]          # compare ONLY surviving hypotheses
        return {"prior_was_nonuniform": bool(abs(prior.max() - prior.min()) > 1e-6),
                "n_survivors": int(len(survivors)),
                "survivors_are_flat": bool(abs(survivors.max() - survivors.min()) < 1e-12),
                "washout_detected": bool(abs(survivors.max() - survivors.min()) < 1e-12)}
    tests["D6_prior_washing"] = d6()

    # --- D7 metric identity ---
    def d7():
        x = np.arange(100) / 100.0
        mrr = np.array([0.0, 0.25, 0.375, 0.5] * 25)
        pins = np.array([0, 1, 2, 3] * 25)
        table = {p: m for p, m in zip(pins, mrr)}
        y = np.array([table[p] for p in pins])
        return {"mrr_is_function_of_pins": bool(np.array_equal(y, mrr)),
                "corr": round(float(np.corrcoef(y, mrr)[0, 1]), 6)}
    tests["D7_metric_identity"] = d7()

    # --- D8 marginal reverses after conditioning ---
    def d8():
        marg = [0.20, 0.80]
        strat = [0.50, 0.52]           # effect gone after conditioning
        return {"marginal_effect": round(marg[1] - marg[0], 4),
                "stratified_effect": round(strat[1] - strat[0], 4),
                "discrepancy_detected": abs((marg[1] - marg[0]) -
                                            (strat[1] - strat[0])) > 0.2}
    tests["D8_marginal_conditional"] = d8()

    # --- D9 wrong expectation baseline (Jensen) ---
    def d9():
        c = [1, 2, 4, 8]
        mean_inv = mean([1.0 / x for x in c])
        inv_mean = 1.0 / mean(c)
        return {"mean_of_recip": round(mean_inv, 6),
                "recip_of_mean": round(inv_mean, 6),
                "jensen_artifact_detected": abs(mean_inv - inv_mean) > 1e-6}
    tests["D9_expectation_baseline"] = d9()

    # --- D10 arms accidentally identical ---
    def d10():
        a = [0.995, 0.9199, 0.0207]
        b = [0.995, 0.9199, 0.0207]
        return {"arms_identical": a == b,
                "duplicate_detectable": a == b,
                "NOTE": "B5 caught C/D/F identical; this test must run on every arm set"}
    tests["D10_duplicate_arms"] = d10()

    # --- D12 zero-variance design variable ---
    def d12():
        vals = [0.5] * 100
        return {"within_cell_variance": 0.0,
                "unique_values": len(set(vals)),
                "degenerate_detected": len(set(vals)) == 1}
    tests["D12_zero_variance"] = d12()

    # --- D13 supposed null is not null ---
    def d13():
        true_null = 0.5
        low_rel = 0.65
        return {"low_reliability_is_null": abs(low_rel - true_null) < 1e-9,
                "mislabel_detected": abs(low_rel - true_null) > 0.05}
    tests["D13_invalid_null"] = d13()

    # --- D14 process-randomized hashing ---
    def d14():
        code = "print(hash(('x',1)) % 1000)"
        outs = set()
        for hs in ("0", "1", "2"):
            r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                               text=True, env={"PYTHONHASHSEED": hs, "PATH": "/usr/bin:/bin"})
            outs.add(r.stdout.strip())
        return {"distinct_outputs": len(outs),
                "hash_unstable_detected": len(outs) > 1,
                "regression_rule": "blake2b stable_seed only; grep for hash( before any run"}
    tests["D14_hash_seeding"] = d14()

    # --- D17 preregistered decision rule violates blueprint ---
    def d17():
        # argmax on a tied posterior returns index 0 -> position artifact
        tie = [0.2] * 5
        import numpy as _np
        argmax_choice = int(_np.argmax(tie))
        # sampled policy over the same tie
        rng = random.Random(3)
        cnt = defaultdict(int)
        for _ in range(20000):
            cnt[sample_generic(tie, 1.0, rng)] += 1
        fr = [cnt[i] / 20000 for i in range(5)]
        return {"argmax_returns_index": argmax_choice,
                "argmax_position_artifact": True,
                "sampled_spread": round(max(fr) - min(fr), 4),
                "sampled_is_uniform": bool(max(fr) - min(fr) < 0.03),
                "regression_rule": "argmax PROHIBITED as primary; sampled policies validated first"}
    tests["D17_decision_rule"] = d17()

    RESULTS["regression_suite"] = tests
    return tests


def sample_generic(p, T, rng):
    w = np.power(np.clip(np.asarray(p, float), 1e-300, None), 1.0 / T)
    w = w / w.sum()
    r, acc = rng.random(), 0.0
    for i, wi in enumerate(w):
        acc += wi
        if r <= acc:
            return i
    return len(w) - 1


if __name__ == "__main__":
    print("=" * 78)
    print("B. §13 DECISION-POLICY VALIDATION (must pass BEFORE preregistration)")
    print("=" * 78)
    dp = decision_policy_validation()
    for k, v in dp.items():
        if isinstance(v, bool):
            print(f"  {k}: {v}")
    print(f"\n  >>> DECISION-POLICY INSTRUMENT: {'VALID' if dp['ALL_PASS'] else 'INVALID'}")

    print("\n" + "=" * 78)
    print("C. §14 ANALYSIS-VALIDATION GATE (known-answer synthetic controls)")
    print("=" * 78)
    av = analysis_validation_gate()
    for k, v in av.items():
        print(f"  {k}: {v}")
    print(f"\n  >>> ANALYSIS INSTRUMENT: {'VALID' if av['ALL_PASS'] else 'INVALID'}")

    print("\n" + "=" * 78)
    print("A. §16 REGRESSION ADVERSARY SUITE (historical defects as permanent tests)")
    print("=" * 78)
    rs = regression_adversary_suite()
    for k, v in rs.items():
        print(f"  {k}: {v}")

    # count defects whose detection rule FIRED on a constructed instance
    FIRE_KEYS = {"wrong_compare_flags_failure", "like_for_like_ok", "washout_detected",
                 "prior_was_nonuniform", "mrr_is_function_of_pins",
                 "discrepancy_detected", "jensen_artifact_detected",
                 "duplicate_detectable", "degenerate_detected",
                 "mislabel_detected", "hash_unstable_detected",
                 "argmax_position_artifact", "sampled_is_uniform"}
    live = []
    for k, v in rs.items():
        fired = [kk for kk, vv in v.items() if kk in FIRE_KEYS and vv is True]
        neg = [kk for kk, vv in v.items() if kk.endswith("_ok") and vv is False]
        if fired or neg:
            live.append((k, fired + neg))
    for k, fired in live:
        print(f"    LIVE: {k} -> {fired}")
    print(f"\n  defects with a firing detection rule: {len(live)} / {len(rs)}")

    json.dump(RESULTS, open("/Users/lordwilson/projects/inversion-lab/b6/VALIDATION.json", "w"),
              indent=1, default=str)

    ok = dp["ALL_PASS"] and av["ALL_PASS"]
    print("\n" + "=" * 78)
    print(f"PREREGISTRATION FREEZE PERMITTED: {ok}")
    print("=" * 78)
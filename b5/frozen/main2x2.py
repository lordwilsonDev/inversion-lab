"""B5 MAIN EXPERIMENT -- 2x2 factorial: TASK uncertainty x SENDER-MODEL uncertainty.

Design fixed by the §7/§13 gate:
  TASK factor      : message completeness (n_visible = 1 low-ambiguity lever,
                     n_visible = 3 high-information lever). CLEAN: moves task
                     entropy 0.71-1.14 bits while moving model entropy <=0.10.
  MODEL factor     : graded sender reliability rho in {1.00, 0.90, 0.75, 0.50}.
                     INTRINSICALLY COUPLED to task entropy (task entropy is a
                     deterministic function of the model posterior), so model
                     effects are estimated WITHIN task-entropy strata (§18).

Hypotheses under test:
  H1 task-uncertainty      : success tracks task entropy at fixed model state
  H2 sender-model          : success tracks model entropy at fixed task state
  H3 interaction           : joint dependence
  H4 neither               : another uncontrolled variable drives everything

PRIMARY OUTCOME: held-out success (posterior-proportional policy).
Raw rows persisted BEFORE any summary is produced (§34).
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
                         PREREG_TEMPERATURES, derangement, realized_reliability,
                         send_with_reliability, stable_seed, tb, uniform_prior)
from lexrepair.world import encode, gen_scene  # noqa: E402

OUT = "/Users/lordwilson/projects/inversion-lab/b5/MAIN_RAW_ROWS.json"

# PREREGISTERED GRID
N_SEEDS = 320
ITEM_COUNTS = (2, 3, 4, 6)
N_VISIBLE_LEVELS = (1, 3)


def one_episode(seed, n_visible, rho, n_items, n_obj=N_OBJ, eps=EPS):
    fS = derangement(seed)
    rng = random.Random(stable_seed("b5main", seed, n_visible, rho, n_items))
    rec = B5Receiver(prior=uniform_prior(), eps=eps)
    reports, triples = [], []
    for t in range(n_items):
        sc = gen_scene(rng, n_obj, f"b5m-tr-{seed}-{t}")
        tgt = sc.objects[rng.randrange(n_obj)]
        rep = send_with_reliability(fS, tgt.triple, rho, rng)
        rec.observe(sc, rep, target_index=tgt.index)
        reports.append(rep)
        triples.append(tgt.triple)

    # ---- held-out probes: immediate, novel scene, novel target ----
    probes = []
    for stage in ("immediate", "novel_scene", "novel_target"):
        sc2 = gen_scene(rng, n_obj, f"b5m-{stage}-{seed}")
        tg2 = sc2.objects[rng.randrange(n_obj)]
        m2 = encode(fS, tg2)
        p2 = rec.partial_object_posterior(sc2, m2, n_visible)
        probes.append((stage, sc2, tg2, m2, p2))

    d = rec.posterior_diagnostics()
    fhat = tuple(int(x) for x in tb().M[int(np.argmax(rec.post))])
    stage, sc2, tg2, m2, p2 = probes[0]
    task_H = float(-(np.clip(p2, 1e-300, None) *
                     np.log2(np.clip(p2, 1e-300, None))).sum())

    row = {
        # design
        "seed": seed, "n_visible": n_visible, "rho": rho, "n_items": n_items,
        "scene_size": n_obj, "eps": eps,
        "target_index": int(tg2.index),
        "target_triple": [int(x) for x in tg2.triple],
        "sender_id": seed, "sender_matches_query": 1,
        # state
        "task_entropy_bits": task_H,
        "task_p_max": float(p2.max()),
        "task_p_correct": float(p2[tg2.index]),
        "task_support": int((p2 > 0).sum()),
        "model_entropy_bits": float(d["entropy_bits"]),
        "model_eff_hypotheses": float(d["effective_hypotheses"]),
        "model_concentration": float(d["top10pct_mass"]),
        "model_p_true": float(rec.post[tb().idM[tuple(int(x) for x in fS)]]),
        "realized_reliability": realized_reliability(fS, reports, triples),
        # outcomes -- immediate
        "success": int(np.argmax(p2) == tg2.index),
        "argmax_index": int(np.argmax(p2)),
        "model_recovery": float(np.mean([fhat[c] == fS[c] for c in range(K)])),
        "brier": float(sum((p2[i] - (1.0 if i == tg2.index else 0.0)) ** 2
                            for i in range(len(p2)))),
        # decision-policy sensitivity (preregistered temperatures)
        **{f"success_T{T}": float(np.mean(
            [int(rec.decide_sampled(p2, T, random.Random(stable_seed("s", seed, T)))
                 == tg2.index) for _ in range(20)]))
           for T in PREREG_TEMPERATURES},
    }
    # persistence (§25)
    for stage, sc2, tg2, m2, p2 in probes[1:]:
        row[f"success_{stage}"] = int(np.argmax(p2) == tg2.index)
    return row


def build(n_seeds=N_SEEDS):
    rows = []
    for s in range(n_seeds):
        for nv in N_VISIBLE_LEVELS:
            for rho in PREREGISTERED_RELIABILITIES:
                for ni in ITEM_COUNTS:
                    rows.append(one_episode(s, nv, rho, ni))
    return rows


if __name__ == "__main__":
    rows = build()
    with open(OUT, "w") as fh:
        json.dump({"meta": {"n_seeds": N_SEEDS,
                            "reliabilities": list(PREREGISTERED_RELIABILITIES),
                            "n_visible_levels": list(N_VISIBLE_LEVELS),
                            "item_counts": list(ITEM_COUNTS),
                            "temperatures": list(PREREG_TEMPERATURES),
                            "eps": EPS, "scene_size": N_OBJ},
                   "rows": rows}, fh, indent=1)
    print(f"persisted {len(rows)} trial-level rows -> {OUT}\n")
    print(f"{'rho':>5} {'nvis':>5} {'items':>6} {'n':>5} {'taskH':>7} {'modelH':>8} "
          f"{'succ':>7} {'modelRec':>9} {'rhoReal':>8}")
    agg = defaultdict(list)
    for r in rows:
        agg[(r["rho"], r["n_visible"], r["n_items"])].append(r)
    for k in sorted(agg):
        v = agg[k]
        print(f"{k[0]:>5.2f} {k[1]:>5} {k[2]:>6} {len(v):>5} "
              f"{np.mean([x['task_entropy_bits'] for x in v]):>7.4f} "
              f"{np.mean([x['model_entropy_bits'] for x in v]):>8.4f} "
              f"{np.mean([x['success'] for x in v]):>7.4f} "
              f"{np.mean([x['model_recovery'] for x in v]):>9.4f} "
              f"{np.mean([x['realized_reliability'] for x in v]):>8.4f}")
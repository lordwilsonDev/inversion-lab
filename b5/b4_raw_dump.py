"""B5 §2 MANDATORY CHECKPOINT -- persist B4 load-bearing raw rows.

B4's Theory-B-vs-D table was reported as SUMMARY-TRACEABLE / NOT_INDEPENDENTLY_
RECOMPUTED because the values were captured from stdout rather than a persisted
trial-level row dump. This module closes that gap.

Writes ONE ROW PER TRIAL with everything needed to reconstruct the reported
values, then a SEPARATE recomputation module rebuilds the table from those rows.

Rows include: condition, episode/seed, sender id, target id, scene id,
global entropy, task entropy, effective hypotheses, posterior concentration,
success, model recovery, decision variables, decision policy, reliability,
and the raw posterior statistics needed for audit.
"""
from __future__ import annotations

import json
import random
import sys

import numpy as np

sys.path.insert(0, "/Users/lordwilson/projects/inversion-lab")
sys.path.insert(0, "/Users/lordwilson/projects/inversion-lab/b4")

from b4.substrate import B4Receiver, uniform_prior, object_likelihood  # noqa: E402
from b4.experiments import derangement, N_OBJ  # noqa: E402
from lexrepair.world import encode, gen_scene  # noqa: E402
from lexrepair.codebook import K  # noqa: E402

N_TRIALS = 400
N_ITEMS = 3
EPS = 0.15
OUT = "/Users/lordwilson/projects/inversion-lab/b5/B4_RAW_ROWS.json"


def build_rows(n=N_TRIALS):
    rows = []
    for s in range(n):
        fS = derangement(s)
        fOther = derangement(s + 10_000)
        rng = random.Random(1234567 + s)          # explicit, reproducible seed
        ho = gen_scene(rng, N_OBJ, f"b5-ho-{s}")
        t_ = ho.objects[rng.randrange(N_OBJ)]
        m_ = encode(fS, t_)

        for cond in ("none", "same_sender", "different_sender"):
            rec = B4Receiver(prior=uniform_prior(), eps=EPS)
            src = {"none": None, "same_sender": fS, "different_sender": fOther}[cond]
            for t in range(N_ITEMS if src is not None else 0):
                sc = gen_scene(rng, N_OBJ, f"b5-tr-{s}-{cond}-{t}")
                tg = sc.objects[rng.randrange(N_OBJ)]
                rec.observe(sc, encode(src, tg), target_index=tg.index)

            d = rec.posterior_diagnostics()
            pobj = rec.object_posterior(ho, m_)
            pe = float(-(np.clip(pobj, 1e-300, None) *
                         np.log2(np.clip(pobj, 1e-300, None))).sum())
            arg = int(np.argmax(pobj))

            # model recovery: does the posterior argmax codebook equal the
            # sender's ACTUAL mapping?
            fhat = tuple(int(x) for x in
                         __import__("lexrepair.receiver", fromlist=["tables"])
                         .tables().M[int(np.argmax(rec.post))])
            rows.append({
                # identity / design
                "trial": s, "condition": cond, "n_items": N_ITEMS, "eps": EPS,
                "sender_id": {"none": -1, "same_sender": s,
                              "different_sender": s + 10_000}[cond],
                "sender_matches_task_sender": int(src is not None and tuple(src) == tuple(fS)),
                "target_index": int(t_.index),
                "target_triple": [int(x) for x in t_.triple],
                "scene_seed": f"b5-ho-{s}",
                "scene_size": N_OBJ,
                # uncertainty measures
                "global_entropy_bits": float(d["entropy_bits"]),
                "global_eff_hypotheses": float(d["effective_hypotheses"]),
                "global_top10pct_mass": float(d["top10pct_mass"]),
                "task_entropy_bits": pe,
                "task_p_max": float(pobj.max()),
                "task_p_correct": float(pobj[t_.index]),
                "task_support": int((pobj > 0).sum()),
                # decision / outcome
                "argmax_index": arg,
                "success": int(arg == t_.index),
                "model_recovery": float(np.mean([fhat[c] == fS[c] for c in range(K)])),
                "model_recovered_exactly": int(all(fhat[c] == fS[c] for c in range(K))),
            })
    return rows


if __name__ == "__main__":
    import os
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    rows = build_rows()
    with open(OUT, "w") as fh:
        json.dump({"meta": {"n_trials": N_TRIALS, "n_items": N_ITEMS,
                            "eps": EPS, "scene_size": N_OBJ,
                            "conditions": ["none", "same_sender",
                                            "different_sender"]},
                   "rows": rows}, fh, indent=1)
    print(f"persisted {len(rows)} trial-level rows -> {OUT}")
    # quick unverified print (the VERIFIED values come from recompute.py)
    for c in ("none", "same_sender", "different_sender"):
        r = [x for x in rows if x["condition"] == c]
        print(f"  {c:>18}: globalH={np.mean([x['global_entropy_bits'] for x in r]):.4f} "
              f"taskH={np.mean([x['task_entropy_bits'] for x in r]):.4f} "
              f"success={np.mean([x['success'] for x in r]):.4f}")
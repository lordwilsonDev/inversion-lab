"""Run the full inversion-experiment suite and write artifacts."""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, "/Users/lordwilson/projects/inversion-lab")

from inversion import experiments as X  # noqa: E402

OUT = "results"


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    R = {}

    print("== E1 information vs hypothesis-space reduction")
    r1 = X.e1(200)
    R["E1"] = {"analysis": X.e1_analysis(r1), "n_rows": len(r1)}
    a = R["E1"]["analysis"]
    for arm, v in a["per_arm"].items():
        print(f"   {arm:14s} success={v['mean_success']:.3f} "
              f"bits/sym={v['mean_bits_per_symbol']:.3f} "
              f"logHypRed={v['mean_log_hyp_reduction']:.3f}")
    print(f"   discriminating={a['comparison']['DISCRIMINATING']}")

    print("== E2 identical feedback, different prior")
    r2 = X.e2(300)
    R["E2"] = {"analysis": X.e2_analysis(r2), "n_rows": len(r2)}
    for fb, v in R["E2"]["analysis"].items():
        if isinstance(v, dict) and "success_spread" in v:
            print(f"   {fb:22s} spread={v['success_spread']:.3f} "
                  f"(prior entropy spread {v['prior_entropy_spread']:.2f} bits)")

    print("== E3 mismatch magnitude sweep m=0..7")
    r3 = X.e3(60)
    R["E3"] = {"analysis": X.e3_analysis(r3), "n_rows": len(r3)}
    for m, v in R["E3"]["analysis"]["by_m"].items():
        print(f"   m={m}  contrastive={v['contrastive']:.3f}  "
              f"verify_only={v['verify_only']:.3f}  "
              f"delta={v['delta_vs_verify_only']:+.3f}  mrr={v['mrr_contrastive']:.3f}")
    print(f"   {R['E3']['analysis']['verdict']}")

    print("== E4 behaviour vs model (probe difficulty)")
    r4 = X.e4(300)
    R["E4"] = {"analysis": X.e4_analysis(r4), "n_rows": len(r4)}
    for p, v in R["E4"]["analysis"].items():
        if p != "DISCRIMINATING":
            print(f"   probe={p:4s} success={v['success_rate']:.3f} "
                  f"full_recovery={v['full_recovery_rate']:.3f} "
                  f"success_without_recovery={v['success_without_full_recovery']:.3f}")
    print(f"   DISCRIMINATING={R['E4']['analysis']['DISCRIMINATING']}")

    print("== E5 channel ablation")
    r5 = X.e5(200)
    R["E5"] = {"analysis": X.e5_analysis(r5), "n_rows": len(r5)}
    for ch, v in R["E5"]["analysis"].items():
        if isinstance(v, dict) and "success" in v:
            print(f"   {ch:20s} success={v['success']:.3f}  mrr={v['mrr']:.3f}  "
                  f"cost={v['symbol_cost']:.0f}  succ/sym={v['success_per_symbol']:.3f}")
    print(f"   {R['E5']['analysis']['interpretation']}")

    print("== E6 distinguishability boundary")
    R["E6"] = {"analysis": X.e6_analysis(200)}
    print(f"   {R['E6']['analysis']['result']}")
    print(f"   {R['E6']['analysis']['verdict']}")

    meta = {"wall_clock_seconds": round(time.time() - t0, 2),
            "rows": {k: v.get("n_rows") for k, v in R.items()},
            "python": sys.version.split()[0], "numpy": np.__version__}
    R["_meta"] = meta
    with open(os.path.join(OUT, "inversion_results.json"), "w") as fh:
        json.dump(R, fh, indent=2, default=float)
    with open(os.path.join(OUT, "E1_rows.json"), "w") as fh:
        json.dump(r1, fh)
    with open(os.path.join(OUT, "E3_rows.json"), "w") as fh:
        json.dump(r3, fh)
    print(f"\n== wrote {OUT}/inversion_results.json in {meta['wall_clock_seconds']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
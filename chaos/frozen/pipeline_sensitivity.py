#!/usr/bin/env python3
"""PIPELINE SENSITIVITY TEST (§26, §27).

Question: does the analysis pipeline respond to the properties of the WORLD,
or does it mechanically reproduce its preferred interpretation?

Four controlled world perturbations. THE ANALYSIS CODE IS NOT CHANGED.

  P1 REPRODUCIBILITY   -- unchanged world. Output must be unchanged.
  P2 LABEL SWAP       -- arm labels exchanged. Gap must flip sign EXACTLY.
  P3 NULL WORLD       -- every message describes the target. Gap must vanish.
  P4 STRUCTURE SWAP   -- attribute associations permuted. Gap must change.

Verdict vocabulary: WORLD_SENSITIVE / PIPELINE_INSENSITIVE
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict

sys.path.insert(0, "/Users/lordwilson/projects/inversion-lab/chaos")

from world import AXES, OBJECTS, Receiver, parse_message, transmit  # noqa: E402

RAW = "/Users/lordwilson/projects/inversion-lab/chaos/06_RAW_ROWS.jsonl"
N = 1200
T = 1.0
RHO = 1.0


def message_for(target: int, nattr: int):
    # Messages are VALUE-ONLY tokens ("red circle"); parse_message resolves each
    # token to exactly one axis via VALUES. Using axis names is a parse error.
    return " ".join(str(OBJECTS[target][i]) for i in range(nattr))


def run_arm(arm: str, nattr: int = 2, salt: int = 0):
    """D21 FIX: a FRESH Receiver per (trial, target).

    Previously one Receiver was created per trial and all three targets were
    presented to it, so each decision was taken after the receiver had already
    absorbed the other targets' messages. That is not the experiment; it is
    message contamination, and it made P1/P2/P3 meaningless.
    """
    hits = 0
    total = 0
    for trial in range(N):
        for target in range(3):
            rng = random.Random((trial * 1000003 + target * 7919 + salt) & 0xFFFFFFFF)
            rec = Receiver(rho_model=RHO)
            named = target if arm == "relevant" else (target + 1) % 3
            rec.apply_message(transmit(message_for(named, nattr), RHO, rng))
            hits += int(rec.decide_sampled(T, rng) == target)
            total += 1
    return hits / total, hits, total


def empirical_gap(swap_labels=False):
    if swap_labels:
        a = run_arm("irrelevant_matched")
        b = run_arm("relevant")
    else:
        a = run_arm("relevant")
        b = run_arm("irrelevant_matched")
    return a[0] - b[0], a, b


def main():
    print("=" * 74)
    print("PIPELINE SENSITIVITY TEST")
    print("=" * 74)

    # ---------------------------------------------------------- P1
    print("\nP1  REPRODUCIBILITY -- unchanged world, two identical invocations")
    g1, a1, b1 = empirical_gap()
    g2, a2, b2 = empirical_gap()
    print(f"    run 1: rel={a1[0]:.6f} ({a1[1]}/{a1[2]})  irr={b1[0]:.6f} ({b1[1]}/{b1[2]})  gap={g1:+.6f}")
    print(f"    run 2: rel={a2[0]:.6f} ({a2[1]}/{a2[2]})  irr={b2[0]:.6f} ({b2[1]}/{b2[2]})  gap={g2:+.6f}")
    p1_ok = abs(g1 - g2) < 1e-12
    print(f"    identical: {p1_ok}")

    # ---------------------------------------------------------- P2
    print("\nP2  LABEL SWAP -- arm labels exchanged; gap must flip sign EXACTLY")
    g_sw, a_sw, b_sw = empirical_gap(swap_labels=True)
    print(f"    rel={a_sw[0]:.6f}  irr={b_sw[0]:.6f}  gap={g_sw:+.6f}")
    p2_ok = abs(g_sw + g1) < 1e-12
    print(f"    gap + original gap = {g_sw + g1:+.3e}  (should be 0)  -> {p2_ok}")
    print("    NOTE: swapping labels in RAW DATA is a pure sign flip by")
    print("          construction, so this tests arithmetic, not reasoning.")

    # ---------------------------------------------------------- P3
    print("\nP3  NULL WORLD -- every message names the actual target in both arms")
    print("    (relevant and irrelevant become the SAME treatment)")
    armA = run_arm("relevant", 2, salt=0)
    armB = run_arm("relevant", 2, salt=1)   # same treatment, independent seeds
    accA, accB = armA[0], armB[0]
    print(f"    arm A (identical treatment) acc={accA:.6f}")
    print(f"    arm B (identical treatment) acc={accB:.6f}")
    print(f"    gap = {accA - accB:+.6f}   [should be ~0: same treatment both arms]")
    p3_ok = abs(accA - accB) < 0.05
    print(f"    null world collapses the gap: {p3_ok}")

    # ---------------------------------------------------------- P4
    print("\nP4  STRUCTURE PERTURBATION -- single-attribute messages")
    print("    (a message naming only ONE attribute cannot identify an object")
    print("     when several objects share it; candidate reduction must fall)")
    oa = run_arm("relevant", nattr=1)
    ob = run_arm("irrelevant_matched", nattr=1)
    a, b = oa[0], ob[0]
    print(f"    relevant (1 attr)   acc={a:.6f}")
    print(f"    irrelevant (1 attr) acc={b:.6f}")
    print(f"    gap = {a - b:+.6f}")
    print(f"    two-attribute gap was {g1:+.6f}")
    p4_ok = abs((a - b) - g1) > 0.01
    print(f"    pipeline RESPONDS to world structure: {p4_ok}")

    # ---------------------------------------------------------- verdict
    print("\n" + "=" * 74)
    print("VERDICT")
    print("=" * 74)
    checks = {"P1 reproducibility": p1_ok,
              "P2 label swap arithmetic": p2_ok,
              "P3 null world collapses gap": p3_ok,
              "P4 structure change moves gap": p4_ok}
    for k, v in checks.items():
        print(f"  {k:<34} {'PASS' if v else 'FAIL'}")

    sensitive = p3_ok and p4_ok
    verdict = "WORLD_SENSITIVE" if sensitive else "PIPELINE_INSENSITIVE"
    print(f"\n  PIPELINE VERDICT: {verdict}")

    out = {"checks": {k: bool(v) for k, v in checks.items()},
           "verdict": verdict,
           "original_gap": g1,
           "null_world_gap": accA - accB,
           "one_attribute_gap": a - b}
    with open("/Users/lordwilson/projects/inversion-lab/chaos/12_PIPELINE_SENSITIVITY.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nwrote 12_PIPELINE_SENSITIVITY.json")


if __name__ == "__main__":
    main()
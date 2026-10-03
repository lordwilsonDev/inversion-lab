"""SELF-TEST for the claim-state / gate / provenance layer.

A guardrail that is never exercised is a guardrail that does not exist. These
tests assert the FAIL-CLOSED behaviour: illegal transitions raise, missing
evidence blocks, retracted claims cannot promote, and ladder skips are refused.
"""
from __future__ import annotations

import sys

from claim_states import (BLOCKED, BOUNDARY, EXTERNALLY_VERIFIED,
                          INDEPENDENTLY_RECOMPUTED, OBSERVED, QUALIFIED,
                          REPRODUCED, RETRACTED, SUPPORTED, UNOBSERVED,
                          UNRESOLVED, Claim, GateBlocked, IllegalTransition,
                          OBSERVER_LEVELS, ProvenanceChain, operational_gate,
                          recompute)

PASS, FAIL = [], []


def check(name, fn):
    try:
        fn()
        PASS.append(name)
        print(f"  PASS  {name}")
    except Exception as e:
        FAIL.append((name, e))
        print(f"  FAIL  {name}: {e}")


def new_claim():
    return Claim(claim_id="C-TEST", text="a claim", scope="synthetic")


# --------------------------------------------------------------------- tests

def t_initial_state():
    c = new_claim()
    assert c.state == UNOBSERVED, c.state


def t_happy_ladder():
    c = new_claim()
    c.transition(OBSERVED, "ran it", "ev1")
    c.transition(REPRODUCED, "ran twice", "ev1")
    c.transition(INDEPENDENTLY_RECOMPUTED, "separate impl", "ev1",
                 auditor_id="a2", independence="I2_SEPARATE_REASONING")
    assert c.last_verification == "I2_SEPARATE_REASONING"


def t_ladder_skip_refused():
    c = new_claim()
    try:
        c.transition(REPRODUCED, "skipping OBSERVED", "ev")
    except IllegalTransition:
        return
    raise AssertionError("ladder skip was ALLOWED -- fail-closed violated")


def t_observed_to_true_refused():
    """The exact promotion SS11 forbids."""
    c = new_claim()
    c.transition(OBSERVED, "ran", "ev")
    try:
        c.transition(SUPPORTED, "promoting without evidence", "ev")
        # SUPPORTED is admissible from OBSERVED only with justification; the
        # guard is that VERIFIED-style promotion requires a verification level.
        assert c.last_verification is None, "promotion recorded a verifier"
    except IllegalTransition:
        return
    raise AssertionError("OBSERVED -> SUPPORTED silently accepted")


def t_retracted_cannot_be_promoted():
    c = new_claim()
    c.transition(OBSERVED, "ran", "ev")
    c.transition(RETRACTED, "found defective", "ev")
    for target in (SUPPORTED, QUALIFIED, EXTERNALLY_VERIFIED):
        try:
            c.transition(target, "attempted resurrection", "ev")
            raise AssertionError(f"RETRACTED -> {target} was ALLOWED")
        except IllegalTransition:
            pass


def t_retracted_only_reopens_to_unresolved():
    c = new_claim()
    c.transition(OBSERVED, "ran", "ev")
    c.transition(RETRACTED, "defect", "ev")
    c.transition(UNRESOLVED, "reopened", "ev")
    assert c.state == UNRESOLVED


def t_boundary_is_terminal_except_reopen():
    c = new_claim()
    c.transition(BOUNDARY, "ceiling reached", "ev")
    try:
        c.transition(EXTERNALLY_VERIFIED, "claiming a boundary was crossed", "ev")
        raise AssertionError("BOUNDARY -> EXTERNALLY_VERIFIED was ALLOWED")
    except IllegalTransition:
        pass


def t_gate_blocks_missing_evidence():
    c = new_claim()
    r = operational_gate(c, "ctx")
    assert r["verdict"] == "BLOCK", r
    assert any("unanswered" in x for x in r["reasons"]), r["reasons"]


def t_gate_blocks_when_scope_assertion_omitted():
    """A fully evidenced claim still BLOCKS without an explicit scope assertion."""
    c = Claim(claim_id="C", text="t", scope="synthetic")
    c.transition(OBSERVED, "ran", "ev1")
    c.transition(REPRODUCED, "again", "ev1")
    c.transition(QUALIFIED, "q", "ev1", auditor_id="s",
                 independence="I1_SEPARATE_EXECUTION")
    r = operational_gate(c, "synthetic three-object world")
    assert r["verdict"] == "BLOCK", r
    assert "7_context_in_scope" in str(r["reasons"]), r["reasons"]


def t_gate_blocks_scope_assertion_without_reason():
    c = Claim(claim_id="C", text="t", scope="synthetic")
    c.transition(OBSERVED, "ran", "ev1")
    c.transition(REPRODUCED, "again", "ev1")
    c.transition(QUALIFIED, "q", "ev1", auditor_id="s",
                 independence="I1_SEPARATE_EXECUTION")
    r = operational_gate(c, "ctx", assert_in_scope=True)
    assert r["verdict"] == "BLOCK", r


def t_gate_blocks_retracted():
    c = new_claim()
    c.transition(OBSERVED, "ran", "ev")
    c.transition(RETRACTED, "defect", "ev")
    r = operational_gate(c, "ctx")
    assert r["verdict"] == "BLOCK", r


def t_gate_blocks_unresolved_and_boundary():
    for st, how in ((UNRESOLVED, None), (BOUNDARY, None)):
        c = new_claim()
        c.transition(OBSERVED, "ran", "ev")
        if st == UNRESOLVED:
            c.transition(UNRESOLVED, "ambiguous", "ev")
        else:
            c.transition(BOUNDARY, "ceiling", "ev")
        assert operational_gate(c, "ctx")["verdict"] == "BLOCK", st


def t_gate_allows_qualified_with_full_provenance():
    c = Claim(claim_id="C-TEST", text="a claim", scope="synthetic")
    c.transition(OBSERVED, "ran", "ev1")
    c.transition(REPRODUCED, "again", "ev1")
    c.transition(QUALIFIED, "qualified by a control defect", "ev1",
                 auditor_id="self", independence="I1_SEPARATE_EXECUTION")
    r = operational_gate(c, "synthetic three-object world",
                         assert_in_scope=True,
                         assert_reason="world size and channel match")
    assert r["verdict"] == "ALLOW", r


def t_recompute_never_bare_pass():
    r = recompute("C-1", "ev1", 0.578, "mean per-target gap",
                  "exact rational", "impl-1", "auditor-1",
                  "I2_SEPARATE_REASONING")
    for k in ("result", "estimand", "method", "evidence_ref",
              "verification_level", "implementation_id", "auditor_id",
              "timestamp"):
        assert k in r, k
    assert r["result"] != "PASS", "recompute returned a bare PASS"


def t_recompute_rejects_unknown_level():
    try:
        recompute("C", "e", 1, "e", "m", "i", "a", "I9_MADE_UP")
        raise AssertionError("unknown observer level accepted")
    except ValueError:
        pass


def t_provenance_receipt_has_hash_and_gaps():
    p = ProvenanceChain(request="r", mission="m", version="1", inputs={},
                        execution_id="x", raw_evidence_ref="",
                        verification_ref="v", claim_id="C",
                        auditor_id="a", auditor_level="I2_CM_CROSS_MODEL")
    gaps = p.validate()
    assert any("raw evidence" in g for g in gaps), gaps
    rc = p.receipt()
    assert rc["receipt_hash"]
    assert rc["observer_level_meaning"] == OBSERVER_LEVELS["I2_CM_CROSS_MODEL"]


def t_observer_levels_are_distinct():
    assert len(OBSERVER_LEVELS) == 5, OBSERVER_LEVELS
    assert (OBSERVER_LEVELS["I2_CM_CROSS_MODEL"]
            != OBSERVER_LEVELS["I2_SEPARATE_REASONING"]), \
        "cross-model and separate-reasoning must not share a meaning"


if __name__ == "__main__":
    print("=" * 70)
    print("CLAIM-STATE / GATE / PROVENANCE SELF-TEST")
    print("=" * 70)
    for name, fn in sorted(list(globals().items())):
        if name.startswith("t_") and callable(fn):
            check(name[2:], fn)
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    sys.exit(1 if FAIL else 0)
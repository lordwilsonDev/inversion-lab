"""FAIL-CLOSED CLAIM STATES, TRANSITIONS, OPERATIONAL GATE, PROVENANCE.

SS11-17. The central rule:

    No downstream execution may silently convert QUALIFIED into VERIFIED,
    or OBSERVED into TRUE.

Unknown is a valid state. Missing evidence BLOCKS promotion rather than
defaulting to allow.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

# ============================================================ SS11 CLAIM STATES

UNOBSERVED = "UNOBSERVED"
OBSERVED = "OBSERVED"
REPRODUCED = "REPRODUCED"
INDEPENDENTLY_RECOMPUTED = "INDEPENDENTLY_RECOMPUTED"
EXTERNALLY_VERIFIED = "EXTERNALLY_VERIFIED"
SUPPORTED = "SUPPORTED"
QUALIFIED = "QUALIFIED"
SUGGESTIVE = "SUGGESTIVE"
UNRESOLVED = "UNRESOLVED"
RETRACTED = "RETRACTED"
BOUNDARY = "BOUNDARY"
BLOCKED = "BLOCKED"

STATES = {
    UNOBSERVED, OBSERVED, REPRODUCED, INDEPENDENTLY_RECOMPUTED,
    EXTERNALLY_VERIFIED, SUPPORTED, QUALIFIED, SUGGESTIVE, UNRESOLVED,
    RETRACTED, BOUNDARY, BLOCKED,
}

# Evidence ladder. An ordinal rank lets us assert "no skipping".
RANK = {
    UNOBSERVED: 0,
    OBSERVED: 1,
    REPRODUCED: 2,
    INDEPENDENTLY_RECOMPUTED: 3,
    EXTERNALLY_VERIFIED: 4,
    SUPPORTED: 5,
    QUALIFIED: 5,
    SUGGESTIVE: 5,
}

# ======================================================== SS12 LEGAL TRANSITIONS

LEGAL = {
    UNOBSERVED: {OBSERVED, BLOCKED, BOUNDARY},
    OBSERVED: {REPRODUCED, UNRESOLVED, RETRACTED, QUALIFIED, SUGGESTIVE,
               BLOCKED, BOUNDARY},
    REPRODUCED: {INDEPENDENTLY_RECOMPUTED, UNRESOLVED, RETRACTED, QUALIFIED,
                 SUGGESTIVE, BLOCKED, BOUNDARY},
    INDEPENDENTLY_RECOMPUTED: {EXTERNALLY_VERIFIED, QUALIFIED, SUGGESTIVE,
                               UNRESOLVED, RETRACTED, BLOCKED, BOUNDARY},
    EXTERNALLY_VERIFIED: {SUPPORTED, QUALIFIED, SUGGESTIVE, UNRESOLVED,
                          RETRACTED, BLOCKED, BOUNDARY},
    SUPPORTED: {QUALIFIED, RETRACTED, UNRESOLVED, BLOCKED},
    QUALIFIED: {RETRACTED, UNRESOLVED, SUPPORTED, BLOCKED},
    SUGGESTIVE: {QUALIFIED, SUPPORTED, RETRACTED, UNRESOLVED, BLOCKED},
    UNRESOLVED: {OBSERVED, REPRODUCED, INDEPENDENTLY_RECOMPUTED, QUALIFIED,
                 SUPPORTED, RETRACTED, BLOCKED, BOUNDARY},
    RETRACTED: {UNRESOLVED},          # a retraction may only be reopened, never
                                      # silently un-retracted into a higher state
    BOUNDARY: {UNRESOLVED, BLOCKED},
    BLOCKED: {UNOBSERVED},
}


class IllegalTransition(Exception):
    pass


@dataclass
class Claim:
    claim_id: str
    text: str
    state: str = UNOBSERVED
    scope: Optional[str] = None
    estimate: Optional[float] = None
    ci: Optional[tuple] = None
    evidence_ref: Optional[str] = None
    auditor_id: Optional[str] = None
    auditor_independence: Optional[str] = None
    last_verification: Optional[str] = None
    retractions: list = field(default_factory=list)
    history: list = field(default_factory=list)

    def transition(self, new_state: str, reason: str, evidence_ref: str = "",
                   auditor_id: str = "", independence: str = "") -> "Claim":
        if new_state not in STATES:
            raise IllegalTransition(f"unknown state {new_state!r}")
        if new_state not in LEGAL.get(self.state, set()):
            raise IllegalTransition(
                f"{self.claim_id}: {self.state} -> {new_state} is not a legal "
                f"transition. Legal: {sorted(LEGAL.get(self.state, set()))}")
        # ladder states may not skip a rung
        if new_state in RANK and self.state in RANK:
            if RANK[new_state] > RANK[self.state] + 1 and \
                    new_state not in (SUPPORTED, QUALIFIED, SUGGESTIVE):
                raise IllegalTransition(
                    f"{self.claim_id}: ladder skip {self.state} -> {new_state}")
        self.history.append({"from": self.state, "to": new_state,
                             "reason": reason, "evidence_ref": evidence_ref,
                             "auditor_id": auditor_id,
                             "independence": independence,
                             "ts": time.time()})
        self.state = new_state
        if evidence_ref:
            self.evidence_ref = evidence_ref
        if auditor_id:
            self.auditor_id = auditor_id
            self.auditor_independence = independence
            self.last_verification = independence or auditor_id
        return self

    def to_dict(self):
        return asdict(self)


# ================================================ SS13 OPERATIONAL CLAIM GATE

class GateBlocked(Exception):
    pass


PROMOTABLE = {SUPPORTED, QUALIFIED, SUGGESTIVE}


def operational_gate(claim: Claim, context: str,
                     assert_in_scope: Optional[bool] = None,
                     assert_reason: str = "") -> dict:
    """Answer SS13's seven questions. Any unavailable answer -> BLOCK.

    Question 7 ("is the operational context inside the tested scope?") cannot
    be inferred from the claim -- only the CALLER can assert it. It is
    therefore an explicit parameter and defaults to None, which BLOCKS.

    This is fail-closed: an omitted assertion is not consent.
    """
    q = {
        "1_claim": claim.text if claim.text else None,
        "2_evidence": claim.evidence_ref if claim.evidence_ref else None,
        "3_status": claim.state if claim.state else None,
        "4_scope": claim.scope if claim.scope else None,
        "5_last_verification": claim.last_verification if claim.last_verification else None,
        "6_retracted_or_unresolved": (
            "RETRACTED" if claim.state == RETRACTED
            else "UNRESOLVED" if claim.state == UNRESOLVED
            else "BOUNDARY" if claim.state == BOUNDARY
            else "BLOCKED" if claim.state == BLOCKED
            else "NO"),
        "7_context_in_scope": assert_in_scope,   # caller-asserted; None => BLOCK
    }
    missing = [k for k, v in q.items() if v is None]
    verdict = "ALLOW"
    reasons = []
    if missing:
        verdict = "BLOCK"
        reasons.append(f"unanswered gate questions: {missing}")
    if claim.state == RETRACTED:
        verdict = "BLOCK"
        reasons.append("claim is RETRACTED")
    if claim.state in (UNRESOLVED, BOUNDARY, BLOCKED):
        verdict = "BLOCK"
        reasons.append(f"claim state {claim.state} is not actionable")
    if claim.state in RANK and claim.last_verification is None:
        verdict = "BLOCK"
        reasons.append("no verification level recorded")
    if assert_in_scope is True and not assert_reason:
        reasons.append("scope asserted as in-scope but no reason given")
        verdict = "BLOCK"
    if not reasons:
        reasons.append(
            f"claim is {claim.state}; caller asserts context '{context}' is "
            f"inside scope ({assert_reason})")
    return {"verdict": verdict, "gate_answers": q, "reasons": reasons,
            "context": context}


# ============================================ SS15-17 PROVENANCE / OBSERVERS

OBSERVER_LEVELS = {
    "I0_SELF_CHECK": "same analytical path checks itself",
    "I1_SEPARATE_EXECUTION": "different code path, no shared imports",
    "I2_SEPARATE_REASONING": "distinct author, independent estimand derivation",
    "I2_CM_CROSS_MODEL": "different model, blind to prior narrative",
    "I3_EXTERNAL": "entity outside the originating reasoning chain",
}


@dataclass
class ProvenanceChain:
    request: str
    mission: str
    version: str
    inputs: dict
    execution_id: str
    raw_evidence_ref: str
    verification_ref: str
    claim_id: str
    auditor_id: str
    auditor_level: str
    created_at: float = field(default_factory=time.time)

    def validate(self) -> list:
        gaps = []
        if self.auditor_level not in OBSERVER_LEVELS:
            gaps.append(f"unknown observer level {self.auditor_level!r}")
        if not self.raw_evidence_ref:
            gaps.append("no raw evidence reference (SS14)")
        if not self.verification_ref:
            gaps.append("no verification reference")
        return gaps

    def receipt(self) -> dict:
        """SS16: a receipt, never a bare PASS."""
        d = asdict(self)
        d["observer_level_meaning"] = OBSERVER_LEVELS.get(self.auditor_level, "?")
        d["gaps"] = self.validate()
        d["receipt_hash"] = hashlib.sha256(
            json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()
        return d


# SS16: recompute must never return only PASS
def recompute(claim_id: str, evidence_ref: str, result: Any, estimand: str,
              method: str, implementation_id: str, auditor_id: str,
              level: str) -> dict:
    if level not in OBSERVER_LEVELS:
        raise ValueError(f"unknown observer level {level!r}")
    return {
        "claim_id": claim_id,
        "evidence_ref": evidence_ref,
        "result": result,
        "estimand": estimand,
        "method": method,
        "implementation_id": implementation_id,
        "auditor_id": auditor_id,
        "verification_level": level,
        "observer_level_meaning": OBSERVER_LEVELS[level],
        "timestamp": time.time(),
    }
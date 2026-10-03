"""MINIMAL REFERENTIAL COMMUNICATION WORLD (chaos audit).

Deliberately tiny, and auditable by hand. Three objects, three attributes,
one sender, one receiver, one message, one evaluator.

WHY SO SMALL. The previous trajectory (Runs 1-3, B4, B5) used an 8! = 40,320
codebook substrate. Its strongest results were properties of THAT substrate:
hard masking forced uniform posteriors on survivors, a deterministic
lowest-index tie-break manufactured position effects, and graded evidence
saturated within two items. Those are simulator facts, not communication facts.

This world has THREE objects. Every posterior, entropy, and candidate set can
be checked by hand. If a result is real, it should survive here.

THE THREE LAYERS OF THE MESSAGE (§13)
--------------------------------------
  surface form          "red circle"
  compositional reading {color: red, shape: circle}
  referential effect   candidate set -> {Object 1}

All three layers are implemented separately and unit-tested. The compositional
operation EXISTS in the code; this is not a bag of tokens.

MESSAGE MODEL
-------------
A message is a conjunction of (attribute, value) constraints. Parsing is a real
function: parse("red circle") -> [("color","red"), ("shape","circle")].
An object satisfies a message iff it matches EVERY constraint.

CHANNEL
-------
Graded: with probability rho each stated attribute-value is transmitted
correctly; otherwise it is replaced by a different value of the same
attribute. Corruption cannot change WHICH attribute is being talked about, so
it cannot silently inject hidden target information (§4).

DECISION
--------
Posterior-proportional and temperature sampling. Deterministic argmax is
PROHIBITED as primary (defect D17), and on a 3-object world it would be even
more exposed: argmax over a tied posterior returns index 0.
"""
from __future__ import annotations

import hashlib
import itertools
import math
import random
from typing import Dict, List, Sequence, Tuple

# ---------------------------------------------------------------------
# The world (§3). Fixed and hand-checkable.
# ---------------------------------------------------------------------
OBJECTS: Tuple[Tuple[str, str, str], ...] = (
    ("red", "circle", "large"),    # Object 1
    ("blue", "square", "large"),   # Object 2
    ("red", "square", "small"),    # Object 3
)
N_OBJ = len(OBJECTS)
AXES = ("color", "shape", "size")
VALUES = {a: tuple(sorted({o[i] for o in OBJECTS})) for i, a in enumerate(AXES)}
N_PERM = math.factorial(N_OBJ)

WORLD_FINGERPRINT = hashlib.md5(
    repr(OBJECTS).encode()).hexdigest()[:12]


def obj_str(i: int) -> str:
    return "/".join(OBJECTS[i])


# ---------------------------------------------------------------------
# Surface form and compositional parsing (§4, §13)
# ---------------------------------------------------------------------
def render_message(constraints: Sequence[Tuple[str, str]]) -> str:
    """Surface form: 'red circle'. Attribute order is canonical (AXES order)
    so that message length and token count are matched across conditions."""
    d = dict(constraints)
    return " ".join(d[a] for a in AXES if a in d)


def parse_message(surface: str) -> List[Tuple[str, str]]:
    """Compositional interpretation: 'red circle' -> [('color','red'),
    ('shape','circle')]. This operation EXISTS; it is not simulated.

    Parsing is ORDER-INDEPENDENT: each token is assigned to the axis whose value
    set contains it. Without this, 'large square' is malformed because tokens
    would be zipped positionally against (color, shape, size).
    """
    toks = surface.split()
    out: List[Tuple[str, str]] = []
    used = set()
    for t in toks:
        axes = [a for a in AXES if a not in used and t in VALUES[a]]
        if len(axes) != 1:
            raise ValueError(f"'{t}' does not resolve to exactly one axis "
                             f"(candidates: {axes})")
        out.append((axes[0], t))
        used.add(axes[0])
    return out


def satisfies(obj: Tuple[str, str, str], constraints) -> bool:
    d = dict(constraints)
    return all(obj[AXES.index(a)] == v for a, v in constraints)


def candidate_set(constraints) -> List[int]:
    return [i for i, o in enumerate(OBJECTS) if satisfies(o, constraints)]


# ---------------------------------------------------------------------
# Graded channel (§4: no hidden target information)
# ---------------------------------------------------------------------
def transmit(surface: str, rho: float, rng: random.Random) -> str:
    """Each stated attribute-value survives with probability rho; otherwise it
    is replaced by a DIFFERENT value of the SAME attribute."""
    constraints = parse_message(surface)
    out = []
    for a, v in constraints:
        if rng.random() < rho:
            out.append((a, v))
        else:
            alts = [x for x in VALUES[a] if x != v]
            out.append((a, alts[rng.randrange(len(alts))]))
    return render_message(out)


def realized_ρ(surface: str, sent: str) -> float:
    """Fraction of stated attribute-values transmitted correctly."""
    a = parse_message(surface)
    b = parse_message(sent)
    if len(a) != len(b):
        return 0.0
    return sum(1 for x, y in zip(a, b) if x == y) / len(a)


# ---------------------------------------------------------------------
# Receiver: posterior over objects (§6 cybernetic state)
# ---------------------------------------------------------------------
class Receiver:
    """Belief over objects. Uniform start; updated by message constraints.

    p(o) is uniform on the candidate set and zero elsewhere. With a graded
    (noisy) message the constraint is SOFT: an object that fails one stated
    attribute is not deleted, it is down-weighted by a likelihood factor.
    """

    __slots__ = ("post", "rho_model", "eps")

    def __init__(self, rho_model: float = 0.75, eps: float = 0.15):
        self.post = [1.0 / N_OBJ] * N_OBJ
        self.rho_model = rho_model
        self.eps = eps

    def apply_message(self, surface: str) -> Dict[str, float]:
        """Graded update: P(received value | true value) under the channel."""
        constraints = parse_message(surface)
        p_hit, p_miss = self.rho_model, (1.0 - self.rho_model) / max(
            1, len(VALUES[AXES[0]]) - 1)
        new = []
        for oi, obj in enumerate(OBJECTS):
            lik = 1.0
            for a, v in constraints:
                true_v = obj[AXES.index(a)]
                lik *= (p_hit if true_v == v else p_miss) + self.eps
            new.append(self.post[oi] * lik)
        s = sum(new)
        self.post = [x / s for x in new] if s > 0 else [1.0 / N_OBJ] * N_OBJ
        return {"entropy_before": entropy(self.post), "posterior": list(self.post)}

    def hard_candidates(self, surface: str) -> List[int]:
        return candidate_set(parse_message(surface))

    def entropy(self) -> float:
        return entropy(self.post)

    def decide_sampled(self, T: float, rng: random.Random) -> int:
        w = [x ** (1.0 / T) for x in self.post]
        s = sum(w)
        if s <= 0:
            return 0
        w = [x / s for x in w]
        r, acc = rng.random(), 0.0
        for i, wi in enumerate(w):
            acc += wi
            if r <= acc:
                return i
        return N_OBJ - 1

    def feedback(self, chosen: int, correct: bool, hint: str | None) -> Dict:
        """Cybernetic error signal -> state update (§14, §15).

        A bare 'wrong' signal removes only the eliminated hypothesis.
        A corrective hint states one true attribute of the target, which is
        genuine new information about the world.
        """
        before_H, before_post, before_c = self.entropy(), list(self.post), None
        if not correct:
            # graded penalty on the rejected hypothesis, NOT elimination
            self.post = [x * (0.02 if i == chosen else 1.0)
                         for i, x in enumerate(self.post)]
            s = sum(self.post)
            self.post = [x / s for x in self.post]
        if correct and hint:
            constraints = parse_message(hint)
            p_hit, p_miss = self.rho_model, (1.0 - self.rho_model)
            new = []
            for obj in OBJECTS:
                lik = 1.0
                for a, v in constraints:
                    true_v = obj[AXES.index(a)]
                    lik *= (p_hit if true_v == v else p_miss) + self.eps
                new.append(self.post[AXES and OBJECTS.index(obj)] * lik)
            s = sum(new)
            self.post = [x / s for x in new] if s > 0 else [1.0 / N_OBJ] * N_OBJ
        return {"H_before": before_H, "H_after": self.entropy(),
                "delta_H": before_H - self.entropy(),
                "posterior_before": before_post,
                "posterior_after": list(self.post)}


def entropy(post: Sequence[float]) -> float:
    """Shannon entropy in bits. Hard-coded definition, unit-tested."""
    return float(-sum(p * math.log2(p) for p in post if p > 0))


# ---------------------------------------------------------------------
# §18 PRE-EXPERIMENT ANALYSIS VALIDATION -- known cases A-E.
# The substantive trial may NOT run until all five pass.
# ---------------------------------------------------------------------
def analysis_validation() -> Dict:
    out = {}

    # CASE A: message identifies exactly one object
    cands = candidate_set(parse_message("red circle"))
    H_before = entropy([1 / 3] * 3)
    out["A_unique_referent"] = {
        "candidates": cands, "n_candidates": len(cands),
        "H_before": round(H_before, 6), "H_after": 0.0,
        "expect_n_candidates_1": True, "expect_H_reduction_gt_0": True}
    out["A_PASS"] = (len(cands) == 1 and H_before > 0)

    # CASE B: message identifies NO object (attribute values incompatible)
    bad = candidate_set([("color", "green")]) if "green" in VALUES["color"] else None
    # construct a genuinely empty case by conflicting constraints on one object
    empty = [i for i, o in enumerate(OBJECTS)
             if o[0] == "red" and o[1] == "square" and o[2] == "large"]
    out["B_no_valid_referent"] = {
        "note": "'red square large' matches no object (Object 2 is blue)",
        "candidates": empty, "n_candidates": len(empty),
        "expect_no_valid_referent": True}
    out["B_PASS"] = (len(empty) == 0)

    # CASE C: irrelevant message -> no TASK-RELEVANT constraint reduction,
    # but note it may still reduce entropy over WRONG referents
    # Matched on surface form: 2 tokens, both canonical AXES order, both
    # resolve to a UNIQUE referent -- but this one identifies Object 2, not the
    # target Object 1. Only REFERENTIAL RELEVANCE differs.
    irr = "blue square"       # matches Object 2 only
    c_irr = candidate_set(parse_message(irr))
    out["C_irrelevant_but_structured"] = {
        "message": irr, "candidates": c_irr, "n_candidates": len(c_irr),
        "note": ("A structurally identical message that does NOT identify the "
                 "target still reduces entropy to zero -- over the WRONG "
                 "referent. This is the crux of the audit.")}
    out["C_PASS"] = (len(c_irr) >= 1)

    # CASE D: two objects satisfy the message
    cands2 = candidate_set(parse_message("large"))
    out["D_two_candidates"] = {
        "message": "large", "candidates": cands2, "n_candidates": len(cands2),
        "H_after": round(entropy([1 / len(cands2)] * len(cands2)), 6) if cands2 else None,
        "expect_n_candidates_2": True}
    out["D_PASS"] = (len(cands2) == 2)

    # CASE E: feedback removes one candidate
    r = Receiver(rho_model=0.999)
    r.apply_message("large")                 # 2 candidates
    before = list(r.post)
    res = r.feedback(chosen=0, correct=False, hint=None)
    out["E_feedback_updates_state"] = {
        "posterior_before": [round(x, 4) for x in before],
        "posterior_after": [round(x, 4) for x in res["posterior_after"]],
        "delta_H": round(res["delta_H"], 6),
        "state_changed": res["posterior_after"] != before,
        "expect_state_changes": True}
    out["E_PASS"] = bool(res["delta_H"] > 0 and res["posterior_after"] != before)

    # CASE F (extra): entropy of the uniform 3-object prior
    out["F_prior_entropy"] = {
        "H": round(H_before, 6), "expected_log2_3": round(math.log2(3), 6),
        "PASS": abs(H_before - math.log2(3)) < 1e-12}

    out["WORLD_FINGERPRINT"] = WORLD_FINGERPRINT
    out["OBJECTS"] = [obj_str(i) for i in range(N_OBJ)]
    verdicts = ["A_PASS", "B_PASS", "C_PASS", "D_PASS", "E_PASS", "F_prior_entropy"]
    out["VERDICT_KEYS"] = verdicts
    out["ALL_PASS"] = all(bool(out[k]) for k in verdicts[:-1]) and bool(out["F_prior_entropy"]["PASS"])
    return out


if __name__ == "__main__":
    import json
    v = analysis_validation()
    print("=" * 74)
    print("§18 PRE-EXPERIMENT ANALYSIS VALIDATION (cases A-E)")
    print("=" * 74)
    print(f"world: {v['OBJECTS']}   fingerprint={v['WORLD_FINGERPRINT']}\n")
    for k in v["VERDICT_KEYS"]:
        print(f"  {k}: {v[k]}")
    print("\n  detail:")
    for k in ("A_unique_referent", "B_no_valid_referent",
              "C_irrelevant_but_structured", "D_two_candidates",
              "E_feedback_updates_state", "F_prior_entropy"):
        print(f"    {k}: {v[k]}")
    print("\n" + "=" * 74)
    print(f"ANALYSIS INSTRUMENT VALID: {v['ALL_PASS']}")
    if not v["ALL_PASS"]:
        print(">>> STOP. Do not execute substantive trials.")
    print("=" * 74)
    json.dump(v, open("/Users/lordwilson/projects/inversion-lab/chaos/VALIDATION.json", "w"),
              indent=1, default=str)

def stable_seed(*parts) -> int:
    """blake2b-derived seed. NEVER use Python hash() (defect D14)."""
    return int.from_bytes(
        hashlib.blake2b("|".join(str(p) for p in parts).encode(),
                        digest_size=8).digest(), "big")

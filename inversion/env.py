"""Extended environment for the inversion exercise.

REUSES the verified core from ../lexical-repair-crt (exact 40,320-codebook
posterior, audited information boundaries, deterministic seeding). Adds only
what the inversion chain needs and the core does not provide:

  * channels        — explicit message, environmental signal, demonstration,
                      consequence, observation-only  (inversion 9)
  * sender modes    — fixed, adaptive               (inversion 7)
  * task variants   — task-sufficient vs exact      (inversion 5)
  * invariant ablation                                 (inversion 6)
  * identifiability   — residual hypothesis count    (inversion 4)
  * prior variation  — non-exchangeable priors      (breaks the confidence
                      degeneracy found in run 1, where q == 1/candidates)
"""
from __future__ import annotations

import itertools
import math
import random
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

sys.path.insert(0, "/Users/lordwilson/projects/lexical-repair-crt")

from lexrepair import codebook as CB          # noqa: E402
from lexrepair.receiver import tables, triple_code, triple_code_of  # noqa: E402
from lexrepair.world import Obj, Scene, gen_scene, CONCEPTS_BY_SLOT  # noqa: E402
from lexrepair.codebook import C_INDEX, CONCEPTS, K, TOKENS  # noqa: E402

CONCEPT_NAMES = CONCEPTS
TOKEN_NAMES = TOKENS


def stable_seed(*parts) -> int:
    import hashlib
    return int.from_bytes(
        hashlib.blake2b("|".join(str(p) for p in parts).encode(), digest_size=8).digest(), "big")


# ---------------------------------------------------------------------------
# 1. Receiver with a NON-EXCHANGEABLE prior.
#    Run 1 found q == 1/candidates identically, because the prior is uniform
#    over residual codebooks. A Dirichlet-style weighting over the residual
#    breaks that symmetry and makes q informative again.
# ---------------------------------------------------------------------------
class GeneralReceiver:
    """Exact posterior over all K! codebooks, arbitrary prior."""

    __slots__ = ("post", "resident", "base_post", "_tb")

    def __init__(self, resident: Tuple[int, ...], prior_floor: float = 0.10,
                 asymmetry: float = 0.0, seed: int = 0):
        tb = tables()
        self._tb = tb
        self.resident = tuple(resident)
        n = tb.n
        if prior_floor >= 1.0:
            # GENUINELY uniform prior over ALL codebooks.
            # (Previously prior_floor=1.0 zeroed the resident codebook, giving a
            # 40319-row support -- not uniform. Found by the Run 2 identity test.)
            base = np.full(n, 1.0 / n, dtype=np.float64)
        else:
            base = np.full(n, prior_floor / (n - 1), dtype=np.float64)
            base[tb.idM[self.resident]] = 1.0 - prior_floor
        if asymmetry > 0.0:
            # Deterministic, reproducible tilt over the non-resident codebooks,
            # keyed by a blake2b hash of (seed, codebook) so it is stable
            # across processes.
            import hashlib
            w = np.empty(n, dtype=np.float64)
            for i, perm in enumerate(tb.idM):
                if perm == self.resident:
                    w[i] = 1.0
                else:
                    h = int.from_bytes(hashlib.blake2b(
                        f"{seed}|{perm}".encode(), digest_size=8).digest(), "big")
                    w[i] = math.exp(asymmetry * ((h % 10_000) / 10_000.0 - 0.5))
            base = base * w
        self.base_post = base / base.sum()
        self.post = self.base_post.copy()

    def clone(self) -> "GeneralReceiver":
        r = GeneralReceiver.__new__(GeneralReceiver)
        r._tb = self._tb
        r.resident = self.resident
        r.base_post = self.base_post
        r.post = self.post.copy()
        return r

    def entropy(self) -> float:
        p = self.post[self.post > 0]
        return float(-(p * np.log(p)).sum())

    def entropy_bits(self) -> float:
        return self.entropy() / math.log(2)

    def effective_support(self) -> float:
        p = self.post[self.post > 0]
        return float(np.exp(-(p * np.log(p)).sum()))

    def n_active(self) -> int:
        return int((self.post > 0).sum())

    def _restrict(self, keep: np.ndarray) -> None:
        new = np.where(keep, self.post, 0.0)
        s = new.sum()
        self.post = np.full_like(self.post, 1.0 / self.post.size) if s <= 0 else new / s

    def constrain_token(self, token_index: int, concept: int) -> None:
        self._restrict(self._tb.M[:, concept] == token_index)

    def exclude_object(self, msg: Tuple[int, ...], triple) -> None:
        INV = self._tb.INV
        codes = triple_code(INV[:, msg[0]], INV[:, msg[1]], INV[:, msg[2]])
        self._restrict(codes != triple_code_of(triple))

    def require_object(self, msg: Tuple[int, ...], triple) -> None:
        INV = self._tb.INV
        codes = triple_code(INV[:, msg[0]], INV[:, msg[1]], INV[:, msg[2]])
        self._restrict(codes == triple_code_of(triple))

    def object_posterior(self, msg: Tuple[int, ...], scene) -> Dict[int, float]:
        INV = self._tb.INV
        codes = triple_code(INV[:, msg[0]], INV[:, msg[1]], INV[:, msg[2]])
        sc = [triple_code_of(o.triple) for o in scene.objects]
        S = float(self.post[np.isin(codes, sc)].sum())
        if S <= 0:
            return {o.index: 1.0 / len(scene.objects) for o in scene.objects}
        return {o.index: float(self.post[codes == triple_code_of(o.triple)].sum()) / S
                for o in scene.objects}

    def decide(self, msg: Tuple[int, ...], scene):
        pr = self.object_posterior(msg, scene)
        best = max(scene.objects, key=lambda o: (pr[o.index], -o.index))
        return best.index, pr[best.index], sum(1 for v in pr.values() if v > 0)

    def token_posterior(self, token_index: int) -> np.ndarray:
        out = np.zeros(K)
        np.add.at(out, self._tb.INV[:, token_index], self.post)
        s = out.sum()
        return out / s if s > 0 else np.full(K, 1.0 / K)

    def recovered(self, token_index: int, true_concept: int) -> bool:
        return int(np.argmax(self.token_posterior(token_index))) == int(true_concept)


# ---------------------------------------------------------------------------
# 2. Encoding under an ablated channel (inversion 6: which invariants matter)
# ---------------------------------------------------------------------------
INVARIANTS = ("color", "shape", "size")


def encode_full(mapping, triple):
    return tuple(mapping[c] for c in triple)


def encode_ablation(mapping, triple, drop: Sequence[str] = ()) -> Tuple[int, ...]:
    """Encode only the slots NOT dropped. A dropped slot emits no token."""
    return tuple(mapping[triple[s]] for s in range(3) if INVARIANTS[s] not in drop)


def decode_slots(msg: Tuple[int, ...], drop: Sequence[str] = ()) -> List[int]:
    return [msg[i] for i in range(3) if INVARIANTS[i] not in drop]


# ---------------------------------------------------------------------------
# 3. Channels (inversion 9). Each returns what the receiver actually observes.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Channel:
    name: str
    kind: str            # "symbolic" | "environmental" | "demonstrative"
    cost_fn: object


def channel_budget(ch: str, n_msg_slots: int, n_rounds: int) -> int:
    """Symbol cost, preregistered per channel kind."""
    if ch == "explicit_message":
        return n_rounds * n_msg_slots * 2          # request + response symbols
    if ch == "environment_signal":
        return n_rounds                              # one signal, no coding
    if ch == "demonstration":
        return n_rounds                              # showing, not telling
    if ch == "consequence_only":
        return n_rounds                              # success/failure bit each
    if ch == "observation_only":
        return n_rounds * n_msg_slots                # free access, no feedback
    raise ValueError(ch)


CHANNELS = ("explicit_message", "environment_signal", "demonstration",
            "consequence_only", "observation_only")


# ---------------------------------------------------------------------------
# 4. Sender adaptation (inversion 7)
# ---------------------------------------------------------------------------
@dataclass
class SenderModel:
    """The sender's own model of the receiver, used only if adapting."""
    resident: Tuple[int, ...]
    mode: str = "fixed"          # "fixed" | "adaptive"
    token_choice: Optional[Dict[int, int]] = None

    def encode(self, triple) -> Tuple[int, ...]:
        if self.mode == "fixed":
            return encode_full(self.resident, triple)
        # adaptive: substitute learned synonyms where known
        out = []
        for c in triple:
            out.append(self.token_choice.get(c, self.resident[c]) if self.token_choice else self.resident[c])
        return tuple(out)


# ---------------------------------------------------------------------------
# 5. Identifiability (inversion 4)
# ---------------------------------------------------------------------------
def residual_hypotheses(rec: GeneralReceiver) -> int:
    return rec.n_active()


def residual_entropy_bits(rec: GeneralReceiver) -> float:
    return rec.entropy_bits()


def task_relevant_uncertainty(rec: GeneralReceiver, msg, scene) -> float:
    """Entropy of the posterior over REFERENTS for this message."""
    pr = rec.object_posterior(msg, scene)
    ps = np.array([v for v in pr.values() if v > 0])
    return float(-(ps * np.log2(ps)).sum())


def identifiability(rec: GeneralReceiver) -> float:
    """Fraction of token meanings pinned to a point mass."""
    toks = [t for t in range(K) if rec.post[(rec._tb.M[:, 0] == t)].sum() > 0]
    pinned = 0
    for t in range(K):
        tp = rec.token_posterior(t)
        if float(tp.max()) > 0.999:
            pinned += 1
    return pinned / K
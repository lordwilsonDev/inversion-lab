"""B5 SUBSTRATE -- graded sender reliability + independently manipulable
TASK uncertainty vs SENDER-MODEL uncertainty.

WHAT B4 LEFT OPEN (§4 of the B5 blueprint)
------------------------------------------
B4 established, at Level 3, that different-sender evidence reduces global
uncertainty by ~12.93 bits and yields chance performance, while same-sender
evidence reduces it by ~12.98 bits and yields success. But the sender was
manipulated BINARY: correct or completely wrong. Task uncertainty and
sender-model uncertainty were never varied independently -- B4 achieved their
decoupling only at the extreme (a fully wrong sender).

B5 DECOUPLING STRATEGY (two independent levers)
-------------------------------------------------
LEVER 1 -- TASK uncertainty, via MESSAGE COMPLETENESS.
  If the receiver observes only 1 of the 3 message tokens, several scene
  objects remain consistent EVEN IF the receiver knows the sender's mapping
  exactly. Task entropy therefore rises WITHOUT any loss of model knowledge.

      P(object | 1 token, perfect model) < P(object | 3 tokens, perfect model)
      P(model | 1 token, perfect model) == P(model | 3 tokens, perfect model)

LEVER 2 -- SENDER-MODEL uncertainty, via GRADED RELIABILITY.
  The sender transmits through a channel of per-token reliability rho. Each
  concept->token pair the sender reports is correct with probability rho and
  corrupted otherwise. rho is a property of the GENERATING PROCESS, not a
  label (§9).

      P(reported pair correct) = rho     rho in PREREGISTERED_RELIABILITIES

These levers act on different state variables (object posterior vs codebook
posterior), so they can be varied orthogonally. That is verified empirically
in the feasibility matrix before the main experiment (§13).

RELIABILITY IS VERIFIED, NOT ASSUMED (§10)
-------------------------------------------
Realized per-item correctness is measured directly against the true mapping and
compared to the intended rho within PREREGISTERED_TOLERANCE.

DETERMINISM (§34)
-----------------
ALL seeds derive from blake2b stable_seed. No Python hash() anywhere -- that
defect (D14) must not recur.
"""
from __future__ import annotations

import hashlib
import math
import random
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

sys.path.insert(0, "/Users/lordwilson/projects/lexical-repair-crt")

from lexrepair.codebook import CONCEPTS, K, TOKENS  # noqa: E402
from lexrepair.world import Obj, Scene, encode, gen_scene  # noqa: E402
from lexrepair.receiver import tables  # noqa: E402

N_PERM = math.factorial(K)

# ---- PREREGISTERED BEFORE DATA COLLECTION (§9) ----
PREREGISTERED_RELIABILITIES = (1.00, 0.90, 0.75, 0.50)
PREREG_TEMPERATURES = (0.5, 1.0, 2.0)
EPS = 0.15                       # receiver's channel model (unchanged from B4)
RELIABILITY_TOLERANCE = 0.05     # §10: realized vs intended
N_OBJ = 5


def stable_seed(*parts) -> int:
    return int.from_bytes(
        hashlib.blake2b("|".join(str(p) for p in parts).encode(), digest_size=8).digest(),
        "big")


_TB = None


def tb():
    global _TB
    if _TB is None:
        _TB = tables()
    return _TB


def uniform_prior() -> np.ndarray:
    n = tb().n
    return np.full(n, 1.0 / n, dtype=np.float64)


# =====================================================================
# GRADED RELIABILITY CHANNEL (§9)
# =====================================================================
def send_with_reliability(mapping: Sequence[int], triple: Sequence[int],
                          rho: float, rng: random.Random) -> Tuple[int, ...]:
    """Sender transmits the encoding of `triple` through a channel of
    per-token reliability rho.

        P(reported token is the sender's true token) = rho
        P(reported token is corrupted)             = 1 - rho

    Corrupted tokens are drawn uniformly from the K-1 alternatives, so the
    corruption carries no information about the true token. This makes rho a
    genuine property of the generating process rather than a condition label.
    """
    out = []
    for c in triple:
        true_tok = mapping[c]
        if rng.random() < rho:
            out.append(int(true_tok))
        else:
            alts = [t for t in range(K) if t != true_tok]
            out.append(int(alts[rng.randrange(len(alts))]))
    return tuple(out)


def realized_reliability(mapping_true: Sequence[int], reports: List[Sequence[int]],
                        triples: List[Sequence[int]]) -> float:
    """Fraction of reported (slot) tokens that were correct -- the realized rho."""
    if not reports:
        return float("nan")
    tot = cor = 0
    for rep, tri in zip(reports, triples):
        for slot in range(len(tri)):
            tot += 1
            if int(rep[slot]) == int(mapping_true[tri[slot]]):
                cor += 1
    return cor / tot if tot else float("nan")


# =====================================================================
# LIKELIHOOD (unchanged graded noisy channel from B4)
# =====================================================================
def object_likelihood(scene: Scene, msg: Sequence[int], eps: float = EPS) -> np.ndarray:
    """L[i, o] = prod_j P(msg[j] | f_i, c_j(o)). Strictly positive for eps>0."""
    t = tb()
    p_hit, p_miss = 1.0 - eps, eps / (K - 1)
    L = np.ones((t.n, len(scene.objects), ))
    for oi, obj in enumerate(scene.objects):
        for slot in range(3):
            c, tok = obj.triple[slot], msg[slot]
            L[:, oi] *= np.where(t.M[:, c] == tok, p_hit, p_miss)
    return L


class B5Receiver:
    """Posterior over codebooks. Graded evidence; never eliminates."""

    __slots__ = ("post", "eps", "n_obs")

    def __init__(self, prior: Optional[np.ndarray] = None, eps: float = EPS):
        self.post = uniform_prior() if prior is None else np.array(prior, float)
        self.eps = eps
        self.n_obs = 0

    def observe(self, scene: Scene, msg: Sequence[int], target_index: int):
        L = object_likelihood(scene, msg, self.eps)
        step = L[:, target_index]
        self.post = self.post * step
        s = self.post.sum()
        self.post = uniform_prior() if s <= 0 else self.post / s
        self.n_obs += 1
        return self

    def partial_object_posterior(self, scene: Scene, msg_full: Sequence[int],
                                 n_visible: int) -> np.ndarray:
        """Object posterior when only the FIRST n_visible message tokens are
        observed. Unobserved slots contribute likelihood 1 (uninformative),
        which is exactly what makes task uncertainty rise without touching the
        model posterior.
        """
        msg = list(msg_full[:n_visible]) + [None] * (3 - n_visible)
        t = tb()
        p_hit, p_miss = 1.0 - self.eps, self.eps / (K - 1)
        L = np.ones((t.n, len(scene.objects)))
        for oi, obj in enumerate(scene.objects):
            for slot in range(3):
                tok = msg[slot]
                if tok is None:          # slot not observed -> uninformative
                    continue
                L[:, oi] *= np.where(t.M[:, obj.triple[slot]] == tok, p_hit, p_miss)
        w = self.post @ L
        s = w.sum()
        return np.full(len(scene.objects), 1.0 / len(scene.objects)) if s <= 0 else w / s

    def object_posterior(self, scene: Scene, msg: Sequence[int]) -> np.ndarray:
        return self.partial_object_posterior(scene, msg, 3)

    def decide_proportional(self, pobj: np.ndarray) -> int:
        return int(np.argmax(pobj))

    def decide_sampled(self, pobj: np.ndarray, T: float, rng: random.Random) -> int:
        w = np.power(np.clip(pobj, 1e-300, None), 1.0 / T)
        s = w.sum()
        if s <= 0:
            return int(np.argmax(pobj))
        w /= s
        r, acc = rng.random(), 0.0
        for i, wi in enumerate(w):
            acc += wi
            if r <= acc:
                return i
        return len(w) - 1

    def posterior_diagnostics(self) -> Dict[str, float]:
        p = self.post
        q = p[p > 0]
        return {
            "n_positive": int((p > 0).sum()),
            "entropy_bits": float(-(q * np.log2(q)).sum()),
            "max_posterior": float(p.max()),
            "min_posterior": float(q.min()),
            "effective_hypotheses": float(np.exp(-(p * np.log(p + 1e-300)).sum())),
            "top10pct_mass": float(np.sort(p)[::-1][:max(1, len(p) // 10)].sum()),
        }

def derangement(seed: int):
    """Deterministic derangement of the identity (blake2b-seeded)."""
    from lexrepair import codebook as CB
    return CB.derangement(random.Random(stable_seed("b5der", seed)))

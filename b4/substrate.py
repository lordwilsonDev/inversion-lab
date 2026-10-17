"""B4 SUBSTRATE -- graded evidence, non-uniform posterior, posterior-sensitive decision.

WHY THIS EXISTS (§2 reconstruction, §3/§4 gates)
-------------------------------------------------
Level-3 re-derivation from frozen Run 1 rows (1920 rows) showed the OLD substrate's
degeneracy is SHARPER than previously stated and also slightly different:

  * At the CODEBOOK level the old posterior CAN be non-uniform. With
    prior_floor=0.10, mass 0.9 sits on IDENTITY and survives `exclude_object`
    (H = 1.99 bits over 40200 hypotheses, max/min ratio 3.6e5).
  * BUT at the OBJECT level -- the level decisions are actually made -- the
    posterior is uniform in EVERY trial. Broad scan: 900/900 observations,
    max-p exactly 1/candidates at every candidate count (2,3,4).

The reason is precise: the concentrated prior mass sits on codebooks that
predict NO scene object under the query message, so it is discarded when
`object_posterior` renormalises over scene-predicting codebooks only.

So the old substrate is NOT IDENTIFYING for posterior structure. That is the
justification for B4, established empirically rather than assumed.

WHAT CHANGES (§3)
-----------------
  OLD: constraint -> hard elimination -> uniform posterior on survivors
       -> deterministic lowest-index tie-break -> behaviour ~ candidate count
  B4: evidence   -> GRADED likelihood (noisy channel, no elimination)
       -> non-uniform posterior over the FULL hypothesis space
       -> posterior-proportional or temperature-sampled decision
       -> behaviour can depend on posterior STRUCTURE

MATHEMATICAL SPECIFICATION (§5, §6, §7)
--------------------------------------
Hypothesis space: F = S_K, all K! codebooks f: concepts -> tokens. |F| = K! = 40320.

Prior: p_0(f) uniform, or a deterministic tilted prior. Verified to remain
  non-uniform after every update (§6).

Likelihood (graded, §7): symmetric noisy channel on the token axis.
  For observed token t at slot j and hypothesis f:
      P(t | f, c_j) = 1 - eps        if f(c_j) = t
                    = eps / (K - 1)   otherwise
  For a message t = (t0,t1,t2) and candidate object o with concepts c(o):
      L(f, o) = prod_{j=0..2} P(t_j | f, c_j(o))

  L is STRICTLY POSITIVE for every (f,o) when eps > 0. No hypothesis is ever
  eliminated; the object-posterior support is ALWAYS the full scene. Candidate
  count is therefore CONSTANT (= scene size) by construction, so every
  discriminative signal must live in the posterior's SHAPE.

Evidence accumulation (codebook level):
      p_t(f) proportional to  p_{t-1}(f) * L(f, target_t)     [attributed evidence]
  Unattributed evidence ("raw information") instead applies Lbar(f) = mean_o L(f,o),
  which is object-independent and therefore carries no target-discriminating signal.

Query (object level):
      P(o | evidence) proportional to  sum_f p(f | evidence) * L_query(f, o)

Decision policies (§8):
  Policy A -- posterior-proportional: choose argmax_o P(o|e). Deterministic.
  Policy B -- temperature sampling:     P(action=o) proportional to P(o|e)^(1/T),
                                         for PREREGISTERED T. T -> 0 recovers A.

TEMPERATURES PREREGISTERED BEFORE DATA COLLECTION: T in {0.5, 1.0, 2.0}.
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

# ---- PREREGISTERED BEFORE DATA COLLECTION (§8) ----
EPS = 0.15
PRIOREG_TEMPERATURES = (0.5, 1.0, 2.0)
DECISION_POLICIES = ("posterior_proportional", "temperature_sampling")


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


def tilted_prior(conc: float, seed: int) -> np.ndarray:
    """Deterministic reproducible non-uniform prior over codebooks."""
    rng = np.random.default_rng(stable_seed("b4prior", seed))
    w = np.exp(conc * (rng.random(tb().n) - 0.5) * 4.0)
    return w / w.sum()


def object_likelihood(scene: Scene, msg: Sequence[int], eps: float = EPS) -> np.ndarray:
    """L[i, o] = prod_j P(msg[j] | f_i, c_j(o))  -- shape (n_codebooks, n_objects).

    Strictly positive everywhere when eps > 0. Nothing is eliminated.
    """
    t = tb()
    p_hit, p_miss = 1.0 - eps, eps / (K - 1)
    L = np.ones((t.n, len(scene.objects)), dtype=np.float64)
    for oi, obj in enumerate(scene.objects):
        for slot in range(3):
            c, tok = obj.triple[slot], msg[slot]
            L[:, oi] *= np.where(t.M[:, c] == tok, p_hit, p_miss)
    return L


class B4Receiver:
    """Posterior over codebooks under graded evidence. Never eliminates a hypothesis."""

    __slots__ = ("post", "eps", "_acc")

    def __init__(self, prior: Optional[np.ndarray] = None, eps: float = EPS):
        self.post = uniform_prior() if prior is None else np.array(prior, dtype=np.float64)
        self.eps = eps
        self._acc: Optional[np.ndarray] = None

    def observe(self, scene: Scene, msg: Sequence[int], target_index: Optional[int] = None):
        """Accumulate one graded evidence item.

        target_index=None -> 'unattributed / raw information' evidence: the
        sender's encoding is not tied to a known scene object, so the
        likelihood is averaged over objects and carries no target signal.
        """
        L = object_likelihood(scene, msg, self.eps)
        if target_index is None:
            step = L.mean(axis=1)
        else:
            step = L[:, target_index]
        self._acc = step if self._acc is None else self._acc * step
        self.post = self.post * step
        s = self.post.sum()
        self.post = uniform_prior() if s <= 0 else self.post / s
        return self

    def object_posterior(self, scene: Scene, query_msg: Sequence[int]) -> np.ndarray:
        """P(o | accumulated evidence, query message). Support = full scene always."""
        L = object_likelihood(scene, query_msg, self.eps)
        w = self.post @ L                      # (n_objects,) posterior mass per object
        s = w.sum()
        return np.full(len(scene.objects), 1.0 / len(scene.objects)) if s <= 0 else w / s

    # ---- decision policies (§8) ----
    def decide_proportional(self, pobj: np.ndarray) -> int:
        return int(np.argmax(pobj))

    def decide_sampled(self, pobj: np.ndarray, T: float, rng: random.Random) -> int:
        w = np.power(np.clip(pobj, 1e-300, None), 1.0 / T)
        s = w.sum()
        if s <= 0:
            return int(np.argmax(pobj))
        w = w / s
        r, acc = rng.random(), 0.0
        for i, wi in enumerate(w):
            acc += wi
            if r <= acc:
                return i
        return len(w) - 1

    def posterior_diagnostics(self) -> Dict[str, float]:
        p = self.post
        q = p[p > 0]
        H = float(-(q * np.log2(q)).sum())
        k = max(1, len(p) // 10)
        return {
            "n_positive": int((p > 0).sum()),
            "entropy_bits": H,
            "max_posterior": float(p.max()),
            "min_posterior": float(q.min()),
            "effective_hypotheses": float(np.exp(-(p * np.log(p + 1e-300)).sum())),
            "top10pct_mass": float(np.sort(p)[::-1][:k].sum()),
        }
"""DEFECT REGISTRY — permanent, machine-readable.

Every defect class discovered in the causal-audit trajectory, with the
information a future regression failure needs in order to be actionable:

    id, title, signature, repair, provenance, invariant

`signature` is what a detector looks for. `repair` is the pattern that worked.
`invariant` links the defect to a promoted engineering invariant (SS8).

Nothing here is a placeholder. Each entry records a defect that actually
occurred, with the artifact that recorded it.
"""
from __future__ import annotations

REGISTRY = {
    # ---------------------------------------------------------------- D5
    "D5": {
        "title": "aggregation mismatch (cumulative vs incremental)",
        "signature": "two quantities being compared use different denominators "
                     "or different reference points -- e.g. a cumulative value "
                     "from ignorance against a per-step increment",
        "detector": "compare_like_with_like",
        "repair": "compare like with like: cumulative-to-cumulative or "
                  "increment-to-increment. Never mix.",
        "invariant": "INV-10",
        "provenance": "Run 2 R2E1: cumulative A vs incremental B produced a "
                      "false max|A-B| of 5.807. Like-for-like the identity held "
                      "to 5.33e-15. False retraction avoided.",
    },
    # ---------------------------------------------------------------- D6
    "D6": {
        "title": "prior asymmetry washed out by first update",
        "signature": "a non-uniform prior whose non-uniform mass sits on a "
                     "hypothesis that the first update eliminates, so the "
                     "posterior renormalises to uniform",
        "detector": "prior_washing",
        "repair": "asymmetric tilt must survive the first operation; verify "
                  "post-update flatness before describing a prior as non-uniform",
        "invariant": "INV-06",
        "provenance": "Run 2 D6: prior_floor=0.10 placed 0.9 mass on IDENTITY, "
                      "which the first constraint eliminated, washing out the "
                      "asymmetry. Control arm was silently vacuous (0/180).",
    },
    # ---------------------------------------------------------------- D7
    "D7": {
        "title": "metric mechanically determined by another variable",
        "signature": "two reported metrics are an exact function of each other; "
                     "the 'dissociation' between them is arithmetically impossible",
        "detector": "metric_identity",
        "repair": "record the identity, remove the metric from the independent "
                  "evidence set, and never call it a dissociation",
        "invariant": "INV-07",
        "provenance": "Run 2 D7: mrr was a deterministic function of n_pins "
                      "(0/0.25/0.375/0.5 across all 56 pin sets). A reported "
                      "'identical mrr dissociation' was an artifact.",
    },
    # ---------------------------------------------------------------- D8
    "D8": {
        "title": "marginal result reverses after conditioning",
        "signature": "a marginal effect whose sign or magnitude changes once a "
                     "known conditioning variable is applied",
        "detector": "conditioning_reversal",
        "repair": "stratify BEFORE interpretation; a marginal reading is not "
                  "admissible when a conditioning variable is known",
        "invariant": "INV-06",
        "provenance": "Run 3 D8: R3E4 marginal +0.284 reversed to -0.060 "
                      "within candidate-count strata.",
    },
    # ---------------------------------------------------------------- D9
    "D9": {
        "title": "incorrect expectation comparison baseline",
        "signature": "a mean is compared against a function of the mean rather "
                     "than the mean of that function (Jensen error)",
        "detector": "expectation_baseline",
        "repair": "compare mean(q) against mean(1/c), not against 1/mean(c)",
        "invariant": "INV-07",
        "provenance": "Run 3 D9: claimed q escaped 1/candidates; the match was "
                      "exact (mean(q)=0.715833=mean(1/c)). Wrong baseline "
                      "manufactured a false novelty claim.",
    },
    # ---------------------------------------------------------------- D10
    "D10": {
        "title": "distinct experimental arms are byte-identical implementations",
        "signature": "two arms intended to differ produce identical "
                     "implementation and identical output distributions",
        "detector": "duplicate_arms",
        "repair": "differentiate the implementations; agreement between "
                  "identical code is not evidence of anything",
        "invariant": "INV-08",
        "provenance": "B4 D10: arms C, D and F were byte-identical. Their "
                      "apparent agreement was an artifact.",
    },
    # ---------------------------------------------------------------- D12
    "D12": {
        "title": "zero-variance explanatory variable caused by design",
        "signature": "a variable proposed as an explanatory factor has zero "
                     "within-cell variance because it was fixed by construction",
        "detector": "zero_variance",
        "repair": "stratify on a variable that actually varies within the cell; "
                  "otherwise you are stratifying on your own design",
        "invariant": "INV-07",
        "provenance": "B4 D12: cb_concentration had zero within-cell variance; "
                      "stratifying by it stratified by design parameters.",
    },
    # ---------------------------------------------------------------- D13
    "D13": {
        "title": "supposed null is not actually null",
        "signature": "a control labelled 'null' still carries a causal pathway "
                     "to the target construct",
        "detector": "null_validity",
        "repair": "construct the null from a source with no intended pathway "
                  "while preserving surface statistics; test the null before "
                  "using it",
        "invariant": "INV-08",
        "provenance": "B4 D13: same-sender evidence about other targets is NOT "
                      "null under model learning (0.990). Reporting it as one "
                      "would have manufactured a false conclusion. Replaced "
                      "with a different-sender null (0.220 vs chance 0.200).",
    },
    # ---------------------------------------------------------------- D14
    "D14": {
        "title": "process-randomised hashing destroys reproducibility",
        "signature": "randomness seeded from hash() on strings, which Python "
                     "randomises per process",
        "detector": "hash_seeding",
        "repair": "derive seeds from explicit stable identifiers (blake2b)",
        "invariant": "INV-10",
        "provenance": "B4 D14: abs(hash((str,int))) seeding made trials "
                      "non-reproducible across processes (PYTHONHASHSEED "
                      "1/2/3 gave three different values). Same class as the "
                      "very first defect of the original trajectory.",
    },
    # ---------------------------------------------------------------- D17
    "D17": {
        "title": "preregistered decision rule violates measurement constraints",
        "signature": "a deterministic tie-break (argmax) over a diffuse "
                     "posterior used as a primary outcome; produces a systematic "
                     "low-index preference",
        "detector": "deterministic_decision",
        "repair": "use posterior-sampled decision at preregistered temperatures; "
                  "preregistration does not validate a defective instrument",
        "invariant": "INV-09",
        "provenance": "B5 D17: preregistered PRIMARY outcome used argmax. "
                      "Position spread 0.358; task effect -0.007 at index 0 "
                      "growing to +0.732 at index 4. Under sampled policies the "
                      "spread collapsed to 0.017 and the effect was uniform.",
    },
    # ---------------------------------------------------------------- D19
    "D19": {
        "title": "truthiness check on a numeric experimental value",
        "signature": "a validation sweep uses Python truthiness over fields "
                     "that may be numeric, so a legitimate 0.0 is falsy",
        "detector": "numeric_truthiness",
        "repair": "test explicit boolean verdicts only; never sweep numeric "
                  "fields with `if value:`",
        "invariant": "INV-09",
        "provenance": "B6 D19: C4_observed=0.0 was falsy, so ALL_PASS reported "
                      "a false negative. Fourth instance of the same bug class.",
    },
    # ---------------------------------------------------------------- D20
    "D20": {
        "title": "freeze / preservation failure on correction",
        "signature": "a defect is corrected in place, overwriting the pre-fix "
                     "artifact, so the prior state is unrecoverable",
        "detector": "preservation",
        "repair": "freeze BEFORE correcting, not after. Never overwrite a "
                  "retracted artifact under the same filename.",
        "invariant": "INV-04",
        "provenance": "chaos D20: the error signal was passed unconditionally "
                      "as correct=False. Fixing it re-ran the experiment and "
                      "overwrote the pre-fix rows. pre_fix/ is empty; four "
                      "pre-fix numbers survive only as prose and are marked "
                      "UNVERIFIABLE.",
    },
    # ---------------------------------------------------------------- D21
    "D21": {
        "title": "receiver/state contamination across trials",
        "signature": "one mutable state object is reused across trials within a "
                     "condition, so a decision is taken after the state has "
                     "already absorbed other trials' inputs",
        "detector": "state_contamination",
        "repair": "fresh state per (trial, condition); assert construction "
                  "count equals trial count",
        "invariant": "INV-09",
        "provenance": "chaos D21: the pipeline-sensitivity harness created one "
                      "Receiver per trial then presented all three targets to "
                      "it. Null-world check gave +0.5433 instead of ~0. Fixed "
                      "to +0.0042.",
    },
    # ---------------------------------------------------------------- D22
    "D22": {
        "title": "integrity check uses the wrong key",
        "signature": "a duplicate/uniqueness check omits a grouping field, so a "
                     "correctly structured dataset reports mass duplication",
        "detector": "uniqueness_key",
        "repair": "verify the check's own key against the design before "
                  "concluding the DATA is wrong; log the false alarm",
        "invariant": "INV-09",
        "provenance": "chaos D22: key (trial,arm,rho,T) omitted `target`; "
                      "reported 9600 duplicates on a correct 400x2x3 design.",
    },
    # ---------------------------------------------------------------- D23
    "D23": {
        "title": "verification output diverges from source representation",
        "signature": "a narrative conclusion is printed alongside code that "
                     "computes a different thing; the two disagree and the "
                     "narrative wins",
        "detector": "narrative_code_divergence",
        "repair": "make narrative output CONDITIONAL on the computed result. "
                  "Never print an asserted conclusion next to an unverified "
                  "check. Reconcile disagreements between two numbers that do "
                  "not add up BEFORE shipping.",
        "invariant": "INV-03",
        "provenance": "chaos D23: object attributes stored 'a/b/c'; "
                      "str.split() splits on whitespace and returned one "
                      "element, so every token comparison was silently empty. "
                      "The prose claimed a confound; the code printed NONE. "
                      "Shipped-narrative risk caught only by reconciling "
                      "against a prior standalone result.",
    },
}


def signature(did: str) -> str:
    return REGISTRY[did]["signature"]


def describe_failure(did: str, module: str, claim: str, detail: str) -> str:
    """SS10: a failure must be actionable, not just 'FAIL'."""
    d = REGISTRY[did]
    return (
        f"\n"
        f"{'='*74}\n"
        f"REGRESSION FAILURE -- resembles historical defect {did}\n"
        f"{'='*74}\n"
        f"  defect        : {did} -- {d['title']}\n"
        f"  module        : {module}\n"
        f"  affected claim: {claim}\n"
        f"  observed      : {detail}\n"
        f"  historical    : {d['provenance']}\n"
        f"  repair pattern: {d['repair']}\n"
        f"  invariant     : {d['invariant']}\n"
        f"{'='*74}\n"
        f"  RECOMMENDED ACTION: repair per the pattern above, then re-run the\n"
        f"  full suite. Do not interpret the claim while this defect is open.\n"
        f"{'='*74}\n"
    )


def ids() -> list[str]:
    return sorted(REGISTRY, key=lambda s: int(s[1:]))
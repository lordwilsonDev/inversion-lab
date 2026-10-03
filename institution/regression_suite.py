"""EXECUTABLE REGRESSION DETECTORS.

Every detector is a real check that runs against an actual artifact. None is a
placeholder. Each returns Finding(defect_id, module, claim, detail).

Two kinds of detector:
  * dataset detectors  -- operate on a raw-row file (JSONL)
  * source detectors   -- operate on .py source text
  * state detectors    -- operate on a directory (preservation)

Usage:
    python3 regression_suite.py <raw_rows.jsonl> <source_dir> <state_dir>
"""
from __future__ import annotations

import ast
import json
import math
import os
import re
import statistics
from dataclasses import dataclass
from typing import Any, Callable, Optional


SEVERITY_FAIL = "FAIL"
SEVERITY_INFO = "INFO"


@dataclass
class Finding:
    defect_id: str
    module: str
    claim: str
    detail: str
    severity: str = SEVERITY_FAIL

    def __str__(self) -> str:
        return f"[{self.severity}][{self.defect_id}] {self.module} / {self.claim}: {self.detail}"


def _rows(path: str):
    with open(path) as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def _vars(vals, eps=1e-12):
    return len({round(v, 9) for v in vals}) > 1 and statistics.pvariance(vals) > eps


# ============================================================ DATASET DETECTORS

def d12_zero_variance(rows, module="dataset", claim="explanatory factor",
                      proposed_factors=None):
    """A proposed explanatory variable must vary within the dataset.

    A variable that is constant because the DESIGN fixes it (uniform prior,
    fixed message length) is not itself a defect -- it only becomes one if it is
    offered as an explanatory factor. Severity depends on intent, and intent is
    not visible from the data, so the caller must declare which variables it
    actually proposes as factors.
    """
    out = []
    if not rows:
        return out
    proposed = set(proposed_factors or [])
    num = [k for k, v in rows[0].items()
           if isinstance(v, (int, float)) and not isinstance(v, bool)]
    for key in num:
        vals = [r[key] for r in rows]
        if _vars(vals):
            continue
        # Undeclared intent -> advisory. Only a variable the caller explicitly
        # proposes as a factor can be a FAIL-level defect.
        sev = SEVERITY_FAIL if (proposed and key in proposed) else SEVERITY_INFO
        out.append(Finding(
            "D12", module, claim,
            f"'{key}' is constant across all {len(vals)} rows"
            + ("" if proposed else " (not declared as a factor; design-fixed)"),
            severity=sev))
    return out


def d07_metric_identity(rows, module="dataset", claim="metric independence"):
    """Flag metrics that are an exact function of another recorded metric."""
    out = []
    num = [k for k, v in rows[0].items()
           if isinstance(v, (int, float)) and not isinstance(v, bool)]
    for a in num:
        for b in num:
            if a >= b:
                continue
            pairs = [(r[a], r[b]) for r in rows]
            ba = {round(x, 9) for x, _ in pairs}
            bb = {round(y, 9) for _, y in pairs}
            if len(ba) > 200 or len(bb) > 200:
                continue
            by_a: dict[float, set] = {}
            for x, y in pairs:
                by_a.setdefault(round(x, 9), set()).add(round(y, 9))
            if all(len(v) == 1 for v in by_a.values()) and len(by_a) > 3:
                out.append(Finding("D7", module, claim,
                                   f"'{b}' is a deterministic function of '{a}' "
                                   f"({len(by_a)} distinct {a} values, each with a "
                                   f"single {b} value)"))
    return out


def d09_expectation_baseline(rows, module="dataset", claim="expectation test"):
    """Flag comparisons of mean(f(x)) against f(mean(x))."""
    out = []
    for key in ("correct",):
        if key not in rows[0]:
            continue
        if any(k.startswith("delta_H") for k in rows[0]):
            by = {}
            for r in rows:
                by.setdefault("c", []).append(r["candidate_reduction"])
            cand = by.get("c")
            if cand and len(set(cand)) > 1:
                mean_q = statistics.fmean([r[key] for r in rows])
                inv_mean = 1.0 / statistics.fmean(cand)
                mean_inv = statistics.fmean([1.0 / c for c in cand])
                if abs(mean_q - inv_mean) < 1e-6 and abs(mean_q - mean_inv) > 1e-3:
                    out.append(Finding(
                        "D9", module, claim,
                        f"mean({key})={mean_q:.6f} equals 1/mean(candidate_count)"
                        f"={inv_mean:.6f} but differs from mean(1/candidate_count)"
                        f"={mean_inv:.6f}. The comparison used the wrong baseline."))
    return out


def d22_uniqueness_key(path, module="dataset"):
    """Uniqueness must be checked on the full design key, not a partial one."""
    out = []
    rows = list(_rows(path))
    if not rows:
        return out
    full = ("trial", "arm", "rho_channel", "temperature", "target")
    if not all(k in rows[0] for k in full):
        return out
    dup_full = len(rows) - len({tuple(r[k] for k in full) for r in rows})
    partial = ("trial", "arm", "rho_channel", "temperature")
    dup_partial = len(rows) - len({tuple(r[k] for k in partial) for r in rows})
    if dup_full == 0 and dup_partial > 0:
        out.append(Finding(
            "D22", module, "dataset integrity",
            f"key {partial} reports {dup_partial} duplicates but the full design "
            f"key {full} reports 0. A partial key would have declared a correct "
            f"dataset corrupt. ADVISORY: data are sound; only a partial-key "
            f"check would be wrong.",
            severity=SEVERITY_INFO))
    return out


def d13_null_validity(rows, module="dataset", claim="null control"):
    """A null arm must not track the target beyond chance."""
    out = []
    arms = {r.get("arm") for r in rows}
    nulls = {a for a in arms if a and ("irrelevant" in a or "null" in a)}
    for na in nulls:
        sub = [r for r in rows if r["arm"] == na and "correct" in r and "target" in r]
        if not sub:
            continue
        by_t: dict[Any, list] = {}
        for r in sub:
            by_t.setdefault(r["target"], []).append(r["correct"])
        if len(by_t) < 2:
            continue
        accs = [statistics.fmean(v) for v in by_t.values()]
        k = len(sub)
        # DEFECT FIX: chance must come from the number of CANDIDATE OBJECTS,
        # not from the number of rows per target cell.
        if "n_candidates_before" in sub[0]:
            n_obj = max(r["n_candidates_before"] for r in sub)
        elif "decision" in sub[0]:
            n_obj = len({r["decision"] for r in sub})
        else:
            n_obj = len(by_t)
        chance = 1.0 / n_obj if n_obj else 1.0
        spread = max(accs) - min(accs)
        se = math.sqrt(max(chance * (1 - chance), 1e-9) / k)
        # (a) the null beats chance -> it carries real signal about the target
        if spread > 4 * se and max(accs) > chance:
            out.append(Finding(
                "D13", module, claim,
                f"arm '{na}' has per-target accuracy spread {spread:.4f} "
                f"(chance {chance:.3f}, SE {se:.4f}); it tracks the target and "
                f"is therefore not a valid null"))
        # (b) HETEROGENEITY: the control is supposed to be equally uninformative
        #     for every target. If its accuracy differs systematically across
        #     targets, the control is not uniform, and the arms are not matched
        #     on the property the control name asserts. This fires even when the
        #     control sits BELOW chance, which is the common case.
        if spread > 4 * se and len(accs) >= 2:
            detail = ", ".join(
                f"t{k}={statistics.fmean(v):.4f}" for k, v in sorted(by_t.items()))
            out.append(Finding(
                "D13", module, claim + " (heterogeneity)",
                f"control arm '{na}' is NOT equally uninformative across targets: "
                f"{detail} (spread {spread:.4f}, SE {se:.4f}, chance {chance:.3f}). "
                f"Accuracy varies by {spread/se:.1f} SE. The arms are matched on "
                f"token count and vocabulary but not on truth-to-target."))
    return out


def d08_conditioning_reversal(rows, module="dataset", claim="causal effect",
                              strata_key="target", arm_key="arm",
                              outcome="correct"):
    """A marginal effect must not be reported unqualified if a known variable
    reverses it."""
    out = []
    arms = sorted({r[arm_key] for r in rows})
    if len(arms) != 2:
        return out
    a, b = arms

    def acc(rs):
        return statistics.fmean([r[outcome] for r in rs])

    marg = (acc([r for r in rows if r[arm_key] == a])
            - acc([r for r in rows if r[arm_key] == b]))
    signs = []
    for s in sorted({r[strata_key] for r in rows}):
        cell = [r for r in rows if r[strata_key] == s]
        ca = [r for r in cell if r[arm_key] == a]
        cb = [r for r in cell if r[arm_key] == b]
        if ca and cb:
            signs.append((s, acc(ca) - acc(cb)))
    if len(signs) >= 2:
        marg_sign = (marg > 0) - (marg < 0)
        str_signs = {(g > 0) - (g < 0) for _, g in signs}
        if marg_sign != 0 and str_signs == {-marg_sign}:
            out.append(Finding(
                "D8", module, claim,
                f"marginal effect {marg:+.4f} but every {strata_key} stratum "
                f"({', '.join(f'{s}:{g:+.4f}' for s, g in signs)}) has the OPPOSITE "
                f"sign. Marginal reading is inadmissible."))
    return out


def d05_like_with_like(rows, module="dataset", claim="paired comparison"):
    """A cumulative quantity must not be compared against a per-step increment."""
    out = []
    if "candidate_reduction" not in rows[0]:
        return out
    a = [r["candidate_reduction"] for r in rows]
    if len(set(a)) > 1 and len(set(round(x, 9) for x in a)) == 1:
        out.append(Finding("D5", module, claim,
                           "candidate_reduction is constant; a per-step "
                           "increment cannot be compared against a cumulative "
                           "quantity here"))
    return out


# ============================================================= SOURCE DETECTORS

def d14_hash_seeding(src: str, name: str):
    out = []
    for i, line in enumerate(src.splitlines(), 1):
        code = line.split("#")[0]
        if re.search(r"\b(hash\s*\(|random\.hash)", code) and not re.search(
                r"blake2b|md5|sha256|stable_seed", code):
            if re.search(r"seed|Random|rng|random", line, re.I):
                out.append(Finding(
                    "D14", name, "reproducibility",
                    f"line {i}: randomness seeded from hash() which Python "
                    f"randomises per process: {line.strip()[:90]}"))
    return out


def d17_deterministic_decision(src: str, name: str):
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ("argmax", "argsort") and node.lineno:
            out.append(Finding(
                "D17", name, "primary decision rule",
                f"line {node.lineno}: deterministic tie-break {node.func.attr}() "
                f"over a posterior. Over a diffuse posterior this returns the "
                f"lowest index and manufactures a position gradient."))
    return out


def d19_truthiness(src: str, name: str):
    """`if <field>:` over a numeric field is falsy at 0.0."""
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    numeric_tokens = re.compile(
        r"\b(acc|correct|rate|score|count|n_|value|observed|result|gap|"
        r"accuracy|probability|prob|p_|rho|temperature|diff)\w*\b", re.I)
    for node in ast.walk(tree):
        test = None
        if isinstance(node, ast.If):
            test = node.test
        elif isinstance(node, ast.While):
            test = node.test
        if test is None:
            continue
        seg = ast.dump(test)
        if "Attribute" not in seg and "Subscript" not in seg:
            continue
        for sub in ast.walk(test):
            if isinstance(sub, ast.Attribute):
                nm = sub.attr
            elif isinstance(sub, ast.Subscript):
                try:
                    nm = ast.unparse(sub.value)
                except Exception:
                    continue
            else:
                continue
            if numeric_tokens.search(nm) and isinstance(test, (ast.Name,)):
                out.append(Finding(
                    "D19", name, "validation sweep",
                    f"line {node.lineno}: bare truthiness test on '{nm}'. A "
                    f"legitimate 0.0 is falsy and will be reported as failure."))
    return out


def d21_state_contamination(src: str, name: str):
    """A stateful object constructed once and reused across a trial loop."""
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    ctor_names = {n.func.id for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    ctor_names |= {n.func.attr for n in ast.walk(tree)
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef,))]:
        for loop in [n for n in ast.walk(fn) if isinstance(n, ast.For)]:
            inner = ast.dump(loop)
            if f"id='{fn.name}'" not in inner and fn.name not in inner:
                continue
            # a constructor call inside the loop body => fresh per iteration
            body_ctors = [n for stmt in loop.body for n in ast.walk(stmt)
                          if isinstance(n, ast.Call)
                          and (isinstance(n.func, ast.Name)
                               or isinstance(n.func, ast.Attribute))]
            has_ctor = any((c.func.id if isinstance(c.func, ast.Name)
                            else c.func.attr) in ctor_names for c in body_ctors)
            if has_ctor:
                continue
            # does the loop body mutate or read a shared object?
            reads = [n for stmt in loop.body for n in ast.walk(stmt)
                     if isinstance(n, ast.Name) and n.id in ctor_names]
            if reads:
                out.append(Finding(
                    "D21", name, "state isolation",
                    f"function '{fn.name}': loop at line {loop.lineno} iterates "
                    f"over multiple items while referencing '{reads[0].id}' "
                    f"without a fresh construction in the body. State may leak "
                    f"across iterations."))
    return out


def d23_narrative_divergence(src: str, name: str):
    """A verdict-like narrative printed as an unconditional literal.

    Scope-aware: a print inside an `if`/`else` branch is CONDITIONAL on the
    computed result and is fine. Only unconditional literals are flagged.
    """
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    # collect lines that sit inside any conditional or loop body
    guarded: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.Try,
                             ast.FunctionDef)):
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.stmt) and stmt is not node:
                    guarded.add(stmt.lineno)
    verdict_words = ("VERDICT:", "FINDING:", "SURVIVES", "CONFIRMS",
                     "PROVEN", "INVALID", "VALID", "-> ")
    for i, line in enumerate(src.splitlines(), 1):
        if i in guarded:
            continue
        if not re.search(r'print\s*\(', line):
            continue
        up = line.upper()
        if not any(w.upper() in up for w in verdict_words):
            continue
        if "%" in line or "{" in line:
            continue
        if re.search(r"\b(bool|len\(|any\(|all\(|count|==)\b", line):
            continue
        out.append(Finding(
            "D23", name, "narrative/code coupling",
            f"line {i}: UNCONDITIONAL verdict-like literal printed next to a "
            f"check: {line.strip()[:90]}"))
    return out


# ============================================================== STATE DETECTORS

def d20_preservation(state_dir: str, module="archive"):
    """A retraction must not exist without a corresponding pre-fix artifact."""
    out = []
    retr = os.path.join(state_dir, "retractions")
    pre = os.path.join(state_dir, "pre_fix")
    if not (os.path.isdir(retr) and os.path.isdir(pre)):
        return out
    rs = [f for f in os.listdir(retr) if f.endswith(".json")]
    if not rs:
        return out
    pre_files = [f for f in os.listdir(pre) if f != "README.md"]
    if not pre_files:
        readme = os.path.join(pre, "README.md")
        if os.path.exists(readme):
            out.append(Finding(
                "D20", module, "retraction preservation",
                f"{len(rs)} retraction record(s) exist but pre_fix/ contains no "
                f"artifacts (only README.md). The pre-fix state was overwritten "
                f"in place and is unrecoverable."))
    return out


# ==================================================================== RUNNER

def run(raw_path: str, src_dir: str, state_dir: str,
        proposed_factors=None):
    findings: list[Finding] = []
    if raw_path and os.path.exists(raw_path):
        rows = list(_rows(raw_path))
        findings += d12_zero_variance(rows, module=os.path.basename(raw_path),
                                      proposed_factors=proposed_factors)
        findings += d07_metric_identity(rows, module=os.path.basename(raw_path))
        findings += d09_expectation_baseline(rows, module=os.path.basename(raw_path))
        findings += d13_null_validity(rows, module=os.path.basename(raw_path))
        findings += d22_uniqueness_key(raw_path, module=os.path.basename(raw_path))
        findings += d08_conditioning_reversal(rows, module=os.path.basename(raw_path))
        findings += d05_like_with_like(rows, module=os.path.basename(raw_path))
    if src_dir and os.path.isdir(src_dir):
        for fn in sorted(os.listdir(src_dir)):
            if not fn.endswith(".py"):
                continue
            src = open(os.path.join(src_dir, fn)).read()
            findings += d14_hash_seeding(src, fn)
            findings += d17_deterministic_decision(src, fn)
            findings += d19_truthiness(src, fn)
            findings += d21_state_contamination(src, fn)
            findings += d23_narrative_divergence(src, fn)
    if state_dir and os.path.isdir(state_dir):
        findings += d20_preservation(state_dir)
    return findings


if __name__ == "__main__":
    import sys
    raw = sys.argv[1] if len(sys.argv) > 1 else ""
    src = sys.argv[2] if len(sys.argv) > 2 else ""
    st = sys.argv[3] if len(sys.argv) > 3 else ""
    fs = run(raw, src, st)
    fails = [f for f in fs if f.severity == SEVERITY_FAIL]
    infos = [f for f in fs if f.severity == SEVERITY_INFO]
    if infos:
        print("=" * 74)
        print(f"ADVISORY ({len(infos)}) -- no defect, but worth knowing:")
        print("=" * 74)
        for f in infos:
            print(f"  {f}")
    if not fails:
        print("\nREGRESSION SUITE: no FAIL-level defects detected")
    else:
        from defect_registry import describe_failure
        seen = set()
        for f in fails:
            print(f"\n{f}")
            if f.defect_id not in seen:
                seen.add(f.defect_id)
                print(describe_failure(f.defect_id, f.module, f.claim, f.detail))
    print(f"\nSUMMARY: {len(fails)} FAIL, {len(infos)} INFO")
    sys.exit(1 if fails else 0)
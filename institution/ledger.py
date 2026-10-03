"""LANCEDB LEDGER — closure record (SS7).

Persists the epistemic state of the closed research cycle. The record's whole
purpose is to make `claim = qualified` survive as `qualified`, and to stop any
later reader from upgrading it to `true`.

SS5: git_sha / git_tag are recorded as BLOCKED until the freeze is resolved.
An unknown provenance field is recorded as the string "UNRESOLVED", never as an
empty string that reads like "not applicable".
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time

import lancedb
import pyarrow as pa

LEDGER = os.path.expanduser("~/projects/inversion-lab/institution/ledger.lance")
CHAOS = os.path.expanduser("~/projects/inversion-lab/chaos")

SCHEMA = pa.schema([
    ("record_type", pa.string()),
    ("cycle_id", pa.string()),
    ("project", pa.string()),
    ("git_sha", pa.string()),
    ("git_tag", pa.string()),
    ("world_fingerprint", pa.string()),
    ("artifact_count", pa.int64()),
    ("checksum_manifest", pa.string()),
    ("claim_id", pa.string()),
    ("claim_status", pa.string()),
    ("estimate", pa.float64()),
    ("ci_low", pa.float64()),
    ("ci_high", pa.float64()),
    ("scope", pa.string()),
    ("control_status", pa.string()),
    ("retraction_ids", pa.string()),
    ("defect_ids", pa.string()),
    ("independence_level", pa.string()),
    ("termination_state", pa.string()),
    ("open_question", pa.string()),
    ("git_tag_signed", pa.string()),
    ("archive_timestamp", pa.float64()),
])


def checksum_manifest_path() -> str:
    p = os.path.join(CHAOS, "frozen", "CHECKSUMS.txt")
    if not os.path.exists(p):
        return "UNRESOLVED"
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def artifact_count() -> int:
    p = os.path.join(CHAOS, "frozen")
    if not os.path.isdir(p):
        return -1
    return sum(len(fs) for _, _, fs in os.walk(p))


def _git(args) -> str:
    """Provenance fields are either a real value or an explicit UNRESOLVED.
    Never an empty string that reads like 'not applicable'."""
    try:
        out = subprocess.run(["git", "-C", CHAOS, *args], capture_output=True,
                             text=True, timeout=20)
        v = out.stdout.strip().splitlines()
        return v[0] if v and out.returncode == 0 else "UNRESOLVED"
    except Exception:
        return "UNRESOLVED"


def build_record() -> dict:
    return {
        "record_type": "research_cycle_closure",
        "cycle_id": "chaos-causal-audit",
        "project": "inversion-lab",
        "git_sha": _git(["rev-parse", "HEAD"]),
        "git_tag": _git(["tag", "--points-at", "HEAD", "v0.8-chaos-audited"]),
        "world_fingerprint": "882027e856db",
        "artifact_count": artifact_count(),
        "checksum_manifest": checksum_manifest_path(),
        "claim_id": "C-B8-001",
        "claim_status": "QUALIFIED",          # NOT "true"
        "estimate": 0.578333,
        "ci_low": 0.5467,
        "ci_high": 0.6100,
        "scope": ("synthetic three-object referential world; arms balanced 400 "
                  "trials per target; channel rho=1.0; temperature T=1.0"),
        "control_status": ("DEFECTIVE_NON_FATAL: the matched-irrelevant control "
                           "is matched on token count and vocabulary but NOT on "
                           "truth-to-target; for 1 of 3 targets one message "
                           "token is literally true of the target. Direction of "
                           "bias is AGAINST the claim."),
        "retraction_ids": "R-01,R-02,R-03,R-04,R-05",
        "defect_ids": ("D5,D6,D7,D8,D9,D10,D12,D13,D14,D17,D19,D20,D21,D22,D23"),
        "independence_level": ("I1_PRESENT;I2_CONTAMINATED_SAME_AUTHOR;"
                               "I2_CM_UNAVAILABLE;I3_LAB_CEILING_NOT_PURSUED"),
        "termination_state": "ARCHIVED_RESEARCH",
        "git_tag_signed": "False",
        "open_question": "Q-B8-001: OPEN / UNSCHEDULED",
        "archive_timestamp": time.time(),
    }


def main():
    db = lancedb.connect(LEDGER)
    tbl = "cycle_closures"
    row = build_record()

    # This table is DERIVED data -- ledger.py regenerates it. The readable
    # mirror (chaos/institution/15_LEDGER_RECORD.json) is the durable copy, so
    # dropping and recreating on a schema change loses nothing. Do NOT switch
    # this to delete-and-append: that silently reuses a stale schema and
    # produces a confusing "field not found in target schema" error.
    existing = db.table_names()
    if tbl in existing:
        db.drop_table(tbl)
    t = db.create_table(tbl, schema=SCHEMA)

    t.add([row])
    print(f"ledger: {LEDGER}")
    print(f"table : {tbl}  (rows={t.count_rows()})")
    print()
    print(f"  claim_id        : {row['claim_id']}")
    print(f"  claim_status    : {row['claim_status']}   <- preserved, not 'true'")
    print(f"  estimate        : {row['estimate']}  CI [{row['ci_low']}, {row['ci_high']}]")
    print(f"  artifact_count  : {row['artifact_count']}")
    print(f"  git_sha         : {row['git_sha']}")
    print(f"  independence    : {row['independence_level']}")
    print(f"  open_question   : {row['open_question']}")
    print()
    out = os.path.join(CHAOS, "institution", "15_LEDGER_RECORD.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(row, fh, indent=2)
    print(f"mirrored to {out}")


if __name__ == "__main__":
    main()
"""
agents/ranker.py
────────────────
Ranks scored candidates and produces the final ShortlistReport.
Supports HR manual overrides with a full JSONL audit trail.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import List

from schemas.models import (
    CandidateScore,
    CandidateRecommendation,
    ShortlistReport,
)

# ── Constants ───────────────────────────────────────────────────────

OVERRIDE_AUDIT_PATH = os.path.join("output", "override_audit.jsonl")


# ── Public API ──────────────────────────────────────────────────────


def rank_candidates(
    scores: List[CandidateScore], job_title: str
) -> ShortlistReport:
    """
    Sort candidates by effective score (descending) and build a report.

    Args:
        scores: List of evaluated ``CandidateScore`` instances.
        job_title: The role title from the parsed JD.

    Returns:
        A ``ShortlistReport`` with candidates ranked best-to-worst.
    """
    ranked = sorted(scores, key=lambda c: c.effective_score, reverse=True)

    return ShortlistReport(
        job_title=job_title,
        total_candidates=len(ranked),
        ranked_candidates=ranked,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def apply_override(
    report: ShortlistReport,
    candidate_name: str,
    new_score: float,
    reason: str,
) -> ShortlistReport:
    """
    Apply an HR manual score override for a candidate.

    The override is logged to a JSONL audit file and the report is
    re-sorted after adjustment.

    Args:
        report: The current shortlist report.
        candidate_name: Name of the candidate to override (case-insensitive).
        new_score: The HR-adjusted total score (0–10).
        reason: Free-text reason for the override.

    Returns:
        An updated ``ShortlistReport`` with the override applied and re-ranked.

    Raises:
        ValueError: If the candidate is not found in the report.
    """
    new_score = max(0.0, min(10.0, new_score))

    target = None
    for candidate in report.ranked_candidates:
        if candidate.candidate_name.strip().lower() == candidate_name.strip().lower():
            target = candidate
            break

    if target is None:
        raise ValueError(
            f"Candidate '{candidate_name}' not found in the report. "
            f"Available: {[c.candidate_name for c in report.ranked_candidates]}"
        )

    original_score = target.effective_score

    # Apply override fields
    target.override = reason
    target.override_adjusted_score = new_score

    # Recompute recommendation based on new score
    if new_score >= 7.5:
        target.recommendation = CandidateRecommendation.HIRE
    elif new_score >= 5.0:
        target.recommendation = CandidateRecommendation.MAYBE
    else:
        target.recommendation = CandidateRecommendation.NO_HIRE

    # Write audit log entry
    _write_audit_log(candidate_name, original_score, new_score, reason)

    # Re-sort by effective score
    report.ranked_candidates.sort(
        key=lambda c: c.effective_score, reverse=True
    )

    return report


# ── Private helpers ─────────────────────────────────────────────────


def _write_audit_log(
    candidate_name: str,
    original_score: float,
    new_score: float,
    reason: str,
) -> None:
    """Append a JSONL entry to the override audit trail."""
    os.makedirs(os.path.dirname(OVERRIDE_AUDIT_PATH), exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "candidate_name": candidate_name,
        "original_score": round(original_score, 2),
        "new_score": round(new_score, 2),
        "reason": reason,
        "actioned_by": "HR",
    }

    with open(OVERRIDE_AUDIT_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")

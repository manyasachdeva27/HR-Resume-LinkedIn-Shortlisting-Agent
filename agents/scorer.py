"""
agents/scorer.py
────────────────
Scores a candidate against a Job Description across 5 weighted
dimensions using a strict, bias-free rubric.

Dimensions & Weights:
    1. Skills Match         — 30 %
    2. Experience Relevance — 25 %
    3. Education & Certs    — 15 %
    4. Project / Portfolio  — 20 %
    5. Communication        — 10 %

Security:
    • Only structured Pydantic fields are sent to the LLM (never raw resume text).
    • All dimension scores are hard-capped to [0, 10] post-parse.
    • Temperature set low externally; rubric prevents subjective scoring.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage, SystemMessage

from schemas.models import CandidateScore, CandidateRecommendation

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from schemas.models import CandidateProfile, JobRequirements

# ── Constants ───────────────────────────────────────────────────────

SCORER_SYSTEM_PROMPT = """\
You are an objective, unbiased AI hiring evaluator. You MUST follow this exact rubric.

DIMENSIONS & WEIGHTS:

1. Skills Match (weight 0.30)
   0–3: less than 30% skills match
   4–6: 50–70% skills match
   7–10: more than 85% skills match

2. Experience Relevance (weight 0.25)
   0–3: completely unrelated domain
   4–6: adjacent domain or wrong seniority level
   7–10: exact domain AND right seniority level

3. Education & Certifications (weight 0.15)
   0–3: does not meet minimum education requirement
   4–6: meets minimum education requirement
   7–10: exceeds minimum AND holds additional relevant certifications

4. Project / Portfolio (weight 0.20)
   0–3: no evidence of relevant projects
   4–6: 1–2 generic projects
   7–10: strong, relevant portfolio with measurable outcomes

5. Communication Quality (weight 0.10)
   0–3: poor structure, grammar, or clarity
   4–6: adequate clarity and organisation
   7–10: crisp, well-structured, impactful presentation

SCORING RULES:
• weighted_score per dimension = (score / 10) × weight × 10
• total_weighted_score = sum of all weighted_scores (this will be on a 0–10 scale)
• Recommendation:
    - total_weighted_score ≥ 7.5 → "Hire"
    - 5.0 ≤ total_weighted_score < 7.5 → "Maybe"
    - total_weighted_score < 5.0 → "No Hire"
• Each justification must be factual, max 20 words.
• NEVER consider candidate name, gender, nationality, age, or any protected attribute.
• Output ONLY valid JSON — no preamble, no explanation, no markdown fences.

JSON Schema:
{
  "candidate_name": "<string>",
  "skills_match": {
    "dimension": "Skills Match",
    "score": <float 0-10>,
    "weight": 0.30,
    "weighted_score": <float>,
    "justification": "<string max 20 words>"
  },
  "experience_relevance": {
    "dimension": "Experience Relevance",
    "score": <float 0-10>,
    "weight": 0.25,
    "weighted_score": <float>,
    "justification": "<string max 20 words>"
  },
  "education_certs": {
    "dimension": "Education & Certifications",
    "score": <float 0-10>,
    "weight": 0.15,
    "weighted_score": <float>,
    "justification": "<string max 20 words>"
  },
  "project_portfolio": {
    "dimension": "Project / Portfolio",
    "score": <float 0-10>,
    "weight": 0.20,
    "weighted_score": <float>,
    "justification": "<string max 20 words>"
  },
  "communication_quality": {
    "dimension": "Communication Quality",
    "score": <float 0-10>,
    "weight": 0.10,
    "weighted_score": <float>,
    "justification": "<string max 20 words>"
  },
  "total_weighted_score": <float>,
  "recommendation": "<Hire | Maybe | No Hire>"
}
"""


# ── Public API ──────────────────────────────────────────────────────


def score_candidate(
    jd: "JobRequirements",
    profile: "CandidateProfile",
    llm: "BaseChatModel",
) -> CandidateScore:
    """
    Score a single candidate against a JD using the 5-dimension rubric.

    Args:
        jd: Parsed job requirements.
        profile: Parsed candidate profile.
        llm: An initialised LangChain chat model.

    Returns:
        A validated ``CandidateScore`` instance.

    Raises:
        ValueError: If the LLM returns invalid JSON after one retry.
    """
    human_content = _build_scoring_prompt(jd, profile)

    messages = [
        SystemMessage(content=SCORER_SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ]

    # First attempt
    try:
        return _call_and_parse(llm, messages)
    except (json.JSONDecodeError, Exception):
        pass

    # Retry with stricter instruction
    messages.append(
        HumanMessage(
            content=(
                "Your previous response was not valid JSON. "
                "Please output ONLY the raw JSON object — no markdown "
                "fences, no explanation, no extra text. Follow the schema exactly."
            )
        )
    )

    try:
        return _call_and_parse(llm, messages)
    except Exception as exc:
        raise ValueError(
            f"LLM failed to produce valid CandidateScore JSON after retry: {exc}"
        ) from exc


# ── Private helpers ─────────────────────────────────────────────────


def _build_scoring_prompt(
    jd: "JobRequirements", profile: "CandidateProfile"
) -> str:
    """
    Build a human-message containing only structured fields.
    Candidate name is placed LAST to minimise bias influence.
    """
    lines = [
        "=== JOB REQUIREMENTS ===",
        f"Role: {jd.role_title}",
        f"Required Skills: {', '.join(jd.required_skills)}",
        f"Preferred Skills: {', '.join(jd.preferred_skills)}",
        f"Min Experience: {jd.min_experience_years} years",
        f"Education: {jd.education_requirement}",
        f"Certifications: {', '.join(jd.certifications)}",
        f"Key Responsibilities: {'; '.join(jd.key_responsibilities)}",
        "",
        "=== CANDIDATE PROFILE ===",
        f"Skills: {', '.join(profile.skills)}",
        f"Years of Experience: {profile.years_of_experience}",
        f"Education: {profile.education}",
        f"Certifications: {', '.join(profile.certifications)}",
        f"Projects: {'; '.join(profile.projects)}",
        f"Summary: {profile.summary or 'N/A'}",
        # Name placed LAST to reduce bias
        f"Candidate Name: {profile.name}",
    ]
    return "\n".join(lines)


def _strip_fences(text: str) -> str:
    """Strip markdown code fences from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _hard_cap_scores(data: dict) -> dict:
    """Ensure every dimension score is within [0, 10]."""
    dim_keys = [
        "skills_match",
        "experience_relevance",
        "education_certs",
        "project_portfolio",
        "communication_quality",
    ]
    for key in dim_keys:
        if key in data and isinstance(data[key], dict):
            raw = float(data[key].get("score", 0))
            data[key]["score"] = max(0.0, min(10.0, raw))
            # Recompute weighted_score
            weight = float(data[key].get("weight", 0))
            data[key]["weighted_score"] = round(
                (data[key]["score"] / 10.0) * weight * 10, 2
            )

    # Recompute total
    total = sum(
        data.get(k, {}).get("weighted_score", 0) for k in dim_keys
    )
    data["total_weighted_score"] = round(total, 2)

    # Recompute recommendation
    if total >= 7.5:
        data["recommendation"] = "Hire"
    elif total >= 5.0:
        data["recommendation"] = "Maybe"
    else:
        data["recommendation"] = "No Hire"

    return data


def _call_and_parse(
    llm: "BaseChatModel", messages: list
) -> CandidateScore:
    """Invoke the LLM, post-process, and validate."""
    response = llm.invoke(messages)
    raw = _strip_fences(response.content)
    data = json.loads(raw)
    data = _hard_cap_scores(data)
    return CandidateScore(**data)

"""
schemas/models.py
─────────────────
Central Pydantic v2 models for every structured data exchange in the
HR Resume Shortlisting Agent.

All LLM responses are validated through these models to guarantee
type-safety, score capping, and deterministic serialisation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ────────────────────────────────────────────────────────────────────
# Enums
# ────────────────────────────────────────────────────────────────────

class CandidateRecommendation(str, Enum):
    """Hiring recommendation derived from weighted total score."""
    HIRE = "Hire"
    MAYBE = "Maybe"
    NO_HIRE = "No Hire"


# ────────────────────────────────────────────────────────────────────
# Job Description Models
# ────────────────────────────────────────────────────────────────────

class JobRequirements(BaseModel):
    """Structured representation of a parsed Job Description."""

    role_title: str = Field(
        ..., description="Title of the role as stated in the JD."
    )
    required_skills: List[str] = Field(
        default_factory=list,
        description="Hard skills explicitly listed as required.",
    )
    preferred_skills: List[str] = Field(
        default_factory=list,
        description="Skills listed as preferred / nice-to-have.",
    )
    min_experience_years: int = Field(
        default=0,
        ge=0,
        description="Minimum years of professional experience required.",
    )
    education_requirement: str = Field(
        default="",
        description="Minimum education qualification (e.g. Bachelor's in CS).",
    )
    certifications: List[str] = Field(
        default_factory=list,
        description="Certifications mentioned in the JD.",
    )
    key_responsibilities: List[str] = Field(
        default_factory=list,
        description="Primary duties / responsibilities of the role.",
    )


# ────────────────────────────────────────────────────────────────────
# Candidate Profile Models
# ────────────────────────────────────────────────────────────────────

class CandidateProfile(BaseModel):
    """Structured representation of a parsed candidate resume."""

    name: str = Field(..., description="Full name of the candidate.")
    email: Optional[str] = Field(
        default=None, description="Email address (if found on resume)."
    )
    skills: List[str] = Field(
        default_factory=list,
        description="Technical and soft skills explicitly listed.",
    )
    years_of_experience: float = Field(
        default=0.0,
        ge=0.0,
        description="Total years of professional experience.",
    )
    education: str = Field(
        default="",
        description="Highest education qualification.",
    )
    certifications: List[str] = Field(
        default_factory=list,
        description="Professional certifications held.",
    )
    projects: List[str] = Field(
        default_factory=list,
        description="Noteworthy projects or portfolio items.",
    )
    summary: Optional[str] = Field(
        default=None,
        description="Brief professional summary / objective from the resume.",
    )


# ────────────────────────────────────────────────────────────────────
# Scoring Models
# ────────────────────────────────────────────────────────────────────

class DimensionScore(BaseModel):
    """Score for a single evaluation dimension."""

    dimension: str = Field(
        ..., description="Name of the scoring dimension."
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Raw score on a 0–10 scale.",
    )
    weight: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weight of this dimension (decimal, e.g. 0.30).",
    )
    weighted_score: float = Field(
        ...,
        ge=0.0,
        description="Computed as (score / 10) × weight × 10.",
    )
    justification: str = Field(
        ...,
        max_length=200,
        description="Factual, one-line justification (max 20 words).",
    )

    # Hard-cap score within 0–10 even if LLM hallucinates
    @field_validator("score", mode="before")
    @classmethod
    def cap_score(cls, v: float) -> float:
        """Ensure score is always within [0, 10]."""
        return max(0.0, min(10.0, float(v)))

    @field_validator("weight", mode="before")
    @classmethod
    def cap_weight(cls, v: float) -> float:
        """Ensure weight is always within [0, 1]."""
        return max(0.0, min(1.0, float(v)))


class CandidateScore(BaseModel):
    """Aggregated evaluation of a single candidate against a JD."""

    candidate_name: str = Field(
        ..., description="Name of the evaluated candidate."
    )
    skills_match: DimensionScore = Field(
        ..., description="Skills Match dimension (weight 30%)."
    )
    experience_relevance: DimensionScore = Field(
        ..., description="Experience Relevance dimension (weight 25%)."
    )
    education_certs: DimensionScore = Field(
        ..., description="Education & Certifications dimension (weight 15%)."
    )
    project_portfolio: DimensionScore = Field(
        ..., description="Project / Portfolio dimension (weight 20%)."
    )
    communication_quality: DimensionScore = Field(
        ..., description="Communication Quality dimension (weight 10%)."
    )
    total_weighted_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Sum of all weighted_scores (0–10 scale).",
    )
    recommendation: CandidateRecommendation = Field(
        ..., description="Hire / Maybe / No Hire."
    )
    override: Optional[str] = Field(
        default=None,
        description="Reason for HR manual override, if any.",
    )
    override_adjusted_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description="HR-adjusted total score after manual override.",
    )

    @model_validator(mode="after")
    def recompute_recommendation(self) -> "CandidateScore":
        """Ensure recommendation aligns with the effective score."""
        effective = (
            self.override_adjusted_score
            if self.override_adjusted_score is not None
            else self.total_weighted_score
        )
        if effective >= 7.5:
            self.recommendation = CandidateRecommendation.HIRE
        elif effective >= 5.0:
            self.recommendation = CandidateRecommendation.MAYBE
        else:
            self.recommendation = CandidateRecommendation.NO_HIRE
        return self

    @property
    def effective_score(self) -> float:
        """Return the score that should be used for ranking."""
        if self.override_adjusted_score is not None:
            return self.override_adjusted_score
        return self.total_weighted_score

    def dimension_list(self) -> List[DimensionScore]:
        """Return all five dimension scores in display order."""
        return [
            self.skills_match,
            self.experience_relevance,
            self.education_certs,
            self.project_portfolio,
            self.communication_quality,
        ]


# ────────────────────────────────────────────────────────────────────
# Report Models
# ────────────────────────────────────────────────────────────────────

class ShortlistReport(BaseModel):
    """Final shortlist report containing ranked candidate evaluations."""

    job_title: str = Field(
        ..., description="Title of the role from the JD."
    )
    total_candidates: int = Field(
        ..., ge=0, description="Total number of candidates evaluated."
    )
    ranked_candidates: List[CandidateScore] = Field(
        default_factory=list,
        description="Candidates sorted descending by effective score.",
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        description="ISO-ish timestamp of report generation.",
    )

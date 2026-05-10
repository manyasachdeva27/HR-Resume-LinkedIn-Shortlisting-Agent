# schemas/__init__.py
# Package initializer for Pydantic data models used across the HR Shortlisting Agent.

from .models import (
    JobRequirements,
    CandidateProfile,
    DimensionScore,
    CandidateScore,
    CandidateRecommendation,
    ShortlistReport,
)

__all__ = [
    "JobRequirements",
    "CandidateProfile",
    "DimensionScore",
    "CandidateScore",
    "CandidateRecommendation",
    "ShortlistReport",
]

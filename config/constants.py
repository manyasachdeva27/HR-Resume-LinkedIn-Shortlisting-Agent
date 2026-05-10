"""
config/constants.py
───────────────────
Central configuration constants for the HR Shortlisting Agent.
All tunable parameters are defined here to avoid magic numbers
scattered across the codebase.

Project: HireIQ — AI-Powered HR Candidate Shortlisting Agent
"""

# ── LLM Configuration ──────────────────────────────────────────────
LLM_MODEL: str = "gemini-1.5-pro"
LLM_TEMPERATURE: float = 0.1
LLM_PROVIDER: str = "google"

# ── Input Limits ───────────────────────────────────────────────────
MAX_JD_CHARS: int = 4000
MAX_RESUME_CHARS: int = 6000

# ── Retry / Resilience ─────────────────────────────────────────────
RETRY_SLEEP_SECONDS: int = 3
MAX_RETRIES: int = 1
RATE_LIMIT_PAUSE: int = 15  # seconds between API calls (free tier)

# ── Scoring ────────────────────────────────────────────────────────
SCORE_MIN: float = 0.0
SCORE_MAX: float = 10.0
HIRE_THRESHOLD: float = 7.5
MAYBE_THRESHOLD: float = 5.0

WEIGHTS: dict[str, float] = {
    "skills_match": 0.30,
    "experience_relevance": 0.25,
    "education_certs": 0.15,
    "project_portfolio": 0.20,
    "communication_quality": 0.10,
}

# ── Paths ──────────────────────────────────────────────────────────
CACHE_DB_PATH: str = ".langchain_cache.db"
OUTPUT_DIR: str = "output"
LOG_DIR: str = "logs"
LOG_FILE: str = "logs/agent.log"
OVERRIDE_AUDIT_FILE: str = "output/override_audit.jsonl"

# ── Supported File Extensions ──────────────────────────────────────
SUPPORTED_RESUME_EXTENSIONS: tuple[str, ...] = (
    ".pdf", ".docx", ".txt", ".json",
)
SUPPORTED_JD_EXTENSIONS: tuple[str, ...] = (
    ".pdf", ".docx", ".txt",
)

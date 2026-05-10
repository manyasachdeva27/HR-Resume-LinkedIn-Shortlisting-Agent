"""
agents/jd_parser.py
───────────────────
Parses a raw Job Description (JD) text into a structured
`JobRequirements` Pydantic model using an LLM.

Security:
    • Regex sanitisation strips prompt-injection patterns before LLM call.
    • Input truncated to 4 000 characters to stay within safe token limits.
    • LLM output validated through Pydantic; invalid JSON triggers one retry.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage, SystemMessage

from schemas.models import JobRequirements

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

# ── Constants ───────────────────────────────────────────────────────

MAX_JD_CHARS = 4_000

JD_PARSER_SYSTEM_PROMPT = """\
You are a senior HR analyst extracting structured job requirements from a Job Description.

INSTRUCTIONS:
1. Extract every skill, qualification, and requirement mentioned in the JD.
2. Separate required skills from preferred / nice-to-have skills.
3. Do NOT hallucinate requirements that are not present in the JD.
4. If a field has no data, return an empty list [] or empty string "".
5. Output ONLY valid JSON matching the schema below — no preamble, no explanation, no markdown fences.

JSON Schema:
{
  "role_title": "<string>",
  "required_skills": ["<string>", ...],
  "preferred_skills": ["<string>", ...],
  "min_experience_years": <int>,
  "education_requirement": "<string>",
  "certifications": ["<string>", ...],
  "key_responsibilities": ["<string>", ...]
}
"""

_INJECTION_PATTERNS = re.compile(
    r"(ignore\s+(all\s+)?previous\s+instructions"
    r"|you\s+are\s+now"
    r"|forget\s+(everything|all)"
    r"|system\s*:\s*"
    r"|<\s*/?script"
    r"|act\s+as\s+a"
    r"|pretend\s+you"
    r"|do\s+not\s+follow\s+the\s+above)",
    re.IGNORECASE,
)


# ── Public API ──────────────────────────────────────────────────────


def parse_jd(jd_text: str, llm: "BaseChatModel") -> JobRequirements:
    """
    Parse a raw JD into a structured ``JobRequirements`` model.

    Args:
        jd_text: Plain-text of the Job Description.
        llm: An initialised LangChain chat model.

    Returns:
        A validated ``JobRequirements`` instance.

    Raises:
        ValueError: If the LLM returns invalid JSON after one retry.
    """
    sanitised = _sanitise(jd_text)
    truncated = sanitised[:MAX_JD_CHARS]

    messages = [
        SystemMessage(content=JD_PARSER_SYSTEM_PROMPT),
        HumanMessage(content=f"JOB DESCRIPTION:\n\n{truncated}"),
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
                "fences, no explanation, no extra text."
            )
        )
    )

    try:
        return _call_and_parse(llm, messages)
    except Exception as exc:
        raise ValueError(
            f"LLM failed to produce valid JobRequirements JSON after retry: {exc}"
        ) from exc


# ── Private helpers ─────────────────────────────────────────────────


def _sanitise(text: str) -> str:
    """Remove prompt-injection patterns from raw text."""
    return _INJECTION_PATTERNS.sub("[REDACTED]", text)


def _strip_fences(text: str) -> str:
    """Strip markdown code fences (```json ... ```) from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        # Remove opening fence (with optional language tag)
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _call_and_parse(
    llm: "BaseChatModel", messages: list
) -> JobRequirements:
    """Invoke the LLM, strip fences, parse and validate JSON."""
    response = llm.invoke(messages)
    raw = _strip_fences(response.content)
    data = json.loads(raw)
    return JobRequirements(**data)

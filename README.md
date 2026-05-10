# HireIQ — AI-Powered HR Candidate Shortlisting Agent

> **Internship Assignment Submission** | AI Enablement Track | Task 1

---

## Overview

HireIQ is a production-grade AI agent that automates the first stage of
candidate screening. An HR team uploads a **Job Description** and a batch
of **resumes** (PDF / DOCX / TXT); the agent parses, evaluates, scores,
ranks, and produces a transparent shortlist report — all in under a
minute.

## Problem Statement

HR teams routinely screen hundreds of applications per role, leading to
**fatigue, inconsistency, and unconscious bias**. A well-designed AI
agent can standardise evaluation, highlight skill gaps, and surface the
best-fit candidates faster — all while keeping a human in the loop for
final decisions.

## Solution Architecture

```
┌──────────────┐
│  HR Uploads  │  JD (TXT/PDF/DOCX) + Resumes (PDF/DOCX)
│  via UI/CLI  │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  JD Parser   │────▶│ Structured   │  JobRequirements (Pydantic)
│  Agent       │     │ Requirements │
└──────────────┘     └──────────────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  Profile     │────▶│ Candidate    │  CandidateProfile (Pydantic)
│  Parser      │     │ Profiles     │
└──────────────┘     └──────────────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  Scorer      │────▶│ 5-Dimension  │  CandidateScore (Pydantic)
│  Agent       │     │ Rubric Scores│
└──────────────┘     └──────────────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  Ranker      │────▶│ Ranked       │  ShortlistReport (Pydantic)
│              │     │ Shortlist    │
└──────────────┘     └──────────────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  Report Gen  │────▶│ HTML + JSON  │  Jinja2 → output/
│  (Jinja2)    │     │ Report Files │
└──────────────┘     └──────────────┘
       │
       ▼
┌──────────────┐
│  HR Override │  Manual score adjustments (audit-logged)
│  Panel (UI)  │
└──────────────┘
```

## Agent Flow Diagram

| Step | Action | Component |
|------|--------|-----------|
| 1 | HR uploads JD + resume files | Streamlit UI / CLI |
| 2 | LLM extracts structured requirements from JD | `agents/jd_parser.py` |
| 3 | Agent parses each resume into structured fields | `agents/profile_parser.py` |
| 4 | Agent scores each candidate across 5 dimensions | `agents/scorer.py` |
| 5 | Candidates sorted by total weighted score | `agents/ranker.py` |
| 6 | HTML + JSON report generated | `report/generator.py` |
| 7 | HR can override any score (logged with timestamp) | `agents/ranker.py` |

## Tech Stack & Decision Log

### LLM Choice — Groq (Llama 3.3 70B) / Google Gemini 1.5 Pro

| Criterion | Justification |
|-----------|---------------|
| Context window | 128K tokens — handles long JDs and multi-page resumes |
| Structured output | Strong JSON mode adherence with Pydantic validation |
| Cost | Groq free tier: 14,400 req/day; Gemini free tier available |
| Speed | Groq: sub-2s inference; Gemini: ~5s inference |
| Swappable | LangChain abstraction allows hot-swapping between providers |

### Framework — LangChain

| Criterion | Justification |
|-----------|---------------|
| Prompt management | PromptTemplate + ChatPromptTemplate for structured prompts |
| Output parsing | Native Pydantic integration for validated structured output |
| Caching | SQLiteCache reduces API costs during development |
| Observability | LangSmith tracing support (optional) |

### Resume Parsing — pdfplumber + python-docx

- **pdfplumber**: Reliable PDF text extraction with layout awareness
- **python-docx**: Native DOCX paragraph extraction
- **Fallback**: Plain-text read for `.txt` and `.json` (LinkedIn exports)

### Output — Jinja2 HTML + JSON

- **Jinja2**: Professional HTML report with inline CSS, dark theme,
  interactive expandable cards, colour-coded score bars
- **JSON**: Machine-readable audit snapshot for downstream integration

## Scoring Rubric

| Dimension | Weight | 0 — Poor | 5 — Average | 10 — Excellent |
|-----------|--------|----------|-------------|----------------|
| Skills Match | 30% | < 30% skills match | 50–70% skills match | > 85% skills match |
| Experience Relevance | 25% | Unrelated domain | Adjacent domain | Exact domain & seniority |
| Education & Certs | 15% | Does not meet minimum | Meets minimum | Exceeds + extra certs |
| Project / Portfolio | 20% | No evidence | 1–2 generic projects | Strong relevant portfolio |
| Communication Quality | 10% | Poor structure/grammar | Adequate clarity | Crisp, structured, impactful |

The agent produces per-dimension scores, a weighted total, and a
one-line justification for each dimension.

## Security Risk Mitigations

| # | Risk | Description | Mitigation |
|---|------|-------------|------------|
| 1 | **Prompt Injection** | Malicious text in resumes could manipulate LLM behaviour | Regex sanitisation strips injection patterns (`ignore`, `system:`, `<script>`) from all input before every LLM call |
| 2 | **Data Privacy / PII** | Candidate emails, phone numbers are sensitive | PII is extracted into local Pydantic objects only; emails are never included in LLM prompts |
| 3 | **API Key Exposure** | Hardcoded keys could leak via version control | `python-dotenv` loads from `.env` (gitignored); `.env.example` contains placeholders only |
| 4 | **Hallucination Risk** | LLM may fabricate scores or justifications | Pydantic v2 validates all outputs; scores hard-capped to 0–10 post-generation; temperature set to 0.1 |
| 5 | **Scoring Bias** | LLM may score based on name, gender, nationality | System prompt explicitly forbids demographic scoring; candidate name is placed last in the prompt to reduce priming bias |
| 6 | **Unauthorised Access** | No authentication on the Streamlit UI | Noted as a production TODO — API auth + rate limiting should be added before any deployment |

## Project Structure

```
hr-shortlisting-agent/
├── agents/                  # LLM-powered agent modules
│   ├── __init__.py
│   ├── jd_parser.py         # JD → JobRequirements
│   ├── profile_parser.py    # Resume → CandidateProfile
│   ├── scorer.py            # Profile + JD → CandidateScore
│   └── ranker.py            # Scores → ShortlistReport + overrides
├── config/
│   ├── __init__.py
│   └── constants.py         # All tunable parameters
├── data/
│   ├── sample_jd.txt        # Example job description
│   └── resumes/             # Sample candidate resumes
├── logs/                    # Runtime log files (gitignored)
├── output/                  # Generated reports (gitignored)
├── report/
│   ├── __init__.py
│   ├── generator.py         # Jinja2 HTML + JSON report writer
│   └── templates/
│       └── report.html      # HTML report template
├── schemas/
│   ├── __init__.py
│   └── models.py            # Pydantic v2 data models
├── tools/
│   ├── __init__.py
│   └── pdf_reader.py        # PDF / DOCX / TXT text extraction
├── utils/
│   ├── __init__.py
│   └── logging_setup.py     # Centralised logging configuration
├── app.py                   # Streamlit web UI
├── main.py                  # CLI entry point
├── requirements.txt         # Pinned dependencies
├── .env.example             # Environment variable template
├── .gitignore
└── README.md
```

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd hr-shortlisting-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API key**
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY (or GOOGLE_API_KEY)
   ```

5. **Place input files**
   - Job Description → `data/sample_jd.txt`
   - Resumes → `data/resumes/` (PDF, DOCX, or TXT)

## How to Run

### CLI Mode
```bash
python main.py --jd data/sample_jd.txt --resumes data/resumes/
```

### Streamlit UI
```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Sample Output

> 📂 **View the generated reports directly:**
> - [**shortlist_report.html**](output/shortlist_report.html) — Interactive dark-themed HTML report with candidate cards, colour-coded score bars, and recommendation pills
> - [**shortlist_report.json**](output/shortlist_report.json) — Machine-readable JSON with all 5 candidates, scores, justifications, and metadata

After execution, the `output/` folder contains:
- **`shortlist_report.html`** — Download and open in a browser to see the full interactive report
- **`shortlist_report.json`** — Structured audit snapshot (5 candidates, 25 dimension scores)
- **`override_audit.jsonl`** — Append-only audit log of any HR overrides

### Sample Results Summary

| Rank | Candidate | Score | Recommendation | Match Quality |
|------|-----------|-------|----------------|---------------|
| 1 | Alice Chen | 8.45 | 🟢 Hire | Strong — ML Engineer, 4 yrs, 31 skills |
| 2 | Priya Sharma | 8.20 | 🟢 Hire | Strong — ML Engineer, 3.5 yrs, 32 skills |
| 3 | Sarah Johnson | 7.20 | 🟡 Maybe | Partial — Data Scientist, NLP focus |
| 4 | Bob Martinez | 4.20 | 🔴 No Hire | Weak — Data Analyst, no ML experience |
| 5 | Deepak Gupta | 0.80 | 🔴 No Hire | None — Web Developer, wrong domain |

## Prompt Design & Guardrails

### Key System Prompts

**JD Parser Prompt** (`agents/jd_parser.py`):
```
You are a senior HR analyst extracting structured job requirements
from a Job Description.
1. Extract every skill, qualification, and requirement mentioned.
2. Separate required skills from preferred / nice-to-have skills.
3. Do NOT hallucinate requirements that are not present in the JD.
4. If a field has no data, return an empty list [] or empty string "".
5. Output ONLY valid JSON matching the schema below.
```

**Scorer Prompt** (`agents/scorer.py`):
```
You are an objective, unbiased AI hiring evaluator.
You MUST follow this exact rubric.
...
SCORING RULES:
• weighted_score = (score / 10) × weight × 10
• total ≥ 7.5 → "Hire" | 5.0–7.5 → "Maybe" | < 5.0 → "No Hire"
• Each justification must be factual, max 20 words.
• NEVER consider candidate name, gender, nationality, age,
  or any protected attribute.
```

### Prompt Design Decisions

| Decision | Rationale |
|----------|-----------|
| JSON-only output instruction | Eliminates markdown fences and preamble that break parsers |
| `max 20 words` justification cap | Forces concise, factual reasoning — reduces hallucination |
| Candidate name placed **last** in prompt | Reduces priming bias — LLM processes skills before seeing the name |
| Explicit rubric with numeric bands | Anchors scoring to objective criteria, not subjective impression |
| `Do NOT hallucinate` instruction | Direct constraint that measurably reduces fabrication |
| Temperature 0.1 | Near-deterministic output for reproducible scoring |

### Guardrails Pipeline

1. **Input Sanitisation** — Regex strips 8 injection patterns
   (`ignore previous`, `system:`, `<script>`, `act as`, etc.)
2. **Truncation** — JD capped at 4,000 chars, resumes at 6,000
3. **Structured Output** — Pydantic v2 schema validation on every
   LLM response — invalid JSON is rejected, not silently accepted
4. **Score Hard-Capping** — Post-parse, all scores clamped to [0, 10]
5. **Retry Logic** — On parse failure, retry once with stricter
   "output ONLY raw JSON" instruction
6. **Weighted Recomputation** — Server-side recalculation of totals
   and recommendations, never trusting LLM arithmetic

### Prompt Iteration Log

| Version | Change | Outcome |
|---------|--------|---------|
| v1 | Basic "score this resume" prompt | Inconsistent JSON, hallucinated fields |
| v2 | Added explicit JSON schema in prompt | JSON structure stabilised, but scores drifted |
| v3 | Added numeric rubric bands (0-3, 4-6, 7-10) | Score consistency improved significantly |
| v4 | Added `NEVER consider name/gender` + moved name last | Reduced demographic bias in scoring |
| v5 (final) | Added `max 20 words` justification cap | Eliminated verbose, speculative justifications |

## Limitations & Future Improvements

| Limitation | Planned Improvement |
|-----------|---------------------|
| No LinkedIn live scraping | Integrate RapidAPI LinkedIn scraper |
| No embedding similarity | Add BGE / Sentence-Transformers for semantic matching |
| Free tier rate limits | Add exponential backoff + provider fallback chain |
| No authentication | Add Streamlit auth + API key rotation |
| English only | Multi-language resume support via translation layer |
| No PDF export | Add ReportLab PDF generation alongside HTML |

## Author

Built as part of the AI Enablement Internship — Task 1.

"""
main.py
───────
CLI entry-point for the HR Resume Shortlisting Agent.

Usage:
    python main.py --jd data/sample_jd.txt --resumes data/resumes/

Pipeline:
    1. Parse Job Description → JobRequirements
    2. Parse each resume    → CandidateProfile
    3. Score each candidate → CandidateScore
    4. Rank all candidates  → ShortlistReport
    5. Generate HTML report → output/shortlist_report.html
"""

from __future__ import annotations

import argparse
import glob
import io
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

# Force UTF-8 output on Windows to handle emoji and special chars
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )


# ── Helpers ─────────────────────────────────────────────────────────


def _ts() -> str:
    """Return a formatted timestamp prefix for console output."""
    return datetime.now().strftime("[%H:%M:%S]")


def _print_banner() -> None:
    """Print a styled banner at startup."""
    banner = """
    +==============================================================+
    |       HR Resume & LinkedIn Shortlisting Agent  v1.0          |
    |       Powered by Google Gemini 1.5 Pro + LangChain           |
    +==============================================================+
    """
    print(banner)


# ── Main pipeline ───────────────────────────────────────────────────


def main() -> None:
    """Run the full shortlisting pipeline from CLI arguments."""

    # ── 0. Load environment & parse args ───────────────────────────
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="HR Resume Shortlisting Agent — score and rank candidates against a JD."
    )
    parser.add_argument(
        "--jd",
        type=str,
        required=True,
        help="Path to the Job Description file (.txt or .pdf).",
    )
    parser.add_argument(
        "--resumes",
        type=str,
        required=True,
        help="Path to a folder containing resume files (.pdf / .docx).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join("output", "shortlist_report.html"),
        help="Output path for the HTML report (default: output/shortlist_report.html).",
    )
    args = parser.parse_args()

    _print_banner()

    # Validate inputs
    if not os.path.isfile(args.jd):
        print(f"{_ts()} ❌ JD file not found: {args.jd}")
        sys.exit(1)

    if not os.path.isdir(args.resumes):
        print(f"{_ts()} ❌ Resumes directory not found: {args.resumes}")
        sys.exit(1)

    # Collect resume files
    resume_files = []
    for ext in ("*.pdf", "*.docx", "*.txt"):
        resume_files.extend(glob.glob(os.path.join(args.resumes, ext)))

    if not resume_files:
        print(f"{_ts()} ❌ No resume files (.pdf, .docx, .txt) found in {args.resumes}")
        sys.exit(1)

    print(f"{_ts()} 📄 JD file   : {args.jd}")
    print(f"{_ts()} 📁 Resumes   : {len(resume_files)} files in {args.resumes}")
    print(f"{_ts()} 📤 Output    : {args.output}")
    print()

    # ── 1. Initialise LLM with caching ────────────────────────────
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print(f"{_ts()} ❌ GOOGLE_API_KEY not set. Add it to your .env file.")
        sys.exit(1)

    # Enable SQLite cache to reduce API costs during development
    from langchain_community.cache import SQLiteCache
    from langchain_core.globals import set_llm_cache

    set_llm_cache(SQLiteCache(database_path=".langchain_cache.db"))
    print(f"{_ts()} 💾 LLM cache enabled (SQLite)")

    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0.1,
        google_api_key=api_key,
    )
    print(f"{_ts()} 🤖 LLM initialised: Google Gemini 1.5 Pro (temperature=0.1)")
    print()

    # ── 2. Parse Job Description ──────────────────────────────────
    from agents.jd_parser import parse_jd
    from tools.pdf_reader import extract_text_from_file
    import time

    print(f"{_ts()} 📝 Parsing Job Description...")
    jd_text = extract_text_from_file(args.jd)
    jd_requirements = parse_jd(jd_text, llm)
    print(f"{_ts()} ✅ JD parsed → Role: {jd_requirements.role_title}")
    print(f"{_ts()}    Required Skills : {', '.join(jd_requirements.required_skills[:5])}{'...' if len(jd_requirements.required_skills) > 5 else ''}")
    print(f"{_ts()}    Min Experience  : {jd_requirements.min_experience_years} years")
    print()

    # ── 3. Parse resumes ──────────────────────────────────────────
    from agents.profile_parser import parse_profile

    profiles = []
    for i, resume_path in enumerate(resume_files, 1):
        fname = os.path.basename(resume_path)
        print(f"{_ts()} 📄 [{i}/{len(resume_files)}] Parsing resume: {fname}...")
        try:
            if i > 1:
                print(f"{_ts()}    ⏳ Rate-limit pause (15s)...")
                time.sleep(15)
            profile = parse_profile(resume_path, llm)
            profiles.append(profile)
            print(f"{_ts()}    ✅ {profile.name} — {profile.years_of_experience} yrs exp, {len(profile.skills)} skills")
        except Exception as exc:
            print(f"{_ts()}    ⚠️  Failed to parse {fname}: {exc}")
    print()

    if not profiles:
        print(f"{_ts()} ❌ No resumes were successfully parsed. Exiting.")
        sys.exit(1)

    # ── 4. Score each candidate ───────────────────────────────────
    from agents.scorer import score_candidate

    scores = []
    print(f"{_ts()} 🏆 Scoring candidates against JD...")
    for i, profile in enumerate(profiles, 1):
        print(f"{_ts()} 📊 [{i}/{len(profiles)}] Scoring: {profile.name}...")
        try:
            print(f"{_ts()}    ⏳ Rate-limit pause (15s)...")
            time.sleep(15)
            result = score_candidate(jd_requirements, profile, llm)
            scores.append(result)
            rec_emoji = {"Hire": "🟢", "Maybe": "🟡", "No Hire": "🔴"}
            emoji = rec_emoji.get(result.recommendation.value, "⚪")
            print(f"{_ts()}    {emoji} Total: {result.total_weighted_score:.2f}/10 → {result.recommendation.value}")
        except Exception as exc:
            print(f"{_ts()}    ⚠️  Failed to score {profile.name}: {exc}")
    print()

    if not scores:
        print(f"{_ts()} ❌ No candidates were successfully scored. Exiting.")
        sys.exit(1)

    # ── 5. Rank candidates ────────────────────────────────────────
    from agents.ranker import rank_candidates

    report = rank_candidates(scores, jd_requirements.role_title)
    print(f"{_ts()} 📋 Candidates ranked. Final standings:")
    print()
    print(f"  {'Rank':<6} {'Candidate':<30} {'Score':<10} {'Recommendation'}")
    print(f"  {'─' * 6} {'─' * 30} {'─' * 10} {'─' * 16}")
    for idx, c in enumerate(report.ranked_candidates, 1):
        rec_emoji = {"Hire": "🟢", "Maybe": "🟡", "No Hire": "🔴"}
        emoji = rec_emoji.get(c.recommendation.value, "⚪")
        print(f"  {idx:<6} {c.candidate_name:<30} {c.effective_score:<10.2f} {emoji} {c.recommendation.value}")
    print()

    # ── 6. Generate report ────────────────────────────────────────
    from report.generator import generate_html_report

    print(f"{_ts()} 📄 Generating HTML report...")
    html_path = generate_html_report(report, args.output)
    print(f"{_ts()} ✅ Report saved to: {html_path}")
    print(f"{_ts()} ✅ JSON audit saved to: {os.path.join(os.path.dirname(args.output), 'shortlist_report.json')}")
    print()
    print(f"{_ts()} 🎉 Pipeline complete! Open the HTML report in your browser.")


if __name__ == "__main__":
    main()

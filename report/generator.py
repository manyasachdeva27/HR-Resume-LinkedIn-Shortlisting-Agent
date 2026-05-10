"""
report/generator.py
───────────────────
Renders the final HTML shortlist report using Jinja2 and persists
both HTML and JSON versions for audit / downstream consumption.
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader

if TYPE_CHECKING:
    from schemas.models import ShortlistReport

# ── Constants ───────────────────────────────────────────────────────

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
_TEMPLATE_NAME = "report.html"


# ── Public API ──────────────────────────────────────────────────────


def generate_html_report(
    report: "ShortlistReport", output_path: str
) -> str:
    """
    Render the shortlist report as a styled HTML file and save it.

    Also writes a JSON snapshot to ``output/shortlist_report.json``
    for programmatic access and auditing.

    Args:
        report: A fully populated ``ShortlistReport`` instance.
        output_path: Destination file path for the HTML output.

    Returns:
        The absolute path to the generated HTML file.
    """
    # Ensure output directory exists
    out_dir = os.path.dirname(output_path) or "."
    os.makedirs(out_dir, exist_ok=True)

    # Render HTML
    env = Environment(
        loader=FileSystemLoader(_TEMPLATE_DIR),
        autoescape=False,  # HTML template controls its own escaping
    )
    template = env.get_template(_TEMPLATE_NAME)
    html_content = template.render(report=report)

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html_content)

    # Save JSON snapshot for audit
    json_path = os.path.join(out_dir, "shortlist_report.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(report.model_dump(mode="json"), fh, indent=2, default=str)

    return os.path.abspath(output_path)

"""
utils/logging_setup.py
──────────────────────
Configures the project-wide Python logging with both console
and file handlers. Import and call ``setup_logging()`` once at
application startup.

Project: HireIQ — AI-Powered HR Candidate Shortlisting Agent
"""

from __future__ import annotations

import logging
import os
import sys

from config.constants import LOG_DIR, LOG_FILE

_LOG_FORMAT = (
    "[%(asctime)s] [%(levelname)s] [%(name)s] — %(message)s"
)
_DATE_FORMAT = "%H:%M:%S"


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure root logger with console + file handlers.

    Args:
        level: Logging verbosity (default ``logging.INFO``).

    Returns:
        The configured root logger instance.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    console.setLevel(level)

    # File handler
    file_h = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_h.setFormatter(formatter)
    file_h.setLevel(level)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(console)
    root.addHandler(file_h)

    return root

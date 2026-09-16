"""Central configuration. Paths and pool sizes can be overridden via environment variables."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("WORDLE_DATA_DIR", PROJECT_ROOT / "data"))
GUESSES_CSV = DATA_DIR / "valid_guesses.csv"
SOLUTIONS_CSV = DATA_DIR / "valid_solutions.csv"

WORD_LENGTH = 5
MAX_GUESSES = 6
SOLVED_PATTERN = "G" * WORD_LENGTH
FEEDBACK_ALPHABET = frozenset("GYB")

# Hybrid solver: use entropy while more than this many candidates remain.
ENTROPY_THRESHOLD = 5
# How many words from the (alphabetical) guess list are scored for entropy.
# 1200 matches the original evaluation.py; the Streamlit page historically used 800.
EVAL_GUESS_POOL = int(os.environ.get("WORDLE_EVAL_GUESS_POOL", "1200"))
APP_GUESS_POOL = int(os.environ.get("WORDLE_APP_GUESS_POOL", "800"))

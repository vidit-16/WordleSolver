"""Loading and validating the word list CSV files."""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path

from wordle_solver import config
from wordle_solver.feedback import is_valid_word

logger = logging.getLogger(__name__)


class WordListError(RuntimeError):
    """Raised when a word list is missing or malformed."""


@dataclass(frozen=True)
class WordLists:
    guesses: list[str]
    solutions: list[str]


def read_word_csv(path: str | Path) -> list[str]:
    """Read a CSV with a ``word`` header column, returning upper-case valid words.

    Invalid rows (wrong length, non-alphabetic) are skipped with a warning.
    """
    path = Path(path)
    if not path.is_file():
        raise WordListError(f"Word list not found: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or "word" not in reader.fieldnames:
            raise WordListError(f"{path} must have a 'word' header column")
        words: list[str] = []
        skipped = 0
        for row in reader:
            w = (row.get("word") or "").strip().upper()
            if is_valid_word(w):
                words.append(w)
            elif w:
                skipped += 1
    if skipped:
        logger.warning("Skipped %d invalid rows in %s", skipped, path)
    if not words:
        raise WordListError(f"{path} contains no valid five-letter words")
    return words


def load_word_lists(
    guesses_csv: str | Path = config.GUESSES_CSV,
    solutions_csv: str | Path = config.SOLUTIONS_CSV,
) -> WordLists:
    """Load both the allowed-guess list and the official solution list."""
    return WordLists(guesses=read_word_csv(guesses_csv), solutions=read_word_csv(solutions_csv))

"""Wordle game rules: feedback patterns and candidate filtering."""

from __future__ import annotations

from collections.abc import Iterable

from wordle_solver.config import FEEDBACK_ALPHABET, WORD_LENGTH


def is_valid_word(word: object) -> bool:
    """Return True if ``word`` is a five-letter ASCII alphabetic string."""
    return isinstance(word, str) and len(word) == WORD_LENGTH and word.isascii() and word.isalpha()


def is_valid_pattern(pattern: object) -> bool:
    """Return True if ``pattern`` is five characters drawn from G/Y/B."""
    return (
        isinstance(pattern, str)
        and len(pattern) == WORD_LENGTH
        and set(pattern) <= FEEDBACK_ALPHABET
    )


def wordle_feedback(guess: str, target: str) -> str:
    """Compute the G/Y/B feedback for ``guess`` against ``target``.

    Duplicate letters follow official Wordle rules: greens are assigned first,
    then yellows consume the remaining unmatched letters left to right.
    """
    if len(guess) != WORD_LENGTH or len(target) != WORD_LENGTH:
        raise ValueError(
            f"guess and target must be {WORD_LENGTH} letters, got {guess!r} and {target!r}"
        )
    pattern = [""] * WORD_LENGTH
    remaining: list[str | None] = list(target)

    for i in range(WORD_LENGTH):
        if guess[i] == target[i]:
            pattern[i] = "G"
            remaining[i] = None

    for i in range(WORD_LENGTH):
        if pattern[i] == "":
            if guess[i] in remaining:
                pattern[i] = "Y"
                remaining[remaining.index(guess[i])] = None
            else:
                pattern[i] = "B"

    return "".join(pattern)


def filter_candidates(candidates: Iterable[str], guess: str, pattern: str) -> list[str]:
    """Keep only candidates that would have produced ``pattern`` for ``guess``."""
    return [w for w in candidates if wordle_feedback(guess, w) == pattern]

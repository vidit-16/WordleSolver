"""Constraint-satisfaction solver ranked by letter frequency."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from wordle_solver.solvers.base import Solver


def letter_frequencies(candidates: Sequence[str]) -> Counter[str]:
    """Count, for each letter, how many candidates contain it."""
    freq: Counter[str] = Counter()
    for w in candidates:
        freq.update(set(w))
    return freq


def score_letter_frequency(word: str, candidates: Sequence[str]) -> int:
    """Sum of candidate-frequencies of the unique letters in ``word``."""
    freq = letter_frequencies(candidates)
    return sum(freq[c] for c in set(word))


def rank_candidates(candidates: Sequence[str], top_n: int | None = None) -> list[tuple[str, int]]:
    """Return ``(word, score)`` sorted by score descending (stable on ties)."""
    freq = letter_frequencies(candidates)
    scored = [(w, sum(freq[c] for c in set(w))) for w in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored if top_n is None else scored[:top_n]


def best_by_frequency(candidates: Sequence[str]) -> str:
    """Highest-scoring candidate; the first occurrence wins ties."""
    if not candidates:
        raise ValueError("no candidates remain")
    freq = letter_frequencies(candidates)
    return max(candidates, key=lambda w: sum(freq[c] for c in set(w)))


class CSPSolver(Solver):
    """Always guesses a still-possible word containing the most common letters."""

    name = "csp"

    def next_guess(self, candidates: Sequence[str], turn: int) -> str:
        return best_by_frequency(candidates)

"""Hybrid solver: Shannon entropy while the space is large, frequency scoring when small."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence

from wordle_solver import config
from wordle_solver.feedback import wordle_feedback
from wordle_solver.solvers.base import Solver
from wordle_solver.solvers.csp import best_by_frequency


def pattern_entropy(guess: str, candidates: Sequence[str]) -> float:
    """Expected information (bits) from playing ``guess`` over uniform ``candidates``."""
    if not candidates:
        return 0.0
    counts = Counter(wordle_feedback(guess, t) for t in candidates)
    total = len(candidates)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def best_by_entropy(pool: Sequence[str], candidates: Sequence[str]) -> str:
    """Guess in ``pool`` with maximum entropy; the first occurrence wins ties."""
    if not pool:
        raise ValueError("guess pool is empty")
    return max(pool, key=lambda g: pattern_entropy(g, candidates))


class HybridEntropySolver(Solver):
    """Entropy over a guess pool above ``threshold`` candidates, CSP scoring at or below it."""

    name = "entropy"

    def __init__(
        self,
        solutions: Sequence[str],
        guesses: Sequence[str],
        pool_size: int = config.EVAL_GUESS_POOL,
        threshold: int = config.ENTROPY_THRESHOLD,
    ) -> None:
        super().__init__(solutions)
        if pool_size < 1:
            raise ValueError("pool_size must be >= 1")
        self.pool = list(guesses)[:pool_size]
        if not self.pool:
            raise ValueError("guesses must be non-empty")
        self.threshold = threshold
        self._opening: str | None = None  # the first guess does not depend on the secret

    def next_guess(self, candidates: Sequence[str], turn: int) -> str:
        if len(candidates) <= self.threshold:
            return best_by_frequency(candidates)
        if turn == 1 and len(candidates) == len(self.solutions):
            if self._opening is None:
                self._opening = best_by_entropy(self.pool, candidates)
            return self._opening
        return best_by_entropy(self.pool, candidates)

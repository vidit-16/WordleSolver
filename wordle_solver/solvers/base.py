"""Common solver interface and game loop."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field

from wordle_solver.config import MAX_GUESSES, SOLVED_PATTERN
from wordle_solver.feedback import filter_candidates, is_valid_word, wordle_feedback


@dataclass
class SolveResult:
    secret: str
    guesses: list[str] = field(default_factory=list)
    solved: bool = False

    @property
    def steps(self) -> int | None:
        """Number of guesses used, or None if not solved within the limit."""
        return len(self.guesses) if self.solved else None


class Solver(ABC):
    """A strategy that picks the next guess from the remaining candidates."""

    name: str = "solver"

    def __init__(self, solutions: Sequence[str]) -> None:
        if not solutions:
            raise ValueError("solutions must be non-empty")
        self.solutions = list(solutions)

    @abstractmethod
    def next_guess(self, candidates: Sequence[str], turn: int) -> str:
        """Return the guess to play given remaining ``candidates`` (turn starts at 1)."""

    def solve(self, secret: str, max_guesses: int = MAX_GUESSES) -> SolveResult:
        """Play a full game against ``secret``."""
        if not isinstance(secret, str) or not is_valid_word(secret.upper()):
            raise ValueError(f"secret must be a five-letter word, got {secret!r}")
        secret = secret.upper()
        result = SolveResult(secret=secret)
        candidates = list(self.solutions)
        for turn in range(1, max_guesses + 1):
            if not candidates:
                break  # secret is not in the solution list
            guess = self.next_guess(candidates, turn)
            result.guesses.append(guess)
            pattern = wordle_feedback(guess, secret)
            if pattern == SOLVED_PATTERN:
                result.solved = True
                break
            candidates = filter_candidates(candidates, guess, pattern)
        return result

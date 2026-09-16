"""UI-independent game session used by the Streamlit pages (kept pure so it is testable)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from wordle_solver import config
from wordle_solver.feedback import filter_candidates, is_valid_pattern, is_valid_word
from wordle_solver.solvers.csp import best_by_frequency, rank_candidates
from wordle_solver.solvers.entropy import best_by_entropy


class InvalidMoveError(ValueError):
    """Raised for user input that cannot be applied to the session."""


@dataclass
class GameSession:
    solutions: list[str]
    candidates: list[str] = field(default_factory=list)
    history: list[tuple[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.candidates:
            self.candidates = list(self.solutions)

    @property
    def solved(self) -> bool:
        return bool(self.history) and self.history[-1][1] == config.SOLVED_PATTERN

    @property
    def finished(self) -> bool:
        return self.solved or len(self.history) >= config.MAX_GUESSES

    def reset(self) -> None:
        self.candidates = list(self.solutions)
        self.history = []

    def apply(self, guess: str, pattern: str) -> None:
        """Record a guess and its G/Y/B feedback, narrowing the candidates."""
        guess = (guess or "").strip().upper()
        pattern = (pattern or "").strip().upper()
        if not is_valid_word(guess):
            raise InvalidMoveError("Guess must be a 5-letter word using the letters A to Z.")
        if not is_valid_pattern(pattern):
            raise InvalidMoveError("Feedback must be 5 letters, each G, Y or B.")
        if self.solved:
            raise InvalidMoveError("This game is already solved. Start a new game to play again.")
        if len(self.history) >= config.MAX_GUESSES:
            raise InvalidMoveError(
                f"Max {config.MAX_GUESSES} guesses reached. Start a new game to play again."
            )
        self.history.append((guess, pattern))
        if pattern != config.SOLVED_PATTERN:
            self.candidates = filter_candidates(self.candidates, guess, pattern)

    def csp_suggestions(self, top_n: int = 10) -> list[tuple[str, int]]:
        return rank_candidates(self.candidates, top_n)

    def hybrid_suggestion(
        self,
        guesses: Sequence[str],
        pool_size: int = config.APP_GUESS_POOL,
        threshold: int = config.ENTROPY_THRESHOLD,
    ) -> tuple[str, str] | None:
        """Return ``(word, method)`` or None when no candidates remain."""
        if not self.candidates:
            return None
        if len(self.candidates) > threshold:
            return best_by_entropy(list(guesses)[:pool_size], self.candidates), "entropy"
        return best_by_frequency(self.candidates), "solution-based"

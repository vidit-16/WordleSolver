"""Wordle solver: CSP letter-frequency and entropy-driven hybrid strategies."""

from wordle_solver.feedback import filter_candidates, is_valid_pattern, wordle_feedback
from wordle_solver.solvers import CSPSolver, HybridEntropySolver, Solver
from wordle_solver.wordlists import WordLists, load_word_lists

__all__ = [
    "CSPSolver",
    "HybridEntropySolver",
    "Solver",
    "WordLists",
    "filter_candidates",
    "is_valid_pattern",
    "load_word_lists",
    "wordle_feedback",
]
__version__ = "1.0.0"

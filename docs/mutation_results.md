Mutation score: **57/64 killed (89.1%)**

Targets: `wordle_solver/feedback.py`, `wordle_solver/solvers/csp.py`, `wordle_solver/solvers/entropy.py`, `wordle_solver/solvers/base.py`, `wordle_solver/app/session.py`

Surviving mutants:
- wordle_solver/feedback.py:32: `f"guess and target must be {WORD_LENGTH} letters, got {guess!r} and {target!r}"` -> `f"guess or target must be {WORD_LENGTH} letters, got {guess!r} and {target!r}"`
- wordle_solver/feedback.py:32: `f"guess and target must be {WORD_LENGTH} letters, got {guess!r} and {target!r}"` -> `f"guess and target must be {WORD_LENGTH} letters, got {guess!r} or {target!r}"`
- wordle_solver/feedback.py:40: `remaining[i] = None` -> `remaining[i] = ""`
- wordle_solver/feedback.py:46: `remaining[remaining.index(guess[i])] = None` -> `remaining[remaining.index(guess[i])] = ""`
- wordle_solver/solvers/entropy.py:50: `self._opening: str | None = None  # the first guess does not depend on the secret` -> `self._opening: str | None = None  # the first guess does depend on the secret`
- wordle_solver/solvers/base.py:48: `break  # secret is not in the solution list` -> `break  # secret is in the solution list`
- wordle_solver/app/session.py:47: `raise InvalidMoveError("Feedback must be exactly 5 characters of G, Y or B.")` -> `raise InvalidMoveError("Feedback must be exactly 5 characters of G, Y and B.")`

import math

import pytest

from wordle_solver.solvers import (
    CSPSolver,
    HybridEntropySolver,
    pattern_entropy,
    rank_candidates,
    score_letter_frequency,
)
from wordle_solver.solvers.csp import best_by_frequency, letter_frequencies
from wordle_solver.solvers.entropy import best_by_entropy

SMALL = ["CRANE", "CRATE", "TRACE", "SLATE", "PLATE", "GRAPE", "SHAPE", "BRAKE", "STALE"]


def test_letter_frequencies_counts_unique_letters_per_word():
    freq = letter_frequencies(["EERIE", "EAGLE"])
    assert freq["E"] == 2
    assert freq["R"] == 1
    assert freq["Z"] == 0


def test_score_and_rank():
    cands = ["AAAAA", "ABCDE", "ABXYZ"]
    assert score_letter_frequency("ABCDE", cands) == 3 + 2 + 1 + 1 + 1
    ranked = rank_candidates(cands)
    assert ranked[0] == ("ABCDE", 8)
    assert rank_candidates(cands, top_n=1) == [("ABCDE", 8)]
    # ties are stable: first occurrence wins, same as max()
    assert best_by_frequency(["ABCDE", "EDCBA"]) == "ABCDE"


def test_best_by_frequency_empty():
    with pytest.raises(ValueError):
        best_by_frequency([])


def test_entropy_values():
    assert pattern_entropy("CRANE", []) == 0.0
    assert pattern_entropy("CRANE", ["CRANE"]) == 0.0
    # two candidates distinguished by the guess -> 1 bit
    assert math.isclose(pattern_entropy("CRANE", ["CRANE", "ZZZZZ"]), 1.0)
    # four candidates each giving distinct patterns -> 2 bits
    assert math.isclose(pattern_entropy("ABCDE", ["ABCDE", "AXXXX", "XBXXX", "XXCXX"]), 2.0)
    assert math.isclose(pattern_entropy("QQQQQ", ["ABCDE", "AXXXX"]), 0.0)


def test_best_by_entropy():
    assert best_by_entropy(["QQQQQ", "ABCDE"], ["ABCDE", "AXXXX"]) == "ABCDE"
    with pytest.raises(ValueError):
        best_by_entropy([], ["ABCDE"])


@pytest.mark.parametrize("secret", SMALL)
def test_csp_solves_every_word_in_small_list(secret):
    r = CSPSolver(SMALL).solve(secret)
    assert r.solved and r.guesses[-1] == secret and 1 <= r.steps <= 6


@pytest.mark.parametrize("secret", SMALL)
def test_hybrid_solves_every_word_in_small_list(secret):
    solver = HybridEntropySolver(SMALL, guesses=[*SMALL, "MOIST"], threshold=2)
    r = solver.solve(secret.lower())
    assert r.solved and r.secret == secret


def test_hybrid_uses_entropy_above_threshold_and_caches_opening():
    s = HybridEntropySolver(SMALL, guesses=["QQQQQ", "SLATE"], threshold=2)
    assert s.next_guess(SMALL, 1) == "SLATE"
    assert s._opening == "SLATE"
    # below threshold -> picks from candidates
    assert s.next_guess(["CRANE", "CRATE"], 3) in {"CRANE", "CRATE"}


def test_unsolvable_secret_not_in_list():
    r = CSPSolver(SMALL).solve("ZZZZZ")
    assert not r.solved and r.steps is None


def test_max_guesses_respected():
    r = CSPSolver(SMALL).solve(SMALL[-1], max_guesses=1)
    assert len(r.guesses) <= 1


@pytest.mark.parametrize("bad", ["", "ABC", "ABCD1", None])
def test_invalid_secret(bad):
    with pytest.raises(ValueError):
        CSPSolver(SMALL).solve(bad)


def test_constructor_validation():
    with pytest.raises(ValueError):
        CSPSolver([])
    with pytest.raises(ValueError):
        HybridEntropySolver(SMALL, guesses=[])
    with pytest.raises(ValueError):
        HybridEntropySolver(SMALL, guesses=SMALL, pool_size=0)


def test_best_by_frequency_picks_highest_not_lowest():
    # "ABCDE" shares letters with every candidate; "VWXYZ" with none of the others.
    assert best_by_frequency(["VWXYZ", "ABCDE", "ABCDF", "ABCDG"]) == "ABCDE"


def test_hybrid_pool_size_of_one_is_allowed():
    solver = HybridEntropySolver(SMALL, SMALL, pool_size=1)
    assert solver.pool == [SMALL[0]]
    with pytest.raises(ValueError):
        HybridEntropySolver(SMALL, SMALL, pool_size=0)


def test_hybrid_opening_cache_only_applies_to_the_full_list():
    solver = HybridEntropySolver(SMALL, SMALL, threshold=0)
    opening = solver.next_guess(SMALL, turn=1)
    subset = ["CRANE", "SLATE"]
    # same turn number, different candidates: must be recomputed, not served from cache
    assert solver.next_guess(subset, turn=1) == best_by_entropy(solver.pool, subset)
    assert best_by_entropy(solver.pool, subset) != opening

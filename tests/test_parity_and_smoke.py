"""Parity with the original evaluation.py (kept verbatim in tests/legacy) and app smoke tests."""

import random
import runpy
from pathlib import Path

import pytest

from tests.legacy import legacy_evaluation as legacy
from wordle_solver import CSPSolver, HybridEntropySolver, load_word_lists, wordle_feedback
from wordle_solver.solvers import pattern_entropy, score_letter_frequency

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def lists():
    return load_word_lists()


def test_feedback_parity_random_pairs(lists):
    rng = random.Random(0)
    pool = lists.solutions + lists.guesses
    for _ in range(3000):
        g, t = rng.choice(pool), rng.choice(pool)
        assert wordle_feedback(g, t) == legacy.wordle_feedback(g, t)


def test_scoring_parity(lists):
    cands = lists.solutions[:300]
    for w in lists.guesses[:50]:
        assert score_letter_frequency(w, cands) == legacy.score_probability(w, cands)
        assert pattern_entropy(w, cands) == pytest.approx(legacy.compute_entropy(w, cands))


def test_csp_solver_parity(lists):
    rng = random.Random(1)
    new = CSPSolver(lists.solutions)
    for secret in rng.sample(lists.solutions, 40):
        assert new.solve(secret).steps == legacy.solve_csp(secret, lists.solutions)


def test_hybrid_solver_parity_reduced_lists(lists):
    # legacy hard-codes a 1200-word pool; use a smaller solution list to stay fast.
    rng = random.Random(2)
    sols = rng.sample(lists.solutions, 150)
    guesses = lists.guesses[:1200]
    new = HybridEntropySolver(sols, guesses, pool_size=1200)
    for secret in sols[:6]:
        assert new.solve(secret).steps == legacy.solve_hybrid(secret, guesses, sols)


def test_package_imports():
    import wordle_solver.app.pages
    import wordle_solver.eval.benchmark  # noqa: F401


def _overview():
    from wordle_solver.app.pages import render_overview_page

    render_overview_page()


def _csp():
    from wordle_solver.app.pages import render_csp_page

    render_csp_page()


def _entropy():
    from wordle_solver.app.pages import render_entropy_page

    render_entropy_page()


def test_app_entry_point_runs():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not at.exception
    assert at.title[0].value == "Wordle Solver"


@pytest.mark.parametrize("page", [_overview, _csp, _entropy])
def test_pages_render(page):
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(page, default_timeout=60).run()
    assert not at.exception


def test_csp_page_interaction():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(_csp, default_timeout=60).run()
    at.text_input(key="csp_guess").input("slate")
    at.text_input(key="csp_fb").input("BBBBX")
    at.button(key="csp_analyze").click().run()
    assert any("Feedback must be" in w.value for w in at.warning)
    at.text_input(key="csp_fb").input("BBBBB")
    at.button(key="csp_analyze").click().run()
    assert not at.exception
    assert [m.label for m in at.metric] == ["Possible answers remaining"]


def test_entropy_page_suggests_a_guess():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(_entropy, default_timeout=120).run()
    at.text_input(key="entropy_guess").input("TARES")
    at.text_input(key="entropy_fb").input("BYBYY")
    at.button(key="entropy_analyze").click().run()
    assert not at.exception
    assert any("Suggested next guess" in m.value for m in at.markdown)


def test_legacy_script_is_untouched_runnable():
    # the original module must still import (no side effects at import time)
    mod = runpy.run_path(str(ROOT / "tests/legacy/legacy_evaluation.py"))
    assert "evaluate" in mod

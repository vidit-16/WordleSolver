import logging
import math

import pytest

from wordle_solver import config
from wordle_solver.app.session import GameSession, InvalidMoveError
from wordle_solver.eval import benchmark
from wordle_solver.wordlists import WordListError, load_word_lists, read_word_csv

# ---------------- word lists ----------------


def test_real_lists_load():
    lists = load_word_lists()
    assert len(lists.solutions) == 2315
    assert len(lists.guesses) == 10657
    assert all(len(w) == 5 and w.isupper() for w in lists.solutions)


def test_missing_file(tmp_path):
    with pytest.raises(WordListError, match="not found"):
        read_word_csv(tmp_path / "nope.csv")


def test_bad_header(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("name\ncrane\n")
    with pytest.raises(WordListError, match="header"):
        read_word_csv(p)


def test_skips_invalid_rows(tmp_path, caplog):
    p = tmp_path / "x.csv"
    p.write_text("word\ncrane\n\nab\nfoo12\n Slate \n")
    with caplog.at_level(logging.WARNING):
        assert read_word_csv(p) == ["CRANE", "SLATE"]
    assert "Skipped 2" in caplog.text


def test_empty_list(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("word\nab\n")
    with pytest.raises(WordListError, match="no valid"):
        read_word_csv(p)


# ---------------- session ----------------

SOL = ["CRANE", "CRATE", "TRACE", "SLATE", "ZESTY"]


def test_session_flow():
    s = GameSession(solutions=SOL)
    assert s.candidates == SOL and not s.finished
    s.apply(" slate ", "bbggg")
    assert s.candidates == ["CRATE"]
    assert s.csp_suggestions() == [("CRATE", 5)]
    assert s.hybrid_suggestion(["QQQQQ"]) == ("CRATE", "solution-based")
    s.apply("crate", "GGGGG")
    assert s.solved and s.finished
    with pytest.raises(InvalidMoveError, match="solved"):
        s.apply("crate", "GGGGG")
    s.reset()
    assert s.history == [] and s.candidates == SOL


@pytest.mark.parametrize(
    ("guess", "fb", "msg"),
    [
        ("CRAN", "GGGGG", "Guess"),
        ("CRANE", "GGGX", "Feedback"),
        ("CRANE", "GGGGX", "Feedback"),
        (None, "GGGGG", "Guess"),
    ],
)
def test_session_rejects_bad_input(guess, fb, msg):
    s = GameSession(solutions=SOL)
    with pytest.raises(InvalidMoveError, match=msg):
        s.apply(guess, fb)
    assert s.history == []


def test_session_max_guesses():
    s = GameSession(solutions=SOL)
    for _ in range(config.MAX_GUESSES):
        s.apply("QQQQQ", "BBBBB")
    assert s.finished
    with pytest.raises(InvalidMoveError, match="Max"):
        s.apply("QQQQQ", "BBBBB")


def test_session_no_candidates_and_entropy_branch():
    s = GameSession(solutions=SOL)
    word, method = s.hybrid_suggestion(["QQQQQ", "CRATE"], threshold=2)
    assert method == "entropy" and word == "CRATE"
    s.apply("CRANE", "YYYYY")
    assert s.candidates == [] and s.hybrid_suggestion(["CRANE"]) is None


# ---------------- benchmark ----------------


def test_summarize():
    r = benchmark.summarize("x", [3, 4, None, 5], seconds=2.0)
    assert r.games == 4 and r.wins == 3
    assert math.isclose(r.avg_guesses, 4.0) and r.max_guesses == 5
    assert math.isclose(r.win_rate, 75.0) and math.isclose(r.ms_per_game, 500.0)
    assert r.distribution == {0: 1, 3: 1, 4: 1, 5: 1}
    empty = benchmark.summarize("e", [], 0.0)
    assert empty.win_rate == 0.0 and empty.ms_per_game == 0.0 and math.isnan(empty.avg_guesses)


def test_build_solver_unknown():
    with pytest.raises(ValueError):
        benchmark.build_solver("nope")


def test_benchmark_cli_small(tmp_path, capsys):
    out = tmp_path / "r.md"
    rc = benchmark.main(["--sample", "3", "--solvers", "csp", "--out", str(out)])
    assert rc == 0
    text = out.read_text()
    assert "| csp | 3 |" in text and "sample_seed=42" in text


def test_benchmark_cli_missing_data(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise WordListError("missing")

    monkeypatch.setattr(benchmark, "load_word_lists", boom)
    assert benchmark.main(["--solvers", "csp"]) == 2


def test_session_switches_to_solution_scoring_at_the_threshold():
    s = GameSession(solutions=SOL)
    assert len(s.candidates) == 5
    _, method = s.hybrid_suggestion(["QQQQQ", "CRATE"], threshold=5)
    assert method == "solution-based"
    _, method = s.hybrid_suggestion(["QQQQQ", "CRATE"], threshold=4)
    assert method == "entropy"

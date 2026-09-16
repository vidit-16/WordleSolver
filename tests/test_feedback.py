import pytest
from hypothesis import given
from hypothesis import strategies as st

from wordle_solver.feedback import (
    filter_candidates,
    is_valid_pattern,
    is_valid_word,
    wordle_feedback,
)

words = st.text(alphabet="ABCDE", min_size=5, max_size=5)


@pytest.mark.parametrize(
    ("guess", "target", "expected"),
    [
        ("CRANE", "CRANE", "GGGGG"),
        ("ABCDE", "FGHIJ", "BBBBB"),
        ("EABCD", "ABCDE", "YYYYY"),
        ("SPEED", "ABIDE", "BBYBY"),  # second E is black: only one E in target
        ("ALLEY", "HELLO", "BYGYB"),
        ("LLAMA", "HELLO", "YYBBB"),
        ("EERIE", "THREE", "YBGBG"),
        ("ABBEY", "BABES", "YYGGB"),
        ("GEESE", "EERIE", "BGYBG"),
    ],
)
def test_known_patterns(guess, target, expected):
    assert wordle_feedback(guess, target) == expected


def test_rejects_wrong_length():
    with pytest.raises(ValueError):
        wordle_feedback("ABC", "ABCDE")
    with pytest.raises(ValueError):
        wordle_feedback("ABCDE", "ABCDEF")


@given(words)
def test_self_feedback_is_all_green(w):
    assert wordle_feedback(w, w) == "GGGGG"


@given(words, words)
def test_pattern_properties(g, t):
    p = wordle_feedback(g, t)
    assert is_valid_pattern(p)
    # green positions exactly match equal letters
    assert all((p[i] == "G") == (g[i] == t[i]) for i in range(5))
    # green+yellow count for a letter never exceeds its count in the target
    for ch in set(g):
        marked = sum(1 for i in range(5) if g[i] == ch and p[i] in "GY")
        assert marked == min(g.count(ch), t.count(ch))


@given(words, words)
def test_filter_keeps_secret(g, t):
    assert t in filter_candidates([t, g], g, wordle_feedback(g, t))


def test_validators():
    assert is_valid_word("CRANE")
    assert not is_valid_word("CRAN")
    assert not is_valid_word("CRAN3")
    assert not is_valid_word("CRÄNE")
    assert not is_valid_word(None)
    assert is_valid_pattern("GYBBG")
    assert not is_valid_pattern("GYBBX")
    assert not is_valid_pattern("GYBB")
    assert not is_valid_pattern(12345)

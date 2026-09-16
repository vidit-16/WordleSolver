"""Streamlit rendering for the app. ``app.py`` wires these into the navigation."""

from __future__ import annotations

import logging

import pandas as pd
import streamlit as st

from wordle_solver import config
from wordle_solver.app.session import GameSession, InvalidMoveError
from wordle_solver.wordlists import WordListError, WordLists, load_word_lists

logger = logging.getLogger(__name__)

FEEDBACK_HELP = (
    "One letter per tile, left to right. "
    "G = green (right letter, right position), "
    "Y = yellow (in the word, wrong position), "
    "B = grey (not in the word)."
)


@st.cache_data
def _cached_lists() -> WordLists:
    return load_word_lists()


def _lists_or_stop() -> WordLists:
    try:
        return _cached_lists()
    except WordListError as exc:
        logger.exception("Failed to load word lists")
        st.error(f"The word lists could not be loaded: {exc}")
        st.stop()
        raise  # pragma: no cover - st.stop raises


def _session(key: str, lists: WordLists) -> GameSession:
    if key not in st.session_state:
        st.session_state[key] = GameSession(solutions=lists.solutions)
    return st.session_state[key]


def _inputs(session: GameSession, key: str) -> None:
    if st.sidebar.button("Start a new game", key=f"{key}_reset"):
        session.reset()
        st.rerun()
    guess = st.text_input("Guess", key=f"{key}_guess", placeholder="e.g. CRANE", max_chars=5)
    fb = st.text_input("Feedback", key=f"{key}_fb", placeholder="e.g. BYBBG", max_chars=5)
    st.caption(FEEDBACK_HELP)
    if st.button("Apply feedback", key=f"{key}_analyze", type="primary"):
        try:
            session.apply(guess, fb)
        except InvalidMoveError as exc:
            st.warning(str(exc))


def _status(session: GameSession) -> bool:
    """Show the game state. Returns True when there is nothing left to suggest."""
    if session.solved:
        st.success(f"Solved in {len(session.history)} guesses.")
        return True
    if not session.candidates:
        st.error(
            "No answer in the word list matches this feedback. "
            "Check the letters you entered, or start a new game."
        )
        return True
    if session.finished:
        st.warning(f"All {config.MAX_GUESSES} guesses have been used.")
        return True
    st.metric("Possible answers remaining", len(session.candidates))
    return False


def _history(session: GameSession) -> None:
    st.divider()
    st.subheader("Guesses so far")
    if session.history:
        table = pd.DataFrame(session.history, columns=["Guess", "Feedback"])
        table.index = range(1, len(table) + 1)
        table.index.name = "Turn"
        st.table(table)
    else:
        st.write("No guesses yet. Enter your first guess and the feedback Wordle gave you.")


def render_overview_page() -> None:
    st.title("Wordle Solver")
    st.write(
        "Suggests the next Wordle guess from the feedback you have so far, using one of "
        "two methods. Both were tested on all 2,315 official Wordle answers."
    )
    st.table(
        pd.DataFrame(
            {
                "Method": ["Constraint solver", "Hybrid entropy solver"],
                "How it picks a guess": [
                    "The remaining answer that shares the most common letters",
                    "The guess that splits the remaining answers most evenly, "
                    "then the most likely answer once few remain",
                ],
                "Games won": ["99.05%", "99.78%"],
                "Average guesses": ["3.65", "3.68"],
                "Time per game": ["78 ms", "1.0 s"],
            }
        ).set_index("Method")
    )
    st.subheader("How to use it")
    st.markdown(
        "1. Choose a solver from the sidebar.\n"
        "2. Enter the word you guessed in Wordle.\n"
        "3. Enter the colours Wordle showed, as five letters: "
        "**G** for green, **Y** for yellow, **B** for grey.\n"
        "4. The solver narrows the possible answers and suggests your next guess."
    )


def render_csp_page() -> None:
    st.title("Constraint solver")
    st.write(
        "Keeps only the answers consistent with every piece of feedback, then ranks them "
        "by how common their letters are among the answers still possible."
    )
    lists = _lists_or_stop()
    session = _session("csp_session", lists)
    _inputs(session, "csp")
    if session.history and not _status(session):
        st.subheader("Suggested guesses")
        suggestions = pd.DataFrame(session.csp_suggestions(10), columns=["Word", "Score"])
        suggestions.index = range(1, len(suggestions) + 1)
        st.table(suggestions)
        st.caption("Score: how many remaining answers contain each of the word's letters, summed.")
    _history(session)


def render_entropy_page() -> None:
    st.title("Hybrid entropy solver")
    st.write(
        "While many answers remain, suggests the guess expected to eliminate the most of them, "
        "even if it cannot be the answer itself. Once "
        f"{config.ENTROPY_THRESHOLD} or fewer remain, it suggests the most likely answer."
    )
    lists = _lists_or_stop()
    session = _session("entropy_session", lists)
    _inputs(session, "entropy")
    if session.history and not _status(session):
        suggestion = session.hybrid_suggestion(lists.guesses)
        if suggestion is not None:
            word, method = suggestion
            reason = (
                "chosen to split the remaining answers as evenly as possible"
                if method == "entropy"
                else "the most likely remaining answer"
            )
            st.markdown(f"**Suggested next guess: {word}**")
            st.caption(reason.capitalize() + ".")
    _history(session)

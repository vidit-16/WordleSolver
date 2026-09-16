"""Streamlit rendering for the solver pages. Imported by the thin files in ``pages/``."""

from __future__ import annotations

import logging

import pandas as pd
import streamlit as st

from wordle_solver.app.session import GameSession, InvalidMoveError
from wordle_solver.wordlists import WordListError, WordLists, load_word_lists

logger = logging.getLogger(__name__)


@st.cache_data
def _cached_lists() -> WordLists:
    return load_word_lists()


def _lists_or_stop() -> WordLists:
    try:
        return _cached_lists()
    except WordListError as exc:
        logger.exception("Failed to load word lists")
        st.error(f"Could not load word lists: {exc}")
        st.stop()
        raise  # pragma: no cover - st.stop raises


def _session(key: str, lists: WordLists) -> GameSession:
    if key not in st.session_state:
        st.session_state[key] = GameSession(solutions=lists.solutions)
    return st.session_state[key]


def _inputs(session: GameSession, key: str) -> None:
    if st.sidebar.button("Reset", key=f"{key}_reset"):
        session.reset()
        st.rerun()
    if not session.history:
        st.info("Start with your first guess")
    guess = st.text_input("Guess", key=f"{key}_guess")
    fb = st.text_input("Feedback (G/Y/B)", key=f"{key}_fb")
    if st.button("Analyze", key=f"{key}_analyze"):
        try:
            session.apply(guess, fb)
        except InvalidMoveError as exc:
            st.warning(str(exc))


def _history(session: GameSession) -> None:
    st.markdown("---")
    st.subheader("History")
    if session.history:
        st.table(pd.DataFrame(session.history, columns=["Guess", "Feedback"]))
    else:
        st.info("No guesses yet.")


def render_csp_page() -> None:
    st.set_page_config(page_title="Wordle Solver (CSP)", page_icon="🧠")
    st.title("🧠 Wordle Solver (CSP)")
    lists = _lists_or_stop()
    session = _session("csp_session", lists)
    _inputs(session, "csp")
    if session.history:
        st.markdown("---")
        if session.solved:
            st.success(f"🎉 Solved in {len(session.history)} guesses!")
        elif not session.candidates:
            st.error("No candidates match that feedback - check your inputs or reset.")
        else:
            st.write(f"Remaining candidates: {len(session.candidates)}")
            st.write("Top suggestions:")
            for w, s in session.csp_suggestions(10):
                st.write(f"{w} ({s})")
    _history(session)


def render_entropy_page() -> None:
    st.set_page_config(page_title="Hybrid Solver", page_icon="🤖")
    st.title("🤖 Wordle Solver (Hybrid)")
    lists = _lists_or_stop()
    session = _session("entropy_session", lists)
    _inputs(session, "entropy")
    if session.history:
        st.markdown("---")
        if session.solved:
            st.success(f"🎉 Solved in {len(session.history)} guesses!")
        else:
            st.subheader(f"Round {len(session.history)}")
            st.write(f"Remaining candidates: {len(session.candidates)}")
            suggestion = session.hybrid_suggestion(lists.guesses)
            if suggestion is None:
                st.error("No candidates match that feedback - check your inputs or reset.")
            else:
                word, method = suggestion
                st.write(f"Best guess ({method}): {word}")
    _history(session)

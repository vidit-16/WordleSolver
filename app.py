import streamlit as st

st.set_page_config(page_title="Wordle Solver", layout="centered", page_icon="🧩")

st.title("🧩 Wordle Solver")
st.markdown("""
An intelligent Wordle solver that combines **constraint-based reasoning (CSP)**
and **entropy-driven optimization** to minimize guesses
and efficiently converge to the correct solution.

The system uses a hybrid strategy to balance exploration and exploitation,
enabling near-optimal performance.

Use the sidebar to explore different solving approaches and analyze Wordle gameplay step-by-step.
""")

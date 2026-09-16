import streamlit as st

from wordle_solver.app.pages import render_csp_page, render_entropy_page, render_overview_page

st.set_page_config(page_title="Wordle Solver", page_icon="assets/favicon.png", layout="centered")

navigation = st.navigation(
    [
        st.Page(render_overview_page, title="Overview", url_path="overview", default=True),
        st.Page(render_csp_page, title="Constraint solver", url_path="constraint-solver"),
        st.Page(render_entropy_page, title="Hybrid entropy solver", url_path="entropy-solver"),
    ]
)
navigation.run()

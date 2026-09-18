"""Visual theme: page styling, feedback tiles, and the colour legend.

Colour carries meaning here rather than decorating the page. The three feedback
colours are Wordle's own, so a tile on screen matches the tile the player saw,
and the letters G, Y and B are shown in those colours wherever they are
explained. Everything else is one navy accent on a white page.

Tile colours are the saturated versions. Green and grey carry white letters;
the amber tile carries dark ones, because white on amber is about 2:1 and hard
to read. The inline text versions are darker again so they stay legible on a
white background, where the bright green would only reach 3:1.
"""

from __future__ import annotations

import html

import streamlit as st

ACCENT = "#24527d"

TILE = {"G": "#5f9e58", "Y": "#c9a227", "B": "#8e9297"}
TEXT = {"G": "#2f7d32", "Y": "#8a6a00", "B": "#5b6472"}
NAMES = {"G": "green", "Y": "yellow", "B": "grey"}

_CSS = f"""
<style>
:root {{
  --accent: {ACCENT};
  --ink: #14181f;
  --muted: #5b6472;
  --surface: #f7f8f9;
  --hairline: #e5e7eb;
}}

/* Streamlit's own red-to-yellow bar sits above every page; make it ours. */
[data-testid="stDecoration"] {{
  background: linear-gradient(90deg, var(--accent), #33668f);
}}

/* A rule under the page title: the whole page's colour, in one place. */
.stMain h1 {{
  padding-bottom: 0.3rem;
  border-bottom: 3px solid var(--accent);
  display: inline-block;
}}

.stMain h2, .stMain h3 {{ color: var(--ink); }}

/* Tables: an accent header and hairline rows, so a table reads as a unit
   instead of floating text. */
[data-testid="stTable"] table {{
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid var(--hairline);
  border-radius: 10px;
  overflow: hidden;
}}
[data-testid="stTable"] thead th {{
  background: var(--surface);
  color: var(--muted);
  font-size: 12px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border-bottom: 2px solid var(--accent);
}}
[data-testid="stTable"] tbody tr:nth-child(even) {{ background: #fbfcfd; }}
[data-testid="stTable"] tbody td {{ border-bottom: 1px solid var(--hairline); }}
[data-testid="stTable"] tbody tr:last-child td {{ border-bottom: none; }}

/* The active page in the sidebar, in the accent rather than plain grey. */
[data-testid="stSidebarNav"] a[aria-current="page"] {{
  border-left: 3px solid var(--accent);
  background: var(--surface);
}}

/* Feedback tiles. */
.tile-row {{ display: flex; gap: 6px; margin: 2px 0; }}
.tile {{
  width: 38px; height: 38px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 6px;
  color: #ffffff;
  font-weight: 700;
  font-size: 18px;
  letter-spacing: 0.02em;
}}
.tile-turn {{
  width: 22px; color: var(--muted); font-size: 13px;
  display: flex; align-items: center; justify-content: flex-end;
  padding-right: 4px;
}}
.legend-key {{ font-weight: 700; }}

/* A result worth looking at, rather than another line of bold text. */
.callout {{
  border: 1px solid var(--hairline);
  border-left: 4px solid var(--accent);
  border-radius: 10px;
  background: var(--surface);
  padding: 12px 16px;
  margin: 6px 0 2px;
}}
.callout-label {{
  font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em;
  color: var(--muted);
}}
.callout-value {{
  font-size: 26px; font-weight: 700; color: var(--accent); letter-spacing: 0.04em;
}}
.callout-note {{ font-size: 13px; color: var(--muted); }}
</style>
"""


def inject() -> None:
    """Apply the page styling. Safe to call on every rerun."""
    st.markdown(_CSS, unsafe_allow_html=True)


def tiles(guess: str, feedback: str, turn: int | None = None) -> str:
    """One row of coloured tiles for a guess and the feedback it got."""
    cells = []
    if turn is not None:
        cells.append(f'<div class="tile-turn">{turn}</div>')
    for letter, code in zip(guess.upper(), feedback.upper(), strict=False):
        colour = TILE.get(code, TILE["B"])
        ink = "#1a1a1a" if code == "Y" else "#ffffff"
        cells.append(
            f'<div class="tile" style="background:{colour};color:{ink}" '
            f'title="{html.escape(NAMES.get(code, "grey"))}">{html.escape(letter)}</div>'
        )
    return f'<div class="tile-row">{"".join(cells)}</div>'


def key(code: str) -> str:
    """The letter G, Y or B in the colour it stands for."""
    return f'<span class="legend-key" style="color:{TEXT[code]}">{code}</span>'


def feedback_help() -> str:
    """The input legend, with each letter in its own colour."""
    return (
        "One letter per tile, left to right. "
        f"{key('G')} = green (right letter, right position), "
        f"{key('Y')} = yellow (in the word, wrong position), "
        f"{key('B')} = grey (not in the word)."
    )


def callout(label: str, value: str, note: str = "") -> str:
    """A bordered result block: the next guess, not just another bold line."""
    note_html = f'<div class="callout-note">{html.escape(note)}</div>' if note else ""
    return (
        f'<div class="callout"><div class="callout-label">{html.escape(label)}</div>'
        f'<div class="callout-value">{html.escape(value)}</div>{note_html}</div>'
    )

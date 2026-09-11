# Wordle Solver

**Constraint satisfaction and information theory, compared on the same Wordle board.**

This project tests two ways of choosing the next Wordle guess. The CSP solver reduces the candidate set using Wordle's feedback rules and ranks the remaining words by letter frequency. The hybrid solver uses information gain to choose exploratory guesses while the candidate set is large, then switches to solution-based scoring near the end.

There is a live Streamlit app if you want to play with both approaches:

https://wordle--solver.streamlit.app/

---

## What it actually does

Both solvers start from the same list of valid solutions and process the exact `G/Y/B` feedback produced by a guess.

**CSP solver**

The candidate set is filtered after every guess. A word is scored using the frequency of its unique letters across the remaining candidates, so the next suggestion favours letters that are likely to split the search space.

**Hybrid entropy solver**

When more than five candidates remain, the solver evaluates guesses by Shannon entropy over the possible feedback patterns. When the search space becomes small, it falls back to the same solution-based frequency score used by the CSP solver.

The implementation therefore has a clear tradeoff: CSP favours cheap candidate scoring, while entropy spends more computation to choose guesses that are useful for exploration.

## Evaluation

The evaluation script runs both solvers against all **2,315 official Wordle solutions** in the repository.

| Model | Average guesses | Max guesses | Success rate |
| --- | ---: | ---: | ---: |
| CSP Solver | 3.65 | 6 | 99.05% |
| Hybrid Solver | 3.68 | 6 | 99.78% |

The result is not simply "entropy is better": the hybrid solver has a slightly higher average number of guesses, while solving a larger share of the test set. The useful comparison is therefore between **average efficiency and coverage**, not a single winning metric.

Run the evaluation with:

```bash
python evaluation.py
```

## The Wordle logic

The feedback implementation handles the normal green, yellow and black cases while respecting repeated letters. After each guess, candidates survive only when their generated feedback pattern exactly matches the observed pattern.

That same feedback function is used during evaluation, so the solver is tested against the same game logic it uses while playing.

## App

The Streamlit app exposes the two approaches separately:

```text
Wordle Solver
├── CSP Solver
└── Hybrid Entropy Solver
```

For either approach, enter a five-letter guess and the resulting `G/Y/B` pattern. The app keeps the candidate state, shows the number of remaining solutions, suggests the next guess, and records the guess history.

## Project structure

```text
.
├── app.py
├── evaluation.py
├── pages/
│   ├── 1_CSP_Solver.py
│   └── 2_Entropy_Solver.py
├── valid_guesses.csv
├── valid_solutions.csv
└── requirements.txt
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The repository contains separate lists for valid guesses and official solutions. The evaluation uses the complete solution list rather than a sampled subset.

## What I was interested in

The interesting part of the project is not just solving Wordle. It is seeing what happens when two different decision rules operate under the same feedback mechanism.

CSP asks: **what can still be true?**

Entropy asks: **which guess will tell us the most?**

The hybrid approach combines those ideas by using information gain while there is still a lot to learn, then narrowing down with solution-based scoring once the state is constrained.
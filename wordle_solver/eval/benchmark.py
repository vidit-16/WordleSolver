"""A/B benchmark: CSP vs hybrid entropy solver (avg guesses, win rate, time).

Usage::

    python -m wordle_solver.eval.benchmark                 # all 2,315 solutions
    python -m wordle_solver.eval.benchmark --sample 200    # seeded random subset
    python -m wordle_solver.eval.benchmark --workers 8 --out docs/benchmark.md
"""

from __future__ import annotations

import argparse
import logging
import random
import statistics
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from wordle_solver import config
from wordle_solver.solvers import CSPSolver, HybridEntropySolver, Solver
from wordle_solver.wordlists import WordListError, load_word_lists

logger = logging.getLogger(__name__)


@dataclass
class StrategyReport:
    name: str
    games: int
    wins: int
    avg_guesses: float  # over wins
    max_guesses: int
    total_seconds: float
    distribution: dict[int, int]

    @property
    def win_rate(self) -> float:
        return 100.0 * self.wins / self.games if self.games else 0.0

    @property
    def ms_per_game(self) -> float:
        return 1000.0 * self.total_seconds / self.games if self.games else 0.0


def summarize(name: str, steps: list[int | None], seconds: float) -> StrategyReport:
    """Aggregate per-game step counts (None = loss) into a report."""
    wins = [s for s in steps if s is not None]
    return StrategyReport(
        name=name,
        games=len(steps),
        wins=len(wins),
        avg_guesses=statistics.fmean(wins) if wins else float("nan"),
        max_guesses=max(wins) if wins else 0,
        total_seconds=seconds,
        distribution=dict(sorted(Counter(s if s is not None else 0 for s in steps).items())),
    )


_WORKER_SOLVER: Solver | None = None


def _init_worker(kind: str, pool_size: int) -> None:
    global _WORKER_SOLVER
    _WORKER_SOLVER = build_solver(kind, pool_size)


def _solve_one(secret: str) -> tuple[int | None, float]:
    assert _WORKER_SOLVER is not None
    t0 = time.perf_counter()
    steps = _WORKER_SOLVER.solve(secret).steps
    return steps, time.perf_counter() - t0


def build_solver(kind: str, pool_size: int = config.EVAL_GUESS_POOL) -> Solver:
    lists = load_word_lists()
    if kind == "csp":
        return CSPSolver(lists.solutions)
    if kind == "entropy":
        return HybridEntropySolver(lists.solutions, lists.guesses, pool_size=pool_size)
    raise ValueError(f"unknown solver {kind!r}")


def run_strategy(kind: str, secrets: list[str], workers: int, pool_size: int) -> StrategyReport:
    t0 = time.perf_counter()
    build_solver(kind, pool_size).solve(secrets[0])  # cold first game: includes opening search
    logger.info("%s cold first game: %.2fs", kind, time.perf_counter() - t0)
    if workers <= 1:
        _init_worker(kind, pool_size)
        _solve_one(secrets[0])
        results = [_solve_one(s) for s in secrets]
    else:
        with ProcessPoolExecutor(
            workers, initializer=_init_worker, initargs=(kind, pool_size)
        ) as ex:
            list(ex.map(_solve_one, [secrets[0]] * workers))  # best-effort warm-up
            results = list(ex.map(_solve_one, secrets, chunksize=8))
    steps = [r[0] for r in results]
    return summarize(kind, steps, sum(r[1] for r in results))


def to_markdown(reports: list[StrategyReport], meta: dict[str, object]) -> str:
    lines = [
        "| Solver | Games | Win rate | Avg guesses (wins) | Max | Losses | ms/game (warm) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in reports:
        lines.append(
            f"| {r.name} | {r.games} | {r.win_rate:.2f}% | {r.avg_guesses:.3f} | "
            f"{r.max_guesses} | {r.games - r.wins} | {r.ms_per_game:.1f} |"
        )
    lines.append("")
    lines.append("Guess distribution (0 = not solved in 6):")
    lines.append("")
    for r in reports:
        lines.append(f"- **{r.name}**: {r.distribution}")
    lines.append("")
    lines.append("Run metadata: " + ", ".join(f"{k}={v}" for k, v in meta.items()))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--sample", type=int, default=0, help="random subset size (0 = all)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--pool-size", type=int, default=config.EVAL_GUESS_POOL)
    parser.add_argument("--solvers", default="csp,entropy")
    parser.add_argument("--out", type=Path, help="write markdown table here")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        secrets = load_word_lists().solutions
    except WordListError as exc:
        logger.error("%s", exc)
        return 2
    if args.sample and args.sample < len(secrets):
        secrets = random.Random(args.seed).sample(secrets, args.sample)

    reports = []
    for kind in args.solvers.split(","):
        logger.info("Running %s on %d secrets ...", kind, len(secrets))
        reports.append(run_strategy(kind.strip(), secrets, args.workers, args.pool_size))
    meta = {
        "secrets": len(secrets),
        "sample_seed": args.seed if args.sample else "full-list",
        "entropy_pool": args.pool_size,
        "workers": args.workers,
        "python": sys.version.split()[0],
    }
    md = to_markdown(reports, meta)
    print(md)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md, encoding="utf-8")
        logger.info("Wrote %s", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

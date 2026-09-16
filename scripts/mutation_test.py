"""Lightweight mutation testing for the core solver logic.

mutmut does not support native Windows, so this script applies a fixed catalogue of
operator / constant mutations one at a time to the core modules, runs the fast unit
tests, and reports how many mutants the suite kills. Files are always restored.

    python scripts/mutation_test.py [--out docs/mutation_results.md]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = [
    "wordle_solver/feedback.py",
    "wordle_solver/solvers/csp.py",
    "wordle_solver/solvers/entropy.py",
    "wordle_solver/solvers/base.py",
    "wordle_solver/app/session.py",
]
TESTS = [
    "tests/test_feedback.py",
    "tests/test_solvers.py",
    "tests/test_wordlists_session_benchmark.py",
]

# (regex, replacement) applied to a single occurrence at a time
OPERATORS: list[tuple[str, str]] = [
    (r"==", "!="),
    (r"!=", "=="),
    (r"<=", "<"),
    (r"(?<![<>=!])>(?!=)", ">="),
    (r"(?<![<>=!-])<(?![=<])", "<="),
    (r"\bnot \b", ""),
    (r"\band\b", "or"),
    (r"\bor\b", "and"),
    (r"\bTrue\b", "False"),
    (r"\bFalse\b", "True"),
    (r'"G"', '"Y"'),
    (r'"Y"', '"B"'),
    (r'"B"', '"G"'),
    (r"\+ 1\b", "+ 2"),
    (r"range\(1,", "range(0,"),
    (r"reverse=True", "reverse=False"),
    (r"\bmax\(", "min("),
    (r"-sum\(", "sum("),
    (r"/ total", "* total"),
    (r"\bNone\b(?=\s*$)", '""'),
    (r"\breturn 0\.0\b", "return 1.0"),
]


def mutants_for(text: str):
    lines = text.splitlines(keepends=True)
    for lineno, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", '"""', "from ", "import ")) or "->" in line:
            continue
        for pattern, repl in OPERATORS:
            for m in re.finditer(pattern, line):
                mutated = line[: m.start()] + repl + line[m.end() :]
                if mutated != line:
                    new = lines.copy()
                    new[lineno] = mutated
                    yield lineno + 1, stripped, mutated.strip(), "".join(new)


def run_tests() -> bool:
    cmd = [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", *TESTS]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, timeout=300)
    return proc.returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    killed = total = 0
    survivors: list[str] = []
    for rel in TARGETS:
        path = ROOT / rel
        original = path.read_text(encoding="utf-8")
        try:
            for lineno, before, after, text in mutants_for(original):
                path.write_text(text, encoding="utf-8")
                total += 1
                try:
                    passed = run_tests()
                except subprocess.TimeoutExpired:
                    passed = False
                if passed:
                    survivors.append(f"{rel}:{lineno}: `{before}` -> `{after}`")
                else:
                    killed += 1
                status = "SURVIVED" if passed else "killed"
                print(f"[{total}] {status} {rel}:{lineno}", flush=True)
        finally:
            path.write_text(original, encoding="utf-8")
    score = 100.0 * killed / total if total else 0.0
    report = [
        f"Mutation score: **{killed}/{total} killed ({score:.1f}%)**",
        "",
        "Targets: " + ", ".join(f"`{t}`" for t in TARGETS),
        "",
        "Surviving mutants:" if survivors else "No surviving mutants.",
        *[f"- {s}" for s in survivors],
    ]
    md = "\n".join(report) + "\n"
    print(md)
    if args.out:
        args.out.write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

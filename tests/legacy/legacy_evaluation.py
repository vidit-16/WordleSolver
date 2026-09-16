import pandas as pd
import math

# -----------------------------
# LOAD DATA
# -----------------------------
def load_lists():
    g = pd.read_csv("valid_guesses.csv")
    s = pd.read_csv("valid_solutions.csv")

    guesses = g['word'].dropna().str.upper().tolist()
    solutions = s['word'].dropna().str.upper().tolist()

    return guesses, solutions


# -----------------------------
# WORDLE FEEDBACK
# -----------------------------
def wordle_feedback(guess, target):
    pattern = [''] * 5
    target_chars = list(target)

    # Greens
    for i in range(5):
        if guess[i] == target[i]:
            pattern[i] = 'G'
            target_chars[i] = None

    # Yellows + Blacks
    for i in range(5):
        if pattern[i] == '':
            if guess[i] in target_chars:
                pattern[i] = 'Y'
                target_chars[target_chars.index(guess[i])] = None
            else:
                pattern[i] = 'B'

    return ''.join(pattern)


# -----------------------------
# ENTROPY
# -----------------------------
def compute_entropy(guess, possible):
    pattern_counts = {}

    for target in possible:
        p = wordle_feedback(guess, target)
        pattern_counts[p] = pattern_counts.get(p, 0) + 1

    total = len(possible)
    entropy = 0

    for count in pattern_counts.values():
        prob = count / total
        entropy -= prob * math.log2(prob)

    return entropy


# -----------------------------
# CSP PROBABILITY SCORE
# -----------------------------
def score_probability(word, possible):
    freq = {}
    for w in possible:
        for c in set(w):
            freq[c] = freq.get(c, 0) + 1
    return sum(freq.get(c, 0) for c in set(word))


# -----------------------------
# SOLVERS
# -----------------------------
def solve_csp(secret, solutions):
    possible = solutions.copy()

    for step in range(1, 7):
        best_guess = max(
            possible,
            key=lambda w: score_probability(w, possible)
        )

        pattern = wordle_feedback(best_guess, secret)

        if pattern == "GGGGG":
            return step

        possible = [
            w for w in possible
            if wordle_feedback(best_guess, w) == pattern
        ]

    return None


def solve_hybrid(secret, guesses, solutions):
    possible = solutions.copy()

    for step in range(1, 7):

        if len(possible) > 5:
            # LIMIT guesses for speed (IMPORTANT)
            subset = guesses[:1200]

            best_guess = max(
                subset,
                key=lambda g: compute_entropy(g, possible)
            )
        else:
            best_guess = max(
                possible,
                key=lambda w: score_probability(w, possible)
            )

        pattern = wordle_feedback(best_guess, secret)

        if pattern == "GGGGG":
            return step

        possible = [
            w for w in possible
            if wordle_feedback(best_guess, w) == pattern
        ]

    return None


# -----------------------------
# EVALUATION
# -----------------------------
def evaluate():
    guesses, solutions = load_lists()

    csp_results = []
    hybrid_results = []

    print("Starting evaluation...\n")

    for i, word in enumerate(solutions):

        csp_steps = solve_csp(word, solutions)
        hybrid_steps = solve_hybrid(word, guesses, solutions)

        if csp_steps:
            csp_results.append(csp_steps)
        if hybrid_steps:
            hybrid_results.append(hybrid_steps)

        if i % 10 == 0:
            print(f"Processed {i}/{len(solutions)}")

    # -----------------------------
    # METRICS
    # -----------------------------
    def compute_metrics(results, total):
        avg = sum(results) / len(results)
        max_steps = max(results)
        success = len(results) / total * 100
        return avg, max_steps, success

    csp_avg, csp_max, csp_success = compute_metrics(csp_results, len(solutions))
    hyb_avg, hyb_max, hyb_success = compute_metrics(hybrid_results, len(solutions))

    # -----------------------------
    # OUTPUT
    # -----------------------------
    print("\n===== RESULTS =====")

    print("\nCSP Solver:")
    print(f"Average guesses: {csp_avg:.2f}")
    print(f"Max guesses: {csp_max}")
    print(f"Success rate: {csp_success:.2f}%")

    print("\nHybrid Solver:")
    print(f"Average guesses: {hyb_avg:.2f}")
    print(f"Max guesses: {hyb_max}")
    print(f"Success rate: {hyb_success:.2f}%")

    print("\n===== IMPROVEMENT =====")
    print(f"Guess reduction: {csp_avg - hyb_avg:.2f} guesses")


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    evaluate()
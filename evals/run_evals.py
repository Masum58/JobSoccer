"""
FILE: evals/run_evals.py
========================
WHAT THIS FILE DOES:
    This is the automated evaluation test runner (Evals Framework).
    It tests our AI evaluation engine (evaluate_candidate) against the
    three benchmark candidate transcripts in evals/benchmark_data.py.

    It validates four essential engineering and governance assertions:
    1. Score Ceiling Test   : Strong candidate scores high (>= 55 / 72).
    2. Score Floor Test     : Weak candidate scores low (<= 36 / 72).
    3. Score Separation     : Strong score is significantly higher than weak score.
    4. Red Flag Safety Test : Serious ethical or safeguarding violations
                              are immediately detected and flagged.

    This ensures our AI model is calibrated, objective, and safe
    before deploying to real recruiters.

HOW TO RUN:
    cd jobsoccer_ai
    python -m evals.run_evals
    (or: python evals/run_evals.py)

CONNECTED TO:
    → evals/benchmark_data.py           : loads benchmark transcripts
    → app/services/interview_scorer.py  : calls evaluate_candidate()
"""

import sys
from pathlib import Path

# Add project root to sys.path so we can import from `app`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.interview_scorer import evaluate_candidate
from evals.benchmark_data import (
    STRONG_HEAD_COACH_TRANSCRIPT,
    WEAK_HEAD_COACH_TRANSCRIPT,
    RED_FLAG_HEAD_COACH_TRANSCRIPT,
)


def run_benchmark_evals():
    """
    WHY THIS EXISTS:
        Executes the benchmark evaluation suite, compares AI outputs
        against predefined quality standards, and prints a clear report.

    INPUT:
        None (uses predefined benchmark transcripts in benchmark_data.py).

    OUTPUT:
        Prints a structured summary table in the terminal and returns
        True if all benchmark assertions pass, or False if any fail.

    CALLED FROM:
        Directly executed when running this script.
    """
    print("\n" + "=" * 65)
    print("      JOBSOCCER AI EVALUATION BENCHMARK SUITE")
    print("=" * 65)
    print("Testing AI engine against fixed Golden Benchmarks (Role: Head Coach)...\n")

    role = "head_coach"
    results = {}

    # ─────────────────────────────────────────────────────────────────────────
    # 1. EVALUATE STRONG CANDIDATE
    # ─────────────────────────────────────────────────────────────────────────
    print("[1/3] Running evaluation on STRONG candidate...")
    res_strong = evaluate_candidate(role_slug=role, transcript=STRONG_HEAD_COACH_TRANSCRIPT)
    score_strong = res_strong.get("total_score", 0)
    flags_strong = res_strong.get("red_flags", [])
    print(f"      -> Total Score: {score_strong} / 72 | Red Flags: {len(flags_strong)}")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. EVALUATE WEAK CANDIDATE
    # ─────────────────────────────────────────────────────────────────────────
    print("[2/3] Running evaluation on WEAK candidate...")
    res_weak = evaluate_candidate(role_slug=role, transcript=WEAK_HEAD_COACH_TRANSCRIPT)
    score_weak = res_weak.get("total_score", 0)
    flags_weak = res_weak.get("red_flags", [])
    print(f"      -> Total Score: {score_weak} / 72 | Red Flags: {len(flags_weak)}")

    # ─────────────────────────────────────────────────────────────────────────
    # 3. EVALUATE RED-FLAG CANDIDATE
    # ─────────────────────────────────────────────────────────────────────────
    print("[3/3] Running evaluation on RED-FLAG candidate...")
    res_flag = evaluate_candidate(role_slug=role, transcript=RED_FLAG_HEAD_COACH_TRANSCRIPT)
    score_flag = res_flag.get("total_score", 0)
    flags_found = res_flag.get("red_flags", [])
    print(f"      -> Total Score: {score_flag} / 72 | Red Flags: {len(flags_found)}")

    # ─────────────────────────────────────────────────────────────────────────
    # 4. ASSERTION CHECKS
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "-" * 65)
    print("                   BENCHMARK ASSERTION CHECKS")
    print("-" * 65)

    assertions = []

    # Check 1: Strong candidate has high score
    pass_strong = score_strong >= 55 and len(flags_strong) == 0
    assertions.append((
        "Strong Candidate Scoring (Expected Score >= 55, No Flags)",
        f"Score: {score_strong}/72, Flags: {len(flags_strong)}",
        pass_strong,
    ))

    # Check 2: Weak candidate has low score
    pass_weak = score_weak <= 36 and len(flags_weak) == 0
    assertions.append((
        "Weak Candidate Scoring (Expected Score <= 36, No Flags)",
        f"Score: {score_weak}/72, Flags: {len(flags_weak)}",
        pass_weak,
    ))

    # Check 3: Score separation
    separation = score_strong - score_weak
    pass_sep = separation >= 20
    assertions.append((
        "Score Separation Metric (Strong - Weak >= 20 points)",
        f"Difference: +{separation} points",
        pass_sep,
    ))

    # Check 4: Red flags detection
    pass_flag = len(flags_found) > 0
    assertions.append((
        "Critical Red-Flag Detection (Must trigger review flags)",
        f"Detected {len(flags_found)} flag(s)",
        pass_flag,
    ))

    # Print results table
    all_passed = True
    for name, detail, passed in assertions:
        status = "[PASS]" if passed else "[FAIL]"
        if not passed:
            all_passed = False
        print(f"{status:<7} {name:<50} | {detail}")

    if flags_found:
        print("\n[INFO] Red flags identified by AI for candidate 3:")
        for idx, flag in enumerate(flags_found, 1):
            print(f"       {idx}. {flag}")

    print("=" * 65)
    if all_passed:
        print("RESULT: ALL 4 BENCHMARK EVALUATIONS PASSED SUCCESSFULLY! [SUCCESS]")
        print("The AI model demonstrates strict rubric adherence and active safety controls.")
    else:
        print("RESULT: SOME BENCHMARK EVALUATIONS FAILED. [FAILED]")
        print("Check prompt rules or scoring thresholds.")
    print("=" * 65 + "\n")

    return all_passed


if __name__ == "__main__":
    run_benchmark_evals()

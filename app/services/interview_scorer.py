"""
FILE: app/services/interview_scorer.py
=======================================
WHAT THIS FILE DOES:
    This file is the brain of the AI evaluation system.
    It takes a candidate's interview transcript (plain text) and a
    role (e.g. "goalkeeper_coach"), loads the correct scoring rubric,
    builds a detailed prompt, sends it to OpenAI GPT-4o-mini, and
    returns a structured score for every rubric question.

    Think of it like an experienced examiner who:
    1. Gets the answer sheet (transcript)
    2. Picks up the marking guide for that specific role (rubric)
    3. Scores each question carefully with evidence and reasoning
    4. Returns the full marked paper with comments

    IMPORTANT: The arithmetic (total score, max score) is always
    calculated by Python code here — NEVER trusted from the AI output,
    because LLMs often make basic maths mistakes.

CONNECTED TO:
    → app/data/rubrics/*.json     : rubric JSON files are read from here
    → app/core/config.py          : OpenAI API key is read from here
    → app/api/endpoints.py        : evaluate_candidate() and
                                    get_available_roles() are called from here
"""

import json
from pathlib import Path
from functools import lru_cache
from openai import OpenAI
from app.core.config import settings

# Create one shared OpenAI client for the entire file.
# This avoids creating a new connection on every API call.
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Path to the folder that contains all role rubric JSON files.
# Example: app/data/rubrics/goalkeeper_coach.json
RUBRICS_DIR = Path(__file__).parent.parent / "data" / "rubrics"


# ─────────────────────────────────────────────────────────────
# PROMPT TEMPLATE
# ─────────────────────────────────────────────────────────────
# This is the instruction we send to GPT-4o-mini.
# The {placeholders} are filled in at runtime with real data
# from the rubric JSON and the candidate's transcript.
# Temperature is set to 0 so the output is deterministic
# (same input always produces the same output).
PROMPT_TEMPLATE = """You are scoring a candidate's interview transcript against \
a fixed evaluation rubric for the role of {role}.

EVALUATION APPROACH:
{evaluation_approach}

MANDATORY SCORING RULES:
{mandatory_rules}

QUESTIONS AND CRITERIA (score each 0-4):
{questions_block}

CRITICAL HUMAN-REVIEW FLAGS (list any that apply based on the transcript):
{critical_flags}

CANDIDATE TRANSCRIPT:
---
{transcript}
---

Return ONLY a JSON object with this exact structure:
{{
  "role": "{role}",
  "candidate_questions": [
    {{
      "question": "string - copy the question text",
      "score": "number 0-4",
      "confidence": "number 0-1",
      "evidence": "string - quote or paraphrase from transcript supporting the score",
      "missing_evidence": "string - what would have made the answer stronger, if applicable",
      "rationale": "string - why this score was given"
    }}
  ],
  "total_score": "number - sum of all question scores",
  "max_possible_score": "number - question count x 4",
  "overall_interpretation": "string - based on the score bands",
  "consistency_note": "string - any written/video or internal consistency observation, or 'N/A' if not assessable from transcript alone",
  "red_flags": ["string - any critical human-review flags that apply, empty array if none"]
}}
"""


# ─────────────────────────────────────────────────────────────
# FUNCTIONS
# ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=None)
def get_available_roles() -> dict:
    """
    WHY THIS EXISTS:
        The frontend needs a dropdown list of all available roles
        so the candidate can select which role they are applying for.
        This function scans the rubrics folder and builds that list
        automatically — no manual list to update when new roles are added.

    HOW IT WORKS:
        Scans app/data/rubrics/ for all *.json files.
        Opens each file and reads the "role" display name.
        Returns a dictionary mapping slug → display name.

    OUTPUT:
        A dictionary like:
        {
            "goalkeeper_coach": "Goalkeeper Coach",
            "head_coach": "Head Coach",
            "data_analyst": "Data Analyst",
            ...
        }

    PERFORMANCE NOTE:
        @lru_cache means this function only reads the files ONCE
        when the server starts. After that, the result is stored in
        memory and reused for every request — no repeated disk reads.

    CALLED FROM:
        → app/api/endpoints.py  — get_roles() endpoint (GET /api/v1/roles)
    """
    roles = {}
    if not RUBRICS_DIR.exists():
        return roles
    for path in sorted(RUBRICS_DIR.glob("*.json")):
        slug = path.stem  # filename without .json → the slug
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        roles[slug] = data.get("role", slug.replace("_", " ").title())
    return roles


@lru_cache(maxsize=None)
def load_rubric(role_slug: str) -> dict:
    """
    WHY THIS EXISTS:
        Before scoring a candidate, the system needs the complete rubric
        for their role. This function loads and returns that rubric.
        It is a separate function so it can be cached independently —
        the same rubric can be reused across many candidate evaluations
        without re-reading the file each time.

    INPUT:
        role_slug : The role identifier string, e.g. "goalkeeper_coach".
                    Must exactly match a filename in app/data/rubrics/.

    OUTPUT:
        The full rubric as a Python dictionary (loaded from JSON).
        Contains: role name, questions, scoring criteria, red flag rules, etc.

    ERROR:
        Raises FileNotFoundError if no rubric file exists for the given slug.
        This error is caught in endpoints.py and returned as a 404 response.

    PERFORMANCE NOTE:
        @lru_cache means each rubric file is only read from disk once
        per server session. Subsequent calls return the cached version.

    CALLED FROM:
        → evaluate_candidate()  (in this same file)
    """
    path = RUBRICS_DIR / f"{role_slug}.json"
    if not path.exists():
        raise FileNotFoundError(f"No rubric found for role slug '{role_slug}'")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _format_questions_block(rubric: dict) -> str:
    """
    WHY THIS EXISTS:
        The rubric JSON file organises questions into sections (A, B, C...).
        This function flattens them into a single readable text block
        that can be inserted directly into the GPT prompt.

        Without this, the prompt would contain raw JSON which is harder
        for the LLM to parse correctly.

    INPUT:
        rubric : The full rubric dictionary (from load_rubric).

    OUTPUT:
        A formatted multi-line string like:

        ### A. Background & Role Definition

        Q: What key experiences most shaped your identity as a coach?
        Evaluates: Coaching identity and self-awareness.
        Strong answer demonstrates: Specific experiences; Learning over time.
        Acceptable: Mentions experience with limited explanation.
        Weak or concerning: Only mentions passion without coaching examples.

        ... (one block per question)

    CALLED FROM:
        → evaluate_candidate()  (in this same file)
    """
    lines = []
    for section in rubric.get("sections", []):
        lines.append(f"\n### {section.get('section_name', '')}")
        for q in section.get("questions", []):
            lines.append(f"\nQ: {q.get('question', '')}")
            lines.append(f"Evaluates: {q.get('evaluates', '')}")
            strong = q.get("strong_answer_criteria", [])
            if strong:
                lines.append("Strong answer demonstrates: " + "; ".join(strong))
            lines.append(f"Acceptable: {q.get('acceptable', '')}")
            lines.append(f"Weak or concerning: {q.get('weak_or_concerning', '')}")
    return "\n".join(lines)


def evaluate_candidate(role_slug: str, transcript: str) -> dict:
    """
    WHY THIS EXISTS:
        This is the main function of the entire AI evaluation pipeline.
        Given a role and a transcript, it returns a complete, structured
        evaluation with a score for every rubric question.

        This is the function that the API endpoint calls. Everything else
        in this file is a helper that this function uses internally.

    HOW IT WORKS (step by step):
        1. Load the rubric JSON for the given role.
        2. Format the rubric questions into a readable text block.
        3. Insert the rubric + transcript into the PROMPT_TEMPLATE.
        4. Send the filled prompt to GPT-4o-mini with temperature=0.
        5. Parse the JSON response from GPT.
        6. OVERRIDE the total_score and max_possible_score with
           Python arithmetic (LLMs make maths mistakes).
        7. Return the final result dictionary.

    INPUT:
        role_slug  : Role identifier, e.g. "head_coach", "data_analyst".
        transcript : Full plain-text interview transcript.

    OUTPUT:
        A Python dictionary containing:
        - role
        - candidate_questions (list with score, evidence, confidence per question)
        - total_score          (sum of all scores — Python calculated)
        - max_possible_score   (questions × 4 — Python calculated)
        - overall_interpretation
        - consistency_note
        - red_flags

    ERRORS:
        FileNotFoundError : if no rubric exists for the given role_slug.
        ValueError        : if OPENAI_API_KEY is not set.

    CALLED FROM:
        → app/api/endpoints.py  — evaluate_interview() (POST /evaluate-interview)
        → app/api/endpoints.py  — evaluate_audio()     (POST /evaluate-audio)
    """
    rubric = load_rubric(role_slug)

    prompt = PROMPT_TEMPLATE.format(
        role=rubric.get("role", role_slug),
        evaluation_approach=rubric.get("evaluation_approach", ""),
        mandatory_rules="\n".join(f"- {r}" for r in rubric.get("mandatory_scoring_rules", [])),
        questions_block=_format_questions_block(rubric),
        critical_flags="\n".join(f"- {f}" for f in rubric.get("critical_human_review_flags", [])),
        transcript=transcript,
    )

    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set. Add it to the .env file.")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},  # forces GPT to return valid JSON
        temperature=0,     # deterministic output — same input = same output
        max_tokens=4000,   # enough for 18 questions with full detail
    )
    result = json.loads(response.choices[0].message.content)

    # ── Recalculate totals in Python ──────────────────────────────────────
    # NEVER trust the LLM for arithmetic. GPT often miscounts or
    # makes off-by-one errors with totals and max scores.
    # We always derive these values from the actual returned questions.
    questions = result.get("candidate_questions", [])
    result["total_score"]        = sum(int(q.get("score", 0)) for q in questions)
    result["max_possible_score"] = len(questions) * 4
    # ──────────────────────────────────────────────────────────────────────

    return result

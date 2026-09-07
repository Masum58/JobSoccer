"""
FILE: app/models/schemas.py
============================
WHAT THIS FILE DOES:
    This file defines the shape (structure) of all data going INTO
    and coming OUT OF the API.

    Think of it like customs forms at an airport. Before a passenger
    (data) can enter or leave, they must fill the correct form with
    the correct fields. If any required field is missing or wrong,
    FastAPI automatically rejects the request and returns a clear error.

    Every API request and response in this project must match one
    of the models defined here.

CONNECTED TO:
    → app/api/endpoints.py  : uses these models to validate requests
                              and document responses in Swagger UI
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ─────────────────────────────────────────────────────────────
# REQUEST MODELS  (data that comes INTO the API)
# ─────────────────────────────────────────────────────────────

class InterviewEvaluationRequest(BaseModel):
    """
    WHY THIS EXISTS:
        This is the input form for the /evaluate-interview endpoint.
        When the backend sends a plain-text transcript to be scored,
        it must send exactly these three fields.

    FIELDS:
        candidate_id : The unique ID of the candidate in the JobSoccer
                       database. Used to link the result back to the
                       correct candidate record.
        role_slug    : The role being evaluated (e.g. "goalkeeper_coach").
                       Must exactly match a JSON rubric filename in
                       app/data/rubrics/. If no rubric is found, the
                       API returns a 404 error.
        transcript   : The full interview text. Either typed by the
                       candidate or converted from audio by Whisper.

    CALLED FROM:
        → app/api/endpoints.py  — evaluate_interview() function
    """

    candidate_id: str = Field(
        ...,
        title="Candidate ID",
        description="The unique identifier of the candidate in the JobSoccer database.",
        example="cand_1025",
    )
    role_slug: str = Field(
        ...,
        title="Role Slug",
        description=(
            "The unique slug of the role being evaluated "
            "(e.g. 'goalkeeper_coach', 'head_coach'). "
            "Must match an existing rubric file in app/data/rubrics/."
        ),
        example="goalkeeper_coach",
    )
    transcript: str = Field(
        ...,
        title="Interview Transcript",
        description=(
            "The full plain-text transcript of the candidate's interview. "
            "This can be typed manually or converted from an audio file "
            "using the /transcribe-audio endpoint first."
        ),
        example="In my previous club, I structured goalkeeper training around match demands...",
    )


# ─────────────────────────────────────────────────────────────
# RESPONSE MODELS  (data that comes OUT OF the API)
# ─────────────────────────────────────────────────────────────

class QuestionEvaluation(BaseModel):
    """
    WHY THIS EXISTS:
        Represents the AI's evaluation result for ONE interview question.
        The full evaluation response contains a list of these, one per
        rubric question.

    FIELDS:
        question        : The exact question text from the rubric document.
        score           : AI score from 0 (very poor) to 4 (excellent).
        confidence      : How confident the AI is in its score (0.0 to 1.0).
                          Low confidence usually means the answer was
                          unclear or the audio quality was poor.
        evidence        : The part of the transcript that justifies the score.
        missing_evidence: What the candidate should have added to score higher.
        rationale       : Plain-English explanation of why this score was given.

    CALLED FROM:
        → InterviewEvaluationResponse  (used as a list inside the response)
    """

    question: str = Field(description="The original interview question from the rubric.")
    score: int = Field(description="AI score for this question: 0 (worst) to 4 (best).")
    confidence: float = Field(description="AI confidence in its score: 0.0 (low) to 1.0 (high).")
    evidence: str = Field(description="Quote or paraphrase from the transcript that supports the score.")
    missing_evidence: str = Field(description="What a stronger answer would have included.")
    rationale: str = Field(description="Plain-English explanation of why this score was assigned.")


class InterviewEvaluationResponse(BaseModel):
    """
    WHY THIS EXISTS:
        This is the complete AI evaluation result for one candidate.
        It contains the score for every rubric question plus a summary.

    FIELDS:
        role                  : The role that was evaluated (e.g. "Head Coach").
        candidate_questions   : List of question-by-question results.
                                Each item is a QuestionEvaluation object.
        total_score           : Sum of all individual question scores.
                                Calculated by Python code, NOT by the AI,
                                to guarantee accuracy.
        max_possible_score    : Maximum total score (number of questions × 4).
                                Also calculated by Python code.
        overall_interpretation: A short text summary based on the score band
                                defined in the rubric document.
        consistency_note      : Notes if the candidate's answers were
                                consistent with each other, or if there
                                were contradictions.
        red_flags             : List of serious concerns (e.g. safeguarding
                                issues) that require a human to review.
                                Empty list means no flags were raised.

    CALLED FROM:
        → APIResponse          (wrapped inside this for /evaluate-interview)
        → FullPipelineResponse (wrapped inside this for /evaluate-audio)
    """

    role: str = Field(description="The role that was evaluated.")
    candidate_questions: List[QuestionEvaluation] = Field(
        description="Question-by-question AI evaluation. One entry per rubric question."
    )
    total_score: int = Field(
        description="Total score across all questions. Calculated in Python (not by AI)."
    )
    max_possible_score: int = Field(
        description="Maximum possible total score (number of questions × 4). Calculated in Python."
    )
    overall_interpretation: str = Field(
        description="Short summary of the candidate's overall performance based on score bands."
    )
    consistency_note: str = Field(
        description="Observation on whether the candidate's answers were consistent throughout the interview."
    )
    red_flags: List[str] = Field(
        description=(
            "Critical issues that require a human reviewer to check. "
            "For example: safeguarding concerns, credential contradictions. "
            "Empty list means no flags were raised."
        )
    )


class APIResponse(BaseModel):
    """
    WHY THIS EXISTS:
        This is the final response wrapper for the /evaluate-interview endpoint.
        It combines the candidate_id (from the request) with the full
        evaluation result so the backend can link the result to the
        correct candidate in the database.

    CALLED FROM:
        → app/api/endpoints.py  — evaluate_interview() function
    """

    candidate_id: str = Field(description="The candidate ID that was passed in the request.")
    evaluation: InterviewEvaluationResponse = Field(
        description="The complete AI evaluation result for this candidate."
    )


class AudioTranscribeResponse(BaseModel):
    """
    WHY THIS EXISTS:
        This is the response for the /transcribe-audio endpoint.
        When the backend sends an audio file, this is what comes back:
        the plain-text transcript plus metadata about the audio.

    FIELDS:
        candidate_id     : Passed through from the request.
        file_name        : Original audio filename (e.g. "interview.mp3").
        language         : Language Whisper detected in the audio
                           (e.g. "english", "french", "spanish").
        duration_seconds : How long the audio is in seconds.
        transcript       : The full converted text from the audio.

    CALLED FROM:
        → app/api/endpoints.py  — transcribe_audio() function
    """

    candidate_id: str = Field(description="The candidate ID passed in the request.")
    file_name: str = Field(description="The original audio file name (e.g. 'interview.mp3').")
    language: str = Field(description="Language detected by Whisper (e.g. 'english', 'french', 'spanish').")
    duration_seconds: Optional[float] = Field(description="Total duration of the audio in seconds.")
    transcript: str = Field(description="Full plain-text transcript extracted from the audio.")


class FullPipelineResponse(BaseModel):
    """
    WHY THIS EXISTS:
        This is the response for the /evaluate-audio endpoint — the main
        endpoint used in production. It combines AudioTranscribeResponse
        and InterviewEvaluationResponse into one single response.

        This means the backend gets EVERYTHING in one API call:
        the transcript AND the full AI evaluation result.

    CALLED FROM:
        → app/api/endpoints.py  — evaluate_audio() function
    """

    candidate_id: str = Field(description="The candidate ID passed in the request.")
    file_name: str = Field(description="The original audio file name.")
    language: str = Field(description="Language detected by Whisper.")
    duration_seconds: Optional[float] = Field(description="Total duration of the audio in seconds.")
    transcript: str = Field(description="Full transcript extracted from the audio by Whisper.")
    evaluation: InterviewEvaluationResponse = Field(
        description="The complete AI evaluation result based on the transcript."
    )

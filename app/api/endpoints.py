from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from app.models.schemas import (
    InterviewEvaluationRequest,
    APIResponse,
    AudioTranscribeResponse,
    FullPipelineResponse,
)
from app.services.interview_scorer import evaluate_candidate, get_available_roles
from app.services.audio_service import transcribe_audio_bytes

router = APIRouter(tags=["AI Evaluation"])


# ─────────────────────────────────────────────
# 1. GET /roles
# ─────────────────────────────────────────────
@router.get(
    "/roles",
    summary="Get Available Roles",
    description=(
        "Returns a list of all role slugs and their display names "
        "that have a corresponding JSON rubric in the system. "
        "Use a slug value in the evaluate-interview or evaluate-audio endpoints."
    ),
)
def get_roles():
    return {"roles": get_available_roles()}


# ─────────────────────────────────────────────
# 2. POST /evaluate-interview  (text transcript)
# ─────────────────────────────────────────────
@router.post(
    "/evaluate-interview",
    summary="Evaluate Interview Transcript (Text Input)",
    description=(
        "Use this endpoint when the backend has already converted the audio "
        "to text (or the candidate submitted a written questionnaire). "
        "Pass the plain-text transcript and the role slug; the AI scores each "
        "rubric question and returns evidence, confidence, and red flags."
    ),
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
)
def evaluate_interview(request: InterviewEvaluationRequest):
    try:
        result = evaluate_candidate(
            role_slug=request.role_slug,
            transcript=request.transcript,
        )
        return {"candidate_id": request.candidate_id, "evaluation": result}
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ─────────────────────────────────────────────
# 3. POST /transcribe-audio  (STT only)
# ─────────────────────────────────────────────
@router.post(
    "/transcribe-audio",
    summary="Transcribe Audio to Text (STT Only)",
    description=(
        "Converts a candidate's interview audio file into a plain-text transcript "
        "using OpenAI Whisper. Supports English, French, and Spanish (auto-detected). "
        "Accepted formats: mp3, mp4, m4a, wav, webm. Max size: 25 MB. "
        "Use this if you want to review the transcript before running the full evaluation."
    ),
    response_model=AudioTranscribeResponse,
    status_code=status.HTTP_200_OK,
)
async def transcribe_audio(
    candidate_id: str = Form(
        ...,
        description="The unique identifier of the candidate in the JobSoccer database.",
        example="cand_1025",
    ),
    language: str | None = Form(
        default=None,
        description="Optional ISO-639-1 language code to improve transcription accuracy. E.g. 'en', 'fr', 'es'. If omitted, Whisper will auto-detect.",
        example="en",
    ),
    audio_file: UploadFile = File(
        ...,
        description="The candidate's interview audio file (mp3, mp4, m4a, wav, webm). Max 25 MB.",
    ),
):
    try:
        file_bytes = await audio_file.read()
        result = transcribe_audio_bytes(
            file_bytes=file_bytes,
            file_name=audio_file.filename or "audio",
            language=language,
        )
        return {
            "candidate_id": candidate_id,
            "file_name": result["file_name"],
            "language": result["language"],
            "duration_seconds": result["duration_seconds"],
            "transcript": result["transcript"],
        }
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


# ─────────────────────────────────────────────
# 4. POST /evaluate-audio  (full pipeline)
# ─────────────────────────────────────────────
@router.post(
    "/evaluate-audio",
    summary="Full AI Pipeline: Audio → Transcript → Evaluation",
    description=(
        "The complete end-to-end AI pipeline. "
        "Step 1: Converts the uploaded audio to text via OpenAI Whisper (STT). "
        "Step 2: Evaluates the transcript against the role-specific JobSoccer rubric via GPT-4o-mini. "
        "Returns the transcript AND the full structured evaluation (score, evidence, confidence, red flags). "
        "This is the main endpoint the backend should call after a candidate uploads their interview video."
    ),
    response_model=FullPipelineResponse,
    status_code=status.HTTP_200_OK,
)
async def evaluate_audio(
    candidate_id: str = Form(
        ...,
        description="The unique identifier of the candidate in the JobSoccer database.",
        example="cand_1025",
    ),
    role_slug: str = Form(
        ...,
        description="The role slug to evaluate against (e.g. 'goalkeeper_coach', 'administrative_director'). Must match an existing rubric.",
        example="goalkeeper_coach",
    ),
    language: str | None = Form(
        default=None,
        description="Optional ISO-639-1 language code for Whisper STT (e.g. 'en', 'fr', 'es'). If omitted, auto-detected.",
        example="en",
    ),
    audio_file: UploadFile = File(
        ...,
        description="The candidate's interview audio/video file (mp3, mp4, m4a, wav, webm). Max 25 MB.",
    ),
):
    # Step 1 — Speech-to-Text
    try:
        file_bytes = await audio_file.read()
        stt_result = transcribe_audio_bytes(
            file_bytes=file_bytes,
            file_name=audio_file.filename or "audio",
            language=language,
        )
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    # Step 2 — LLM Evaluation
    try:
        evaluation = evaluate_candidate(
            role_slug=role_slug,
            transcript=stt_result["transcript"],
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return {
        "candidate_id": candidate_id,
        "file_name": stt_result["file_name"],
        "language": stt_result["language"],
        "duration_seconds": stt_result["duration_seconds"],
        "transcript": stt_result["transcript"],
        "evaluation": evaluation,
    }


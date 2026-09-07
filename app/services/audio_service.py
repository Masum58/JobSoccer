"""
FILE: app/services/audio_service.py
=====================================
WHAT THIS FILE DOES:
    This file converts an audio or video file into plain text (transcript)
    using OpenAI Whisper — a speech recognition AI model.

    This is Step 1 of the JobSoccer interview evaluation pipeline:

        Candidate uploads audio/video
                ↓
        audio_service.py  →  converts to text (this file)
                ↓
        interview_scorer.py  →  AI scores the transcript
                ↓
        Result returned to backend

    Think of it like a professional typist who listens to a voice
    recording and types out exactly what was said, in the correct
    language (English, French, or Spanish).

    Supported languages : English, French, Spanish (auto-detected)
    Supported formats   : mp3, mp4, mpeg, mpga, m4a, wav, webm
    Max file size       : 25 MB (OpenAI Whisper API hard limit)

CONNECTED TO:
    → app/core/config.py     : reads OPENAI_API_KEY from here
    → app/api/endpoints.py   : transcribe_audio_bytes() is called from
                               transcribe_audio() and evaluate_audio()
"""

import os
from pathlib import Path
from openai import OpenAI
from app.core.config import settings

# Create one shared OpenAI client for this file.
# Reusing one client is more efficient than creating a new one per request.
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# The set of audio/video formats that OpenAI Whisper API accepts.
# Sending any other format will result in a 400 error from OpenAI.
SUPPORTED_FORMATS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"}

# OpenAI Whisper API will reject any file larger than 25 MB.
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


def transcribe_audio_file(file_path: str, language: str | None = None) -> dict:
    """
    WHY THIS EXISTS:
        Use this function when the audio file is already saved on disk
        (e.g. during local testing or batch processing).
        It reads the file, validates it, then sends it to OpenAI Whisper
        to convert the audio into plain text.

    INPUT:
        file_path : Full path to the audio file on disk.
                    Example: "C:/interviews/jesse_montana.mp3"
        language  : Optional. The spoken language in the audio.
                    Use ISO-639-1 codes: "en" (English), "fr" (French),
                    "es" (Spanish). Leave as None to let Whisper auto-detect.

    OUTPUT:
        A dictionary with 4 keys:
        {
            "transcript"      : str   — The full converted text
            "language"        : str   — Detected language (e.g. "english")
            "duration_seconds": float — How long the audio is in seconds
            "file_name"       : str   — The audio filename
        }

    ERRORS:
        FileNotFoundError : if the file path does not exist on disk
        ValueError        : if the format is unsupported OR file > 25 MB
        RuntimeError      : if the Whisper API call itself fails

    CALLED FROM:
        → Not currently used by the API endpoints (which use bytes instead).
          Available for local testing or batch processing scripts.
    """
    path = Path(file_path)

    # Check the file exists before trying to open it
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    # Check the file extension is one Whisper accepts
    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported audio format '{path.suffix}'. "
            f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )

    # Check the file is within OpenAI's 25 MB size limit
    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"Audio file is too large ({file_size / 1024 / 1024:.1f} MB). "
            f"OpenAI Whisper API limit is 25 MB."
        )

    # Clean up the language value — guard against Swagger placeholder "string"
    # being accidentally submitted, or empty strings, etc.
    clean_language = language.strip() if language else None
    if clean_language in ("", "string", "null", "none"):
        clean_language = None

    try:
        with open(path, "rb") as audio_file:
            whisper_kwargs = {
                "model": "whisper-1",
                "file": audio_file,
                "response_format": "verbose_json",  # returns language + duration info
            }
            if clean_language:
                whisper_kwargs["language"] = clean_language

            response = client.audio.transcriptions.create(**whisper_kwargs)

    except Exception as e:
        raise RuntimeError(f"Whisper API call failed: {e}")

    return {
        "transcript": response.text.strip(),
        "language": getattr(response, "language", language or "unknown"),
        "duration_seconds": getattr(response, "duration", None),
        "file_name": path.name,
    }


def transcribe_audio_bytes(
    file_bytes: bytes,
    file_name: str,
    language: str | None = None,
) -> dict:
    """
    WHY THIS EXISTS:
        This is the main transcription function used by the API.
        When a candidate uploads an audio file through the API,
        FastAPI reads it into memory as raw bytes (without saving to disk).
        This function takes those bytes and sends them directly to
        OpenAI Whisper for transcription — no disk storage needed.

        This is the preferred function over transcribe_audio_file()
        for all API-based usage because it is faster (no disk I/O)
        and simpler (no file path management).

    INPUT:
        file_bytes : The audio file content as raw bytes.
                     FastAPI provides this via `await audio_file.read()`.
        file_name  : The original filename including extension
                     (e.g. "interview.mp3"). Used to tell Whisper the
                     audio format, since bytes alone have no extension.
        language   : Optional. ISO-639-1 language code ("en", "fr", "es").
                     Leave as None for Whisper to auto-detect the language.

    OUTPUT:
        A dictionary with 4 keys — same structure as transcribe_audio_file():
        {
            "transcript"      : str   — The full converted text
            "language"        : str   — Detected language (e.g. "english")
            "duration_seconds": float — How long the audio is in seconds
            "file_name"       : str   — The original filename
        }

    ERRORS:
        ValueError   : if the format is unsupported OR bytes size > 25 MB
        RuntimeError : if the Whisper API call itself fails

    CALLED FROM:
        → app/api/endpoints.py  — transcribe_audio()  (POST /transcribe-audio)
        → app/api/endpoints.py  — evaluate_audio()    (POST /evaluate-audio)
    """
    suffix = Path(file_name).suffix.lower()

    # Check the file extension is one Whisper accepts
    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported audio format '{suffix}'. "
            f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )

    # Check the file bytes are within the 25 MB limit
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"Audio file is too large ({len(file_bytes) / 1024 / 1024:.1f} MB). "
            f"OpenAI Whisper API limit is 25 MB."
        )

    try:
        # Clean up the language value — guard against "string" placeholder
        # from Swagger UI being accidentally submitted
        clean_language = language.strip() if language else None
        if clean_language in ("", "string", "null", "none"):
            clean_language = None

        # OpenAI SDK accepts a (filename, bytes) tuple as the file argument
        audio_tuple = (file_name, file_bytes)

        whisper_kwargs = {
            "model": "whisper-1",
            "file": audio_tuple,
            "response_format": "verbose_json",  # returns language + duration info
        }
        if clean_language:
            whisper_kwargs["language"] = clean_language

        response = client.audio.transcriptions.create(**whisper_kwargs)

    except Exception as e:
        raise RuntimeError(f"Whisper API call failed: {e}")

    return {
        "transcript": response.text.strip(),
        "language": getattr(response, "language", language or "unknown"),
        "duration_seconds": getattr(response, "duration", None),
        "file_name": file_name,
    }


"""
FILE: app/core/config.py
========================
WHAT THIS FILE DOES:
    This file is the settings manager for the entire project.
    It reads secret values (like API keys) from the .env file
    and makes them available to any other file that needs them.

    Think of it like a key cabinet — all important keys are kept
    here in one place. Any file that needs a key comes here to
    pick it up. No file should read the .env file directly.

CONNECTED TO:
    → .env file                  : reads OPENAI_API_KEY from here
    → app/services/interview_scorer.py : gets OPENAI_API_KEY from here
    → app/services/audio_service.py    : gets OPENAI_API_KEY from here
    → app/main.py                      : gets PROJECT_NAME from here
"""

import os
from dotenv import load_dotenv

# Read the .env file and load its values into environment variables.
# This must run before we try to read any env variable below.
load_dotenv()


class Settings:
    """
    WHY THIS CLASS EXISTS:
        To group all project settings in one place.
        If a setting needs to change (e.g. the project name),
        we change it here and every file that uses it is updated
        automatically — without touching any other file.

    OUTPUT / ATTRIBUTES:
        PROJECT_NAME    : The name shown in Swagger UI and API responses.
        OPENAI_API_KEY  : The secret key used to call OpenAI (Whisper + GPT).
                          Comes from the .env file. Empty string if not set.

    CALLED FROM:
        → app/main.py                       : uses PROJECT_NAME
        → app/services/interview_scorer.py  : uses OPENAI_API_KEY
        → app/services/audio_service.py     : uses OPENAI_API_KEY
    """

    PROJECT_NAME: str = "JobSoccer AI API"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")


# Create one shared instance of Settings.
# Every other file imports this single `settings` object.
# This means the .env file is only read once when the server starts.
settings = Settings()

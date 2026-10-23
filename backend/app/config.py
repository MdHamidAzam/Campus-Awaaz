"""All settings in one place. Values come from environment variables / backend/.env"""
import os
from datetime import timezone, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:                                   # python-dotenv optional
    load_dotenv = None

BACKEND_DIR = Path(__file__).resolve().parent.parent
if load_dotenv: load_dotenv(BACKEND_DIR / ".env")

FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", BACKEND_DIR.parent / "frontend"))
DATA_DIR = BACKEND_DIR / "data"
DOCS_DIR = BACKEND_DIR / "docs"
DB_PATH = Path(os.getenv("DATABASE_PATH", BACKEND_DIR / "storage" / "campus.db"))   # <- all user data lives in this one file

IST = timezone(timedelta(hours=5, minutes=30))
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
SESSION_DAYS = int(os.getenv("SESSION_DAYS", 30))

# ---- email (class reminders / notices)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM") or SMTP_USER

# ---- class reminder: how many minutes BEFORE the class starts the alert goes out (0 = exactly at class time)
CLASS_REMINDER_MINUTES = int(os.getenv("CLASS_REMINDER_MINUTES", 10))

# ---- ElevenLabs (voice assistant)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_TTS_MODEL = os.getenv("ELEVENLABS_TTS_MODEL", "eleven_multilingual_v2")
ELEVENLABS_STT_MODEL = os.getenv("ELEVENLABS_STT_MODEL", "scribe_v1")
# "Assistant 1..4" -> ElevenLabs voice ids (defaults are ElevenLabs premade voices; override in .env)
ASSISTANT_VOICES = {
    "1": os.getenv("ELEVENLABS_VOICE_1", "21m00Tcm4TlvDq8ikWAM"),   # Rachel
    "2": os.getenv("ELEVENLABS_VOICE_2", "pNInz6obpgDQGcFmaJgB"),   # Adam
    "3": os.getenv("ELEVENLABS_VOICE_3", "EXAVITQu4vr4xnSDxMaL"),   # Bella
    "4": os.getenv("ELEVENLABS_VOICE_4", "TxGEqnHWrfWFTfGW9XjX"),   # Josh
}

# ---- demo mode: seeds one demo student (demo@campusawaaz.app / demo1234, section CS3H) so judges can try the app in one click
DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"

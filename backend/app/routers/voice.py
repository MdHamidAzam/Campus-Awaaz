"""Voice assistant endpoints backed by ElevenLabs (TTS + STT)."""
import re
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from ..config import ASSISTANT_VOICES
from ..core.security import roles
from ..services import elevenlabs

router = APIRouter(prefix="/voice")
LANG = {0: "en", 1: "hi", 2: "hi"}                      # chat language code -> ElevenLabs language hint
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u2022]")
class Speak(BaseModel): text: str; voice: str = "1"; lang: int = 0


@router.get("/config")
def config(u=Depends(roles("student", "faculty"))):
    return {"elevenlabs": elevenlabs.configured(), "voices": [{"id": k, "name": f"Assistant {k}"} for k in ASSISTANT_VOICES]}


@router.post("/tts")
def tts(b: Speak, u=Depends(roles("student", "faculty"))):
    text = re.sub(r"\s+", " ", EMOJI.sub("", b.text)).strip()[:900]
    if not text: raise HTTPException(400, "Nothing to speak")
    return Response(elevenlabs.tts(text, b.voice, LANG.get(b.lang, "en")), media_type="audio/mpeg")


@router.post("/stt")
async def stt(file: UploadFile = File(...), language: str = "", u=Depends(roles("student", "faculty"))):
    data = await file.read()
    if not data: raise HTTPException(400, "No audio received")
    if len(data) > 10 * 2 ** 20: raise HTTPException(400, "Recording too long")
    return elevenlabs.stt(data, file.filename or "speech.webm", file.content_type or "audio/webm", language)

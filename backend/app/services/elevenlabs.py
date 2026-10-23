"""ElevenLabs client (server side only - the API key never reaches the browser).
   TTS -> text to speech (Assistant 1-4 voices, multilingual model)
   STT -> speech to text (Scribe, auto-detects the spoken language)"""
import re
from collections import OrderedDict
import httpx
from fastapi import HTTPException
from ..config import ELEVENLABS_API_KEY, ELEVENLABS_TTS_MODEL, ELEVENLABS_STT_MODEL, ASSISTANT_VOICES

BASE = "https://api.elevenlabs.io/v1"
_cache = OrderedDict()          # small in-memory cache so repeated answers do not burn credits


def configured(): return bool(ELEVENLABS_API_KEY)


def _need_key():
    if not ELEVENLABS_API_KEY:
        raise HTTPException(503, "ElevenLabs API key is not set on the server (ELEVENLABS_API_KEY in backend/.env)")


def _fail(r):
    try:
        msg = r.json().get("detail")
        msg = msg.get("message") if isinstance(msg, dict) else msg
    except Exception:
        msg = r.text[:200]
    raise HTTPException(502, f"ElevenLabs error {r.status_code}: {msg}")


def tts(text, voice="1", lang="en"):
    _need_key()
    vid = ASSISTANT_VOICES.get(voice, ASSISTANT_VOICES["1"]); key = (vid, lang, text)
    if key in _cache:
        _cache.move_to_end(key); return _cache[key]
    body = {"text": text, "model_id": ELEVENLABS_TTS_MODEL, "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}}
    if "v2_5" in ELEVENLABS_TTS_MODEL: body["language_code"] = lang      # only turbo/flash v2.5 accept a language hint
    try:
        r = httpx.post(f"{BASE}/text-to-speech/{vid}", params={"output_format": "mp3_44100_128"},
                       headers={"xi-api-key": ELEVENLABS_API_KEY}, json=body, timeout=40)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Could not reach ElevenLabs: {e}")
    if r.status_code != 200: _fail(r)
    _cache[key] = r.content
    while len(_cache) > 60: _cache.popitem(last=False)
    return r.content


STT_LANG = {"en": "eng", "hi": "hin"}          # language the user picked in the app; "" = let Scribe auto-detect


def stt(audio: bytes, filename="speech.webm", content_type="audio/webm", language=""):
    """Speech -> text. Passing the language the person speaks makes Scribe far more accurate (esp. Indian English / Hindi)."""
    _need_key()
    data = {"model_id": ELEVENLABS_STT_MODEL, "tag_audio_events": "false", "diarize": "false", "timestamps_granularity": "none"}
    code = STT_LANG.get(language, "")
    r = None
    for attempt in ((code, "") if code else ("",)):                # if the language hint is refused, retry once with auto-detect
        d = dict(data); 
        if attempt: d["language_code"] = attempt
        try:
            r = httpx.post(f"{BASE}/speech-to-text", headers={"xi-api-key": ELEVENLABS_API_KEY}, data=d, files={"file": (filename, audio, content_type)}, timeout=60)
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Could not reach ElevenLabs: {e}")
        if r.status_code == 200: break
    if r.status_code != 200: _fail(r)
    j = r.json()
    text = re.sub(r"\s+", " ", re.sub(r"[\(\[][^)\]]*[\)\]]", " ", j.get("text") or "")).strip()      # drop any "(noise)" tags
    return {"text": text, "language": j.get("language_code") or ""}

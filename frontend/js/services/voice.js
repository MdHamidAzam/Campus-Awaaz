// Voice: ElevenLabs (via backend) for speaking + listening, browser voice as fallback.
import { api, apiUrl } from '../core/api.js';
import { S } from '../core/state.js';
import { $, toast } from '../core/utils.js';

const V = { elevenlabs: false, voices: [1, 2, 3, 4].map(i => ({ id: String(i), name: `Assistant ${i}` })) };
export const voiceList = () => V.voices;
export const getVoice = () => localStorage.voice || '1';
export const setVoice = id => { localStorage.voice = id; };

export async function loadVoiceConfig() {
  try { const c = await api('/voice/config'); V.elevenlabs = c.elevenlabs; V.voices = c.voices; } catch (e) { /* keep defaults */ }
}

const FULL = { Mon: 'Monday', Tue: 'Tuesday', Wed: 'Wednesday', Thu: 'Thursday', Fri: 'Friday', Sat: 'Saturday', Sun: 'Sunday', Jan: 'January', Feb: 'February', Mar: 'March', Apr: 'April', Jun: 'June', Jul: 'July', Aug: 'August', Sep: 'September', Oct: 'October', Nov: 'November', Dec: 'December' };
const speechText = x => x.replace(/\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b/g, m => FULL[m]).replace(/→/g, ' to ').replace(/[•]/g, '').replace(/\n+/g, '. ');

/* ---------- speaking ---------- */
let audio = null;
export function stopSpeaking() { if (audio) { audio.pause(); audio = null; } if (window.speechSynthesis) speechSynthesis.cancel(); }

export async function speak(text, lang = 0) {                 // lang: 0 English, 1 Hinglish, 2 Hindi (answer language)
  stopSpeaking(); text = speechText(text);
  if (V.elevenlabs) {
    try {
      const r = await fetch(apiUrl('/voice/tts'), { method: 'POST', headers: { 'X-Token': S.token, 'Content-Type': 'application/json' }, body: JSON.stringify({ text, voice: getVoice(), lang }) });
      if (!r.ok) { const j = await r.json().catch(() => ({})); throw Error(j.detail || 'voice failed'); }
      const url = URL.createObjectURL(await r.blob()); audio = new Audio(url);
      audio.onended = () => URL.revokeObjectURL(url); await audio.play(); return;
    } catch (e) { toast('ElevenLabs: ' + e.message + ' (using browser voice)'); }
  }
  browserSpeak(text, lang);
}

function browserSpeak(text, lang) {
  if (!window.speechSynthesis) return;
  const all = speechSynthesis.getVoices(), pool = all.filter(v => v.lang.toLowerCase().startsWith(lang ? 'hi' : 'en')), list = pool.length ? pool : all;
  const v = list.length ? list[(Number(getVoice()) - 1) % list.length] : null, u = new SpeechSynthesisUtterance(text);
  u.lang = v ? v.lang : (lang ? 'hi-IN' : 'en-IN'); if (v) u.voice = v; u.rate = 0.95; speechSynthesis.speak(u);
}

/* ---------- listening ---------- */
// Which language the person speaks: 'auto' | 'en' | 'hi'. Telling the recogniser the language is the biggest accuracy win.
export const getVLang = () => { try { return localStorage.ca_vlang || 'auto'; } catch (e) { return 'auto'; } };
export const setVLang = v => { try { localStorage.ca_vlang = v; } catch (e) { /* ignore */ } };

let rec = null, stopTimer = null, vad = null;
const mark = on => { const b = $('#mb'); if (b) b.classList.toggle('on', on); const c = $('#cmp'); if (c) c.classList.toggle('lis', on); };

// Stops the recording by itself ~1.6 s after the person stops talking (so no need to tap again, and no long silent tail).
function watchSilence(stream, stop) {
  try {
    const ac = new (window.AudioContext || window.webkitAudioContext)(), src = ac.createMediaStreamSource(stream), an = ac.createAnalyser();
    an.fftSize = 1024; src.connect(an); const buf = new Uint8Array(an.fftSize); let heard = false, quiet = 0, t0 = Date.now();
    const id = setInterval(() => {
      an.getByteTimeDomainData(buf); let sum = 0; for (const v of buf) sum += (v - 128) * (v - 128);
      const rms = Math.sqrt(sum / buf.length);
      if (rms > 9) { heard = true; quiet = 0; } else if (heard) quiet += 100;
      if (heard && quiet >= 1600) stop(); else if (!heard && Date.now() - t0 > 7000) stop();       // nobody spoke
    }, 100);
    vad = () => { clearInterval(id); try { ac.close(); } catch (e) { /* ignore */ } };
  } catch (e) { vad = null; }
}

export async function toggleMic(onText) {
  if (rec) { rec.stop(); return; }                                // second tap = stop & send
  if (!V.elevenlabs || !window.MediaRecorder) return browserMic(onText);
  let stream;
  try { stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 } }); }
  catch (e) { return toast('Microphone blocked. Click the lock icon in the address bar and allow the microphone.', true); }
  const chunks = [], mt = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/webm'].find(t => MediaRecorder.isTypeSupported(t));
  const r = new MediaRecorder(stream, mt ? { mimeType: mt, audioBitsPerSecond: 128000 } : {}); rec = r;
  r.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
  r.onstart = () => { mark(true); watchSilence(stream, () => rec && rec.state === 'recording' && rec.stop()); };
  r.onstop = async () => {
    clearTimeout(stopTimer); if (vad) vad(); vad = null; stream.getTracks().forEach(t => t.stop()); mark(false); rec = null;
    const type = r.mimeType || 'audio/webm', blob = new Blob(chunks, { type });
    if (blob.size < 2500) return toast('I did not hear anything. Tap the mic and speak a little closer.', true);
    const fd = new FormData(); fd.append('file', blob, 'speech.' + (type.includes('mp4') ? 'mp4' : 'webm'));
    const l = getVLang();
    try { const j = await api('/voice/stt' + (l !== 'auto' ? '?language=' + l : ''), { body: fd }); if (j.text) onText(j.text); else toast('I could not make that out. Please try again.', true); }
    catch (e) { toast(e.message, true); }
  };
  r.start(250); stopTimer = setTimeout(() => rec && rec.state === 'recording' && rec.stop(), 20000);
}

function browserMic(onText) {                                    // fallback when ElevenLabs is not configured
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return toast('Voice input needs ElevenLabs (backend) or Chrome / Edge.', true);
  const l = getVLang(), r = new SR(); r.lang = l === 'hi' ? 'hi-IN' : 'en-IN'; r.interimResults = false; r.maxAlternatives = 1;
  r.onstart = () => mark(true); r.onend = () => mark(false);
  r.onerror = e => toast(e.error === 'no-speech' ? 'I did not hear anything, please try again.' : 'Mic error: ' + e.error, true);
  r.onresult = e => onText(e.results[0][0].transcript); r.start();
}

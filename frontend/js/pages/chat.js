import { api } from '../core/api.js';
import { S } from '../core/state.js';
import { $, E, greeting, rich, hm, empty } from '../core/utils.js';
import { action } from '../core/actions.js';
import { pg } from '../core/router.js';
import { LOGO } from './shell.js';
import { speak, toggleMic, voiceList, getVoice, setVoice, stopSpeaking, getVLang, setVLang } from '../services/voice.js';

const CHIPS = { student: ['Where is my class now?', 'Next class', 'Aaj ka schedule', 'Exam kab hai?', 'Holidays', 'CN syllabus', 'Who is my class coordinator?', 'Any events?'],
                faculty: ['Where is my next class?', 'Aaj ka schedule', 'Holidays', 'When are the exams?'] };
const MIC = '<svg viewBox="0 0 24 24"><path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2z"/></svg>';

export function pChat() {
  const m = S.me, d = new Date().toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', weekday: 'long', day: 'numeric', month: 'long' });
  pg(`<div class="top"><div><h1>${greeting()}, ${E(m.name.replace(/^(dr|mr|ms|mrs|prof)\.?\s+/i, '').split(' ')[0])}</h1><p>${d}${m.section ? ' · ' + E(m.section) : ''}</p></div>
<div class="clk"><i class="dot"></i><span id="dw"></span><b id="tm"></b></div></div>
<div class="g"><section class="cd chat" aria-label="Assistant"><div class="chh"><h3><i class="live"></i>Ask Awaaz</h3><div class="tools">
<select id="vl" title="Language you speak" aria-label="Language you speak" data-change="vlang"><option value="auto" ${getVLang() === 'auto' ? 'selected' : ''}>I speak: Auto</option><option value="en" ${getVLang() === 'en' ? 'selected' : ''}>I speak: English</option><option value="hi" ${getVLang() === 'hi' ? 'selected' : ''}>I speak: हिंदी</option></select>
<button class="bt sm sec" data-a="stopsay" aria-label="Stop speaking">Stop</button>
<select id="vs" title="Assistant voice" aria-label="Assistant voice" data-change="voice">${voiceList().map(v => `<option value="${E(v.id)}" ${v.id === getVoice() ? 'selected' : ''}>${E(v.name)}</option>`).join('')}</select></div></div>
<div id="log" aria-live="polite"></div>
<div class="chs" id="chs">${(CHIPS[m.role] || CHIPS.student).map(c => `<button class="ch" data-a="chip" data-q="${E(c)}">${E(c)}</button>`).join('')}</div>
<div class="cmp" id="cmp"><button id="mb" class="mc" data-a="mic" title="Speak" aria-label="Speak your query">${MIC}</button>
<div class="lsn"><div class="wv"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>Listening… tap the mic to send</div>
<input id="qi" placeholder="Ask in English, हिंदी or Hinglish…" aria-label="Your query" data-enter="send" autocomplete="off"><button class="bt" id="sb" data-a="send">Send</button></div></section>
<div class="col"><div id="nowc"></div><div class="cd" id="tdc"></div><div class="cds" id="ovc"></div></div></div>`);
  tick2(); drawLog(); overview().catch(() => {}); return today();
}
const tick2 = () => { const d = new Date(), w = $('#dw'); if (!w) return; w.textContent = d.toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', weekday: 'short', day: 'numeric', month: 'short' }); $('#tm').textContent = d.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: true }).toUpperCase(); };

function drawLog(typing) {
  const l = $('#log'); if (!l) return;
  const msg = (m, i) => m.w === 'u'
    ? `<div class="mw u"><div><div class="m u"><p>${E(m.t)}</p></div></div></div>`
    : `<div class="mw"><span class="bav">${LOGO}</span><div><div class="m b">${rich(m.t)}</div><div class="mf"><span>${hm(new Date(m.ts || Date.now()))}</span><button data-a="say" data-i="${i}">Listen</button><button data-a="copy" data-i="${i}">Copy</button></div></div></div>`;
  l.innerHTML = S.chat.map(msg).join('') + (typing ? `<div class="mw"><span class="bav">${LOGO}</span><div class="m b"><div class="typing"><i></i><i></i><i></i></div></div></div>` : '');
  l.scrollTop = l.scrollHeight;
  const c = $('#chs'); if (c) c.style.display = S.chat.length > 3 ? 'none' : '';     // chips are for getting started
}

let pending = false;
async function send(text) {
  const i = $('#qi'), x = (typeof text === 'string' ? text : i.value).trim(); if (!x || pending) return;
  pending = true; i.value = ''; S.chat.push({ w: 'u', t: x, ts: Date.now() }); drawLog(true);
  const sb = $('#sb'); if (sb) sb.disabled = true;
  try { const r = await api('/chat', { body: { t: x } }); S.chat.push({ w: 'b', t: r.a, lang: r.lang, ts: Date.now() }); drawLog(); speak(r.a, r.lang); }
  catch (e) { S.chat.push({ w: 'b', t: 'Sorry, that did not go through. ' + e.message, ts: Date.now() }); drawLog(); }
  finally { pending = false; if ($('#sb')) $('#sb').disabled = false; }
}

export async function today() {
  const r = await api('/today'); S.today = r; const el = $('#tdc'); if (!el) return;
  const now = new Date(), nowIdx = Number(now.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', hour: 'numeric', hour12: false })) - 9;
  if (r.blocks === null) {
    el.innerHTML = '<h3>Today</h3>' + empty(r.faculty_unmatched ? 'Your name is not in the timetable' : 'Timetable not uploaded yet', r.faculty_unmatched ? 'Sign up with your name exactly as it appears in the timetable.' : 'Ask the assistant anything. Queries I cannot answer go to the admin.');
    $('#nowc').innerHTML = ''; return;
  }
  el.innerHTML = `<h3>Today <span class="pill">${r.day}</span></h3>` + (r.blocks.length ? '<ol class="tl">' + r.blocks.map(b => {
    const lib = b.s === 'Library';
    return `<li class="${b.on ? 'on' : b.end < nowIdx ? 'dn' : ''}"><time>${E(b.t.split(' - ')[0])}</time><i class="pt"></i><div><b>${E(b.s)} ${b.on ? '<span class="tag">Now</span>' : ''}</b>${lib ? '' : `<span>${E(b.f)}${b.f ? ' · ' : ''}${E(b.p)}${b.sec ? ' · ' + E(b.sec) : ''}</span>`}</div></li>`;
  }).join('') + '</ol>' : empty('No classes today', 'Enjoy the free day.'));
  // "Now" card: current class with progress, otherwise the next one
  const real = r.blocks.filter(b => b.s !== 'Library'), cur = real.find(b => b.on), nxt = real.find(b => b.i > nowIdx);
  const mins = (now.getMinutes()), pct = cur ? Math.min(100, Math.round(((nowIdx - cur.i) * 60 + mins) / ((cur.end - cur.i + 1) * 60) * 100)) : 0;
  const nc = $('#nowc'); if (!nc) return;
  const b = cur || nxt;
  nc.innerHTML = b ? `<div class="cd now"><small>${cur ? 'Happening now' : 'Up next at ' + E(b.t.split(' - ')[0])}</small><h2>${E(b.s)}</h2><p>${E(b.f)}${b.f ? ' · ' : ''}${E(b.p)}</p>${cur ? `<div class="bar" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"><i style="width:${pct}%"></i></div>` : ''}</div>`
    : `<div class="cd now"><small>Today</small><h2>You’re done for the day</h2><p>No more classes. Ask me about tomorrow.</p></div>`;
}

async function overview() {
  const o = await api('/overview'), el = $('#ovc'); if (!el) return;
  const card = (h, x) => x ? `<div class="cd cdn"><h4>${h}</h4><div class="n">${x.in === 0 ? 'Today' : x.in}<small>${x.in === 0 ? '' : x.in === 1 ? 'day' : 'days'}</small></div><p>${E(x.n)}</p></div>` : '';
  el.innerHTML = card('Next holiday', o.holiday) + card('Next deadline', o.milestone);
}

action('send', () => send());
action('chip', d => send(d.q));
action('mic', () => { stopSpeaking(); return toggleMic(t => send(t)); });
action('voice', (d, el) => { setVoice(el.value); speak('Hello, this is my voice', 0); });
action('vlang', (d, el) => setVLang(el.value));
action('stopsay', () => stopSpeaking());
action('say', d => { const m = S.chat[d.i]; if (m) speak(m.t, m.lang || 0); });
action('copy', d => { const m = S.chat[d.i]; if (m && navigator.clipboard) navigator.clipboard.writeText(m.t).catch(() => {}); });

// Entry point: wires pages together and boots the app.
import { api } from './core/api.js';
import { S } from './core/state.js';
import { firstName } from './core/utils.js';
import { registerPages } from './core/router.js';
import { authView } from './pages/auth.js';
import { shell, tick, logout } from './pages/shell.js';
import { pChat, today } from './pages/chat.js';
import { pNt } from './pages/notifications.js';
import { pEv } from './pages/events.js';
import { pDc } from './pages/documents.js';
import { pCp } from './pages/complaints.js';
import { aO, aQ, aC, aN, aU, aR } from './pages/admin.js';
import { startPolling } from './services/notifier.js';
import { loadVoiceConfig } from './services/voice.js';
import { API_BASE } from './config.js';

registerPages({ chat: pChat, nt: pNt, ev: pEv, dc: pDc, cp: pCp, ao: aO, aq: aQ, ac: aC, an: aN, au: aU, ar: aR });

async function boot() {
  try { S.me = await api('/me'); } catch (e) { S.me = null; return authView(); }
  const admin = S.me.role === 'admin';
  S.view = admin ? 'ao' : 'chat';
  S.chat = [{ w: 'b', t: `Hi ${firstName(S.me.name)}! I’m Awaaz, your campus assistant. Ask me about classes, rooms, holidays, exams, syllabus or notices in English, हिंदी or Hinglish.`, ts: Date.now() }];
  if (!admin) { await loadVoiceConfig(); startPolling(); }
  shell();
}

window.addEventListener('logged-in', boot);
window.addEventListener('session-expired', () => logout(false));
setInterval(tick, 1000);
setInterval(() => { if (S.me && S.view === 'chat') today().catch(() => {}); }, 60000);

fetch(API_BASE + '/api/meta').then(r => r.json()).then(j => { S.secs = j.sections; }).catch(() => {}).finally(() => (S.token ? boot() : authView()));

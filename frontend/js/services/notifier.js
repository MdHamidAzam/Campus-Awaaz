// Polls the backend for new notifications -> badge, popup + pop sound.
import { api } from '../core/api.js';
import { S } from '../core/state.js';
import { badge } from '../core/utils.js';
import { go } from '../core/router.js';
import { showPopup } from './popup.js';

export async function poll() {
  if (!S.me || S.me.role === 'admin') return;
  try {
    const r = await api('/notes'); S.notes = r.items; S.seen = r.seen;
    const top = S.notes.length ? S.notes[0].id : 0;
    if (S.lastId === null) {                                   // first load after login
      const unread = S.notes.filter(n => n.ts > S.seen).length;
      if (unread) showPopup('Notifications', `You have ${unread} unread notification${unread > 1 ? 's' : ''}`);
    } else if (top > S.lastId) {                               // new ones arrived while the dashboard is open
      S.notes.filter(n => n.id > S.lastId).reverse().slice(-3).forEach((n, i) => setTimeout(() => showPopup(n.title, n.body), i * 800));
      if (S.view === 'nt') go('nt');
    }
    S.lastId = top; badge();
  } catch (e) { /* offline: try again next tick */ }
}

export function startPolling() { stopPolling(); S.lastId = null; poll(); S.timer = setInterval(poll, 5000); }
export function stopPolling() { clearInterval(S.timer); S.timer = null; }

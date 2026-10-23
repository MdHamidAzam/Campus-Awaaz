import { api } from '../core/api.js';
import { S } from '../core/state.js';
import { $, E, firstName } from '../core/utils.js';
import { action } from '../core/actions.js';
import { go } from '../core/router.js';
import { stopPolling } from '../services/notifier.js';
import { stopSpeaking } from '../services/voice.js';
import { authView } from './auth.js';

export const LOGO = '<svg viewBox="0 0 32 32" fill="none" stroke="#f2a516" stroke-width="2.8" stroke-linecap="round"><path d="M7 18v-4M11.5 21V11M16 24V8M20.5 21V11M25 18v-4"/></svg>';
const IC = {
  chat: 'M4 5h16v11H9l-5 4z', ev: 'M4 6h16v14H4zM4 10h16M9 3v4M15 3v4', nt: 'M6 17v-6a6 6 0 0112 0v6l2 2H4zM10 21h4',
  cp: 'M5 3v18M5 4h12l-2 4 2 4H5', dc: 'M7 3h8l4 4v14H7zM14 3v5h5', ao: 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
  aq: 'M12 21a9 9 0 100-18 9 9 0 000 18zM9.5 9a2.5 2.5 0 114 2c-1 .7-1.5 1.2-1.5 2.5M12 17h.01', ac: 'M5 3v18M5 4h12l-2 4 2 4H5',
  an: 'M3 11v2l12 5V6zM15 9a3 3 0 010 6', au: 'M12 16V4M7 9l5-5 5 5M4 20h16', ar: 'M7 7h13l-4-4M17 17H4l4 4',
};
const icon = k => `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${IC[k]}"/></svg>`;

// Tabs per role. Faculty: no events, documents or complaints.
export const TABS = role => role === 'admin'
  ? [['ao', 'Overview'], ['aq', 'Queries'], ['ac', 'Complaints'], ['an', 'Announce'], ['au', 'Notices'], ['ar', 'Rooms'], ['dc', 'Documents']]
  : role === 'faculty'
    ? [['chat', 'Assistant'], ['nt', 'Notifications']]
    : [['chat', 'Assistant'], ['ev', 'Events'], ['nt', 'Notifications'], ['cp', 'Complaints'], ['dc', 'Documents']];

export function shell() {
  const m = S.me, a = m.role === 'admin', init = (firstName(m.name)[0] || 'A').toUpperCase();
  const tools = '<div class="mini"><button class="gh" data-a="theme" aria-label="Switch light / dark theme">Theme</button><button class="gh" data-a="logout">Logout</button></div>';
  $('#app').innerHTML = `<div class="shell">
<aside class="rail"><div class="brand"><span class="mark">${LOGO}</span>Campus Awaaz</div>
<nav class="nav" aria-label="Main">${TABS(m.role).map(t => `<button class="nv" data-a="go" data-arg="${t[0]}">${icon(t[0])}<span>${E(t[1])}</span>${t[0] === 'nt' ? '<sup id="nb"></sup>' : ''}</button>`).join('')}</nav>
<div class="me"><div class="who"><span class="av">${E(init)}</span><div><b>${E(m.name)}</b><small>${E(a ? 'Administrator' : m.section || 'Faculty')}</small></div></div>${tools}</div></aside>
<div><div class="mtop"><div class="brand"><span class="mark">${LOGO}</span>Campus Awaaz</div>${tools}</div><main class="main" id="pg"></main></div></div>`;
  tick(); go(S.view);
}

export function tick() {
  const d = new Date(), w = $('#dw'); if (!w) return;
  const IST = { timeZone: 'Asia/Kolkata' };
  w.textContent = d.toLocaleDateString('en-IN', { ...IST, weekday: 'short', day: 'numeric', month: 'short' });
  $('#tm').textContent = d.toLocaleTimeString('en-IN', { ...IST, hour12: true }).toUpperCase();
}

export async function logout(callApi = true) {
  if (callApi) { try { await api('/logout', { method: 'POST' }); } catch (e) { /* ignore */ } }
  stopPolling(); stopSpeaking();
  S.token = ''; try { localStorage.removeItem('tk'); } catch (e) { /* ignore */ } S.me = null; S.notes = []; S.lastId = null; authView();
}

action('go', d => go(d.arg));
action('logout', () => logout());
action('closePop', (d, el) => el.parentElement.remove());
action('theme', () => {
  const r = document.documentElement, dark = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme:dark)').matches;
  r.dataset.theme = dark ? 'light' : 'dark'; try { localStorage.ca_theme = r.dataset.theme; } catch (e) { /* ignore */ }
});

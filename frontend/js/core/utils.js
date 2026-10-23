import { S } from './state.js';

export const $ = s => document.querySelector(s);
export const E = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const IST = { timeZone: 'Asia/Kolkata' };
export const fdate = s => new Date(s + 'T00:00:00+05:30').toLocaleDateString('en-IN', { ...IST, weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
export const ftime = ts => new Date(ts * 1000).toLocaleString('en-IN', { ...IST, day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' });
export const firstName = n => (n || '').replace(/^(dr|mr|ms|mrs|prof)\.?\s+/i, '').split(' ')[0];
export const hm = d => d.toLocaleTimeString('en-IN', { ...IST, hour: 'numeric', minute: '2-digit', hour12: true }).toUpperCase();

export function ago(ts) {
  const s = Math.max(0, Date.now() / 1000 - ts);
  if (s < 60) return 'just now'; if (s < 3600) return Math.floor(s / 60) + ' min ago';
  if (s < 86400) return Math.floor(s / 3600) + ' h ago'; if (s < 604800) return Math.floor(s / 86400) + ' d ago';
  return ftime(ts);
}
export function greeting() {
  const h = Number(new Date().toLocaleString('en-IN', { ...IST, hour: 'numeric', hour12: false }));
  return h < 5 ? 'Good night' : h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
}
// assistant text -> safe HTML: "•" lines become a list, other lines become paragraphs
export function rich(t) {
  const out = []; let list = [];
  const flush = () => { if (list.length) { out.push('<ul>' + list.map(x => `<li>${x}</li>`).join('') + '</ul>'); list = []; } };
  String(t).split('\n').forEach(l => {
    const m = l.match(/^\s*[•\-]\s+(.*)/);
    if (m) list.push(E(m[1])); else if (/^\s{2,}\S/.test(l) && list.length) list[list.length - 1] += '<br><small class="mu">' + E(l.trim()) + '</small>'; else if (l.trim()) { flush(); out.push(`<p>${E(l)}</p>`); }
  });
  flush(); return out.join('');
}

export function toast(m, bad) {
  const d = document.createElement('div'); d.className = 'ts' + (bad ? ' bad' : ''); d.setAttribute('role', 'status'); d.textContent = m;
  document.body.appendChild(d); setTimeout(() => d.remove(), bad ? 6000 : 3800);
}

export function badge() {                         // unread count on the Notifications tab
  const c = S.notes.filter(n => n.ts > S.seen).length;
  document.querySelectorAll('#nb').forEach(e => { e.textContent = c || ''; });
}

export const empty = (title, hint = '') => `<div class="empty"><b>${E(title)}</b>${E(hint)}</div>`;
export const skeleton = (n = 3) => '<div class="cd wide">' + '<div class="sk"></div>'.repeat(n) + '</div>';

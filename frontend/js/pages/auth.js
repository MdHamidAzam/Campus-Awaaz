import { api } from '../core/api.js';
import { S } from '../core/state.js';
import { $, E } from '../core/utils.js';
import { action } from '../core/actions.js';
import { LOGO } from './shell.js';

const snap = () => { ['nm', 'em', 'rl', 'sc'].forEach(i => { const e = $('#' + i); if (e) S.form[i] = e.value; }); };

export function authView() {
  const r = S.authRole, su = S.authMode === 'up' && r !== 'admin', f = S.form;
  $('#app').innerHTML = `<div class="au"><section class="hero"><div class="brand"><span class="mark">${LOGO}</span>Campus Awaaz</div>
<h1>Campus ki awaaz, ab aapki <em>voice</em> me.</h1>
<p>One assistant for your classes, rooms, holidays, exams and notices. Type or speak in English, हिंदी or Hinglish.</p>
<div class="demo" aria-hidden="true"><div class="m u">mera next class kahan hai?</div><div class="m b">Computer Networks with Ms. Preeti Srivastava, 10:00 AM, Room 418, Wing C.</div></div>
<div class="fts"><span>Voice and chat</span><span>Class reminders by email</span><span>Learns from admin answers</span></div></section>
<section class="fw"><div class="cd lc"><div class="rl" role="tablist">${['student', 'faculty', 'admin'].map(x => `<button role="tab" class="${r === x ? 'on' : ''}" data-a="authRole" data-r="${x}">${x[0].toUpperCase() + x.slice(1)}</button>`).join('')}</div>
<h3>${su ? 'Create your ' + r + ' account' : r === 'admin' ? 'Admin login' : 'Welcome back'}</h3>
${su ? `<label>${r === 'faculty' ? 'Full name (as in the timetable)' : 'Full name'}<input id="nm" value="${E(f.nm || '')}" autocomplete="name"></label>` : ''}
<label>Email<input id="em" type="email" value="${E(f.em || '')}" autocomplete="username" data-enter="auth"></label>
${su && r === 'student' ? `<div class="row"><label>University roll no.<input id="rl" value="${E(f.rl || '')}"></label><label>Section<select id="sc">${S.secs.map(s => `<option value="${E(s.sec)}" ${f.sc === s.sec ? 'selected' : ''}>${E(s.sec)}${s.tt ? '' : ' (timetable pending)'}</option>`).join('')}</select></label></div>` : ''}
<label>Password<span class="pw"><input id="pw" type="password" autocomplete="${su ? 'new-password' : 'current-password'}" data-enter="auth"><button type="button" data-a="showpw">Show</button></span></label>
<div class="er" id="er" role="alert"></div><button class="bt full" id="ab" data-a="auth">${su ? 'Create account' : 'Login'}</button>
${r === 'admin' ? '<p class="sw">Admin accounts are fixed. Only registered admins can login here.</p>'
    : `<p class="sw">${su ? 'Already registered?' : 'New here?'} <a data-a="authMode" data-m="${su ? 'in' : 'up'}" tabindex="0">${su ? 'Login' : 'Create an account'}</a></p>`}
${r === 'student' && !su ? '<div class="or">or</div><button class="bt sec full" data-a="demo">Try the demo student (CS-3H)</button>' : ''}</div></section></div>`;
}

action('authRole', d => { snap(); S.authRole = d.r; authView(); });
action('authMode', d => { snap(); S.authMode = d.m; authView(); });
action('showpw', (d, el) => { const i = $('#pw'); i.type = i.type === 'password' ? 'text' : 'password'; el.textContent = i.type === 'password' ? 'Show' : 'Hide'; });
async function enter(path, body) {
  const b = $('#ab'), er = $('#er'); if (b) { b.disabled = true; b.textContent = 'Please wait…'; } if (er) er.textContent = '';
  try {
    const r = await api(path, { body }); S.token = r.token; try { localStorage.tk = r.token; } catch (e) { /* ignore */ }
    S.form = {}; window.dispatchEvent(new Event('logged-in'));
  } catch (e) { if ($('#er')) $('#er').textContent = e.message; if (b) { b.disabled = false; b.textContent = S.authMode === 'up' ? 'Create account' : 'Login'; } }
}
action('demo', () => enter('/login', { email: 'demo@campusawaaz.app', password: 'demo1234', role: 'student' }));
action('auth', () => {
  const g = i => ($('#' + i)?.value || '').trim(), su = S.authMode === 'up' && S.authRole !== 'admin';
  if (!g('em') || !$('#pw').value) return ($('#er').textContent = 'Enter your email and password.');
  return enter(su ? '/signup' : '/login', su ? { name: g('nm'), email: g('em'), password: $('#pw').value, role: S.authRole, roll: g('rl'), section: g('sc') }
                                              : { email: g('em'), password: $('#pw').value, role: S.authRole });
});

import { api } from '../core/api.js';
import { S } from '../core/state.js';
import { $, E, ftime, toast, empty } from '../core/utils.js';
import { action } from '../core/actions.js';
import { box, pg, act, go } from '../core/router.js';
import { dRow } from './documents.js';
import { evCard } from './events.js';

const ta = (id, ph) => `<textarea id="${id}" placeholder="${ph}"></textarea>`;

export async function aO() {
  const s = await api('/admin/stats'), c = (n, l, hot) => `<div class="stc ${hot && n ? 'hot' : ''}"><b>${n}</b><span>${l}</span></div>`;
  pg(`<div class="top"><div><h1>Overview</h1><p>What needs your attention today.</p></div></div><div class="st">${c(s.pending_q, 'Queries waiting for an answer', 1)}${c(s.open_c, 'Open complaints', 1)}${c(s.drafts, 'Notices not yet published')}${c(s.students, 'Students signed up')}${c(s.faculty, 'Faculty signed up')}${c(s.taught, 'Answers the AI has learned')}${c(s.reminders, 'Class reminders sent')}${c(s.alerts, 'Notifications sent')}</div>
<p class="mu">Start with <a class="lk" style="margin:0" data-a="go" data-arg="aq">unanswered queries</a>. Every answer you write is learned by the assistant and emailed to the student.</p>`);
}

export async function aQ() {
  const l = await api('/admin/queries');
  box(`<h3>Queries the assistant could not answer <span class="pill">${l.length} waiting</span></h3>` + (l.map(x => `<div class="it"><b>${E(x.q)}</b><br><small>${E(x.who)} · ${ftime(x.ts)}</small>${ta('a' + x.id, 'Type the answer. The assistant learns it and the student gets it by email.')}<button class="bt sm" data-a="answerQ" data-id="${x.id}">Send answer and teach AI</button></div>`).join('') || empty('All caught up', 'New queries the assistant cannot answer will land here.')));
}

export async function aC() {
  const l = await api('/complaints');
  box(`<h3>Complaints <span class="pill">${l.filter(x => !x.r).length} open</span></h3>` + (l.map(x => `<div class="it"><span class="chip ${x.r ? 'g' : 'w'}">${x.r ? 'Resolved' : 'Open'}</span> <b>${E(x.t)}</b><br><small>${E(x.who)} · ${ftime(x.ts)}</small>${x.r ? `<p>Reply: ${E(x.r)}</p>` : `${ta('c' + x.id, 'Reply to the student')}<button class="bt sm" data-a="resolve" data-id="${x.id}">Send reply and resolve</button>`}</div>`).join('') || empty('No complaints', 'Nothing to resolve right now.')));
}

export async function aN() {
  const ev = await api('/events');
  box(`<h3>Announce an event</h3><div class="row"><label>Type<select id="ek">${['Event', 'Competition', 'Fees', 'Sports', 'Holiday', 'Notice'].map(k => `<option>${k}</option>`).join('')}</select></label><label>Title<input id="et"></label><label>Date<input id="ed" type="date"></label><label>Time<input id="em" placeholder="e.g. 10:00 AM"></label></div><label>Details<input id="ex"></label>
<button class="bt" data-a="announce">Publish and notify students</button><h3 style="margin-top:26px">Upcoming events <span class="pill">${ev.length}</span></h3>`
    + (ev.map(x => evCard(x).replace(/<\/div><\/div>$/, `<div style="margin-top:6px"><button class="lk dg" data-a="delEvent" data-id="${x.id}">Delete</button></div></div></div>`)).join('') || empty('No upcoming events', 'Published events appear here.')));
}

export async function aU() {
  const d = (await api('/docs')).filter(x => x.cat === 'notice');
  box(`<h3>Upload a notice <span class="pill">pdf · docx · xlsx · jpg</span></h3><div class="fx"><input type="file" id="uf" accept=".pdf,.docx,.xlsx,.jpg,.jpeg" class="sch" style="flex:1;min-width:200px;margin:0"><input id="ut" class="grow sch" placeholder="Notice title"><button class="bt" data-a="upload">Upload</button></div>
<p class="mu">Uploads stay hidden until you press <b>Publish</b>. Publishing notifies students.</p>` + (d.map(x => dRow(x, 1)).join('') || empty('No notices yet', 'Upload a file to get started.')));
}

const PER = ['9:00 AM', '10:00 AM', '11:00 AM', '12:00 PM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM', '5:00 PM'];
const MONS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const todayIST = () => new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' });

export async function aR() {
  const l = await api('/admin/rooms'), opt = (n, sel) => PER.slice(0, n).map((p, i) => `<option value="${i}" ${i === sel ? 'selected' : ''}>${p}</option>`).join('');
  box(`<h3>Room change</h3><p class="mu" style="margin-top:-6px">Only the section, date and periods you pick are affected. Those students and their teachers are notified.</p>
<div class="row"><label>Section<select id="rs"><option value="">All sections</option>${S.secs.map(s => `<option>${E(s.sec)}</option>`).join('')}</select></label><label>Date<input id="rd" type="date" value="${todayIST()}"></label>
<label>From period<select id="r0">${opt(8, 0)}</select></label><label>Until (end of period)<select id="r1">${PER.slice(1).map((p, i) => `<option value="${i}" ${i === 0 ? 'selected' : ''}>${p}</option>`).join('')}</select></label></div>
<div class="row"><label>Engaged room <span class="mu" id="rsub"></span><input id="rf" placeholder="Fills in from the timetable"></label><label>Alternative room<input id="rt" placeholder="e.g. Lab 3, Wing B, 6th Floor"></label><label>Reason (optional)<input id="rn"></label></div>
<button class="bt" data-a="room">Announce change</button><h3 style="margin-top:24px">Active room changes <span class="pill">${l.length}</span></h3>` + (l.map(x => {
    const [y, m, d] = (x.dt || '').split('-'), when = x.dt ? `${Number(d)} ${MONS[m - 1]}` : 'Every day', t = x.s0 == null ? 'All day' : `${PER[x.s0]} – ${PER[(x.s1 ?? x.s0) + 1]}`;
    return `<div class="it"><span class="chip">${E(x.sec || 'All sections')}</span> <span class="chip w">${when} · ${t}</span><br>Room <b>${E(x.f)}</b> → ${E(x.t)}${x.n ? `<p>${E(x.n)}</p>` : ''}<button class="lk dg" data-a="delRoom" data-id="${x.id}">Remove</button></div>`;
  }).join('') || empty('No room changes', 'Timetable rooms are shown as scheduled.')));
}
async function lookup() {                                   // pre-fill "engaged room" from the timetable
  const sec = $('#rs')?.value, dt = $('#rd')?.value, sl = $('#r0')?.value; if (!sec || !dt) { if ($('#rsub')) $('#rsub').textContent = ''; return; }
  try { const r = await api(`/admin/room-lookup?sec=${encodeURIComponent(sec)}&dt=${dt}&slot=${sl}`); $('#rf').value = r.room || ''; $('#rsub').textContent = r.subject ? '(' + r.subject + ')' : ''; } catch (e) { /* ignore */ }
}
document.addEventListener('change', e => { if (['rs', 'rd', 'r0'].includes(e.target.id)) lookup(); if (e.target.id === 'r0') { const u = $('#r1'), v = Number(e.target.value); if (u && Number(u.value) < v) u.value = v; } });

const need = (f, m) => { if (!f) throw Error(m); };
action('answerQ', d => act(async () => { need($('#a' + d.id).value.trim(), 'Write an answer first'); await api(`/admin/queries/${d.id}`, { body: { t: $('#a' + d.id).value } }); }, 'Answer saved. The assistant has learned it.'));
action('resolve', d => act(async () => { need($('#c' + d.id).value.trim(), 'Write a reply first'); await api(`/admin/complaints/${d.id}`, { body: { t: $('#c' + d.id).value } }); }, 'Complaint resolved'));
action('announce', () => act(async () => { need($('#et').value.trim() && $('#ed').value, 'Add a title and a date'); await api('/admin/events', { body: { k: $('#ek').value, title: $('#et').value, d: $('#ed').value, tm: $('#em').value, x: $('#ex').value } }); }, 'Published. Students were notified.'));
action('delEvent', d => confirm('Delete this event?') && act(() => api(`/admin/events/${d.id}`, { method: 'DELETE' }), 'Event deleted'));
action('room', () => act(async () => {
  need($('#rf').value.trim() && $('#rt').value.trim(), 'Enter the engaged room and an alternative'); need($('#rd').value, 'Choose the date');
  const s0 = Number($('#r0').value), s1 = Number($('#r1').value); need(s1 >= s0, 'The end period must not be before the start period');
  await api('/admin/rooms', { body: { f: $('#rf').value, t: $('#rt').value, n: $('#rn').value, sec: $('#rs').value, dt: $('#rd').value, s0, s1 } });
}, 'Room change announced. Students and teachers were notified.'));
action('delRoom', d => act(() => api(`/admin/rooms/${d.id}`, { method: 'DELETE' }), 'Removed'));
action('upload', () => {
  const f = $('#uf').files[0]; if (!f) return toast('Choose a file first', true);
  const fd = new FormData(); fd.append('file', f); fd.append('title', $('#ut').value);
  return act(() => api('/admin/upload', { body: fd }), 'Uploaded. Press Publish to show it to students.');
});

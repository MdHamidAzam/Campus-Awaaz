import { api } from '../core/api.js';
import { S } from '../core/state.js';
import { E, ago, badge, empty } from '../core/utils.js';
import { box } from '../core/router.js';

export async function pNt() {
  box(`<h3>Notifications <span class="pill">class reminders are also emailed to you</span></h3>` + (S.notes.length
    ? S.notes.map(n => `<div class="it ${n.ts > S.seen ? 'nw' : ''}"><b>${E(n.title)}</b>${n.ts > S.seen ? ' <span class="chip w">New</span>' : ''}<p>${E(n.body)}</p><small>${ago(n.ts)}</small></div>`).join('')
    : empty('No notifications yet', 'Class reminders, notices and room changes show up here.')));
  await api('/notes/seen', { method: 'POST' });
  setTimeout(() => { S.seen = Date.now() / 1000; badge(); }, 1500);
}

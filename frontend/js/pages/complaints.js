import { api } from '../core/api.js';
import { $, E, empty } from '../core/utils.js';
import { action } from '../core/actions.js';
import { box, act } from '../core/router.js';

export async function pCp() {
  const l = await api('/complaints');
  box(`<h3>Complaint box</h3><p class="mu" style="margin-top:-6px">Goes straight to the admin. You get the reply here and by email.</p><textarea id="ct" rows="3" maxlength="600" placeholder="What went wrong, and where?"></textarea>
<button class="bt" data-a="sendComplaint">Send complaint</button><h3 style="margin-top:24px">Your complaints</h3>`
    + (l.map(c => `<div class="it"><span class="chip ${c.r ? 'g' : 'w'}">${c.r ? 'Resolved' : 'Pending'}</span> <b>${E(c.t)}</b>${c.r ? `<p>Admin: ${E(c.r)}</p>` : ''}</div>`).join('') || empty('No complaints', 'Anything that needs fixing on campus can go here.')));
}
action('sendComplaint', () => { if (!$('#ct').value.trim()) return act(async () => { throw Error('Write your complaint first'); }); return act(() => api('/complaints', { body: { t: $('#ct').value } }), 'Complaint sent to the admin'); });

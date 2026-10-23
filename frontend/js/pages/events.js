import { api } from '../core/api.js';
import { E, empty } from '../core/utils.js';
import { box } from '../core/router.js';
import { dRow } from './documents.js';

const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
export const evCard = x => { const [y, m, d] = x.d.split('-'); return `<div class="it row2"><div class="date"><b>${Number(d)}</b><span>${MON[m - 1]}</span></div><div><b>${E(x.title)}</b> <span class="chip">${E(x.k)}</span>${x.tm ? `<p>${E(x.tm)}</p>` : ''}${x.x ? `<p>${E(x.x)}</p>` : ''}</div></div>`; };

export async function pEv() {
  const [e, d] = await Promise.all([api('/events'), api('/docs')]), n = d.filter(x => x.cat === 'notice');
  box('<h3>Events</h3>' + (e.map(evCard).join('') || empty('Nothing scheduled', 'New events from the admin appear here.')) + '<h3 style="margin-top:22px">Notices</h3>' + (n.map(x => dRow(x)).join('') || empty('No notices', '')));
}

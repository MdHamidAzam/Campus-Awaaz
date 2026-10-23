import { api } from '../core/api.js';
import { S } from '../core/state.js';
import { E, ftime, empty, $ } from '../core/utils.js';
import { action } from '../core/actions.js';
import { box, act } from '../core/router.js';

export const dRow = (x, adm) => {
  const u = `/api/docs/${x.id}/file?t=${encodeURIComponent(S.token)}`, v = ['pdf', 'jpg', 'jpeg'].includes(x.ext);
  return `<div class="it ${adm && !x.pub ? 'nw' : ''}" data-t="${E(x.title.toLowerCase())}"><span class="ft">${E(x.ext.toUpperCase())}</span><b>${E(x.title)}</b>
<p>${x.cat === 'notice' ? ftime(x.ts) : 'Official document'}${adm ? (x.pub ? ' · Published' : ' · Draft, not visible to students') : ''}</p>
<div style="margin-top:6px">${v ? `<a class="lk" target="_blank" rel="noopener" href="${u}">View</a>` : ''}<a class="lk" href="${u}&dl=1">Download</a>
${adm ? `${x.pub ? '' : `<button class="lk" data-a="publishDoc" data-id="${x.id}">Publish</button>`}<button class="lk dg" data-a="deleteDoc" data-id="${x.id}">Delete</button>` : ''}</div></div>`;
};

export async function pDc() {
  const d = await api('/docs'), a = S.me.role === 'admin', off = d.filter(x => x.cat !== 'notice'), nt = d.filter(x => x.cat === 'notice');
  box(`<h3>Documents <span class="pill">${d.length} files</span></h3><input class="sch" id="ds" placeholder="Search documents…" aria-label="Search documents" style="margin-bottom:14px">`
    + (nt.length ? '<h4 class="hd3 mu">Notices</h4>' + nt.map(x => dRow(x, a)).join('') : '') + (off.length ? '<h4 class="hd3 mu" style="margin-top:16px">Official</h4>' + off.map(x => dRow(x, a)).join('') : '') + (d.length ? '' : empty('No documents yet', 'Timetables, syllabus and notices will show here.')));
}

document.addEventListener('input', e => { if (e.target.id === 'ds') { const q = e.target.value.toLowerCase(); document.querySelectorAll('#pg .it[data-t]').forEach(r => { r.style.display = r.dataset.t.includes(q) ? '' : 'none'; }); } });
action('publishDoc', d => act(() => api(`/admin/docs/${d.id}/publish`, { method: 'POST' }), 'Published. Students were notified.'));
action('deleteDoc', d => confirm('Delete this document for everyone?') && act(() => api(`/admin/docs/${d.id}`, { method: 'DELETE' }), 'Deleted'));

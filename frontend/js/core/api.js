import { API_BASE } from '../config.js';
import { S } from './state.js';

export const apiUrl = p => API_BASE + '/api' + p;

// FastAPI sends 422 errors as a list of objects - turn any shape into a readable sentence.
const msg = d => Array.isArray(d) ? d.map(x => (x.loc ? String(x.loc[x.loc.length - 1]) + ': ' : '') + (x.msg || '')).join('; ')
  : typeof d === 'string' ? d : 'Something went wrong. Please try again.';

export async function api(p, o = {}) {
  let body = o.body; const h = { 'X-Token': S.token };
  if (body && !(body instanceof FormData)) { h['Content-Type'] = 'application/json'; body = JSON.stringify(body); }
  let r;
  try { r = await fetch(apiUrl(p), { method: o.method || (body ? 'POST' : 'GET'), headers: h, body }); }
  catch (e) { throw Error('Cannot reach the server. Check your connection and try again.'); }
  const j = await r.json().catch(() => ({}));
  if (r.status === 401 && S.me) { window.dispatchEvent(new Event('session-expired')); throw Error('Session expired, please login again'); }
  if (!r.ok) throw Error(msg(j.detail));
  return j;
}

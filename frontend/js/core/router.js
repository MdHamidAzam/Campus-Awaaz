import { S } from './state.js';
import { $, toast, badge, skeleton } from './utils.js';

const pages = {};
export const registerPages = p => Object.assign(pages, p);

export function go(v, quiet) {
  S.view = v;
  document.querySelectorAll('.nv').forEach(b => { const on = b.dataset.arg === v; b.classList.toggle('on', on); if (on) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current'); });
  if (!quiet && v !== 'chat') pg(skeleton());
  window.scrollTo(0, 0);
  Promise.resolve(pages[v]()).catch(e => { pg(`<div class="cd wide"><div class="empty"><b>Could not load this page</b>${e.message}</div></div>`); toast(e.message, true); });
  badge();
}

export const pg = h => { const p = $('#pg'); if (p) p.innerHTML = h; };
export const box = h => pg(`<div class="cd wide">${h}</div>`);

// run an API call, show a toast, refresh the current page. Ignores clicks while a call is running (no double submits).
let busy = false;
export const act = async (f, ok) => {
  if (busy) return; busy = true;
  try { await f(); if (ok) toast(ok); go(S.view, true); } catch (e) { toast(e.message, true); } finally { busy = false; }
};

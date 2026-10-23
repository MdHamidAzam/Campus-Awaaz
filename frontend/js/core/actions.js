// Tiny event-delegation layer: HTML uses data-a="name" (click), data-change="name", data-enter="name".
const reg = {};
export const action = (name, fn) => { reg[name] = fn; };
const call = (name, el, ev) => { const f = reg[name]; if (f) Promise.resolve(f({ ...el.dataset }, el, ev)).catch(e => console.error(e)); };

document.addEventListener('click', e => { const el = e.target.closest('[data-a]'); if (el) call(el.dataset.a, el, e); });
document.addEventListener('change', e => { const el = e.target.closest('[data-change]'); if (el) call(el.dataset.change, el, e); });
document.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.dataset && e.target.dataset.enter) call(e.target.dataset.enter, e.target, e); });

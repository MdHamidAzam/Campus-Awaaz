// Banner that drops in at the top of the dashboard for a few seconds, with a pop sound.
import { $, E } from '../core/utils.js';
import { popSound } from './sound.js';

export function showPopup(title, body, ms = 6000) {
  const d = document.createElement('div');
  d.className = 'pop'; d.setAttribute('role', 'alert');
  d.innerHTML = `<button class="pb" data-a="go" data-arg="nt"><b>${E(title)}</b><span>${E(body)}</span></button><button class="px" data-a="closePop" aria-label="Close">x</button>`;
  $('#popups').appendChild(d);
  requestAnimationFrame(() => d.classList.add('show'));
  popSound();
  setTimeout(() => { d.classList.remove('show'); setTimeout(() => d.remove(), 400); }, ms);
}

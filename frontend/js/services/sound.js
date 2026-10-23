// Notification "pop" sound, synthesised in the browser (no audio file needed).
let ac;
const ctx = () => (ac = ac || new (window.AudioContext || window.webkitAudioContext)());
export const unlockAudio = () => { try { ctx().resume(); } catch (e) { /* ignore */ } };
['click', 'keydown', 'touchstart'].forEach(ev => document.addEventListener(ev, unlockAudio, { passive: true }));

export function popSound() {
  try {
    const c = ctx(); c.resume(); const t = c.currentTime;
    [[520, 980, 0], [780, 1250, 0.14]].forEach(([f0, f1, d]) => {
      const o = c.createOscillator(), g = c.createGain();
      o.type = 'sine'; o.frequency.setValueAtTime(f0, t + d); o.frequency.exponentialRampToValueAtTime(f1, t + d + 0.08);
      g.gain.setValueAtTime(0.0001, t + d); g.gain.exponentialRampToValueAtTime(0.35, t + d + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, t + d + 0.2);
      o.connect(g); g.connect(c.destination); o.start(t + d); o.stop(t + d + 0.22);
    });
  } catch (e) { /* ignore */ }
}

// Single shared state object for the whole UI.
const ls = k => { try { return localStorage.getItem(k) || ''; } catch (e) { return ''; } };
export const S = {
  token: ls('tk'),
  me: null,            // {name,email,role,section}
  view: 'chat',
  chat: [],            // assistant conversation
  notes: [], seen: 0, lastId: null, timer: null,
  secs: [],            // sections list for signup
  authRole: 'student', authMode: 'in', form: {},
  today: null,         // /today payload, used by the "Now" card
};

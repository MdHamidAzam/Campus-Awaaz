"""Timetable / calendar data + helper functions (pure logic, no web code)."""
import re, json
from datetime import datetime, date
from ..config import DATA_DIR, DAYS
from ..database import one, q, now


def _load(name): return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


TT, CAL, HOL, SYL, COORD = _load("tt.json"), _load("cal.json"), _load("hol.json"), _load("syl.json"), _load("coord.json")
for h in HOL: h["n"] = h["n"].replace("Dushehra", "Dussehra")
norm = lambda s: re.sub(r"[^A-Z0-9]", "", (s or "").upper())
TTN = {norm(k): v for k, v in TT.items()}

def nm(s): return [w for w in re.split(r'[^a-z]+', re.sub(r'\b(dr|mr|ms|mrs|prof)\b\.?', '', (s or '').lower())) if len(w) > 2]

def same(a, b):                      # needs 2 shared name words (so two different "Srivastava"s never match)
    x, y = nm(a), nm(b); c = set(x) & set(y)
    return len(c) >= 2 or (bool(c) and min(len(x), len(y)) == 1)

tl = lambda i: f"{[9, 10, 11, 12, 1, 2, 3, 4, 5][i]}:00 {'AM' if i < 3 else 'PM'}"
fd = lambda s: (lambda d: f'{d:%a}, {d.day} {d:%b} {d.year}')(datetime.fromisoformat(s))

def slots(u, day):                   # 8 hourly slots -> list of entries; None = no timetable for this user
    if u['role'] == 'student':
        t = TTN.get(norm(u['section']))
        return [[e] if e else [] for e in t['slots'].get(day, [None] * 8)] if t else None
    out = [[] for _ in range(8)]
    for sec, t in TT.items():
        for i, e in enumerate(t['slots'].get(day, [])):
            if e and e.get('f') and same(u['name'], e['f']): out[i].append({**e, 'sec': sec})
    return out

def blocks(sl):                      # merge consecutive identical slots (2-hour labs)
    res = []
    for i, es in enumerate(sl or []):
        for e in es:
            p = next((b for b in res if b['end'] == i - 1 and b['k'] == e['k'] and b.get('r') == e.get('r') and b.get('sec') == e.get('sec')), None)
            if p: p['end'] = i
            else: res.append({**e, 'i': i, 'end': i})
    return res

def place(r, sec='', day='', i=None):
    """Where a room is. An admin room change only applies to the section, date and period(s) it was created for."""
    today = now().date()
    for o in q('select * from rooms where f=? order by id desc', r):
        if o.get('sec') and norm(o['sec']) != norm(sec): continue                     # other section -> not affected
        if o.get('dt'):
            d = date.fromisoformat(o['dt'])
            if d < today or (d - today).days > 6: continue                            # past or too far ahead
            if day and d.strftime('%a') != day: continue
        if i is not None and o.get('s0') is not None and not (o['s0'] <= i <= (o['s1'] if o.get('s1') is not None else o['s0'])): continue
        return f"{o['t']} (Room {r} is engaged)"
    n = int(r) if r.isdigit() else 0
    w = 'Wing A' if 401 <= n <= 407 else 'Wing B' if 408 <= n <= 413 else 'Wing C' if 414 <= n <= 419 else 'Wing A, 6th Floor' if 601 <= n <= 605 else 'Upper Ground Floor' if r.upper().startswith('UGF') else ''
    return f'Room No. {r}' + (f', {w}' if w else '')

def courses(u):
    t = TTN.get(norm(u['section'])) if u['role'] == 'student' else None
    return t['courses'] if t else [c for x in TT.values() for c in x['courses']]


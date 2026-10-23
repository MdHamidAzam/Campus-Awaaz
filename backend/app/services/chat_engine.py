"""Rule-based campus assistant. Auto-detects the language of the question (English / Hinglish / Hindi) and answers in the same one."""
import re
from ..config import DAYS
from ..database import q, one, run, now
from .timetable import TT, CAL, HOL, SYL, COORD, TTN, norm, slots, blocks, place, courses, tl, fd

T = {
 'now': ('Your class right now: {s} with {f} — {p}.', 'Aapki class abhi hai: {s} ({f}), {p}.', 'आपकी क्लास अभी है: {s} ({f}), {p}।'),
 'next': ('No class right now. Next class at {t}: {s} with {f} — {p}.', 'Abhi koi class nahi hai. Agli class {t} par hai: {s} ({f}), {p}.', 'अभी कोई क्लास नहीं है। अगली क्लास {t} पर: {s} ({f}), {p}।'),
 'none': ('No more classes for you today 🎉', 'Aaj aapki aur koi class nahi hai 🎉', 'आज आपकी और कोई क्लास नहीं है 🎉'),
 'sched': ('Schedule for {d}:', '{d} ka schedule:', '{d} का शेड्यूल:'),
 'free': ('No classes on {d}.', '{d} ko koi class nahi hai.', '{d} को कोई क्लास नहीं है।'),
 'hol': ('Holidays:', 'Chhuttiyan:', 'छुट्टियाँ:'),
 'cal': ('Academic calendar:', 'Academic calendar:', 'अकादमिक कैलेंडर:'),
 'past': ('Already completed:', 'Ye ho chuka hai:', 'यह हो चुका है:'),
 'ev': ('Upcoming events & notices:', 'Aane wale events aur notices:', 'आगामी इवेंट और नोटिस:'),
 'lib': ('Your library periods:', 'Aapke library periods:', 'आपके लाइब्रेरी पीरियड:'),
 'coord': ('Class coordinator of {c}: {n} ({m}).', '{c} ke class coordinator: {n} ({m}).', '{c} के क्लास कोऑर्डिनेटर: {n} ({m})।'),
 'fac': ('{s} is taught by {f}.', '{s} ke teacher: {f}.', '{s} के शिक्षक: {f}।'),
 'sy': ('Syllabus — {s}:', '{s} ka syllabus:', '{s} का सिलेबस:'),
 'pick': ('Tell me the subject too, e.g. “CN syllabus”.', 'Subject ka naam bhi batao, jaise “CN syllabus”.', 'विषय का नाम भी बताइए, जैसे “CN syllabus”।'),
 'wknd': ('{d} is a holiday for classes. Here is {n}:', '{d} ko class nahi hoti. Ye raha {n} ka schedule:', '{d} को क्लास नहीं होती। यह रहा {n} का शेड्यूल:'),
 'thx': ('You’re welcome! Ask me anything else about campus.', 'Koi baat nahi! Campus ke baare me kuch aur poochho.', 'कोई बात नहीं! कैंपस के बारे में कुछ और पूछिए।'),
 'who': ('I’m Awaaz, the campus assistant. I know your timetable, rooms, holidays, exam dates, syllabus and notices. Ask in English, हिंदी or Hinglish.', 'Main Awaaz hoon, aapki campus assistant. Mujhe timetable, rooms, holidays, exam dates, syllabus aur notices pata hain.', 'मैं अवाज़ हूँ, आपकी कैंपस असिस्टेंट। मुझे टाइमटेबल, कमरे, छुट्टियाँ, परीक्षा, सिलेबस और नोटिस पता हैं।'),
 'tm': ('It’s {x} IST.', 'Abhi {x} IST baje hain.', 'अभी {x} IST है।'),
 'hi': ('Hi! Ask me about your classes, rooms, holidays, exams, syllabus or notices.', 'Hi! Mujhse apni class, room, holidays, exams, syllabus ya notices ke baare me poochho.', 'नमस्ते! क्लास, कमरे, छुट्टियाँ, परीक्षा, सिलेबस या नोटिस के बारे में पूछिए।'),
 'map': ('Wing A: Rooms 401–407. Wing B: 408–413. Wing C: 414–419. 6th floor: Labs 1–4 (Wing B) and Rooms 601–605 (Wing A); Room 603 is a faculty room where the CS-3H coordinator sits.',
         'Wing A: Room 401–407. Wing B: 408–413. Wing C: 414–419. 6th floor par: Lab 1–4 (Wing B) aur Room 601–605 (Wing A); Room 603 me faculty baithte hain, wahi CS-3H ki coordinator ka office hai.',
         'विंग A: कमरे 401–407। विंग B: 408–413। विंग C: 414–419। 6ठी मंज़िल: लैब 1–4 (विंग B) और कमरे 601–605 (विंग A); कमरा 603 में फैकल्टी बैठती हैं।'),
 'nots': ('I don’t have the timetable for {c} yet. I’ve forwarded this to the admin.', '{c} ka timetable abhi mere paas nahi hai. Maine ye admin tak bhej diya hai.', '{c} का टाइमटेबल अभी मेरे पास नहीं है। मैंने यह एडमिन को भेज दिया है।'),
 'fev': ('Events and notices are shown on the student dashboard. I can help you with your classes, rooms and schedule.', 'Events aur notices student dashboard par dikhte hain. Main aapki class, room aur schedule me madad kar sakti hoon.', 'इवेंट और नोटिस स्टूडेंट डैशबोर्ड पर दिखते हैं। मैं आपकी क्लास, कमरे और शेड्यूल में मदद कर सकती हूँ।'),
 'unk': ('I don’t have an answer to this yet. I’ve sent your request to the admin; once they add the data I’ll be able to answer.', 'Mere paas iss sawal ka jawab abhi nahi hai. Maine ye admin tak bhej diya hai. Jab admin data add karenge, tab mai answer de paungi.', 'मेरे पास इस सवाल का जवाब अभी नहीं है। मैंने आपकी रिक्वेस्ट एडमिन को भेज दी है। डेटा जुड़ते ही मैं जवाब दे पाऊँगी।'),
}
HI = re.compile(r'[\u0900-\u097F]')
HGS = re.compile(r'\b(kaha|kahan|hai|hain|kya|kab|mera|meri|mere|mujhe|hamara|humara|abhi|aaj|kal|batao|bataiye|bata|kaun|kitne|kitna|kitni|kaise|nahi|chahiye|wala|wali|hoga|hogi|agli|agla|padhate|padhata|padhati|hota|hoti|tarikh|chhutti|chuti)\b', re.I)   # clearly Hindi words
HGW = re.compile(r'\b(aur|mein|ka|ki|ke)\b', re.I)                                                                                                       # also appear in English text: need two
def lang(s):                                    # 0 English, 1 Hinglish (Hindi in Roman letters), 2 Hindi (Devanagari)
    if HI.search(s): return 2
    return 1 if HGS.search(s) or len(HGW.findall(s)) >= 2 else 0
R = {k: re.compile(v) for k, v in dict(
    lib=r'librar|लाइब्रेरी', hol=r'holiday|chhutti|chuti|vacation|छुट्ट|\bholi\b|christmas|dussehra|deepawali|raksha|independence|republic|gandhi|\beid\b|id-ul|moharram|janmashtmi|shivratri|ambedkar|buddha|guru nanak|new year',
    cal=r'exam|calendar|sessional|\bcia\b|admit|result|\btest\b|परीक्षा|एग्जाम|रिजल्ट|एडमिट', co=r'coordinator|कोऑर्डिनेटर|कोआर्डिनेटर',
    sy=r'syllabus|topics|modules?|units?|experiments?|सिलेबस|पाठ्यक्रम', fc=r'teacher|faculty|who teach|kaun padh|kaun sir|kaun madam|professor|शिक्षक',
    mp=r'\bwing|\bhod\b|office|floor|building|where is lab|lab kaha|\blabs\b|rooms?\s+(kaha|where)', ev=r'event|hackathon|\bfees?\b|sports|competition|contest|fest|notice|workshop|seminar|announce|इवेंट|प्रतियोगिता',
    tt=r'today|\baaj\b|tomorrow|\bkal\b|timetable|time table|schedule|\b(mon|tues?|wed(nes)?|thu(rs)?|fri|sat(ur)?|sun)(day)?\b|आज|कल', cl=r'class|room|kaha|kahan|where|abhi|\bnow\b|lecture|next|agli|agla|कहाँ|कहां|क्लास|अभी').items()}
CRS = [(r'microprocessor|\bmai\b|8085|8086', 'Microprocessor'), (r'network|\bcn\b', 'Networks'), (r'automata|atafl|\btoc\b|formal', 'Automata'), (r'graphics|\bcg\b', 'Graphics'),
       (r'econom|\beme\b', 'Economics'), (r'constitution|\bic\b', 'Constitution'), (r'indian|eikt|essence|\bikt\b', 'Indian'), (r'\bjava\b|\bcaj\b', 'Java'),
       (r'data struct|\bdsuc\b', 'Data Structure'), (r'digital|\bdld\b', 'Digital Logic'), (r'discrete', 'Discrete'), (r'organi|\bob\b', 'Organizational'), (r'complex|\bcait\b', 'Computerlex')]
crs = lambda s: next((k for p, k in CRS if re.search(p, s)), None)
tk = lambda s: [w for w in re.split(r'[^a-z\u0900-\u097F0-9]+', s.lower()) if len(w) > 3]

def kbm(s):                          # answers the admin "taught" the assistant
    a, best, sc = tk(s), None, 0
    for k in q('select q,a from ques where a is not null'):
        w = tk(k['q'])
        r = len([x for x in w if x in a]) / len(w) if w else 0
        if r > sc: best, sc = k, r
    return best['a'] if best and sc >= .6 else None

def cal_reply(s, t):
    td = now().strftime('%Y-%m-%d')
    up = [r for r in CAL if r['s'] is None or (r['e'] or r['s']) >= td]
    def pick(rows, *k): return [r for r in rows if any(x in r['n'].lower() for x in k)]
    if re.search(r'admit|एडमिट', s): keys = ('admit',)
    elif re.search(r'result|रिजल्ट', s): keys = ('result',)
    elif re.search(r'sessional|\bcia\b|\btest\b', s): keys = ('sessional',)
    elif 'even' in s: keys = ('even semester',)
    elif re.search(r'\bform\b', s): keys = ('examination form',)
    elif re.search(r'odd|semester|university|theory|practical|यूनिवर्सिटी', s) and re.search(r'exam|परीक्षा|एग्जाम', s): keys = ('sessional', 'university odd')
    else: keys = None                # plain "exam kab hai" / "calendar": full upcoming list
    sel, head = (up, t('cal')) if not keys else (pick(up, *keys), t('cal'))
    if keys and not sel: sel, head = pick(CAL, *keys), t('past')
    def line(r):
        d = f"{fd(r['s'])}" + (f" → {fd(r['e'])}" if r['e'] else '') if r['s'] else r['raw']
        on = ' (ongoing)' if r['s'] and r['e'] and r['s'] <= td <= r['e'] else ''
        return f"• {r['n']} — {d}{on}"
    return head + '\n' + '\n'.join(line(r) for r in sel)

DH = {'Mon': 'सोमवार', 'Tue': 'मंगलवार', 'Wed': 'बुधवार', 'Thu': 'गुरुवार', 'Fri': 'शुक्रवार', 'Sat': 'शनिवार', 'Sun': 'रविवार'}

def answer(raw, u):
    L = lang(raw); s = raw.lower().replace('diwali', 'deepawali'); td = now().strftime('%Y-%m-%d')
    t = lambda k, **o: T[k][L].format(**{**o, **({x: DH.get(o[x], o[x]) for x in ('d', 'n') if L == 2 and x in o and o[x] in DH})})
    def unk(k='unk', **o):
        if not one('select 1 x from ques where q=? and email=? and a is null', raw, u['email']):
            run('insert into ques(email,who,q,ts) values(?,?,?,?)', u['email'], f"{u['name']} · {u['section'] or u['role']}", raw, now().timestamp())
        return t(k, **o)
    kb = kbm(s)
    if kb: return kb, L
    if re.match(r'\s*(hi+|hello|hey|namaste|namaskar)\b|\s*नमस्ते', s): return t('hi'), L
    if re.search(r'\b(thanks?|thank you|thx|shukriya|dhanyavad)\b|धन्यवाद|शुक्रिया', s): return t('thx'), L
    if re.search(r'who are you|what can you do|help me|tum kaun|aap kaun|kya kar sakti|तुम कौन|आप कौन', s): return t('who'), L
    if re.search(r'what(?:.s| is) the (time|date)|kitne baje|time kya|aaj ki tarikh|आज की तारीख', s): return t('tm', x=now().strftime('%a, %d %b %Y, %I:%M %p')), L
    if R['lib'].search(s):
        rows = [f"• {d}: {tl(b['i'])}–{tl(b['end'] + 1)}" for d in DAYS for b in blocks(slots(u, d)) if b['k'] == 'LIB']
        return ((t('lib') + '\n' + '\n'.join(rows)) if rows and re.search(r'kab|when|time|timing|period|slot|कब', s) else unk()), L
    if R['hol'].search(s):
        m = [h for h in HOL if any(len(w) > 3 and w not in ('vacations', 'jayanti', 'purnima', 'friday') and re.search(r'\b' + w + r'\b', s) for w in re.split(r'[^a-z]+', h['n'].lower()))
             or ('eid' in s and h['n'].lower().startswith('id-'))]
        if not m: m = [h for h in HOL if (h['e'] or h['s']) >= td][:3]
        return t('hol') + '\n' + '\n'.join(f"• {h['n']} — {fd(h['s'])}" + (f" → {fd(h['e'])}" if h['e'] else '') for h in m), L
    if R['cal'].search(s): return cal_reply(s, t), L
    if R['co'].search(s):
        m = re.search(r'(cse\s*\(?\s*(?:ai|ccml|iotbc|aibc)\s*\)?|cs)\s*-?\s*([234])\s*-?\s*([a-l])\b', s)
        c = COORD.get(norm(m[1]) + m[2] + m[3].upper() if m else norm(u['section']))
        if not c: return unk(), L
        return t('coord', c=c['sec'], n=c['name'], m=c['mob']) + (' Office: Room 603, Wing A (6th floor).' if norm(c['sec']) == 'CS3H' else ''), L
    if R['sy'].search(s):
        k = crs(s)
        if not k: return t('pick'), L
        n = next((n for n in SYL if k.lower() in n.lower()), None)
        return (t('sy', s=n) + '\n' + SYL[n][:1500] + ('…' if len(SYL[n]) > 1500 else '') if n else unk()), L
    if R['fc'].search(s):
        k, lab = crs(s), bool(re.search(r'lab|practical', s))
        cs = [c for c in courses(u) if k and k.lower() in c['name'].lower()]
        c = next((c for c in cs if c['name'].endswith('Lab') == lab), cs[0] if cs else None)
        return (t('fac', s=c['name'], f=c['f']) if c else unk()), L
    if R['mp'].search(s): return t('map'), L
    if R['ev'].search(s):
        if u['role'] == 'faculty': return t('fev'), L
        ev = q('select * from events where d>=? order by d', td); nt = q("select title from docs where cat='notice' and pub=1 order by ts desc limit 5")
        if not ev and not nt: return unk(), L
        rows = [f"• [{e['k']}] {e['title']} — {fd(e['d'])}" + (f", {e['tm']}" if e['tm'] else '') + (f"\n   {e['x']}" if e['x'] else '') for e in ev] + [f"• [Notice] {n['title']}" for n in nt]
        return t('ev') + '\n' + '\n'.join(rows), L
    n = now(); wd = n.strftime('%a')
    if R['tt'].search(s):
        W = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']; m = re.search(r'\b(mon|tues?|wed(?:nes)?|thu(?:rs)?|fri|sat(?:ur)?|sun)(?:day)?\b', s); d = wd
        if m: d = next(x for x in W if x.lower() == m[1][:3])
        elif re.search(r'tomorrow|\bkal\b|कल', s): d = W[(W.index(wd) + 1) % 7]
        pre = ''
        if d not in DAYS:
            nd = 'Mon'; pre = t('wknd', d=d, n=nd) + '\n'; d = nd
        sl = slots(u, d)
        if sl is None: return unk('nots', c=u['section']), L
        bl = blocks(sl)
        return pre + (t('sched', d=d) + '\n' + '\n'.join(f"• {tl(b['i'])}–{tl(b['end'] + 1)}: " + ('Library' if b['k'] == 'LIB' else f"{b['s']} ({b['f']}) · {place(b['r'], b.get('sec') or u['section'], d, b['i'])}") for b in bl) if bl else t('free', d=d)), L
    if R['cl'].search(s):
        sl = slots(u, wd) if wd in DAYS else [[]] * 8
        if sl is None: return unk('nots', c=u['section']), L
        i = (n.hour + 1 if n.minute >= 50 else n.hour) - 9
        o = lambda e, j: dict(s=e['s'] + (f" ({e['sec']})" if e.get('sec') else ''), f=e['f'], p=place(e['r'], e.get('sec') or u['section'], wd, j), t=tl(j))
        cur = next((e for e in sl[i] if e['k'] != 'LIB'), None) if 0 <= i < 8 else None
        want_next = bool(re.search(r'\bnext\b|agli|agla|अगली|अगला', s))
        if cur and n.minute >= 50: return t('next', **o(cur, i)), L          # last 10 min of the hour: the next class is about to start
        if cur and not want_next: return t('now', **o(cur, i)), L
        for j in range(max(i + 1, 0), 8):
            e = next((e for e in sl[j] if e['k'] != 'LIB'), None)
            if e and not (cur and e['k'] == cur['k'] and e.get('r') == cur.get('r')): return t('next', **o(e, j)), L
        return t('none'), L
    return unk(), L


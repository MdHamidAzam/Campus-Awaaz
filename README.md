# Campus Awaaz

```
campus-awaaz/
├── backend/                  FastAPI + SQLite
│   ├── app/
│   │   ├── main.py           app start, routers jodta hai, class-reminder loop chalata hai
│   │   ├── config.py         saari settings (.env se)
│   │   ├── admin_accounts.py ★ 3 FIXED admin email/password yahan hain
│   │   ├── database.py       SQLite schema + admin sync
│   │   ├── core/security.py  password hash, session, role guards, login throttle
│   │   ├── routers/          auth · assistant · campus (events/docs/complaints) · admin · voice
│   │   └── services/         chat_engine · timetable · notifications · elevenlabs
│   ├── data/  docs/  source_docs/   college ka data
│   ├── scripts/              build_data.py · show_db.py · test_email.py
│   ├── storage/campus.db     ★ DATABASE (backend pehli baar chalne par ban jaata hai)
│   ├── .env.example  requirements.txt
└── frontend/                 plain HTML/CSS/JS (ES modules, build ki zarurat nahi)
    ├── index.html  css/style.css
    └── js/  main.js · config.js · core/ · services/ · pages/
```

## Run
```
cd backend
python -m venv venv && venv\Scripts\activate      (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env                            (Mac/Linux: cp .env.example .env)   -> .env me keys bharo
uvicorn app.main:app --reload
```
Browser: http://localhost:8000  (backend `../frontend` ko khud serve karta hai).
Frontend alag host karna ho to `frontend/js/config.js` me `API_BASE` backend URL kar do aur backend `.env` me `CORS_ORIGINS` set karo.

## Database kaha hai?
`backend/storage/campus.db` (SQLite, ek file). Tables: users, sess, notes, events, docs, compl, ques, rooms, fired.
Dekhne ke liye: `python scripts/show_db.py` ya `python scripts/show_db.py users`
(ya "DB Browser for SQLite" app se `campus.db` kholo). File tabhi dikhegi jab backend ek baar start ho chuka ho.
Deploy (Render/Railway) par disk temporary hoti hai -> persistent disk lagao aur `DATABASE_PATH` set karo, warna restart par data jaata hai.

## Admin email / password badalna
`backend/app/admin_accounts.py` kholo, `email` / `password` badlo, save karo, backend restart karo. Bas.
Purana login band, naya chalu (purane session logout). Kisi admin ki line hata do to wo admin delete ho jaata hai.
Naya admin = list me ek aur dict add karo.

## ElevenLabs
`backend/.env` me `ELEVENLABS_API_KEY` daalo. Key sirf backend me rehti hai, browser tak nahi jaati.
- `POST /api/voice/tts`  -> jawab ki awaaz (Assistant 1-4)
- `POST /api/voice/stt`  -> mic recording -> text (language auto-detect)
Voices badalni ho to `.env` me `ELEVENLABS_VOICE_1..4` (voice ids).

## Email notifications
`.env` me SMTP_* bharo (Gmail App Password). Test: `python scripts/test_email.py tumhari@email.com`
Class reminder kitne minute pehle jaye: `CLASS_REMINDER_MINUTES` (default 10, 0 = theek class ke time).

## Demo mode (hackathon)
`DEMO_MODE=1` (default) creates a demo student (CS-3H) so judges can click "Try the demo student" on the login page. Set `DEMO_MODE=0` in `.env` to switch it off.
`docs/official/Student_List_*.docx` is NOT shown to students (it contains names + roll numbers); admins can still see it under Documents.

## Voice setup (ElevenLabs)
Create a key at https://elevenlabs.io/app/settings/api-keys and paste it in `backend/.env` as `ELEVENLABS_API_KEY=...`, then restart the backend.
In the assistant, pick "I speak: English / हिंदी" for the most accurate transcription. The assistant always speaks its replies aloud (Stop button next to it).

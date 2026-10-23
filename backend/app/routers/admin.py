"""Admin-only endpoints (the 3 fixed admins)."""
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from ..config import DOCS_DIR
from ..core.security import admin_only
from ..database import q, one, run, now
from ..services.notifications import notify
from datetime import date
from ..services.timetable import fd, tl, TT, TTN, norm
from .assistant import Txt

router = APIRouter(prefix="/admin")
class Ev(BaseModel): k: str = "Event"; title: str; d: str; tm: str = ""; x: str = ""
class Room(BaseModel): f: str; t: str; n: str = ""; sec: str = ""; dt: str = ""; s0: int = 0; s1: int = 7


@router.get("/queries")
def queries(u=Depends(admin_only)): return q("select * from ques where a is null order by id desc")


@router.post("/queries/{i}")
def answer_query(i: int, b: Txt, u=Depends(admin_only)):
    x = one("select * from ques where id=?", i)
    if not x or not b.t.strip(): raise HTTPException(400, "Nothing to answer")
    run("update ques set a=? where id=?", b.t.strip(), i)
    notify("em:" + x["email"], "Admin answered your query", f"{x['q']} -> {b.t.strip()}"); return {}


@router.post("/complaints/{i}")
def resolve(i: int, b: Txt, u=Depends(admin_only)):
    x = one("select * from compl where id=?", i)
    if not x or not b.t.strip(): raise HTTPException(400, "Write a response")
    run("update compl set r=? where id=?", b.t.strip(), i); notify("em:" + x["email"], "Complaint resolved", b.t.strip()); return {}


@router.post("/events")
def add_event(b: Ev, u=Depends(admin_only)):
    run("insert into events(k,title,d,tm,x) values(?,?,?,?,?)", b.k, b.title.strip(), b.d, b.tm, b.x)
    notify("students", f"New {b.k}: {b.title}", fd(b.d) + (f", {b.tm}" if b.tm else "") + (f" - {b.x}" if b.x else "")); return {}


@router.post("/upload")                                          # step 1: upload (stays hidden)
async def upload(file: UploadFile = File(...), title: str = Form(""), u=Depends(admin_only)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".pdf", ".docx", ".xlsx", ".jpg", ".jpeg"}: raise HTTPException(400, "Allowed: pdf, docx, xlsx, jpg, jpeg")
    data = await file.read()
    if len(data) > 15 * 2 ** 20: raise HTTPException(400, "Max file size is 15 MB")
    (DOCS_DIR / "notices").mkdir(parents=True, exist_ok=True)
    fn = f"notices/{uuid.uuid4().hex}{ext}"; (DOCS_DIR / fn).write_bytes(data)
    run("insert into docs(title,fn,cat,pub,ts) values(?,?,?,?,?)", title.strip() or Path(file.filename).stem, fn, "notice", 0, now().timestamp()); return {}


@router.post("/docs/{i}/publish")                                # step 2: publish -> students see it + notification + email
def publish(i: int, u=Depends(admin_only)):
    d = one("select * from docs where id=?", i)
    if not d: raise HTTPException(404, "Not found")
    run("update docs set pub=1 where id=?", i)
    notify("students", "New notice: " + d["title"], "Open Events & Notices on your dashboard to view or download it."); return {}


@router.post("/rooms")
def add_room(b: Room, u=Depends(admin_only)):
    f, t = b.f.strip(), b.t.strip()
    if not f or not t: raise HTTPException(400, "Enter the engaged room and the alternative room")
    if not b.dt: raise HTTPException(400, "Choose the date of the change")
    try: dd = date.fromisoformat(b.dt)
    except ValueError: raise HTTPException(400, "Invalid date")
    if not (0 <= b.s0 <= b.s1 <= 7): raise HTTPException(400, "Choose a valid time range")
    sec = b.sec.strip()
    run("insert into rooms(f,t,sec,dt,s0,s1,n) values(?,?,?,?,?,?,?)", f, t, sec, b.dt, b.s0, b.s1, b.n.strip())
    when = f"{fd(b.dt)}, {tl(b.s0)} - {tl(b.s1 + 1)}"
    body = f"{sec or 'All sections'} · {when}: Room {f} is engaged{' (' + b.n.strip() + ')' if b.n.strip() else ''}. Please go to {t}."
    notify(("sec:" + sec) if sec else "all", f"Room change: {f} → {t}", body)
    if sec:                                                     # the teachers taking that class get told too
        day = dd.strftime("%a"); tt = TTN.get(norm(sec))
        for f_ in {e["f"] for i, e in enumerate((tt or {"slots": {}})["slots"].get(day, [])) if e and e.get("f") and b.s0 <= i <= b.s1 and e.get("r") == f}:
            notify("fac:" + f_, f"Room change: {f} → {t}", body)
    return {}


@router.get("/rooms")
def rooms(u=Depends(admin_only)):
    run("delete from rooms where dt is not null and dt != '' and dt < ?", now().strftime("%Y-%m-%d"))      # expired changes clean themselves up
    return q("select * from rooms order by dt, s0")


@router.get("/room-lookup")                                     # fills in "engaged room" from the timetable
def room_lookup(sec: str, dt: str, slot: int, u=Depends(admin_only)):
    try: day = date.fromisoformat(dt).strftime("%a")
    except ValueError: return {"room": "", "subject": ""}
    tt = TTN.get(norm(sec)); sl = (tt["slots"].get(day, []) if tt else []); e = sl[slot] if 0 <= slot < len(sl) else None
    return {"room": (e or {}).get("r", ""), "subject": (e or {}).get("s", "")}


@router.delete("/{kind}/{i}")
def delete(kind: str, i: int, u=Depends(admin_only)):
    if kind not in ("events", "docs", "rooms"): raise HTTPException(404, "Unknown")
    if kind == "docs":
        d = one("select * from docs where id=?", i)
        if d and d["cat"] == "notice": (DOCS_DIR / d["fn"]).unlink(missing_ok=True)
    run(f"delete from {kind} where id=?", i); return {}


@router.get("/stats")
def stats(u=Depends(admin_only)):
    c = lambda sql: one(sql)["c"]
    return {"students": c("select count(*) c from users where role='student'"), "faculty": c("select count(*) c from users where role='faculty'"),
            "pending_q": c("select count(*) c from ques where a is null"), "taught": c("select count(*) c from ques where a is not null"),
            "open_c": c("select count(*) c from compl where r is null"), "resolved_c": c("select count(*) c from compl where r is not null"),
            "notices": c("select count(*) c from docs where cat='notice' and pub=1"), "drafts": c("select count(*) c from docs where cat='notice' and pub=0"),
            "reminders": c("select count(*) c from fired"), "alerts": c("select count(*) c from notes")}

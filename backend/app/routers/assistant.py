"""Assistant chat + today's timetable + notifications list (student & faculty)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..core.security import current_user, roles
from ..database import q, one, run, now
from ..services.chat_engine import answer
from ..services.notifications import match
from ..services.timetable import slots, blocks, place, tl, TT, CAL, HOL, same
from ..config import DAYS

router = APIRouter()
class Txt(BaseModel): t: str


@router.post("/chat")
def chat(b: Txt, u=Depends(roles("student", "faculty"))):
    a, L = answer(b.t.strip()[:300], u); return {"a": a, "lang": L}          # lang: 0 English, 1 Hinglish, 2 Hindi


@router.get("/today")
def today(u=Depends(roles("student", "faculty"))):
    n = now(); d = n.strftime("%a"); sl = slots(u, d) if d in DAYS else [[]] * 8
    if sl is None: return {"day": d, "blocks": None}
    if u["role"] == "faculty" and not any(e and e.get("f") and same(u["name"], e["f"]) for t in TT.values() for dd in t["slots"].values() for e in dd):
        return {"day": d, "blocks": None, "faculty_unmatched": True}
    return {"day": d, "blocks": [{"t": f"{tl(b['i'])} - {tl(b['end'] + 1)}", "s": "Library" if b["k"] == "LIB" else b["s"], "f": b.get("f", ""),
                                   "p": place(b["r"], b.get("sec") or u["section"], d, b["i"]) if b.get("r") else "", "sec": b.get("sec", ""), "on": b["i"] <= n.hour - 9 <= b["end"], "i": b["i"], "end": b["end"]} for b in blocks(sl)]}


@router.get("/notes")
def notes(u=Depends(roles("student", "faculty"))):
    return {"seen": u["seen"], "items": [n for n in q("select * from notes order by id desc limit 300") if match(u, n["to_"])][:60]}


@router.post("/notes/seen")
def seen(u=Depends(roles("student", "faculty"))):
    run("update users set seen=? where email=?", now().timestamp(), u["email"]); return {}


@router.get("/overview")
def overview(u=Depends(roles("student", "faculty"))):
    """Countdown cards for the dashboard: next holiday + next academic milestone."""
    td = now().strftime("%Y-%m-%d"); today = now().date()
    from datetime import date
    days = lambda s: (date.fromisoformat(s) - today).days
    hol = next(({"n": h["n"], "d": h["s"], "in": days(h["s"])} for h in sorted(HOL, key=lambda h: h["s"]) if (h["e"] or h["s"]) >= td), None)
    ms = next(({"n": c["n"], "d": c["s"], "in": days(c["s"])} for c in CAL if c["s"] and (c["e"] or c["s"]) >= td), None)
    notices = one("select count(*) c from docs where cat='notice' and pub=1")["c"] if True else 0
    return {"holiday": hol, "milestone": ms, "notices": notices}

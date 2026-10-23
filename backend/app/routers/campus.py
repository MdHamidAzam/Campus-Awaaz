"""Events, documents and complaints - students (and admin). Faculty accounts get 403 here."""
import re
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from ..config import DOCS_DIR
from ..core.security import roles, student_or_admin
from ..database import q, one, run, now
from .assistant import Txt

router = APIRouter()


@router.get("/events")
def events(u=Depends(student_or_admin)): return q("select * from events where d>=? order by d", now().strftime("%Y-%m-%d"))


@router.get("/docs")
def docs(u=Depends(student_or_admin)):
    rows = q("select * from docs order by ts desc" if u["role"] == "admin" else "select * from docs where pub=1 order by ts desc")
    return [{**r, "ext": Path(r["fn"]).suffix[1:].lower()} for r in rows]


@router.get("/docs/{i}/file")                                   # view / download (token via ?t=)
def doc_file(i: int, dl: int = 0, u=Depends(student_or_admin)):
    d = one("select * from docs where id=?", i)
    if not d or (not d["pub"] and u["role"] != "admin"): raise HTTPException(404, "Not found")
    p = DOCS_DIR / d["fn"]
    if not p.exists(): raise HTTPException(404, "File missing")
    return FileResponse(p, filename=re.sub(r"[^\w\- ]", "", d["title"]) + p.suffix,
                        content_disposition_type="attachment" if dl or p.suffix in (".docx", ".xlsx") else "inline")


@router.post("/complaints")
def complain(b: Txt, u=Depends(roles("student"))):
    if not b.t.strip(): raise HTTPException(400, "Write your complaint first")
    run("insert into compl(email,who,t,ts) values(?,?,?,?)", u["email"], f"{u['name']} - {u['section'] or u['role']}", b.t.strip(), now().timestamp()); return {}


@router.get("/complaints")
def complaints(u=Depends(student_or_admin)):
    return q("select * from compl order by id desc") if u["role"] == "admin" else q("select * from compl where email=? order by id desc", u["email"])

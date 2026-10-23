"""Login / signup. Admins are fixed (see app/admin_accounts.py) - there is NO admin signup."""
import re, secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from ..admin_accounts import ADMIN_ACCOUNTS
from ..core.security import hpw, new_salt, new_session, current_user, throttled, record_fail, clear_fails
from ..database import one, run, now, clean_pw
from ..services.timetable import COORD, TTN, norm, nm

router = APIRouter()
ADMIN_EMAILS = {a["email"].strip().lower() for a in ADMIN_ACCOUNTS}


class Signup(BaseModel): name: str; email: str; password: str; role: str = "student"; roll: str = ""; section: str = ""
class Login(BaseModel): email: str; password: str; role: str = ""


@router.get("/meta")
def meta(): return {"sections": [{"sec": c["sec"], "tt": norm(c["sec"]) in TTN} for c in COORD.values()]}


@router.post("/signup")
def signup(b: Signup):
    em = b.email.strip().lower()
    if b.role not in ("student", "faculty"): raise HTTPException(400, "Signup is only for students and faculty")
    if em in ADMIN_EMAILS: raise HTTPException(403, "This email is reserved. Please use the Admin login.")
    if not re.match(r"[^@\s]+@[^@\s]+\.\w+$", em) or len(b.password) < 6: raise HTTPException(400, "Enter a valid email and a password of at least 6 characters")
    if b.role == "student" and not (b.roll.strip() and b.section): raise HTTPException(400, "Roll number and section are required")
    if b.role == "faculty" and len(nm(b.name)) < 2: raise HTTPException(400, "Enter your full name as in the timetable")
    if one("select 1 x from users where email=?", em): raise HTTPException(409, "Already registered. Please login.")
    salt = new_salt()
    run("insert into users(email,name,role,roll,section,salt,h,created) values(?,?,?,?,?,?,?,?)",
        em, b.name.strip(), b.role, b.roll.strip(), b.section if b.role == "student" else "", salt, hpw(b.password, salt), now().timestamp())
    return new_session(em)


@router.post("/login")
def login(b: Login, request: Request):
    em = b.email.strip().lower(); key = f"{em}|{request.client.host if request.client else ''}"
    if throttled(key): raise HTTPException(429, "Too many wrong attempts. Please wait 10 minutes and try again.")
    u = one("select * from users where email=?", em)
    pw = clean_pw(b.password) if u and u["role"] == "admin" else b.password          # admin passwords may be typed with spaces
    if not u or not secrets.compare_digest(hpw(pw, u["salt"]), u["h"]):
        record_fail(key); raise HTTPException(401, "Wrong email or password")
    if b.role and b.role != u["role"]: raise HTTPException(403, f"This is a {u['role']} account. Please choose the {u['role'].capitalize()} tab to login.")
    clear_fails(key)
    return new_session(u["email"])


@router.post("/logout")
def logout(request: Request, u=Depends(current_user)):
    run("delete from sess where token=?", request.headers.get("x-token")); return {}


@router.get("/me")
def whoami(u=Depends(current_user)): return {k: u[k] for k in ("name", "email", "role", "section")}

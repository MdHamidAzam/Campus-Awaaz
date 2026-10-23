"""Notifications: dashboard (notes table) + email, and the class-reminder scheduler."""
import re, smtplib, threading
from datetime import timedelta
from email.message import EmailMessage
from ..config import DAYS, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM, CLASS_REMINDER_MINUTES
from ..database import q, one, run, now
from .timetable import TT, norm, same, place, tl


def match(u, to):
    """Does notification target `to` belong to user u?
    targets: all (students+faculty) | students | sec:<section> | fac:<name> | em:<email>"""
    k, _, v = to.partition(":")
    if u["role"] == "admin": return k == "em" and u["email"] == v
    return (to == "all") or (to == "students" and u["role"] == "student") or (k == "em" and u["email"] == v) \
        or (k == "sec" and u["role"] == "student" and norm(u["section"]) == norm(v)) \
        or (k == "fac" and u["role"] == "faculty" and same(u["name"], v))


def send_mail(to, subject, body):
    if not SMTP_HOST or not SMTP_USER:
        print(f"[email not configured - set SMTP_* in backend/.env] to={to} | {subject}")
        return False
    m = EmailMessage(); m["From"] = SMTP_FROM; m["To"] = to; m["Subject"] = subject; m.set_content(body)
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
            s.starttls(); s.login(SMTP_USER, SMTP_PASS); s.send_message(m)
        return True
    except Exception as e:
        print("email error:", to, e)
        return False


def notify(to, title, body):
    """Save a dashboard notification and email every matching user (in a background thread)."""
    rc = [u["email"] for u in q("select * from users") if match(u, to)]
    if not rc: return
    run("insert into notes(to_,title,body,ts) values(?,?,?,?)", to, title, body, now().timestamp())
    subject = re.sub(r"[^\w\s:,.()/&!?'\"\u0900-\u097F-]", "", title).strip()          # no emoji in email subjects
    threading.Thread(target=lambda: [send_mail(m, f"Campus Awaaz: {subject}", f"{body}\n\n- Campus Awaaz") for m in rc], daemon=True).start()


def check_class_reminders():
    """Called every 30s. For each class starting within CLASS_REMINDER_MINUTES, notify that section's
    students and the teacher (dashboard + email), once per class."""
    n = now(); d = n.strftime("%a")
    if d not in DAYS: return
    for i in range(8):                                   # slot i starts at (9 + i):00
        start = n.replace(hour=9 + i, minute=0, second=0, microsecond=0)
        if not (start - timedelta(minutes=CLASS_REMINDER_MINUTES) <= n < start + timedelta(minutes=2)): continue
        for sec, t in TT.items():
            sl = t["slots"].get(d, []); e = sl[i] if i < len(sl) else None; p = sl[i - 1] if i and i - 1 < len(sl) else None
            if not e or e["k"] == "LIB" or (p and p["k"] == e["k"] and p.get("r") == e.get("r")): continue   # free / library / 2nd hour of a lab
            key = f"{n:%Y-%m-%d}-{sec}-{i}"
            if one("select 1 x from fired where k=?", key): continue
            run("insert into fired values(?)", key)
            when, where = tl(i), place(e["r"], sec, d, i)
            notify("sec:" + sec, f"Class at {when}: {e['s']}", f"Your {e['s']} class with {e['f']} starts at {when} - {where}.")
            if e["f"]: notify("fac:" + e["f"], f"Class at {when}: {e['s']} ({sec})", f"You have {e['s']} with {sec} at {when} - {where}.")

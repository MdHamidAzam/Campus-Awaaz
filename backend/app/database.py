"""SQLite access + schema + start-up seeding (including the fixed admin accounts)."""
import re, sqlite3
from contextlib import closing
from datetime import datetime
from .config import DB_PATH, DOCS_DIR, IST, DEMO_MODE
from .admin_accounts import ADMIN_ACCOUNTS

now = lambda: datetime.now(IST)

SCHEMA = """
create table if not exists users(email text primary key, name, role, roll, section, salt, h, seen real default 0, created real);
create table if not exists sess(token text primary key, email, exp real);
create table if not exists notes(id integer primary key autoincrement, to_ text, title, body, ts real);
create table if not exists events(id integer primary key autoincrement, k, title, d, tm, x);
create table if not exists docs(id integer primary key autoincrement, title, fn, cat, pub integer, ts real);
create table if not exists compl(id integer primary key autoincrement, email, who, t, r, ts real);
create table if not exists ques(id integer primary key autoincrement, email, who, q, a, ts real);
create table if not exists rooms(id integer primary key autoincrement, f, t, sec, dt, s0 integer, s1 integer, n);
create table if not exists fired(k text primary key);
"""


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute("pragma journal_mode=wal")
    return c


def run(sql, *a):
    with closing(_connect()) as c:
        cur = c.execute(sql, a); rows = [dict(r) for r in cur.fetchall()]; c.commit()
        return rows, cur.lastrowid


q = lambda sql, *a: run(sql, *a)[0]
one = lambda sql, *a: (q(sql, *a) or [None])[0]


def _ensure_column(table, col):               # lets an older campus.db keep working
    if col not in [r["name"] for r in q(f"pragma table_info({table})")]:
        run(f"alter table {table} add column {col}")


def clean_pw(pw): return re.sub(r"\s+", "", pw or "")      # admin passwords are compared without spaces


def sync_admins():
    """Make the users table match admin_accounts.py exactly."""
    from .core.security import hpw, new_salt              # local import avoids a circular import
    wanted = {}
    for a in ADMIN_ACCOUNTS:
        wanted[a["email"].strip().lower()] = a
    for em, a in wanted.items():
        u = one("select * from users where email=?", em); pw = clean_pw(a["password"])
        if u and u["role"] == "admin" and hpw(pw, u["salt"]) == u["h"]:
            if u["name"] != a["name"]: run("update users set name=? where email=?", a["name"], em)
            continue
        salt = new_salt()
        if u:
            run("update users set name=?, role='admin', roll='', section='', salt=?, h=? where email=?", a["name"], salt, hpw(pw, salt), em)
            run("delete from sess where email=?", em)           # password changed -> force re-login
        else:
            run("insert into users(email,name,role,roll,section,salt,h,created) values(?,?,?,?,?,?,?,?)", em, a["name"], "admin", "", "", salt, hpw(pw, salt), now().timestamp())
    for u in q("select email from users where role='admin'"):   # admins removed from the list are deleted
        if u["email"] not in wanted:
            run("delete from users where email=?", u["email"]); run("delete from sess where email=?", u["email"])


def init_db():
    with closing(_connect()) as c: c.executescript(SCHEMA)
    _ensure_column("users", "created"); _ensure_column("sess", "exp")
    for col in ("sec", "dt", "s0", "s1", "n"): _ensure_column("rooms", col)      # older campus.db files get the new room-change columns
    for p in sorted((DOCS_DIR / "official").glob("*.docx")):
        if not one("select 1 x from docs where fn=?", f"official/{p.name}"):
            private = "student_list" in p.name.lower()           # contains names + roll numbers -> never auto-publish
            run("insert into docs(title,fn,cat,pub,ts) values(?,?,?,?,?)", p.stem.replace("_", " "), f"official/{p.name}", "official", 0 if private else 1, now().timestamp())
    run("update docs set pub=0 where lower(fn) like '%student_list%' and cat='official'")
    if not q("select 1 x from events limit 1"):
        run("insert into events(k,title,d,tm,x) values(?,?,?,?,?)", "Event", "Hacktoberfest Hack Day (MLH x ReImagine(IT))", "2026-10-23", "10:00 AM - 5:00 PM", "Stepper Hall, 2nd Floor, Room 207, BBDITM")
    sync_admins()
    if DEMO_MODE and not one("select 1 x from users where email=?", "demo@campusawaaz.app"):
        from .core.security import hpw, new_salt
        salt = new_salt()
        run("insert into users(email,name,role,roll,section,salt,h,created) values(?,?,?,?,?,?,?,?)", "demo@campusawaaz.app", "Demo Student", "student", "DEMO", "CS3H", salt, hpw("demo1234", salt), now().timestamp())

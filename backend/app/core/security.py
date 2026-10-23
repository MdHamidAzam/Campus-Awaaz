"""Password hashing, sessions, login throttling and role guards."""
import hashlib, secrets, time
from collections import defaultdict
from fastapi import Depends, HTTPException, Request
from ..config import SESSION_DAYS
from ..database import one, run, now


def new_salt(): return secrets.token_hex(16)
def hpw(pw, salt): return hashlib.scrypt(pw.encode(), salt=bytes.fromhex(salt), n=2 ** 14, r=8, p=1).hex()


def new_session(email):
    t = secrets.token_urlsafe(32)
    run("delete from sess where exp < ?", now().timestamp())
    run("insert into sess(token,email,exp) values(?,?,?)", t, email, now().timestamp() + SESSION_DAYS * 86400)
    return {"token": t}


def current_user(request: Request):
    t = request.headers.get("x-token") or request.query_params.get("t")
    u = one("select u.* from users u join sess s on s.email=u.email where s.token=? and (s.exp is null or s.exp>?)", t, now().timestamp())
    if not u: raise HTTPException(401, "Please login again")
    return u


def roles(*allowed):                       # dependency factory: Depends(roles("admin")) etc.
    def dep(u=Depends(current_user)):
        if u["role"] not in allowed: raise HTTPException(403, "This section is not available for your account")
        return u
    return dep


admin_only = roles("admin")
student_or_admin = roles("student", "admin")        # faculty have no events / documents / complaints


# ---- tiny in-memory brute-force guard: 6 wrong passwords -> 10 minute pause for that email
_fails = defaultdict(list)
def throttled(key):
    _fails[key] = [t for t in _fails[key] if time.time() - t < 600]
    return len(_fails[key]) >= 6
def record_fail(key): _fails[key].append(time.time())
def clear_fails(key): _fails.pop(key, None)

"""Campus Awaaz backend.   Run from the backend/ folder:   uvicorn app.main:app --reload"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import CORS_ORIGINS, DOCS_DIR, FRONTEND_DIR
from .database import init_db
from .routers import auth, assistant, campus, admin, voice
from .services.notifications import check_class_reminders


async def reminder_loop():                       # class alerts: dashboard + email, once per class
    while True:
        try: await asyncio.to_thread(check_class_reminders)
        except Exception as ex: print("reminder error:", ex)
        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app):
    (DOCS_DIR / "notices").mkdir(parents=True, exist_ok=True)
    init_db()                                    # creates tables, seeds data, syncs the fixed admins
    task = asyncio.create_task(reminder_loop())
    yield
    task.cancel()


app = FastAPI(title="Campus Awaaz", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])
for r in (auth.router, assistant.router, campus.router, admin.router, voice.router):
    app.include_router(r, prefix="/api")

if FRONTEND_DIR.exists():                        # convenience: serve ../frontend too, so one command runs everything
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

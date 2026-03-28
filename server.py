"""
Scraperrr — FastAPI Backend
Serves articles via REST API and static dashboard.
"""

import json
import logging
import sys
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

# Ensure tools/ is importable
sys.path.insert(0, str(Path(__file__).parent / "tools"))
import run_scrapers

TMP_DIR = Path(__file__).parent / ".tmp"
CACHE_FILE = TMP_DIR / "articles_cache.json"
RUN_FILE = TMP_DIR / "last_run.json"
DASHBOARD_DIR = Path(__file__).parent / "dashboard"
CACHE_MAX_AGE_HOURS = 24

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger(__name__)

app = FastAPI(title="Scraperrr", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Mount static dashboard
app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _cache_is_stale() -> bool:
    if not RUN_FILE.exists():
        return True
    try:
        meta = json.loads(RUN_FILE.read_text())
        last_run = datetime.fromisoformat(meta["last_run"])
        age = datetime.now(timezone.utc) - last_run
        return age > timedelta(hours=CACHE_MAX_AGE_HOURS)
    except Exception:
        return True


def _read_cache() -> list[dict]:
    if not CACHE_FILE.exists():
        return []
    try:
        return json.loads(CACHE_FILE.read_text())
    except Exception:
        return []


def _read_run_meta() -> dict:
    if not RUN_FILE.exists():
        return {}
    try:
        return json.loads(RUN_FILE.read_text())
    except Exception:
        return {}


def _do_scrape():
    log.info("Starting scheduled scrape...")
    try:
        run_scrapers.run_all()
    except Exception as e:
        log.error("Scheduled scrape failed: %s", e, exc_info=True)


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def serve_dashboard():
    return FileResponse(str(DASHBOARD_DIR / "index.html"))


@app.get("/api/articles")
def get_articles(background_tasks: BackgroundTasks):
    """
    Return cached articles. If cache is stale (>24h), trigger a background refresh
    and return stale data immediately so the UI isn't blocked.
    """
    if _cache_is_stale():
        log.info("Cache stale — triggering background refresh")
        background_tasks.add_task(_do_scrape)

    articles = _read_cache()
    meta = _read_run_meta()

    return JSONResponse({
        "articles": articles,
        "fetched_at": meta.get("last_run", datetime.now(timezone.utc).isoformat()),
        "new_count": len(articles),
        "sources": meta.get("sources", {}),
        "cache_stale": _cache_is_stale(),
    })


@app.get("/api/articles/refresh")
def refresh_articles():
    """Force a fresh scrape synchronously and return new results."""
    log.info("Manual refresh triggered")
    try:
        result = run_scrapers.run_all()
        return JSONResponse(result)
    except Exception as e:
        log.error("Manual refresh failed: %s", e)
        return JSONResponse({"error": str(e), "articles": [], "new_count": 0}, status_code=500)


@app.get("/api/status")
def get_status():
    meta = _read_run_meta()
    return JSONResponse({
        "last_run": meta.get("last_run"),
        "sources": meta.get("sources", {}),
        "cache_stale": _cache_is_stale(),
        "article_count": len(_read_cache()),
    })


# ─── Scheduler & Lifespan ─────────────────────────────────────────────────────

scheduler = BackgroundScheduler()
scheduler.add_job(_do_scrape, "interval", hours=24, id="daily_scrape")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    TMP_DIR.mkdir(exist_ok=True)
    scheduler.start()
    if _cache_is_stale():
        log.info("Initial scrape on startup...")
        threading.Thread(target=_do_scrape, daemon=True).start()
    yield
    scheduler.shutdown()

app.router.lifespan_context = lifespan


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)

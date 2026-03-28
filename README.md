# scraperrr

A gorgeous, interactive AI news dashboard. Scrapes the latest articles from Ben's Bites, The AI Rundown, and Reddit every 24 hours and presents them in a beautiful dark UI.

## Stack

- **Backend** — Python 3.11 + FastAPI + APScheduler
- **Scrapers** — feedparser (RSS), Playwright (headless Chromium), requests (Reddit JSON API)
- **Frontend** — Vanilla HTML/CSS/JS (no build step)
- **Storage** — `.tmp/` JSON cache + browser `localStorage` for saved articles

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Run

```bash
python server.py
# → http://localhost:8000
```

On startup the server scrapes all sources and caches the results. Subsequent visits serve from cache. Cache auto-refreshes every 24 hours.

## Sources

| Source | Method |
|---|---|
| Ben's Bites | RSS feed via `feedparser` |
| The AI Rundown | Playwright headless browser (Beehiiv/JS-rendered) |
| Reddit | Public JSON API (`r/artificial`, `r/MachineLearning`, `r/singularity`) |

## API

| Endpoint | Description |
|---|---|
| `GET /` | Dashboard UI |
| `GET /api/articles` | Cached articles (triggers background refresh if stale) |
| `GET /api/articles/refresh` | Force fresh scrape, returns new results |
| `GET /api/status` | Cache status + source health |

## Phase 2 (coming)

Supabase integration for persistent article storage across sessions. Add credentials to `.env`:

```
SUPABASE_URL=...
SUPABASE_KEY=...
```

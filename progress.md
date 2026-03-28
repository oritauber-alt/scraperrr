# Progress Log

## 2026-03-28

### Completed
- Protocol 0: all project memory files initialized
- Research: Ben's Bites RSS confirmed, AI Rundown = Playwright, Reddit = JSON API
- Architecture SOPs written: scraper_sop.md, dashboard_sop.md
- Tools built and tested:
  - scrape_bens_bites.py — feedparser, verified working (0 articles in 24h as expected — latest post was 2 days ago)
  - scrape_ai_rundown.py — Playwright, 16 articles found
  - scrape_reddit.py — requests JSON API, 15 articles from 3 subreddits
  - run_scrapers.py — orchestrator, 31 total articles written to .tmp/articles_cache.json
- server.py (FastAPI) built and tested — /api/articles, /api/articles/refresh, /api/status all working
- Dashboard redesigned to brand guidelines:
  - Colors: #BFF549 lime / #0D0D0D bg
  - Fonts: Aspekta (headings), Inter (body), Geist Mono (mono)
  - Layout: fixed left sidebar + topbar + hero card + pills + card grid
  - UX inspiration applied: sidebar nav, hero featured article, source pills, card grid

### Test Results
- API /api/status: 31 articles, all 3 sources ok
- Ben's Bites: 0/24h (expected — last post was Thu Mar 26)
- AI Rundown: 16 articles
- Reddit: 15 articles (r/artificial: 19, r/MachineLearning: 9, r/singularity: 16 → top 15 by score)

### Errors / Fixes
- FastAPI on_event deprecation → migrated to asynccontextmanager lifespan
- Unused import warning → resolved

### Next (Phase 5)
- Supabase integration
- Cron deployment

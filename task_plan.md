# Task Plan

## Status: PHASE 1 COMPLETE → PHASE 2 IN PROGRESS

## Approved Blueprint
Build a Python FastAPI backend with scrapers for Ben's Bites, The AI Rundown, and Reddit.
Serve articles via a REST API. Frontend is a single-page dashboard with card layout,
source filters, saved articles, and 24-hour auto-refresh. Supabase added in Phase 2.

---

## Phases

### Phase 0: Initialization ✅
- [x] task_plan.md created
- [x] findings.md created
- [x] progress.md created
- [x] claude.md initialized
- [x] Discovery Questions answered
- [x] Data Schema defined

### Phase 1: Blueprint ✅
- [x] North Star defined
- [x] Integrations identified
- [x] Source of Truth confirmed
- [x] Delivery Payload defined
- [x] Behavioral Rules documented
- [x] JSON Data Schema approved

### Phase 2: Link (IN PROGRESS)
- [ ] Research target website structures
- [ ] Verify Reddit JSON API responds
- [ ] Build tool: scrape_bens_bites.py
- [ ] Build tool: scrape_ai_rundown.py
- [ ] Build tool: scrape_reddit.py
- [ ] Test each scraper independently

### Phase 3: Architect
- [ ] architecture/scraper_sop.md
- [ ] architecture/dashboard_sop.md
- [ ] server.py (FastAPI with /api/articles)
- [ ] dashboard/index.html
- [ ] dashboard/style.css
- [ ] dashboard/app.js

### Phase 4: Stylize
- [ ] Card layout with source badges
- [ ] Save/bookmark interaction
- [ ] Source filter tabs
- [ ] "New" article badge
- [ ] Dark/light mode toggle

### Phase 5: Trigger
- [ ] Cron schedule (24h)
- [ ] Supabase integration
- [ ] Production deployment

---

## Tech Stack
- **Backend**: Python 3.11 + FastAPI + BeautifulSoup4 + httpx
- **Frontend**: Vanilla HTML/CSS/JS (no build step)
- **Storage (Phase 1)**: .tmp/ JSON cache + localStorage
- **Storage (Phase 2)**: Supabase
- **Scheduler**: APScheduler (embedded in FastAPI)

# Project Constitution (claude.md)

> This file is law. Update only when: schema changes, a rule is added, or architecture is modified.

## Project Name
**Scraperrr** — AI Newsletter Intelligence Dashboard

## North Star
A gorgeous, interactive dashboard displaying the latest AI articles and newsletters from the last 24 hours, with persistent article saving across sessions.

---

## Data Schema

### Article Object (Core Unit)
```json
{
  "id": "<sha256 of url — stable dedup key>",
  "title": "string",
  "summary": "string",
  "url": "string",
  "source": "bens_bites | ai_rundown | reddit",
  "source_label": "Ben's Bites | The AI Rundown | Reddit",
  "published_at": "ISO8601 string",
  "scraped_at": "ISO8601 string",
  "image_url": "string | null",
  "tags": ["string"],
  "is_new": true
}
```

### Saved Articles (localStorage key: `scraperrr_saved`)
```json
{
  "<article_id>": {
    "saved_at": "ISO8601 string",
    "article": { /* Article Object */ }
  }
}
```

### Scrape Run Record (`.tmp/last_run.json`)
```json
{
  "last_run": "ISO8601 string",
  "article_ids_seen": ["<id>", "..."],
  "sources": {
    "bens_bites": { "status": "ok | error", "count": 0 },
    "ai_rundown": { "status": "ok | error", "count": 0 },
    "reddit": { "status": "ok | error", "count": 0 }
  }
}
```

### API Response (Backend → Frontend)
```json
{
  "articles": [ /* Article[] */ ],
  "fetched_at": "ISO8601 string",
  "new_count": 12,
  "sources": {
    "bens_bites": { "status": "ok", "count": 5 },
    "ai_rundown": { "status": "ok", "count": 4 },
    "reddit": { "status": "ok", "count": 3 }
  }
}
```

---

## Behavioral Rules

1. **24-Hour Filter**: Only return articles published within the last 24 hours. Discard older content silently.
2. **Deduplication**: Articles are deduplicated by `id` (sha256 of URL). Never show the same article twice.
3. **No Data = No Noise**: If no new articles exist, the dashboard shows the saved collection silently. No error banners.
4. **Saved Articles Persist**: Saved articles are stored in `localStorage`. A page refresh must restore them.
5. **Source Priority Order**: Ben's Bites → The AI Rundown → Reddit
6. **Secrets in .env only**: No credentials hardcoded in scripts.
7. **All intermediates in .tmp/**: Article cache, logs, scrape state.

---

## Integrations

| Service | Type | Auth Required | Status |
|---|---|---|---|
| Ben's Bites | Web Scrape | None | Pending |
| The AI Rundown | Web Scrape | None | Pending |
| Reddit | Public JSON API | None | Pending |
| Supabase | Database | API Key | Phase 2 (later) |

---

## Architectural Invariants
- All intermediate files live in `.tmp/`
- All secrets live in `.env`
- Tools in `tools/` must be atomic and independently testable
- SOPs in `architecture/` must be updated before code changes
- Backend serves articles via `GET /api/articles`
- Frontend is a single-page app in `dashboard/`

## Maintenance Log
*Empty — updated at Phase 5.*

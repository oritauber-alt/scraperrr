# SOP: Dashboard

## Goal
A single-page web app that displays the day's AI articles in a gorgeous, interactive layout with saved article persistence.

## Architecture
- **Backend**: FastAPI (`server.py`) serves articles via REST API
- **Frontend**: Static HTML/CSS/JS in `dashboard/`
- **State**: `localStorage` key `scraperrr_saved` for saved articles

---

## API Endpoints

### `GET /api/articles`
Returns all articles from the last 24 hours from cache.
- If cache is stale (>24h old), triggers a fresh scrape before responding
- Response: see `claude.md` API Response schema

### `GET /api/articles/refresh`
Forces a fresh scrape regardless of cache age.

### `GET /`
Serves `dashboard/index.html`

---

## Frontend Components

### 1. Header Bar
- Logo/wordmark: "scraperrr"
- Source filter tabs: All | Ben's Bites | The AI Rundown | Reddit
- Last updated timestamp
- Refresh button (spinner on load)
- Saved count badge

### 2. Article Card
Each card shows:
- Source badge (color-coded: Ben's Bites = purple, AI Rundown = blue, Reddit = orange)
- "NEW" pill if `is_new = true`
- Article title (clickable, opens in new tab)
- Summary (2-3 lines, truncated with `...`)
- Publication time (relative: "2h ago")
- Save/bookmark button (heart or bookmark icon, toggles)
- Saved state is visually distinct (filled icon)

### 3. Saved Articles Panel
- Slide-in drawer or dedicated tab
- Shows all saved articles
- Each has a "remove" button
- Persists in `localStorage`

### 4. Empty States
- No articles today: "Nothing new in the last 24 hours. Check back soon."
- Source filtered to 0 results: "No articles from this source today."
- Saved panel empty: "No saved articles yet. Bookmark articles to save them here."

### 5. Loading State
- Skeleton card placeholders during fetch

---

## Design System

### Colors
- Background: `#0f0f13` (near-black)
- Card background: `#1a1a24`
- Card border: `#2a2a3a`
- Accent: `#6366f1` (indigo)
- Ben's Bites badge: `#a855f7` (purple)
- AI Rundown badge: `#3b82f6` (blue)
- Reddit badge: `#f97316` (orange)
- Text primary: `#f1f5f9`
- Text secondary: `#94a3b8`
- New badge: `#10b981` (emerald)

### Typography
- Font: Inter (Google Fonts)
- Title: 16px, 600 weight
- Summary: 14px, 400 weight, secondary color
- Meta (source, time): 12px, secondary color

### Layout
- Grid: 3 columns on desktop, 2 on tablet, 1 on mobile
- Card: rounded-xl, subtle shadow, hover lift animation
- Filter tabs: pill-style, active = filled indigo

### Animations
- Card entrance: fade + slide up (staggered)
- Hover: transform translateY(-2px), shadow deepen
- Save button: scale pulse on click
- Filter switch: smooth fade

---

## Auto-Refresh Logic
- On page load: fetch `/api/articles`
- Every 24 hours (using `setInterval`): fetch `/api/articles/refresh`
- Show "Updated X minutes ago" in header
- If new articles arrive on refresh: flash "N new articles" toast notification

## Saved Articles Persistence
- On save: write article to `localStorage.scraperrr_saved`
- On page load: merge saved articles from localStorage with fresh API response
- `is_saved` state is derived client-side — backend never knows about saves

# Findings

## Source Research (2026-03-28)

### Ben's Bites
- **Platform**: Substack (custom domain bensbites.com)
- **RSS Feed**: `https://www.bensbites.com/feed` — CONFIRMED WORKING
- **Post URL pattern**: `https://www.bensbites.com/p/{slug}`
- **Content**: Daily AI newsletter, ~1 post/day, public posts available in RSS
- **Scrape method**: `feedparser` — reliable, no JS rendering needed

### The AI Rundown
- **Platform**: Beehiiv (confirmed via `beehiiv-adnetwork-production.s3.amazonaws.com` in HTML)
- **RSS Feed**: NOT available at `/feed`, `/rss`, or `therundown.beehiiv.com/feed`
- **Archive**: `https://www.therundown.ai/archive/` exists but is fully JS-rendered (Tailwind + TypeDream)
- **Post URL pattern**: `https://www.therundown.ai/p/{slug}`
- **Scrape method**: Playwright headless Chromium required

### Reddit
- **Method**: Public `.json` API (no auth required)
- **URL pattern**: `https://www.reddit.com/r/{sub}/top.json?t=day&limit=25`
- **Key requirement**: Custom `User-Agent` header to avoid 429 errors
  - Format: `scraperrr/1.0 (news dashboard)`
- **Rate limit**: ~60 req/min when properly identified
- **Post JSON path**: `.data.children[].data`
- **Subreddits**: `artificial`, `MachineLearning`, `singularity`

## Constraints
- WebFetch cannot access `www.reddit.com` directly (Python requests with User-Agent works fine)
- Ben's Bites is Substack — RSS is most reliable approach (JS rendering not needed)
- The AI Rundown has no RSS — Playwright is mandatory

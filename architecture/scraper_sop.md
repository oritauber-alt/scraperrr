# SOP: Article Scrapers

## Goal
Collect articles published within the last 24 hours from three sources and return a unified list of Article objects.

## Inputs
- None (scrapers are self-contained)
- Runtime: current UTC timestamp

## Outputs
- List of Article objects matching the schema in `claude.md`
- Written to `.tmp/articles_cache.json`
- Run metadata written to `.tmp/last_run.json`

---

## Source 1: Ben's Bites (`tools/scrape_bens_bites.py`)

**Method**: RSS via `feedparser`
**Feed URL**: `https://www.bensbites.com/feed`
**Cadence**: Daily newsletter (1 post/day typical)

### Steps
1. Fetch RSS feed with `feedparser.parse(FEED_URL)`
2. For each entry, check `published_parsed` against 24h window
3. Extract: `title`, `link`, `summary` (strip HTML tags), `published`
4. Generate `id` = `sha256(link)`
5. Set `source = "bens_bites"`, `source_label = "Ben's Bites"`

### Edge Cases
- Feed unavailable → log error, return empty list for this source, do not crash
- Summary contains HTML → strip with `BeautifulSoup(summary, 'html.parser').get_text()`
- Published date missing → skip entry

---

## Source 2: The AI Rundown (`tools/scrape_ai_rundown.py`)

**Method**: Playwright headless browser (JS-rendered Beehiiv site)
**URL**: `https://www.therundown.ai/archive/`
**Cadence**: Daily newsletter

### Steps
1. Launch `playwright` in headless Chromium
2. Navigate to archive URL, wait for `networkidle`
3. Query all post card elements (try: `article`, `[class*="post"]`, `[class*="card"]`)
4. For each card, extract: title (h2/h3), link (a href), date (time element or text)
5. Filter to last 24 hours by parsed date
6. For cards without summary, navigate to article URL and extract first 2 sentences of body text
7. Generate `id` = `sha256(link)`
8. Set `source = "ai_rundown"`, `source_label = "The AI Rundown"`

### Edge Cases
- Playwright timeout → retry once, then return empty list
- Date parsing ambiguity → log and skip that entry
- No articles in 24h → return empty list silently

### Known Constraints (update here if discovered)
- Site uses Beehiiv platform (TypeDream-based frontend, Tailwind CSS)
- JS must fully render before scraping — always `wait_until="networkidle"`

---

## Source 3: Reddit (`tools/scrape_reddit.py`)

**Method**: Reddit public JSON API (no auth required)
**Subreddits**: `r/artificial`, `r/MachineLearning`, `r/singularity`
**Endpoint pattern**: `https://www.reddit.com/r/{sub}/top.json?t=day&limit=25`

### Steps
1. For each subreddit, GET the `.json` endpoint with `User-Agent: scraperrr/1.0`
2. Parse `.data.children[].data` for each post
3. Filter: `created_utc` within last 24 hours
4. Extract: `title`, `url`, `selftext[:300]` as summary, `created_utc`, `thumbnail`, `subreddit`, `score`, `permalink`
5. Set article `url` = `https://reddit.com{permalink}` (use permalink, not external url)
6. Generate `id` = `sha256(permalink)`
7. Set `source = "reddit"`, `source_label = f"Reddit · r/{subreddit}"`
8. Sort by `score` descending, take top 10 total across all subreddits

### Edge Cases
- 429 Too Many Requests → wait 2s, retry once
- Deleted/removed posts (`[removed]`, `[deleted]`) → skip
- NSFW posts → skip
- No thumbnail or thumbnail is "self"/"default" → set `image_url = null`

---

## Deduplication & Cache

- After all scrapers run, merge all lists
- Dedup by `id` (sha256 of URL)
- Write merged list to `.tmp/articles_cache.json`
- Write run metadata to `.tmp/last_run.json`

## Error Handling Philosophy
- **Never crash the whole pipeline** because one source fails
- Log errors per-source and report in `last_run.json`
- A partial result (e.g., only Ben's Bites + Reddit) is always better than no result

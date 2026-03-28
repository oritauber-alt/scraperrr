"""
Scraper: Reddit
Method: Public JSON API (no auth required)
Subreddits: r/artificial, r/MachineLearning, r/singularity
"""

import hashlib
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests

SOURCE = "reddit"
SUBREDDITS = ["artificial", "MachineLearning", "singularity"]
TOP_N_TOTAL = 15  # Max articles across all subreddits
HEADERS = {"User-Agent": "scraperrr/1.0 (news dashboard)"}

log = logging.getLogger(__name__)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _fetch_subreddit(subreddit: str, hours: int, retries: int = 1) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/top.json?t=day&limit=25"
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 429:
                if attempt < retries:
                    log.warning("Reddit 429 on r/%s — waiting 2s", subreddit)
                    time.sleep(2)
                    continue
                log.error("Reddit rate limit exceeded for r/%s", subreddit)
                return []
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            if attempt < retries:
                time.sleep(1)
                continue
            log.error("Reddit fetch failed for r/%s: %s", subreddit, e)
            return []

    articles = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})

        # Skip removed/deleted/NSFW
        if post.get("removed_by_category"):
            continue
        if post.get("over_18"):
            continue
        selftext = post.get("selftext", "")
        if selftext in ("[removed]", "[deleted]"):
            continue

        # Date filter
        created = post.get("created_utc", 0)
        pub_date = datetime.fromtimestamp(created, tz=timezone.utc)
        if pub_date < cutoff:
            continue

        permalink = post.get("permalink", "")
        article_url = f"https://www.reddit.com{permalink}"
        title = post.get("title", "").strip()
        if not title:
            continue

        # Summary: prefer selftext, fall back to title
        summary = selftext.strip()[:400] if selftext else ""

        # Image: thumbnail if valid
        thumbnail = post.get("thumbnail", "")
        image_url: Optional[str] = None
        if thumbnail and thumbnail not in ("self", "default", "nsfw", "spoiler", "", "image"):
            image_url = thumbnail
        # Better: check preview images
        preview = post.get("preview", {})
        if preview:
            try:
                image_url = preview["images"][0]["source"]["url"].replace("&amp;", "&")
            except (KeyError, IndexError):
                pass

        articles.append({
            "id": _sha256(permalink),
            "title": title,
            "summary": summary,
            "url": article_url,
            "source": SOURCE,
            "source_label": f"Reddit · r/{subreddit}",
            "published_at": pub_date.isoformat(),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "image_url": image_url,
            "tags": [subreddit],
            "score": post.get("score", 0),
            "is_new": True,
        })

    log.info("Reddit r/%s: %d posts in last %dh", subreddit, len(articles), hours)
    return articles


def scrape(hours: int = 24) -> list[dict]:
    """
    Scrape top posts from configured subreddits.
    Returns top N articles by score within the last `hours` hours.
    """
    all_articles = []

    for sub in SUBREDDITS:
        articles = _fetch_subreddit(sub, hours)
        all_articles.extend(articles)
        time.sleep(0.5)  # Be polite

    # Sort by score descending, take top N
    all_articles.sort(key=lambda a: a.get("score", 0), reverse=True)
    result = all_articles[:TOP_N_TOTAL]

    # Remove score field (not in public schema)
    for a in result:
        a.pop("score", None)

    log.info("Reddit total: %d articles selected", len(result))
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = scrape()
    for a in results:
        print(f"[r/{a['tags'][0] if a['tags'] else '?'}] {a['title']}")
        print(f"  {a['url']}")
        print(f"  {a['summary'][:100]}..." if a['summary'] else "  (no summary)")
        print()
    print(f"Total: {len(results)} articles")

"""
Scraper: Ben's Bites
Method: RSS feed via feedparser
Feed: https://www.bensbites.com/feed
"""

import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import feedparser
from bs4 import BeautifulSoup

FEED_URL = "https://www.bensbites.com/feed"
SOURCE = "bens_bites"
SOURCE_LABEL = "Ben's Bites"

log = logging.getLogger(__name__)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _strip_html(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text(separator=" ").strip()


def _parse_date(entry) -> Optional[datetime]:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    return None


def _extract_image(entry) -> Optional[str]:
    # Check media_thumbnail
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")
    # Check enclosures
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image/"):
                return enc.get("href") or enc.get("url")
    # Check content for first <img>
    content = ""
    if hasattr(entry, "content") and entry.content:
        content = entry.content[0].get("value", "")
    elif hasattr(entry, "summary"):
        content = entry.summary
    if content:
        soup = BeautifulSoup(content, "html.parser")
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]
    return None


def scrape(hours: int = 24) -> list[dict]:
    """
    Fetch and parse Ben's Bites RSS feed.
    Returns articles published within the last `hours` hours.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles = []

    try:
        feed = feedparser.parse(FEED_URL)
        if feed.bozo and not feed.entries:
            log.error("Ben's Bites feed parse error: %s", feed.bozo_exception)
            return []

        for entry in feed.entries:
            pub_date = _parse_date(entry)
            if pub_date is None:
                log.warning("Skipping entry with no date: %s", entry.get("title", "?"))
                continue
            if pub_date < cutoff:
                continue

            link = entry.get("link", "")
            title = entry.get("title", "").strip()
            raw_summary = entry.get("summary", "") or entry.get("description", "")
            summary = _strip_html(raw_summary)[:500]

            articles.append({
                "id": _sha256(link),
                "title": title,
                "summary": summary,
                "url": link,
                "source": SOURCE,
                "source_label": SOURCE_LABEL,
                "published_at": pub_date.isoformat(),
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "image_url": _extract_image(entry),
                "tags": [],
                "is_new": True,
            })

        log.info("Ben's Bites: %d articles in last %dh", len(articles), hours)

    except Exception as e:
        log.error("Ben's Bites scraper failed: %s", e, exc_info=True)
        return []

    return articles


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = scrape()
    for a in results:
        print(f"[{a['published_at'][:10]}] {a['title']}")
        print(f"  {a['url']}")
        print(f"  {a['summary'][:100]}...")
        print()
    print(f"Total: {len(results)} articles")

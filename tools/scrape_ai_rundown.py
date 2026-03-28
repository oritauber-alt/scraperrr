"""
Scraper: The AI Rundown
Method: Playwright headless browser (Beehiiv/JS-rendered)
URL: https://www.therundown.ai/archive/
"""

import hashlib
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

log = logging.getLogger(__name__)

SOURCE = "ai_rundown"
SOURCE_LABEL = "The AI Rundown"
ARCHIVE_URL = "https://www.therundown.ai/archive/"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _parse_relative_date(text: str) -> Optional[datetime]:
    """Parse strings like '2 hours ago', 'yesterday', 'March 27, 2026'."""
    now = datetime.now(timezone.utc)
    text = text.strip().lower()

    if "just now" in text or "minutes ago" in text:
        m = re.search(r"(\d+)\s+minute", text)
        mins = int(m.group(1)) if m else 5
        return now - timedelta(minutes=mins)
    if "hour" in text:
        m = re.search(r"(\d+)\s+hour", text)
        hrs = int(m.group(1)) if m else 1
        return now - timedelta(hours=hrs)
    if "yesterday" in text:
        return now - timedelta(days=1)
    if "day" in text:
        m = re.search(r"(\d+)\s+day", text)
        days = int(m.group(1)) if m else 1
        return now - timedelta(days=days)

    # Try absolute date formats
    formats = [
        "%B %d, %Y",   # March 27, 2026
        "%b %d, %Y",   # Mar 27, 2026
        "%Y-%m-%d",    # 2026-03-27
        "%m/%d/%Y",    # 03/27/2026
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(text.strip(), fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _extract_summary_from_article(page, url: str) -> str:
    """Navigate to article page and extract first paragraph as summary."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        # Try common content selectors
        for selector in ["article p", ".post-content p", "main p", "p"]:
            paras = page.query_selector_all(selector)
            for p in paras[:3]:
                text = p.inner_text().strip()
                if len(text) > 60:
                    return text[:400]
    except Exception as e:
        log.warning("Could not extract summary from %s: %s", url, e)
    return ""


def scrape(hours: int = 24) -> list[dict]:
    """
    Scrape The AI Rundown archive using Playwright.
    Returns articles published within the last `hours` hours.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.error("playwright not installed. Run: pip install playwright && playwright install chromium")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # Load archive page
            try:
                page.goto(ARCHIVE_URL, wait_until="networkidle", timeout=30000)
            except Exception as e:
                log.warning("Archive page timeout, retrying: %s", e)
                page.goto(ARCHIVE_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)

            # Try multiple card selectors — Beehiiv uses different class names
            card_selectors = [
                "article",
                "[class*='post-card']",
                "[class*='PostCard']",
                "[class*='newsletter-post']",
                "[class*='archive'] a[href*='/p/']",
                "a[href*='/p/']",
            ]

            cards = []
            for selector in card_selectors:
                found = page.query_selector_all(selector)
                if found:
                    cards = found
                    log.info("AI Rundown: found %d cards with selector '%s'", len(found), selector)
                    break

            if not cards:
                log.warning("AI Rundown: no post cards found, dumping page title: %s", page.title())
                browser.close()
                return []

            for card in cards[:20]:  # max 20 cards
                try:
                    # Extract link
                    link_el = card if card.get_attribute("href") else card.query_selector("a[href*='/p/']")
                    if not link_el:
                        link_el = card.query_selector("a")
                    href = link_el.get_attribute("href") if link_el else None
                    if not href:
                        continue
                    if href.startswith("/"):
                        href = "https://www.therundown.ai" + href

                    # Extract title
                    title_el = card.query_selector("h2, h3, h4, [class*='title']")
                    title = title_el.inner_text().strip() if title_el else ""
                    if not title:
                        # fall back to link text
                        title = (link_el.inner_text().strip() if link_el else "")[:120]
                    if not title:
                        continue

                    # Extract date
                    date_el = card.query_selector("time, [class*='date'], [class*='Date']")
                    date_text = ""
                    if date_el:
                        date_text = date_el.get_attribute("datetime") or date_el.inner_text()
                    pub_date = _parse_relative_date(date_text) if date_text else datetime.now(timezone.utc)

                    if pub_date and pub_date < cutoff:
                        continue

                    # Extract summary
                    summary_el = card.query_selector("p, [class*='summary'], [class*='excerpt']")
                    summary = summary_el.inner_text().strip()[:400] if summary_el else ""

                    # Extract image
                    img_el = card.query_selector("img")
                    image_url = img_el.get_attribute("src") if img_el else None
                    if image_url and image_url.startswith("/"):
                        image_url = "https://www.therundown.ai" + image_url

                    articles.append({
                        "id": _sha256(href),
                        "title": title,
                        "summary": summary,
                        "url": href,
                        "source": SOURCE,
                        "source_label": SOURCE_LABEL,
                        "published_at": (pub_date or datetime.now(timezone.utc)).isoformat(),
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                        "image_url": image_url,
                        "tags": [],
                        "is_new": True,
                    })

                except Exception as e:
                    log.warning("Error parsing AI Rundown card: %s", e)
                    continue

            browser.close()
            log.info("AI Rundown: %d articles in last %dh", len(articles), hours)

    except Exception as e:
        log.error("AI Rundown scraper failed: %s", e, exc_info=True)
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

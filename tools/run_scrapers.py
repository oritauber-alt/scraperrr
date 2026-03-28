"""
Orchestrator: Run all scrapers and write unified cache to .tmp/
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

import scrape_bens_bites
import scrape_ai_rundown
import scrape_reddit

TMP_DIR = Path(__file__).parent.parent / ".tmp"
CACHE_FILE = TMP_DIR / "articles_cache.json"
RUN_FILE = TMP_DIR / "last_run.json"

log = logging.getLogger(__name__)


def run_all(hours: int = 24) -> dict:
    TMP_DIR.mkdir(exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()
    run_meta = {
        "last_run": now,
        "article_ids_seen": [],
        "sources": {}
    }

    all_articles = []

    # --- Ben's Bites ---
    try:
        bites = scrape_bens_bites.scrape(hours)
        run_meta["sources"]["bens_bites"] = {"status": "ok", "count": len(bites)}
        all_articles.extend(bites)
    except Exception as e:
        log.error("Ben's Bites orchestration error: %s", e)
        run_meta["sources"]["bens_bites"] = {"status": "error", "error": str(e), "count": 0}

    # --- The AI Rundown ---
    try:
        rundown = scrape_ai_rundown.scrape(hours)
        run_meta["sources"]["ai_rundown"] = {"status": "ok", "count": len(rundown)}
        all_articles.extend(rundown)
    except Exception as e:
        log.error("AI Rundown orchestration error: %s", e)
        run_meta["sources"]["ai_rundown"] = {"status": "error", "error": str(e), "count": 0}

    # --- Reddit ---
    try:
        reddit = scrape_reddit.scrape(hours)
        run_meta["sources"]["reddit"] = {"status": "ok", "count": len(reddit)}
        all_articles.extend(reddit)
    except Exception as e:
        log.error("Reddit orchestration error: %s", e)
        run_meta["sources"]["reddit"] = {"status": "error", "error": str(e), "count": 0}

    # Dedup by id
    seen = {}
    for article in all_articles:
        seen[article["id"]] = article
    deduped = list(seen.values())

    # Sort by published_at descending
    deduped.sort(key=lambda a: a.get("published_at", ""), reverse=True)

    run_meta["article_ids_seen"] = [a["id"] for a in deduped]

    # Write cache
    CACHE_FILE.write_text(json.dumps(deduped, indent=2))
    RUN_FILE.write_text(json.dumps(run_meta, indent=2))

    log.info("Scrape complete: %d total articles from %d sources", len(deduped), len(run_meta["sources"]))
    return {
        "articles": deduped,
        "fetched_at": now,
        "new_count": len(deduped),
        "sources": run_meta["sources"],
    }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    result = run_all()
    print(f"\nFetched at: {result['fetched_at']}")
    print(f"Total articles: {result['new_count']}")
    for source, meta in result["sources"].items():
        status = meta["status"]
        count = meta["count"]
        err = meta.get("error", "")
        print(f"  {source}: {status} ({count} articles) {err}")

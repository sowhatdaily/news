import threading
import time
from datetime import date, timedelta
from urllib.parse import urlparse

from .client import exa_client
from .prompts import EXA_INDIA_SUMMARY_QUERY

_NUM_RESULTS = 8
_LOOKBACK_DAYS = 7

# ── Rate limiter ─────────────────────────────────────────────────────────────
# Exa hard limit: 10 QPS. We cap at 8 to stay safely under.

class _RateLimiter:
    """Thread-safe token bucket: guarantees at most `rps` calls per second."""
    def __init__(self, rps: int):
        self._interval = 1.0 / rps
        self._lock = threading.Lock()
        self._last = 0.0

    def acquire(self):
        with self._lock:
            now = time.monotonic()
            wait = self._interval - (now - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()


_exa_limiter = _RateLimiter(rps=8)   # 8 QPS → safely under 10 QPS limit

# ── Exa summary query (India-focused, for sector news) ──────────────────────

_SUMMARY_QUERY = EXA_INDIA_SUMMARY_QUERY


# ── Helpers ───────────────────────────────────────────────────────────────────

def _domain_to_source(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower().replace("www.", "")
        _map = {
            "economictimes.indiatimes.com": "Economic Times",
            "livemint.com": "Mint",
            "businesstoday.in": "Business Today",
            "thehindu.com": "The Hindu",
            "ndtv.com": "NDTV",
            "cnbctv18.com": "CNBC TV18",
            "moneycontrol.com": "Moneycontrol",
            "reuters.com": "Reuters",
            "bloomberg.com": "Bloomberg",
            "ft.com": "Financial Times",
            "wsj.com": "Wall Street Journal",
            "techcrunch.com": "TechCrunch",
            "wired.com": "Wired",
            "theverge.com": "The Verge",
            "digitimes.com": "Digitimes",
            "newsbytesapp.com": "NewsBytesApp",
            "thehansindia.com": "Hans India",
            "indiatribune.com": "India Tribune",
            "bbc.com": "BBC",
            "bbc.co.uk": "BBC",
            "cnbc.com": "CNBC",
            "nytimes.com": "New York Times",
            "theguardian.com": "The Guardian",
            "aljazeera.com": "Al Jazeera",
        }
        for domain, name in _map.items():
            if domain in host:
                return name
        parts = host.split(".")
        return parts[-2].capitalize() if len(parts) >= 2 else host
    except Exception:
        return ""


# ── Main fetch (sector-specific) ─────────────────────────────────────────────

def fetch_news_for_bucket(sector: str, topics: list) -> list:
    """
    Exa semantic search for one sector + sub-interest bucket.
    Rate-limited to 8 QPS across all parallel threads.
    Returns list of {title, url, source, published_date, raw_summary, sector}.
    """
    today = date.today()
    week_ago = today - timedelta(days=_LOOKBACK_DAYS)

    topic_str = ", ".join(topics) if topics else sector
    query = (
        f"Latest news about {sector}: {topic_str}. "
        f"Developments that could impact India's economy, markets, or industries."
    )

    _exa_limiter.acquire()   # enforce 8 QPS

    result = exa_client.search(
        query,
        num_results=_NUM_RESULTS,
        start_published_date=week_ago.strftime("%Y-%m-%dT00:00:00.000Z"),
        end_published_date=today.strftime("%Y-%m-%dT23:59:59.999Z"),
        type="auto",
        contents={"summary": {"query": _SUMMARY_QUERY}},
    )

    items = []
    for r in result.results:
        items.append({
            "title":          r.title or "Untitled",
            "url":            r.url or "#",
            "source":         getattr(r, "author", None) or _domain_to_source(r.url or ""),
            "published_date": getattr(r, "published_date", "") or "",
            "raw_summary":    getattr(r, "summary", "") or "",
            "sector":         sector,
        })
    return items


# ── Global news fetch ────────────────────────────────────────────────────────

_GLOBAL_QUERIES = [
    (
        "Latest major global business and economic news from Bloomberg, Reuters, "
        "BBC, Financial Times, Wall Street Journal this week. "
        "Global developments that could impact India's economy, markets, trade, "
        "commodities, currency, or geopolitics.",
        "Global Economy"
    ),
    (
        "Latest global market news: US Federal Reserve, oil prices, commodity markets, "
        "global trade tensions, geopolitical developments. "
        "Impact on emerging markets and India.",
        "Global Markets"
    ),
]


def fetch_global_news() -> list:
    """
    Fetch global news from major international sources (Bloomberg, BBC, Reuters, etc.)
    that may impact India's economy, sectors, markets, commodities.
    """
    today = date.today()
    week_ago = today - timedelta(days=_LOOKBACK_DAYS)

    all_items = []
    for query, sector_label in _GLOBAL_QUERIES:
        _exa_limiter.acquire()

        try:
            result = exa_client.search(
                query,
                num_results=6,
                start_published_date=week_ago.strftime("%Y-%m-%dT00:00:00.000Z"),
                end_published_date=today.strftime("%Y-%m-%dT23:59:59.999Z"),
                type="auto",
                contents={"summary": {"query": _SUMMARY_QUERY}},
            )

            for r in result.results:
                all_items.append({
                    "title":          r.title or "Untitled",
                    "url":            r.url or "#",
                    "source":         getattr(r, "author", None) or _domain_to_source(r.url or ""),
                    "published_date": getattr(r, "published_date", "") or "",
                    "raw_summary":    getattr(r, "summary", "") or "",
                    "sector":         sector_label,
                })
        except Exception:
            pass

    return all_items

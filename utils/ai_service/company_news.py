"""
Company-specific news fetcher.
Uses Exa to search for news about specific stock symbols / company names,
with impact analysis focused on the COMPANY (not India).
"""

from datetime import date, timedelta

from .client import exa_client
from .news_fetcher import _exa_limiter, _domain_to_source
from .prompts import EXA_COMPANY_SUMMARY_QUERY

_NUM_RESULTS = 6
_LOOKBACK_DAYS = 7

# Map common Indian stock symbols to full company names for better search
_SYMBOL_NAME_MAP = {
    "RELIANCE": "Reliance Industries",
    "TCS": "Tata Consultancy Services",
    "INFY": "Infosys",
    "HDFCBANK": "HDFC Bank",
    "ICICIBANK": "ICICI Bank",
    "HINDUNILVR": "Hindustan Unilever",
    "ITC": "ITC Limited",
    "SBIN": "State Bank of India",
    "BHARTIARTL": "Bharti Airtel",
    "KOTAKBANK": "Kotak Mahindra Bank",
    "LT": "Larsen & Toubro",
    "AXISBANK": "Axis Bank",
    "WIPRO": "Wipro",
    "HCLTECH": "HCL Technologies",
    "BAJFINANCE": "Bajaj Finance",
    "MARUTI": "Maruti Suzuki",
    "TATAMOTORS": "Tata Motors",
    "TATASTEEL": "Tata Steel",
    "SUNPHARMA": "Sun Pharma",
    "ADANIENT": "Adani Enterprises",
    "ONGC": "ONGC",
    "NTPC": "NTPC",
    "POWERGRID": "Power Grid Corporation",
    "ULTRACEMCO": "UltraTech Cement",
    "TECHM": "Tech Mahindra",
    "ASIANPAINT": "Asian Paints",
    "TITAN": "Titan Company",
    "NESTLEIND": "Nestle India",
    "JSWSTEEL": "JSW Steel",
    "BAJAJFINSV": "Bajaj Finserv",
    "NVDA": "NVIDIA Corporation",
    "AAPL": "Apple Inc",
    "GOOGL": "Alphabet Google",
    "MSFT": "Microsoft Corporation",
    "AMZN": "Amazon",
    "TSLA": "Tesla",
    "META": "Meta Platforms",
}

_COMPANY_SUMMARY_QUERY = EXA_COMPANY_SUMMARY_QUERY


def _symbol_to_search_name(symbol: str) -> str:
    """Convert a stock symbol to a more searchable company name."""
    sym = symbol.strip().upper()
    return _SYMBOL_NAME_MAP.get(sym, sym)


def fetch_company_news(symbol: str) -> list:
    """
    Fetch recent news for a single company symbol via Exa.
    Returns list of {title, url, source, published_date, raw_summary, sector, symbol}.
    """
    today = date.today()
    week_ago = today - timedelta(days=_LOOKBACK_DAYS)

    company_name = _symbol_to_search_name(symbol)
    query = (
        f"Latest news about {company_name} ({symbol}). "
        f"Business developments, earnings, partnerships, regulatory actions, "
        f"market impact and stock performance."
    )

    _exa_limiter.acquire()

    result = exa_client.search(
        query,
        num_results=_NUM_RESULTS,
        start_published_date=week_ago.strftime("%Y-%m-%dT00:00:00.000Z"),
        end_published_date=today.strftime("%Y-%m-%dT23:59:59.999Z"),
        type="auto",
        contents={"summary": {"query": _COMPANY_SUMMARY_QUERY}},
    )

    items = []
    for r in result.results:
        items.append({
            "title":          r.title or "Untitled",
            "url":            r.url or "#",
            "source":         getattr(r, "author", None) or _domain_to_source(r.url or ""),
            "published_date": getattr(r, "published_date", "") or "",
            "raw_summary":    getattr(r, "summary", "") or "",
            "sector":         symbol.upper(),
            "symbol":         symbol.upper(),
        })
    return items

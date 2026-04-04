"""
Stock price fetcher using Exa search + LLM parsing.
Searches for current stock prices for indices and company symbols,
then uses OpenAI to extract structured price data.
"""

import json
from datetime import date

from .client import exa_client, openai_client, OPENAI_MODEL
from .news_fetcher import _exa_limiter


def _strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        inner = lines[1:]
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        text = "\n".join(inner).strip()
    return text


def fetch_stock_prices(symbols: list) -> list:
    """
    Fetch current stock prices for a list of symbols/indices using Exa + LLM.

    symbols: list of strings like ["NIFTY 50", "SENSEX", "RELIANCE", "TCS"]
    Returns: list of {name, price, change, change_pct} dicts
    """
    if not symbols:
        return []

    sym_str = ", ".join(symbols)
    today = date.today().strftime("%B %d, %Y")

    query = (
        f"Latest stock market prices today {today} for: {sym_str}. "
        f"NSE BSE India stock market live prices today."
    )

    _exa_limiter.acquire()

    try:
        result = exa_client.search(
            query,
            num_results=5,
            type="auto",
            contents={
                "summary": {
                    "query": (
                        f"What are the current/latest stock prices and daily change for: {sym_str}? "
                        f"Include the last traded price and percentage change from previous close."
                    )
                }
            },
        )

        # Collect all summaries into one block for the LLM
        raw_texts = []
        for r in result.results:
            summary = getattr(r, "summary", "") or ""
            if summary:
                raw_texts.append(summary)

        if not raw_texts:
            return [{"name": s, "price": 0, "change": 0, "change_pct": 0} for s in symbols]

        combined = "\n---\n".join(raw_texts)

    except Exception:
        return [{"name": s, "price": 0, "change": 0, "change_pct": 0} for s in symbols]

    # Use LLM to parse the raw text into structured data
    symbols_json = json.dumps(symbols)
    llm_prompt = f"""From the market data below, extract the latest stock price information.

Market data:
{combined}

I need data for these symbols/indices: {symbols_json}

Return ONLY a JSON array (no markdown, no code fences) with one object per symbol:
[
  {{
    "name": "<symbol or index name exactly as given>",
    "price": <last traded price as a number, 0 if unknown>,
    "change": <absolute price change from previous close, positive or negative, 0 if unknown>,
    "change_pct": <percentage change from previous close, positive or negative, 0 if unknown>
  }}
]

Rules:
- Use the exact names from the list: {symbols_json}
- price, change, change_pct must be numbers (not strings)
- If data is not found for a symbol, use 0 for all numeric fields
- Return ONLY the JSON array, nothing else"""

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": llm_prompt}],
            temperature=0.1,
            max_tokens=500,
        )
        raw = _strip_fence(response.choices[0].message.content or "")
        parsed = json.loads(raw)

        # Validate and clean
        result_map = {}
        for item in parsed:
            name = item.get("name", "")
            result_map[name] = {
                "name": name,
                "price": float(item.get("price", 0) or 0),
                "change": float(item.get("change", 0) or 0),
                "change_pct": float(item.get("change_pct", 0) or 0),
            }

        # Return in the original order, filling missing ones
        rows = []
        for sym in symbols:
            rows.append(result_map.get(sym, {"name": sym, "price": 0, "change": 0, "change_pct": 0}))
        return rows

    except Exception:
        return [{"name": s, "price": 0, "change": 0, "change_pct": 0} for s in symbols]

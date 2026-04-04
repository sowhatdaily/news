import json

from .client import openai_client, OPENAI_MODEL
from .prompts import (
    ARTICLE_STRUCTURED_SUMMARY,
    COMPANY_STRUCTURED_SUMMARY,
    TOPIC_CLASSIFICATION,
    PERSONALIZED_INSIGHT,
    SECTOR_SENTIMENT,
    DAILY_BRIEF_SYNTHESIS,
    WEEKLY_BRIEF_SYNTHESIS,
    THEME_SYNTHESIS,
)

_FALLBACK_INDIA = {
    "impact_score": 0,
    "signal_direction": "mixed",
    "signal_reason": "Analysis unavailable.",
    "impact_summary": "Analysis unavailable.",
    "impact_chain": "Insufficient data to determine causal path.",
    "affected_sectors": [],
    "what_happened": "Analysis unavailable.",
    "so_what": "Analysis unavailable.",
    "who_is_affected": [],
    "what_to_watch": [],
}

_FALLBACK_COMPANY = {
    "impact_score": 0,
    "signal_direction": "mixed",
    "signal_reason": "Analysis unavailable.",
    "impact_summary": "Analysis unavailable.",
    "impact_chain": "Insufficient data to determine causal path.",
    "affected_sectors": [],
    "what_happened": "Analysis unavailable.",
    "so_what": "Analysis unavailable.",
    "who_is_affected": [],
    "what_to_watch": [],
}


def _strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        inner = lines[1:]
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        text = "\n".join(inner).strip()
    return text


def _safe_parse(raw_text: str, fallback: dict) -> dict:
    """Parse JSON from LLM response with fallback."""
    try:
        raw = _strip_fence(raw_text)
        return json.loads(raw)
    except Exception:
        return dict(fallback)


def derive_signal_category(score: int) -> str:
    """Deterministic category from score — keeps LLM out of this decision."""
    abs_score = abs(score)
    if abs_score >= 8:
        return "high_impact"
    elif abs_score >= 5:
        return "developing"
    elif abs_score >= 3:
        return "watch"
    else:
        return "low_urgency"


def _ensure_lists(result: dict) -> dict:
    """Ensure list fields are actually lists."""
    for key in ("affected_sectors", "who_is_affected", "what_to_watch"):
        val = result.get(key)
        if val is None:
            result[key] = []
        elif isinstance(val, str):
            result[key] = [val]
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1: Structured article analysis
# ─────────────────────────────────────────────────────────────────────────────

def consolidate_impact(
    title: str,
    source: str,
    published_date: str,
    raw_summary: str,
) -> dict:
    """
    Consolidate Exa's raw summary into a structured India impact object.
    Returns: {impact_score, signal_direction, signal_category, signal_reason,
              impact_summary, impact_chain, affected_sectors,
              what_happened, so_what, who_is_affected, what_to_watch}
    """
    prompt = ARTICLE_STRUCTURED_SUMMARY.format(
        title=title,
        source=source,
        published_date=published_date,
        raw_summary=raw_summary,
    )

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=700,
        )
        result = _safe_parse(response.choices[0].message.content or "", _FALLBACK_INDIA)
        result["impact_score"] = max(-10, min(10, int(result.get("impact_score", 0))))
        result["signal_category"] = derive_signal_category(result["impact_score"])
        result = _ensure_lists(result)
        return result
    except Exception:
        return {**_FALLBACK_INDIA, "signal_category": "low_urgency"}


def consolidate_company_impact(
    title: str,
    source: str,
    published_date: str,
    raw_summary: str,
    symbol: str,
) -> dict:
    """
    Consolidate Exa's raw summary into a structured COMPANY impact object.
    """
    prompt = COMPANY_STRUCTURED_SUMMARY.format(
        title=title,
        source=source,
        published_date=published_date,
        raw_summary=raw_summary,
        symbol=symbol,
    )

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=700,
        )
        result = _safe_parse(response.choices[0].message.content or "", _FALLBACK_COMPANY)
        result["impact_score"] = max(-10, min(10, int(result.get("impact_score", 0))))
        result["signal_category"] = derive_signal_category(result["impact_score"])
        result = _ensure_lists(result)
        return result
    except Exception:
        return {**_FALLBACK_COMPANY, "signal_category": "low_urgency"}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1: Daily & Weekly Brief synthesis
# ─────────────────────────────────────────────────────────────────────────────

def synthesize_daily_brief(articles: list, region: str, date_str: str) -> dict:
    """
    Synthesize a list of enriched articles into a daily brief.
    Returns: {bottom_line, top_developments, signals_today, what_to_watch_next}
    """
    # Prepare slim article payload for the prompt
    slim = []
    for a in articles[:20]:  # cap at 20 to stay within token limits
        slim.append({
            "headline": a.get("title", ""),
            "what_happened": a.get("what_happened", a.get("impact_summary", "")),
            "so_what": a.get("so_what", ""),
            "signal_score": a.get("impact_score", 0),
            "signal_direction": a.get("signal_direction", "mixed"),
            "sector": a.get("sector", ""),
        })

    prompt = DAILY_BRIEF_SYNTHESIS.format(
        region=region,
        date=date_str,
        articles_json=json.dumps(slim, indent=2),
    )

    fallback = {
        "bottom_line": "Daily brief generation failed. Please try again.",
        "top_developments": [],
        "signals_today": [],
        "what_to_watch_next": [],
    }

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1500,
        )
        result = _safe_parse(response.choices[0].message.content or "", fallback)
        return result
    except Exception:
        return fallback


def synthesize_weekly_brief(articles: list, region: str, week_start: str, week_end: str) -> dict:
    """
    Synthesize a week's worth of articles into a weekly brief.
    Returns: {bottom_line, biggest_shifts, recurring_themes, what_to_watch_next_week}
    """
    slim = []
    for a in articles[:40]:  # cap at 40 for weekly
        slim.append({
            "headline": a.get("title", ""),
            "what_happened": a.get("what_happened", a.get("impact_summary", "")),
            "so_what": a.get("so_what", ""),
            "signal_score": a.get("impact_score", 0),
            "signal_direction": a.get("signal_direction", "mixed"),
            "sector": a.get("sector", ""),
            "published_date": a.get("published_date", ""),
        })

    prompt = WEEKLY_BRIEF_SYNTHESIS.format(
        region=region,
        week_start=week_start,
        week_end=week_end,
        articles_json=json.dumps(slim, indent=2),
    )

    fallback = {
        "bottom_line": "Weekly brief generation failed. Please try again.",
        "biggest_shifts": [],
        "recurring_themes": [],
        "what_to_watch_next_week": [],
    }

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2000,
        )
        result = _safe_parse(response.choices[0].message.content or "", fallback)
        return result
    except Exception:
        return fallback


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: Topic classification
# ─────────────────────────────────────────────────────────────────────────────

def classify_topic(title: str, summary: str) -> str:
    """Classify an article into a single theme for clustering."""
    prompt = TOPIC_CLASSIFICATION.format(title=title, summary=summary)

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=50,
        )
        result = _safe_parse(response.choices[0].message.content or "", {"theme": "other"})
        return result.get("theme", "other")
    except Exception:
        return "other"


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: Multi-article theme synthesis
# ─────────────────────────────────────────────────────────────────────────────

def synthesize_theme(articles: list, theme: str, period: str, region: str) -> dict:
    """Synthesize multiple articles about the same theme."""
    slim = []
    for a in articles[:15]:
        slim.append({
            "headline": a.get("title", ""),
            "what_happened": a.get("what_happened", a.get("impact_summary", "")),
            "so_what": a.get("so_what", ""),
            "signal_score": a.get("impact_score", 0),
            "signal_direction": a.get("signal_direction", "mixed"),
        })

    prompt = THEME_SYNTHESIS.format(
        theme=theme,
        period=period,
        region=region,
        articles_json=json.dumps(slim, indent=2),
    )

    fallback = {
        "theme": theme,
        "summary": "Synthesis unavailable.",
        "key_changes": [],
        "risks": [],
        "opportunities": [],
        "what_to_watch": [],
        "overall_direction": "mixed",
        "confidence": "low",
    }

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000,
        )
        result = _safe_parse(response.choices[0].message.content or "", fallback)
        return result
    except Exception:
        return fallback


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: Personalized "Why this matters to YOU"
# ─────────────────────────────────────────────────────────────────────────────

def generate_personalized_insight(article: dict, user_profile: dict) -> str:
    """Generate a personalized explanation of why this article matters to the user."""
    prompt = PERSONALIZED_INSIGHT.format(
        title=article.get("title", ""),
        what_happened=article.get("what_happened", article.get("impact_summary", "")),
        so_what=article.get("so_what", ""),
        impact_score=article.get("impact_score", 0),
        signal_direction=article.get("signal_direction", "mixed"),
        user_role=user_profile.get("persona", "Professional"),
        user_interests=", ".join(user_profile.get("interests", [])),
        user_geography=user_profile.get("geography", "Global"),
        user_experience=user_profile.get("years_experience", ""),
    )

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        result = _safe_parse(response.choices[0].message.content or "", {})
        return result.get("why_it_matters_to_you", "")
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: Sector / Stock sentiment
# ─────────────────────────────────────────────────────────────────────────────

def generate_sector_sentiment(article: dict) -> list:
    """Map an article to sector-level sentiment signals."""
    prompt = SECTOR_SENTIMENT.format(
        title=article.get("title", ""),
        what_happened=article.get("what_happened", article.get("impact_summary", "")),
        so_what=article.get("so_what", ""),
        impact_score=article.get("impact_score", 0),
        signal_direction=article.get("signal_direction", "mixed"),
    )

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500,
        )
        result = _safe_parse(response.choices[0].message.content or "", {})
        return result.get("sector_sentiments", [])
    except Exception:
        return []

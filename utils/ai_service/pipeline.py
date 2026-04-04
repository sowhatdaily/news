from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from .news_fetcher import fetch_news_for_bucket, fetch_global_news
from .company_news import fetch_company_news
from .causal_analyzer import (
    consolidate_impact,
    consolidate_company_impact,
    synthesize_daily_brief,
    synthesize_weekly_brief,
    classify_topic,
    synthesize_theme,
    generate_personalized_insight,
    generate_sector_sentiment,
)

_MAX_FETCH_WORKERS = 6
_MAX_ANALYSIS_WORKERS = 10


# ─────────────────────────────────────────────────────────────────────────────
# Step helpers (shared)
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_all_news(main_sectors: list, sub_interests: dict) -> list:
    """Parallel Step 1: Exa search for every sector bucket simultaneously."""
    buckets = [(s, sub_interests.get(s, [])) for s in main_sectors]

    all_news = []
    seen_urls = set()

    with ThreadPoolExecutor(max_workers=min(len(buckets) + 1, _MAX_FETCH_WORKERS)) as ex:
        futures = {ex.submit(fetch_news_for_bucket, s, t): s for s, t in buckets}
        global_future = ex.submit(fetch_global_news)
        futures[global_future] = "__global__"

        for future in as_completed(futures):
            try:
                for item in future.result():
                    url = item.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_news.append(item)
            except Exception:
                pass
    return all_news


def _fetch_company_news(symbols: list) -> list:
    """Parallel fetch of company-specific news for all watchlist symbols."""
    if not symbols:
        return []

    all_news = []
    seen_urls = set()

    with ThreadPoolExecutor(max_workers=min(len(symbols), _MAX_FETCH_WORKERS)) as ex:
        futures = {ex.submit(fetch_company_news, sym): sym for sym in symbols}
        for future in as_completed(futures):
            try:
                for item in future.result():
                    url = item.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_news.append(item)
            except Exception:
                pass
    return all_news


def _enrich_with_impact(news_items: list) -> list:
    """Parallel Step 2: OpenAI India-impact consolidation for each article."""

    def _enrich(item):
        impact = consolidate_impact(
            title=item.get("title", ""),
            source=item.get("source", ""),
            published_date=item.get("published_date", ""),
            raw_summary=item.get("raw_summary", ""),
        )
        return {**item, **impact}

    enriched = []
    with ThreadPoolExecutor(max_workers=min(len(news_items), _MAX_ANALYSIS_WORKERS)) as ex:
        futures = [ex.submit(_enrich, item) for item in news_items]
        for future in as_completed(futures):
            try:
                enriched.append(future.result())
            except Exception:
                pass
    return enriched


def _enrich_with_company_impact(news_items: list) -> list:
    """Parallel Step 2: OpenAI company-impact consolidation for each article."""

    def _enrich(item):
        impact = consolidate_company_impact(
            title=item.get("title", ""),
            source=item.get("source", ""),
            published_date=item.get("published_date", ""),
            raw_summary=item.get("raw_summary", ""),
            symbol=item.get("symbol", ""),
        )
        return {**item, **impact}

    enriched = []
    with ThreadPoolExecutor(max_workers=min(len(news_items), _MAX_ANALYSIS_WORKERS)) as ex:
        futures = [ex.submit(_enrich, item) for item in news_items]
        for future in as_completed(futures):
            try:
                enriched.append(future.result())
            except Exception:
                pass
    return enriched


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1: Core feed pipelines
# ─────────────────────────────────────────────────────────────────────────────

def run_for_you_pipeline(user_profile: dict) -> list:
    """
    Full pipeline for the "For You" feed.
    Now returns enriched articles with structured insights:
    what_happened, so_what, who_is_affected, what_to_watch,
    signal_direction, signal_category, signal_reason.
    """
    onboarding = user_profile.get("onboarding", {})
    main_sectors = onboarding.get("main_sectors", [])
    sub_interests = onboarding.get("sub_interests", {})

    if not main_sectors:
        return []

    news = _fetch_all_news(main_sectors, sub_interests)
    if not news:
        return []

    enriched = _enrich_with_impact(news)
    enriched.sort(key=lambda x: abs(x.get("impact_score", 0)), reverse=True)
    return enriched


def run_company_news_pipeline(symbols: list) -> list:
    """
    Pipeline for company/watchlist news tab.
    Now returns structured insights per article.
    """
    if not symbols:
        return []

    news = _fetch_company_news(symbols)
    if not news:
        return []

    enriched = _enrich_with_company_impact(news)
    enriched.sort(key=lambda x: abs(x.get("impact_score", 0)), reverse=True)
    return enriched


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1: Daily & Weekly Brief pipelines
# ─────────────────────────────────────────────────────────────────────────────

def run_daily_brief_pipeline(articles: list, region: str, date_str: str) -> dict:
    """
    Generate a daily brief from already-enriched articles.
    articles: list of enriched article dicts (from the feed)
    """
    if not articles:
        return {
            "bottom_line": "No articles available for today's brief.",
            "top_developments": [],
            "signals_today": [],
            "what_to_watch_next": [],
        }
    # Sort by absolute impact and take top articles for the brief
    sorted_articles = sorted(articles, key=lambda x: abs(x.get("impact_score", 0)), reverse=True)
    return synthesize_daily_brief(sorted_articles, region, date_str)


def run_weekly_brief_pipeline(articles: list, region: str, week_start: str, week_end: str) -> dict:
    """
    Generate a weekly brief from a week's worth of enriched articles.
    """
    if not articles:
        return {
            "bottom_line": "No articles available for this week's brief.",
            "biggest_shifts": [],
            "recurring_themes": [],
            "what_to_watch_next_week": [],
        }
    sorted_articles = sorted(articles, key=lambda x: abs(x.get("impact_score", 0)), reverse=True)
    return synthesize_weekly_brief(sorted_articles, region, week_start, week_end)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: Multi-article theme synthesis
# ─────────────────────────────────────────────────────────────────────────────

def run_theme_synthesis_pipeline(articles: list, region: str, period: str = "weekly") -> list:
    """
    Cluster articles by theme and synthesize each cluster.
    Returns list of theme synthesis dicts.
    """
    if not articles:
        return []

    # Step 1: Classify each article into a theme (parallel)
    def _classify(article):
        theme = classify_topic(
            title=article.get("title", ""),
            summary=article.get("impact_summary", article.get("what_happened", "")),
        )
        return {**article, "theme": theme}

    classified = []
    with ThreadPoolExecutor(max_workers=_MAX_ANALYSIS_WORKERS) as ex:
        futures = [ex.submit(_classify, a) for a in articles]
        for future in as_completed(futures):
            try:
                classified.append(future.result())
            except Exception:
                pass

    # Step 2: Group by theme
    clusters = defaultdict(list)
    for article in classified:
        clusters[article.get("theme", "other")].append(article)

    # Step 3: Synthesize each cluster with 2+ articles (parallel)
    valid_clusters = {t: arts for t, arts in clusters.items() if len(arts) >= 2}
    if not valid_clusters:
        return []

    syntheses = []
    with ThreadPoolExecutor(max_workers=min(len(valid_clusters), _MAX_ANALYSIS_WORKERS)) as ex:
        futures = {
            ex.submit(synthesize_theme, arts, theme, period, region): theme
            for theme, arts in valid_clusters.items()
        }
        for future in as_completed(futures):
            try:
                syntheses.append(future.result())
            except Exception:
                pass

    # Sort by number of articles in cluster (most covered theme first)
    syntheses.sort(key=lambda x: len(valid_clusters.get(x.get("theme", ""), [])), reverse=True)
    return syntheses


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: Personalization pipeline
# ─────────────────────────────────────────────────────────────────────────────

def run_personalization_for_article(article: dict, user_profile: dict) -> str:
    """Generate a personalized 'why this matters to you' for one article."""
    return generate_personalized_insight(article, user_profile)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: Sector sentiment pipeline
# ─────────────────────────────────────────────────────────────────────────────

def run_sector_sentiment_for_article(article: dict) -> list:
    """Generate sector sentiment signals for one article."""
    return generate_sector_sentiment(article)

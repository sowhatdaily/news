"""
Daily scheduler — run at 8:30 AM via cron to auto-fetch news and generate briefs.

Cron entry (add via `crontab -e`):
  30 8 * * * cd /home/prafull/praful_kt/imapp/utils && /home/prafull/miniconda3/bin/python daily_scheduler.py >> /tmp/imapp_scheduler.log 2>&1

What it does:
  1. For each registered user:
     a. Fetches sector news (For You feed) via Exa + LLM impact analysis
     b. Fetches company news for their watchlist
     c. Generates daily brief
     d. Generates weekly brief (if Monday or if none exists for the week)
     e. Caches everything in the database
  2. Logs progress to stdout
"""

import sys
import os
from datetime import date, timedelta, datetime

# Ensure the utils directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import (
    get_all_users,
    load_user_by_email,
    save_news_cache,
    load_news_cache,
    get_watchlist,
    save_brief,
    load_brief,
)
from ai_service import (
    run_for_you_pipeline,
    run_company_news_pipeline,
    run_daily_brief_pipeline,
    run_weekly_brief_pipeline,
)
from db import init_db

init_db()


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def run_for_user(user_profile: dict):
    """Run the full daily pipeline for one user."""
    email = user_profile["email"]
    geography = user_profile.get("geography", "India")
    onboarding = user_profile.get("onboarding", {})
    main_sectors = onboarding.get("main_sectors", [])
    today = date.today()

    if not main_sectors:
        log(f"  [{email}] No sectors configured — skipping.")
        return

    # 1. Fetch sector news
    log(f"  [{email}] Fetching sector news ({len(main_sectors)} sectors)…")
    try:
        feed = run_for_you_pipeline(user_profile)
        if feed:
            save_news_cache(email, feed, cache_type="sector")
            log(f"  [{email}] Fetched {len(feed)} articles.")
        else:
            log(f"  [{email}] No articles returned.")
            # Try loading from cache for brief generation
            feed = load_news_cache(email, cache_type="sector")
    except Exception as e:
        log(f"  [{email}] Sector news error: {e}")
        feed = load_news_cache(email, cache_type="sector")

    # 2. Fetch company news
    watchlist = get_watchlist(email)
    if watchlist:
        log(f"  [{email}] Fetching company news ({len(watchlist)} symbols)…")
        try:
            cfeed = run_company_news_pipeline(watchlist)
            if cfeed:
                save_news_cache(email, cfeed, cache_type="company")
                log(f"  [{email}] Fetched {len(cfeed)} company articles.")
        except Exception as e:
            log(f"  [{email}] Company news error: {e}")

    # 3. Generate daily brief
    if feed:
        log(f"  [{email}] Generating daily brief…")
        try:
            daily = run_daily_brief_pipeline(feed, geography, str(today))
            save_brief(email, "daily", geography, str(today), daily)
            log(f"  [{email}] Daily brief saved.")
        except Exception as e:
            log(f"  [{email}] Daily brief error: {e}")

    # 4. Generate weekly brief (every day, overwrite — always fresh)
    if feed:
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_key = f"{week_start}_{week_end}"
        log(f"  [{email}] Generating weekly brief ({week_key})…")
        try:
            weekly = run_weekly_brief_pipeline(feed, geography, str(week_start), str(week_end))
            save_brief(email, "weekly", geography, week_key, weekly)
            log(f"  [{email}] Weekly brief saved.")
        except Exception as e:
            log(f"  [{email}] Weekly brief error: {e}")


def main():
    log("=" * 60)
    log("Daily scheduler started.")

    users = get_all_users()
    log(f"Found {len(users)} registered users.")

    for u in users:
        email = u["email"]
        log(f"Processing user: {email}")
        user_profile = load_user_by_email(email)
        if not user_profile:
            log(f"  [{email}] Could not load profile — skipping.")
            continue
        try:
            run_for_user(user_profile)
        except Exception as e:
            log(f"  [{email}] Unexpected error: {e}")

    log("Daily scheduler finished.")
    log("=" * 60)


if __name__ == "__main__":
    main()

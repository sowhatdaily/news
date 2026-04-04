import sqlite3
import hashlib
import json
import secrets
from datetime import datetime, timedelta

DB_PATH = "anonimous_ai.db"


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def safe_add_column(conn, table_name, column_name, column_type):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    existing = [row[1] for row in cur.fetchall()]
    if column_name not in existing:
        cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        conn.commit()


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            persona TEXT,
            years_experience TEXT,
            interests TEXT,
            onboarding_json TEXT,
            geography TEXT,
            output_preference TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            article_title TEXT,
            article_text TEXT,
            summary_json TEXT,
            created_at TEXT
        )
    """)

    # ── News cache: stores fetched + enriched articles for 7-day window ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            cache_type TEXT NOT NULL DEFAULT 'sector',
            article_url TEXT NOT NULL,
            article_json TEXT NOT NULL,
            fetched_date TEXT NOT NULL,
            UNIQUE(user_email, cache_type, article_url)
        )
    """)

    # ── Stock watchlist: up to 5 symbols per user ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            symbol TEXT NOT NULL,
            added_at TEXT NOT NULL,
            UNIQUE(user_email, symbol)
        )
    """)

    # ── Bookmarks: user-saved articles ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            article_url TEXT NOT NULL,
            article_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_email, article_url)
        )
    """)

    # ── Briefs cache: daily/weekly briefs ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS briefs_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            brief_type TEXT NOT NULL,
            region TEXT NOT NULL,
            brief_date TEXT NOT NULL,
            brief_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_email, brief_type, region, brief_date)
        )
    """)

    # ── Persistent login sessions (45-day tokens) ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS login_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            session_token TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    safe_add_column(conn, "users", "onboarding_json", "TEXT")
    safe_add_column(conn, "users", "geography", "TEXT")
    safe_add_column(conn, "users", "output_preference", "TEXT")
    safe_add_column(conn, "news_cache", "cache_type", "TEXT DEFAULT 'sector'")

    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_user(
    full_name,
    email,
    password,
    persona,
    years_experience,
    interests,
    onboarding_payload,
    geography,
    output_preference,
):
    email = email.strip().lower()
    password_hash = hash_password(password)
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO users (
                full_name, email, password_hash, persona, years_experience,
                interests, onboarding_json, geography, output_preference, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            full_name.strip(),
            email,
            password_hash,
            persona,
            years_experience,
            json.dumps(interests),
            json.dumps(onboarding_payload),
            geography,
            output_preference,
            datetime.utcnow().isoformat(),
        ))
        conn.commit()
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."
    finally:
        conn.close()


def load_user_by_email(email):
    email = email.strip().lower()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT full_name, email, persona, years_experience, interests,
               onboarding_json, geography, output_preference
        FROM users
        WHERE email = ?
    """, (email,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "full_name": row[0],
        "email": row[1],
        "persona": row[2] or "Other",
        "years_experience": row[3] or "Just exploring",
        "interests": json.loads(row[4]) if row[4] else [],
        "onboarding": json.loads(row[5]) if row[5] else {},
        "geography": row[6] or "Global",
        "output_preference": row[7] or "Short summaries",
    }


def authenticate_user(email, password):
    email = email.strip().lower()
    password_hash = hash_password(password)
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT full_name, email, persona, years_experience, interests,
               onboarding_json, geography, output_preference
        FROM users
        WHERE email = ? AND password_hash = ?
    """, (email, password_hash))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "full_name": row[0],
        "email": row[1],
        "persona": row[2] or "Other",
        "years_experience": row[3] or "Just exploring",
        "interests": json.loads(row[4]) if row[4] else [],
        "onboarding": json.loads(row[5]) if row[5] else {},
        "geography": row[6] or "Global",
        "output_preference": row[7] or "Short summaries",
    }


def update_user_preferences(email, onboarding_payload, interests_flat):
    """Update user's sector/sub-interest preferences."""
    email = email.strip().lower()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users
        SET onboarding_json = ?, interests = ?
        WHERE email = ?
    """, (json.dumps(onboarding_payload), json.dumps(interests_flat), email))
    conn.commit()
    conn.close()


def save_summary(user_email, article_title, article_text, summary_payload):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO summaries (
            user_email, article_title, article_text, summary_json, created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_email,
        article_title,
        article_text,
        json.dumps(summary_payload),
        datetime.utcnow().isoformat(),
    ))
    conn.commit()
    conn.close()


def fetch_user_history(user_email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT article_title, article_text, summary_json, created_at
        FROM summaries
        WHERE user_email = ?
        ORDER BY created_at DESC
    """, (user_email,))
    rows = cur.fetchall()
    conn.close()

    out = []
    for row in rows:
        out.append({
            "article_title": row[0],
            "article_text": row[1],
            "summary": json.loads(row[2]) if row[2] else {},
            "created_at": row[3],
        })
    return out


# ── News cache operations ────────────────────────────────────────────────────

def save_news_cache(user_email, articles, cache_type="sector"):
    """Upsert articles into the news cache."""
    conn = get_conn()
    cur = conn.cursor()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    for article in articles:
        url = article.get("url", "")
        if not url:
            continue
        cur.execute("""
            INSERT INTO news_cache (user_email, cache_type, article_url, article_json, fetched_date)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_email, cache_type, article_url) DO UPDATE SET
                article_json = excluded.article_json,
                fetched_date = excluded.fetched_date
        """, (user_email, cache_type, url, json.dumps(article), today))
    conn.commit()
    conn.close()


def load_news_cache(user_email, cache_type="sector"):
    """Load cached articles from the last 7 days."""
    conn = get_conn()
    cur = conn.cursor()
    cutoff = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    cur.execute("""
        SELECT article_json FROM news_cache
        WHERE user_email = ? AND cache_type = ? AND fetched_date >= ?
        ORDER BY fetched_date DESC
    """, (user_email, cache_type, cutoff))
    rows = cur.fetchall()
    conn.close()
    return [json.loads(row[0]) for row in rows]


def clear_old_cache(user_email=None):
    """Remove cache entries older than 7 days."""
    conn = get_conn()
    cur = conn.cursor()
    cutoff = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    if user_email:
        cur.execute("DELETE FROM news_cache WHERE user_email = ? AND fetched_date < ?",
                     (user_email, cutoff))
    else:
        cur.execute("DELETE FROM news_cache WHERE fetched_date < ?", (cutoff,))
    conn.commit()
    conn.close()


# ── Stock watchlist operations ───────────────────────────────────────────────

def get_watchlist(user_email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT symbol FROM stock_watchlist WHERE user_email = ? ORDER BY added_at",
                (user_email,))
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]


def add_to_watchlist(user_email, symbol):
    """Add a symbol. Returns (success, message)."""
    symbol = symbol.strip().upper()
    if not symbol:
        return False, "Symbol cannot be empty."
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM stock_watchlist WHERE user_email = ?", (user_email,))
    count = cur.fetchone()[0]
    if count >= 5:
        conn.close()
        return False, "Maximum 5 symbols allowed. Remove one first."
    try:
        cur.execute("""
            INSERT INTO stock_watchlist (user_email, symbol, added_at)
            VALUES (?, ?, ?)
        """, (user_email, symbol, datetime.utcnow().isoformat()))
        conn.commit()
        return True, f"{symbol} added."
    except sqlite3.IntegrityError:
        return False, f"{symbol} is already in your watchlist."
    finally:
        conn.close()


def remove_from_watchlist(user_email, symbol):
    symbol = symbol.strip().upper()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM stock_watchlist WHERE user_email = ? AND symbol = ?",
                (user_email, symbol))
    conn.commit()
    conn.close()


# ── Admin operations ─────────────────────────────────────────────────────────

def get_all_users():
    """Return all users as a list of dicts."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, full_name, email, persona, years_experience, geography,
               onboarding_json, created_at
        FROM users ORDER BY created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0], "full_name": r[1], "email": r[2], "persona": r[3],
            "years_experience": r[4], "geography": r[5],
            "onboarding": json.loads(r[6]) if r[6] else {},
            "created_at": r[7],
        }
        for r in rows
    ]


def delete_user(email):
    """Remove a user and all their related data."""
    email = email.strip().lower()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE email = ?", (email,))
    cur.execute("DELETE FROM summaries WHERE user_email = ?", (email,))
    cur.execute("DELETE FROM news_cache WHERE user_email = ?", (email,))
    cur.execute("DELETE FROM stock_watchlist WHERE user_email = ?", (email,))
    cur.execute("DELETE FROM bookmarks WHERE user_email = ?", (email,))
    cur.execute("DELETE FROM briefs_cache WHERE user_email = ?", (email,))
    conn.commit()
    conn.close()


def clear_user_preferences(email):
    """Reset a user's onboarding preferences and watchlist."""
    email = email.strip().lower()
    empty_onboarding = json.dumps({
        "persona": None, "experience_level": None, "main_sectors": [],
        "sub_interests": {}, "geography": None, "output_preference": None,
    })
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users SET onboarding_json = ?, interests = ? WHERE email = ?
    """, (empty_onboarding, json.dumps([]), email))
    cur.execute("DELETE FROM stock_watchlist WHERE user_email = ?", (email,))
    cur.execute("DELETE FROM news_cache WHERE user_email = ?", (email,))
    conn.commit()
    conn.close()


# ── Bookmark operations ─────────────────────────────────────────────────────

def add_bookmark(user_email, article: dict):
    """Bookmark an article. Returns (success, message)."""
    url = article.get("url", "")
    if not url:
        return False, "Article has no URL."
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO bookmarks (user_email, article_url, article_json, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_email, url, json.dumps(article), datetime.utcnow().isoformat()))
        conn.commit()
        return True, "Bookmarked."
    except sqlite3.IntegrityError:
        return False, "Already bookmarked."
    finally:
        conn.close()


def remove_bookmark(user_email, article_url):
    """Remove a bookmark."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM bookmarks WHERE user_email = ? AND article_url = ?",
                (user_email, article_url))
    conn.commit()
    conn.close()


def get_bookmarks(user_email):
    """Load all bookmarks for a user, newest first."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT article_json, created_at FROM bookmarks
        WHERE user_email = ?
        ORDER BY created_at DESC
    """, (user_email,))
    rows = cur.fetchall()
    conn.close()
    results = []
    for row in rows:
        article = json.loads(row[0])
        article["bookmarked_at"] = row[1]
        results.append(article)
    return results


def is_bookmarked(user_email, article_url):
    """Check if an article is bookmarked."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM bookmarks WHERE user_email = ? AND article_url = ?",
                (user_email, article_url))
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def get_bookmarked_urls(user_email):
    """Return set of all bookmarked URLs for quick lookup."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT article_url FROM bookmarks WHERE user_email = ?", (user_email,))
    urls = {row[0] for row in cur.fetchall()}
    conn.close()
    return urls


# ── Briefs cache operations ─────────────────────────────────────────────────

def save_brief(user_email, brief_type, region, brief_date, brief_data):
    """Save a daily or weekly brief. Upserts by (user, type, region, date)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO briefs_cache (user_email, brief_type, region, brief_date, brief_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_email, brief_type, region, brief_date) DO UPDATE SET
            brief_json = excluded.brief_json,
            created_at = excluded.created_at
    """, (user_email, brief_type, region, brief_date, json.dumps(brief_data),
          datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def load_brief(user_email, brief_type, region, brief_date):
    """Load a cached brief. Returns dict or None."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT brief_json FROM briefs_cache
        WHERE user_email = ? AND brief_type = ? AND region = ? AND brief_date = ?
    """, (user_email, brief_type, region, brief_date))
    row = cur.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None


# ── Persistent login sessions ───────────────────────────────────────────────

_SESSION_DAYS = 45

def create_login_session(user_email):
    """Create a persistent login token valid for 45 days. Returns token string."""
    token = secrets.token_urlsafe(48)
    expires = (datetime.utcnow() + timedelta(days=_SESSION_DAYS)).isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO login_sessions (user_email, session_token, expires_at, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_email.strip().lower(), token, expires, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return token


def validate_login_session(token):
    """Validate a session token. Returns user dict or None if expired/invalid."""
    if not token:
        return None
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_email, expires_at FROM login_sessions
        WHERE session_token = ?
    """, (token,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    email, expires_at = row
    if datetime.fromisoformat(expires_at) < datetime.utcnow():
        # Expired — clean up
        delete_login_session(token)
        return None
    return load_user_by_email(email)


def delete_login_session(token):
    """Remove a session token (logout)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM login_sessions WHERE session_token = ?", (token,))
    conn.commit()
    conn.close()


def delete_user_sessions(user_email):
    """Remove all sessions for a user."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM login_sessions WHERE user_email = ?",
                (user_email.strip().lower(),))
    conn.commit()
    conn.close()


def cleanup_expired_sessions():
    """Remove all expired session tokens."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM login_sessions WHERE expires_at < ?",
                (datetime.utcnow().isoformat(),))
    conn.commit()
    conn.close()


# ── Password reset ──────────────────────────────────────────────────────────

def update_password(email, current_password, new_password):
    """Change password. Returns (success, message)."""
    email = email.strip().lower()
    current_hash = hash_password(current_password)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE email = ? AND password_hash = ?",
                (email, current_hash))
    if not cur.fetchone():
        conn.close()
        return False, "Current password is incorrect."
    new_hash = hash_password(new_password)
    cur.execute("UPDATE users SET password_hash = ? WHERE email = ?",
                (new_hash, email))
    conn.commit()
    conn.close()
    return True, "Password updated successfully."

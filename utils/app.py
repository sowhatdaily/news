import html as _html
import json as _json
import os as _os
import streamlit as st
from datetime import date, datetime

from ai_service import (
    run_for_you_pipeline,
    run_company_news_pipeline,
    run_daily_brief_pipeline,
    run_weekly_brief_pipeline,
    run_theme_synthesis_pipeline,
    run_personalization_for_article,
    run_sector_sentiment_for_article,
    fetch_stock_prices,
    derive_signal_category,
)
from core import (
    APP_TITLE,
    PERSONAS,
    EXPERIENCE_LEVELS,
    GEOGRAPHIES,
    SECTOR_OPTIONS,
    SECTOR_SUBINTERESTS,
    generate_ai_outputs,
)
from db import (
    init_db,
    authenticate_user,
    create_user,
    load_user_by_email,
    save_summary,
    update_user_preferences,
    save_news_cache,
    load_news_cache,
    clear_old_cache,
    get_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    add_bookmark,
    remove_bookmark,
    get_bookmarks,
    get_bookmarked_urls,
    save_brief,
    load_brief,
    create_login_session,
    validate_login_session,
    delete_login_session,
    cleanup_expired_sessions,
    update_password,
)

from ai_service.client import exa_client, openai_client

init_db()
cleanup_expired_sessions()

# Check if required API clients are initialized
_missing_config = []
if not openai_client:
    _missing_config.append("OPENAI_API_KEY")
if not exa_client:
    _missing_config.append("EXA_API_KEY")

# ---------- Persistent Login (45 days) ----------
# Tokens are stored in the browser URL via st.query_params (per-browser-tab,
# survives reloads).  This replaces the old server-side file which was shared
# across ALL users — the root cause of the "seeing another user's session" bug.

def _save_session_token(token: str):
    """Persist session token in the browser URL query params."""
    st.query_params["token"] = token


def _load_session_token() -> str:
    """Load session token from browser query params, or empty string."""
    return st.query_params.get("token", "")


def _clear_session_token():
    """Remove session token from browser query params."""
    if "token" in st.query_params:
        del st.query_params["token"]


# ---------- Session State ----------
_defaults = {
    "auth_user": None,
    "auth_mode": "signin",
    "signup_data": {"full_name": "", "email": "", "password": "", "confirm_password": ""},
    "onboarding_step": 0,
    "onboarding_answers": {
        "persona": None, "experience_level": None, "main_sectors": [],
        "sub_interests": {}, "geography": None, "output_preference": None,
    },
    "selected_sector_index": 0,
    "post_login_message": None,
    "for_you_feed": None,
    "for_you_feed_date": None,
    "company_feed": None,
    "company_feed_date": None,
    "bookmarked_urls": set(),
    "daily_brief": None,
    "daily_brief_date": None,
    "weekly_brief": None,
    "weekly_brief_date": None,
    "theme_syntheses": None,
}
for key, val in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

st.set_page_config(page_title=APP_TITLE, page_icon="✨", layout="wide")

# ---------- Global CSS ----------
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; color: #1e293b; }
    .brand-pill {
        display: inline-block; padding: 0.3rem 0.8rem; border-radius: 999px;
        background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2);
        color: #6366f1; font-size: 0.82rem; font-weight: 500; margin-bottom: 0.75rem;
    }
    .hero-title {
        font-size: 2.4rem; line-height: 1.15; font-weight: 800; color: #0f172a;
        margin-bottom: 0.35rem; letter-spacing: -0.03em;
    }
    .hero-subtitle {
        color: #64748b; font-size: 1rem; margin-bottom: 1.2rem; max-width: 860px;
    }
    .glass-card {
        background: white; border: 1px solid #e2e8f0; border-radius: 18px;
        padding: 1.2rem; box-shadow: 0 1px 6px rgba(0,0,0,0.06); margin-bottom: 1rem;
    }
    .chat-bot {
        background: rgba(99,102,241,0.05); border: 1px solid rgba(99,102,241,0.15);
        color: #1e293b; padding: 0.9rem 1rem; border-radius: 18px 18px 18px 6px;
        margin-bottom: 0.65rem; max-width: 860px;
    }
    .chat-user {
        background: rgba(16,185,129,0.05); border: 1px solid rgba(16,185,129,0.18);
        color: #1e293b; padding: 0.8rem 1rem; border-radius: 18px 18px 6px 18px;
        margin: 0.5rem 0 0.75rem auto; max-width: 860px; text-align: left;
    }
    .profile-chip {
        display: inline-block; padding: 0.2rem 0.6rem; border-radius: 999px;
        background: #f1f5f9; border: 1px solid #e2e8f0; color: #475569;
        margin: 0.2rem 0.3rem 0.2rem 0; font-size: 0.8rem;
    }
    /* ── Market ticker ── */
    .ticker-table {
        width: 100%; border-collapse: separate; border-spacing: 0;
        background: white; border-radius: 14px; overflow: hidden;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    .ticker-table th {
        background: #f8fafc; color: #64748b; font-size: 0.72rem;
        text-transform: uppercase; letter-spacing: 0.06em; padding: 0.6rem 1rem;
        border-bottom: 1px solid #e2e8f0; text-align: left; font-weight: 600;
    }
    .ticker-table td {
        padding: 0.7rem 1rem; font-size: 0.88rem; color: #1e293b;
        border-bottom: 1px solid #f1f5f9; font-weight: 500;
    }
    .ticker-table tr:last-child td { border-bottom: none; }
    .ticker-up { color: #059669; font-weight: 700; }
    .ticker-down { color: #dc2626; font-weight: 700; }
    .ticker-neutral { color: #64748b; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='brand-pill'>Personalized intelligence for professionals</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-title'>{APP_TITLE}</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='hero-subtitle'>A cleaner way to personalize your news, understand why a story matters, and turn articles into sharp briefs.</div>",
    unsafe_allow_html=True,
)


# ---------- Helpers ----------
def reset_onboarding():
    st.session_state.onboarding_step = 0
    st.session_state.selected_sector_index = 0
    st.session_state.onboarding_answers = {
        "persona": None, "experience_level": None, "main_sectors": [],
        "sub_interests": {}, "geography": None, "output_preference": None,
    }


def reset_signup():
    st.session_state.signup_data = {"full_name": "", "email": "", "password": "", "confirm_password": ""}
    reset_onboarding()


def onboarding_complete(answers):
    return all([answers.get("persona"), answers.get("experience_level"),
                answers.get("main_sectors"), answers.get("geography")])


def build_interest_flat_list(answers):
    flat = list(answers.get("main_sectors", []))
    for sector, subs in answers.get("sub_interests", {}).items():
        flat.extend(subs)
    seen = set()
    out = []
    for item in flat:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


# ---------- Market Ticker ----------

def render_market_ticker(watchlist_symbols):
    """
    Render the market overview table at the top.
    Uses Exa + LLM to fetch live stock prices for NIFTY, SENSEX + watchlist.
    Cached in session state to avoid re-fetching on every rerun.
    """
    all_symbols = ["NIFTY 50", "SENSEX"] + list(watchlist_symbols)

    # Cache ticker data in session for the current day
    cache_key = "ticker_data"
    cache_date_key = "ticker_data_date"
    today_str = str(date.today())

    if (cache_key not in st.session_state
            or st.session_state.get(cache_date_key) != today_str
            or st.session_state[cache_key] is None):
        with st.spinner("Fetching market data…"):
            data = fetch_stock_prices(all_symbols)
        st.session_state[cache_key] = data
        st.session_state[cache_date_key] = today_str
    else:
        data = st.session_state[cache_key]

    if not data:
        return

    table_rows = ""
    for item in data:
        name = _html.escape(item["name"])
        price = item["price"]
        change = item["change"]
        pct = item["change_pct"]

        if change > 0:
            arrow = "▲"
            css_class = "ticker-up"
            row_bg = "rgba(5, 150, 105, 0.04)"
        elif change < 0:
            arrow = "▼"
            css_class = "ticker-down"
            row_bg = "rgba(220, 38, 38, 0.04)"
        else:
            arrow = "–"
            css_class = "ticker-neutral"
            row_bg = "transparent"

        price_str = f"₹{price:,.2f}" if price else "—"
        change_str = f"<span class='{css_class}'>{arrow} {abs(change):,.2f}</span>" if price else "—"
        pct_str = f"<span class='{css_class}'>({abs(pct):.2f}%)</span>" if price else ""

        table_rows += (
            f"<tr style='background:{row_bg};'>"
            f"<td style='font-weight:700;'>{name}</td>"
            f"<td>{price_str}</td>"
            f"<td>{change_str} {pct_str}</td>"
            f"</tr>"
        )

    # Refresh button
    col_t, col_r = st.columns([6, 1])
    with col_r:
        if st.button("↻ Refresh", key="ticker_refresh", help="Refresh market data"):
            st.session_state[cache_key] = None
            st.rerun()

    st.markdown(
        f"<table class='ticker-table'>"
        f"<tr><th>Index / Stock</th><th>Price</th><th>Change</th></tr>"
        f"{table_rows}</table>",
        unsafe_allow_html=True,
    )


# ---------- Auth Screens ----------
def render_chat_history_preview():
    a = st.session_state.onboarding_answers
    if a.get("persona"):
        st.markdown(f"<div class='chat-user'><strong>You:</strong> {a['persona']}</div>", unsafe_allow_html=True)
    if a.get("experience_level"):
        st.markdown(f"<div class='chat-user'><strong>You:</strong> {a['experience_level']}</div>", unsafe_allow_html=True)
    if a.get("main_sectors"):
        st.markdown(f"<div class='chat-user'><strong>You:</strong> {', '.join(a['main_sectors'])}</div>", unsafe_allow_html=True)
        for sector in a["main_sectors"]:
            chosen = a["sub_interests"].get(sector, [])
            if chosen:
                st.markdown(f"<div class='chat-user'><strong>{sector}:</strong> {', '.join(chosen)}</div>", unsafe_allow_html=True)
    if a.get("geography"):
        st.markdown(f"<div class='chat-user'><strong>You:</strong> {a['geography']}</div>", unsafe_allow_html=True)


def render_signin():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Sign in")
    with st.form("signin_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        remember = st.checkbox("Remember me", value=True)
        submitted = st.form_submit_button("Sign in", use_container_width=True)
        if submitted:
            user = authenticate_user(email, password)
            if user:
                st.session_state.auth_user = user
                st.session_state.post_login_message = f"Welcome back, {user['full_name']}."
                if remember:
                    token = create_login_session(user["email"])
                    _save_session_token(token)
                st.rerun()
            else:
                st.error("Invalid email or password.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_signup():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Create your account")
    with st.form("signup_form"):
        full_name = st.text_input("Full name", value=st.session_state.signup_data["full_name"])
        email = st.text_input("Email", value=st.session_state.signup_data["email"])
        password = st.text_input("Password", type="password", value=st.session_state.signup_data["password"])
        confirm_password = st.text_input("Confirm password", type="password", value=st.session_state.signup_data["confirm_password"])
        submitted = st.form_submit_button("Continue to onboarding", use_container_width=True)

        if submitted:
            if not full_name.strip() or not email.strip() or not password.strip():
                st.error("Please fill all required fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password should be at least 6 characters.")
            else:
                st.session_state.signup_data = {
                    "full_name": full_name.strip(), "email": email.strip(),
                    "password": password, "confirm_password": confirm_password,
                }
                reset_onboarding()
                st.session_state.auth_mode = "signup_onboarding"
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_signup_onboarding():
    answers = st.session_state.onboarding_answers
    step = st.session_state.onboarding_step
    main_sectors = answers.get("main_sectors", [])

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Onboarding chat")
    st.caption("A few quick choices and your feed will be ready.")
    st.markdown("</div>", unsafe_allow_html=True)

    render_chat_history_preview()

    if step == 0:
        st.markdown("<div class='chat-bot'><strong>Anonimous AI:</strong> Which best describes you?</div>", unsafe_allow_html=True)
        choice = st.radio("Who are you?", PERSONAS, label_visibility="collapsed")
        if st.button("Next", use_container_width=True):
            answers["persona"] = choice
            st.session_state.onboarding_step = 1
            st.rerun()

    elif step == 1:
        st.markdown("<div class='chat-bot'><strong>Anonimous AI:</strong> How would you describe your experience level?</div>", unsafe_allow_html=True)
        choice = st.radio("Experience", EXPERIENCE_LEVELS, label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back", use_container_width=True):
                st.session_state.onboarding_step = 0
                st.rerun()
        with c2:
            if st.button("Next ", use_container_width=True):
                answers["experience_level"] = choice
                st.session_state.onboarding_step = 2
                st.rerun()

    elif step == 2:
        st.markdown("<div class='chat-bot'><strong>Anonimous AI:</strong> Which sectors do you want to follow? Select as many as you like.</div>", unsafe_allow_html=True)
        selected = st.multiselect(
            "Choose sectors", SECTOR_OPTIONS,
            default=answers.get("main_sectors", []), label_visibility="collapsed",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back ", use_container_width=True):
                st.session_state.onboarding_step = 1
                st.rerun()
        with c2:
            if st.button("Next  ", use_container_width=True):
                if not selected:
                    st.error("Please choose at least 1 sector.")
                else:
                    answers["main_sectors"] = selected
                    for sector in selected:
                        answers["sub_interests"].setdefault(sector, [])
                    answers["sub_interests"] = {k: v for k, v in answers["sub_interests"].items() if k in selected}
                    st.session_state.selected_sector_index = 0
                    st.session_state.onboarding_step = 3
                    st.rerun()

    elif step == 3:
        idx = st.session_state.selected_sector_index
        current_sector = main_sectors[idx]
        st.markdown(
            f"<div class='chat-bot'><strong>Anonimous AI:</strong> Within <strong>{current_sector}</strong>, what should I track? Pick up to 3. Optional.</div>",
            unsafe_allow_html=True
        )
        selected_subs = st.multiselect(
            current_sector, SECTOR_SUBINTERESTS[current_sector],
            default=answers["sub_interests"].get(current_sector, []),
            max_selections=3, label_visibility="collapsed", key=f"sub_{current_sector}",
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Back  ", use_container_width=True):
                if idx == 0:
                    st.session_state.onboarding_step = 2
                else:
                    answers["sub_interests"][current_sector] = selected_subs
                    st.session_state.selected_sector_index = idx - 1
                st.rerun()
        with c2:
            if st.button("Skip", use_container_width=True):
                answers["sub_interests"][current_sector] = []
                if idx < len(main_sectors) - 1:
                    st.session_state.selected_sector_index = idx + 1
                else:
                    st.session_state.onboarding_step = 4
                st.rerun()
        with c3:
            if st.button("Continue", use_container_width=True):
                answers["sub_interests"][current_sector] = selected_subs
                if idx < len(main_sectors) - 1:
                    st.session_state.selected_sector_index = idx + 1
                else:
                    st.session_state.onboarding_step = 4
                st.rerun()

    elif step == 4:
        st.markdown("<div class='chat-bot'><strong>Anonimous AI:</strong> Which geography matters most to you?</div>", unsafe_allow_html=True)
        choice = st.radio("Geography", GEOGRAPHIES, label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back   ", use_container_width=True):
                st.session_state.onboarding_step = 3
                st.session_state.selected_sector_index = max(len(main_sectors) - 1, 0)
                st.rerun()
        with c2:
            if st.button("Finish onboarding", type="primary", use_container_width=True):
                answers["geography"] = choice
                if not onboarding_complete(answers):
                    st.error("Some onboarding details are still missing.")
                    return

                flat_interests = build_interest_flat_list(answers)
                ok, msg = create_user(
                    full_name=st.session_state.signup_data["full_name"],
                    email=st.session_state.signup_data["email"],
                    password=st.session_state.signup_data["password"],
                    persona=answers["persona"],
                    years_experience=answers["experience_level"],
                    interests=flat_interests,
                    onboarding_payload=answers,
                    geography=answers["geography"],
                    output_preference="All of the above",
                )
                if ok:
                    new_user = load_user_by_email(st.session_state.signup_data["email"])
                    st.session_state.auth_user = new_user
                    st.session_state.post_login_message = f"Welcome, {new_user['full_name']}."
                    token = create_login_session(new_user["email"])
                    _save_session_token(token)
                    reset_signup()
                    st.rerun()
                else:
                    st.error(msg)

    with st.sidebar:
        st.markdown("### Signup")
        if st.button("Start over", use_container_width=True):
            reset_signup()
            st.session_state.auth_mode = "signup"
            st.rerun()


def render_sidebar_logged_out():
    with st.sidebar:
        mode = st.radio(
            "Mode", ["signin", "signup"],
            index=0 if st.session_state.auth_mode == "signin" else 1,
            format_func=lambda x: "Sign in" if x == "signin" else "Sign up",
            label_visibility="collapsed",
        )
        if st.session_state.auth_mode != "signup_onboarding":
            st.session_state.auth_mode = mode


# ---------- Impact display helpers ----------

def _score_color(score: int) -> str:
    if score >= 7:   return "#059669"
    if score >= 4:   return "#16a34a"
    if score >= 1:   return "#22c55e"
    if score <= -7:  return "#dc2626"
    if score <= -4:  return "#ef4444"
    if score <= -1:  return "#f87171"
    return "#94a3b8"


def _border_color(score: int) -> str:
    if score > 0:  return "#22c55e"
    if score < 0:  return "#ef4444"
    return "#e2e8f0"


def _fmt_date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return iso[:10] if iso else ""


def _signal_icon(category: str) -> str:
    icons = {"high_impact": "&#x1F525;", "developing": "&#x26A1;", "watch": "&#x1F440;", "low_urgency": "&#x1F9CA;"}
    return icons.get(category, "")


def _direction_dot(direction: str) -> str:
    colors = {"positive": "#059669", "negative": "#dc2626", "mixed": "#d97706"}
    c = colors.get(direction, "#94a3b8")
    return f"<span style='color:{c};font-size:1.1rem;'>&#x25CF;</span>"


def _signal_label(category: str) -> str:
    labels = {"high_impact": "High Impact", "developing": "Developing", "watch": "Watch", "low_urgency": "Low Urgency"}
    return labels.get(category, "")


def render_news_card(item: dict, badge_label: str = "India", card_key: str = ""):
    score        = item.get("impact_score", 0)
    txt_color    = _score_color(score)
    bdr_color    = _border_color(score)
    score_label  = f"+{score}" if score > 0 else str(score)
    url          = item.get("url", "#")
    pub_date     = _fmt_date(item.get("published_date", ""))

    title        = _html.escape(item.get("title", "Untitled"))
    source       = _html.escape(item.get("source", ""))
    sector       = _html.escape(item.get("sector", ""))
    impact_chain = _html.escape(item.get("impact_chain", ""))
    affected     = [_html.escape(s) for s in item.get("affected_sectors", [])]

    # New structured fields
    what_happened   = _html.escape(item.get("what_happened", ""))
    so_what         = _html.escape(item.get("so_what", ""))
    who_is_affected = [_html.escape(s) for s in (item.get("who_is_affected") or [])]
    what_to_watch   = [_html.escape(s) for s in (item.get("what_to_watch") or [])]
    signal_dir      = item.get("signal_direction", "mixed")
    signal_cat      = item.get("signal_category", derive_signal_category(score))
    signal_reason   = _html.escape(item.get("signal_reason", ""))

    meta = " · ".join(filter(None, [source, pub_date]))

    if score > 0:
        badge_bg, badge_bdr = "rgba(34,197,94,0.08)",  "rgba(34,197,94,0.3)"
    elif score < 0:
        badge_bg, badge_bdr = "rgba(239,68,68,0.08)",  "rgba(239,68,68,0.3)"
    else:
        badge_bg, badge_bdr = "rgba(148,163,184,0.08)", "rgba(148,163,184,0.3)"

    sector_chip = (
        f"<span style='background:#f1f5f9;border:1px solid #e2e8f0;border-radius:999px;"
        f"padding:2px 10px;font-size:0.74rem;color:#475569;margin-right:0.4rem;"
        f"font-weight:500;'>{sector}</span>"
    ) if sector else ""

    affected_chips = "".join(
        f"<span style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:999px;"
        f"padding:1px 8px;font-size:0.72rem;color:#64748b;margin-right:0.3rem;'>{s}</span>"
        for s in affected
    )

    who_chips = "".join(
        f"<span style='background:#eff6ff;border:1px solid #bfdbfe;border-radius:999px;"
        f"padding:1px 8px;font-size:0.72rem;color:#1e40af;margin-right:0.3rem;margin-bottom:0.2rem;"
        f"display:inline-block;'>{s}</span>"
        for s in who_is_affected
    )

    watch_items = "".join(
        f"<div style='color:#475569;font-size:0.8rem;line-height:1.5;padding-left:0.8rem;"
        f"border-left:2px solid #e2e8f0;margin-bottom:0.2rem;'>{s}</div>"
        for s in what_to_watch
    )

    chain_color = "#2563eb" if score >= 0 else "#dc2626"

    # Signal badge: direction dot + icon + score + category label
    signal_badge_html = (
        f"<div style='background:{badge_bg};border:1px solid {badge_bdr};border-radius:10px;"
        f"padding:0.5rem 0.7rem;text-align:center;min-width:68px;flex-shrink:0;'>"
        f"<div style='font-size:0.7rem;margin-bottom:2px;'>{_direction_dot(signal_dir)} {_signal_icon(signal_cat)}</div>"
        f"<div style='font-size:1.7rem;font-weight:900;color:{txt_color};line-height:1;"
        f"letter-spacing:-0.03em;'>{score_label}</div>"
        f"<div style='color:#94a3b8;font-size:0.6rem;margin-top:3px;"
        f"letter-spacing:0.04em;text-transform:uppercase;font-weight:600;'>{_html.escape(_signal_label(signal_cat))}</div>"
        f"<div style='color:#94a3b8;font-size:0.58rem;margin-top:1px;"
        f"letter-spacing:0.05em;text-transform:uppercase;'>{_html.escape(badge_label)}</div>"
        f"</div>"
    )

    # What happened + So what (always visible) — styled with accent borders
    structured_visible = ""
    if what_happened and what_happened != "Analysis unavailable.":
        structured_visible += (
            f"<div style='margin-top:0.6rem;background:#f8fafc;border-left:3px solid #6366f1;"
            f"border-radius:0 8px 8px 0;padding:0.55rem 0.75rem;'>"
            f"<div style='font-size:0.68rem;font-weight:800;color:#6366f1;text-transform:uppercase;"
            f"letter-spacing:0.06em;margin-bottom:0.2rem;'>What happened</div>"
            f"<div style='color:#1e293b;font-size:0.85rem;line-height:1.6;font-weight:450;'>{what_happened}</div>"
            f"</div>"
        )
    if so_what and so_what != "Analysis unavailable.":
        structured_visible += (
            f"<div style='margin-top:0.4rem;background:#fefce8;border-left:3px solid #d97706;"
            f"border-radius:0 8px 8px 0;padding:0.55rem 0.75rem;'>"
            f"<div style='font-size:0.68rem;font-weight:800;color:#b45309;text-transform:uppercase;"
            f"letter-spacing:0.06em;margin-bottom:0.2rem;'>So what</div>"
            f"<div style='color:#1e293b;font-size:0.85rem;line-height:1.6;font-weight:450;'>{so_what}</div>"
            f"</div>"
        )

    # Render the main card HTML
    st.markdown(
        f"<div style='background:white;border:1px solid #e2e8f0;"
        f"border-left:4px solid {bdr_color};border-radius:14px;"
        f"padding:1rem 1.1rem;margin-bottom:0.65rem;box-shadow:0 1px 4px rgba(0,0,0,0.05);'>"
        f"<div style='display:flex;gap:1rem;align-items:flex-start;'>"
        f"<div style='flex:1;min-width:0;'>"
        f"<div style='margin-bottom:0.3rem;'>{sector_chip}</div>"
        f"<div style='margin:0 0 0.18rem;font-size:0.95rem;font-weight:700;color:#0f172a;line-height:1.4;'>"
        f"<a href='{url}' target='_blank' style='color:#0f172a;text-decoration:none;'>{title}</a></div>"
        f"<div style='color:#94a3b8;font-size:0.78rem;margin-bottom:0.5rem;'>{meta}</div>"
        f"{structured_visible}"
        f"<div style='color:{chain_color};font-size:0.8rem;margin-top:0.4rem;line-height:1.5;opacity:0.85;'>"
        f"&#x27F6;&nbsp;{impact_chain}</div>"
        f"<div style='margin-top:0.5rem;'>{affected_chips}</div>"
        f"</div>"
        f"{signal_badge_html}"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    # Expandable section: Who is affected + What to watch + Signal reason
    if who_is_affected or what_to_watch or signal_reason:
        with st.expander("Who is affected · What to watch", expanded=False):
            if who_is_affected:
                st.markdown(
                    f"<div style='margin-bottom:0.5rem;'>"
                    f"<div style='font-size:0.7rem;font-weight:700;color:#64748b;text-transform:uppercase;"
                    f"letter-spacing:0.05em;margin-bottom:0.3rem;'>Who is affected</div>"
                    f"{who_chips}</div>",
                    unsafe_allow_html=True,
                )
            if what_to_watch:
                st.markdown(
                    f"<div style='margin-bottom:0.5rem;'>"
                    f"<div style='font-size:0.7rem;font-weight:700;color:#64748b;text-transform:uppercase;"
                    f"letter-spacing:0.05em;margin-bottom:0.3rem;'>What to watch</div>"
                    f"{watch_items}</div>",
                    unsafe_allow_html=True,
                )
            if signal_reason:
                st.markdown(
                    f"<div style='font-size:0.7rem;font-weight:700;color:#64748b;text-transform:uppercase;"
                    f"letter-spacing:0.05em;margin-bottom:0.15rem;'>Signal reason</div>"
                    f"<div style='color:#475569;font-size:0.82rem;line-height:1.5;'>{signal_reason}</div>",
                    unsafe_allow_html=True,
                )


# ---------- Filter & Sort helpers ----------

def _apply_filters(feed, sector_filter, score_filter, sort_by):
    """Filter and sort the news feed."""
    filtered = list(feed)

    if sector_filter and sector_filter != "All":
        filtered = [a for a in filtered if a.get("sector", "") == sector_filter]

    if score_filter == "Positive only":
        filtered = [a for a in filtered if a.get("impact_score", 0) > 0]
    elif score_filter == "Negative only":
        filtered = [a for a in filtered if a.get("impact_score", 0) < 0]

    if sort_by == "Impact (high to low)":
        filtered.sort(key=lambda x: abs(x.get("impact_score", 0)), reverse=True)
    elif sort_by == "Impact (low to high)":
        filtered.sort(key=lambda x: abs(x.get("impact_score", 0)))
    elif sort_by == "Newest first":
        filtered.sort(key=lambda x: x.get("published_date", ""), reverse=True)
    elif sort_by == "Oldest first":
        filtered.sort(key=lambda x: x.get("published_date", ""))

    return filtered


def render_filter_bar(feed, key_prefix="fy"):
    """Render filter and sort controls. Returns (sector_filter, score_filter, sort_by)."""
    all_sectors = sorted(set(a.get("sector", "") for a in feed if a.get("sector")))

    c1, c2, c3 = st.columns(3)
    with c1:
        sector_filter = st.selectbox(
            "Filter by sector", ["All"] + all_sectors,
            key=f"{key_prefix}_sector_filter",
        )
    with c2:
        score_filter = st.selectbox(
            "Filter by impact", ["All", "Positive only", "Negative only"],
            key=f"{key_prefix}_score_filter",
        )
    with c3:
        sort_by = st.selectbox(
            "Sort by", ["Impact (high to low)", "Impact (low to high)", "Newest first", "Oldest first"],
            key=f"{key_prefix}_sort",
        )
    return sector_filter, score_filter, sort_by


# ---------- Settings Section ----------

def render_settings(user):
    """Settings tab: update topics/subtopics preferences."""
    onboarding = user.get("onboarding", {})
    current_sectors = onboarding.get("main_sectors", [])
    current_subs = onboarding.get("sub_interests", {})

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Update your preferences")
    st.caption("Change the sectors and sub-topics you follow. Max 3 sub-topics per sector.")

    with st.form("settings_form"):
        new_sectors = st.multiselect(
            "Sectors to follow", SECTOR_OPTIONS,
            default=current_sectors,
        )

        st.markdown("---")
        st.markdown("**Sub-topics** (up to 3 per sector)")

        new_subs = {}
        for sector in new_sectors:
            if sector in SECTOR_SUBINTERESTS:
                defaults = [s for s in current_subs.get(sector, []) if s in SECTOR_SUBINTERESTS[sector]][:3]
                chosen = st.multiselect(
                    sector, SECTOR_SUBINTERESTS[sector],
                    default=defaults, max_selections=3,
                    key=f"settings_sub_{sector}",
                )
                new_subs[sector] = chosen

        submitted = st.form_submit_button("Save preferences", type="primary", use_container_width=True)

        if submitted:
            if not new_sectors:
                st.error("Select at least one sector.")
            else:
                new_onboarding = {**onboarding, "main_sectors": new_sectors, "sub_interests": new_subs}
                flat = build_interest_flat_list(new_onboarding)
                update_user_preferences(user["email"], new_onboarding, flat)

                # Refresh user in session
                refreshed = load_user_by_email(user["email"])
                st.session_state.auth_user = refreshed
                # Invalidate feed cache so next load picks up new preferences
                st.session_state.for_you_feed = None
                st.session_state.for_you_feed_date = None
                st.success("Preferences saved. Your feed will update on next refresh.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Watchlist management ──
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Stock watchlist")
    st.caption("Track up to 5 company symbols. These appear in the market ticker and Company News tab.")

    watchlist = get_watchlist(user["email"])
    if watchlist:
        for sym in watchlist:
            col_sym, col_rm = st.columns([4, 1])
            with col_sym:
                st.markdown(f"**{sym}**")
            with col_rm:
                if st.button("✕", key=f"rm_{sym}", help=f"Remove {sym}"):
                    remove_from_watchlist(user["email"], sym)
                    st.rerun()

    if len(watchlist) < 5:
        with st.form("add_symbol_form"):
            new_sym = st.text_input("Enter stock symbol (e.g. RELIANCE, TCS, INFY)", max_chars=20)
            if st.form_submit_button("Add to watchlist", use_container_width=True):
                ok, msg = add_to_watchlist(user["email"], new_sym)
                if ok:
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.info("Watchlist full (5/5). Remove a symbol to add a new one.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Change password ──
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Change password")
    with st.form("change_password_form"):
        current_pw = st.text_input("Current password", type="password")
        new_pw = st.text_input("New password", type="password")
        confirm_pw = st.text_input("Confirm new password", type="password")
        pw_submitted = st.form_submit_button("Update password", type="primary", use_container_width=True)
        if pw_submitted:
            if not current_pw or not new_pw:
                st.error("Please fill all fields.")
            elif len(new_pw) < 6:
                st.error("New password must be at least 6 characters.")
            elif new_pw != confirm_pw:
                st.error("New passwords do not match.")
            else:
                ok, msg = update_password(user["email"], current_pw, new_pw)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
    st.markdown("</div>", unsafe_allow_html=True)


# ---------- Bookmark helper ----------

def render_bookmark_button(item: dict, user_email: str, key_prefix: str, idx: int):
    """Render a heart bookmark/unbookmark button for an article."""
    url = item.get("url", "")
    if not url:
        return
    bookmarked = url in st.session_state.bookmarked_urls
    btn_key = f"bm_{key_prefix}_{idx}"
    if st.button(
        "\u2764\uFE0F" if bookmarked else "\U0001F90D",
        key=btn_key,
        help="Remove from saved" if bookmarked else "Save article",
    ):
        if bookmarked:
            remove_bookmark(user_email, url)
            st.session_state.bookmarked_urls.discard(url)
        else:
            add_bookmark(user_email, item)
            st.session_state.bookmarked_urls.add(url)
        st.rerun()


def render_feed_with_bookmarks(displayed: list, user_email: str, key_prefix: str, badge_label_fn=None):
    """Render a list of articles with bookmark buttons."""
    for idx, item in enumerate(displayed):
        col_card, col_bm = st.columns([20, 1])
        with col_card:
            badge = badge_label_fn(item) if badge_label_fn else "India"
            render_news_card(item, badge_label=badge, card_key=f"{key_prefix}_{idx}")
        with col_bm:
            render_bookmark_button(item, user_email, key_prefix, idx)


# ---------- Daily Brief renderer ----------

def render_daily_brief_content(brief: dict):
    """Render a daily brief dict as styled HTML."""
    bottom_line = _html.escape(brief.get("bottom_line", ""))
    if bottom_line:
        st.markdown(
            f"<div style='background:rgba(99,102,241,0.05);border:1px solid rgba(99,102,241,0.15);"
            f"border-radius:14px;padding:1rem 1.2rem;margin-bottom:1rem;'>"
            f"<div style='font-size:0.7rem;font-weight:700;color:#6366f1;text-transform:uppercase;"
            f"letter-spacing:0.06em;margin-bottom:0.4rem;'>Bottom line</div>"
            f"<div style='color:#1e293b;font-size:0.92rem;line-height:1.6;'>{bottom_line}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    developments = brief.get("top_developments", [])
    if developments:
        st.markdown("#### Key developments")
        for dev in developments:
            score = dev.get("signal_score", 0)
            direction = dev.get("signal_direction", "mixed")
            dir_color = {"positive": "#059669", "negative": "#dc2626", "mixed": "#d97706"}.get(direction, "#94a3b8")
            headline = _html.escape(dev.get("headline", ""))
            summary = _html.escape(dev.get("summary", ""))
            score_label = f"+{score}" if score > 0 else str(score)
            st.markdown(
                f"<div style='background:white;border:1px solid #e2e8f0;border-radius:10px;"
                f"padding:0.7rem 1rem;margin-bottom:0.5rem;display:flex;align-items:center;gap:0.8rem;'>"
                f"<div style='color:{dir_color};font-weight:900;font-size:1.1rem;min-width:36px;"
                f"text-align:center;'>{score_label}</div>"
                f"<div><div style='font-weight:700;font-size:0.88rem;color:#0f172a;'>{headline}</div>"
                f"<div style='color:#475569;font-size:0.82rem;margin-top:0.1rem;'>{summary}</div></div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    signals = brief.get("signals_today", [])
    if signals:
        st.markdown("#### Signals today")
        for sig in signals:
            st.markdown(f"- {sig}")

    watch = brief.get("what_to_watch_next", [])
    if watch:
        st.markdown("#### What to watch next")
        for w in watch:
            st.markdown(f"- {w}")


# ---------- Weekly Brief renderer ----------

def render_weekly_brief_content(brief: dict):
    """Render a weekly brief dict as styled HTML."""
    bottom_line = _html.escape(brief.get("bottom_line", ""))
    if bottom_line:
        st.markdown(
            f"<div style='background:rgba(99,102,241,0.05);border:1px solid rgba(99,102,241,0.15);"
            f"border-radius:14px;padding:1rem 1.2rem;margin-bottom:1rem;'>"
            f"<div style='font-size:0.7rem;font-weight:700;color:#6366f1;text-transform:uppercase;"
            f"letter-spacing:0.06em;margin-bottom:0.4rem;'>Week in review</div>"
            f"<div style='color:#1e293b;font-size:0.92rem;line-height:1.6;'>{bottom_line}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    shifts = brief.get("biggest_shifts", [])
    if shifts:
        st.markdown("#### Biggest shifts")
        for shift in shifts:
            direction = shift.get("direction", "mixed")
            dir_color = {"positive": "#059669", "negative": "#dc2626", "mixed": "#d97706"}.get(direction, "#94a3b8")
            theme = _html.escape(shift.get("theme", ""))
            desc = _html.escape(shift.get("description", ""))
            st.markdown(
                f"<div style='background:white;border:1px solid #e2e8f0;border-left:4px solid {dir_color};"
                f"border-radius:10px;padding:0.7rem 1rem;margin-bottom:0.5rem;'>"
                f"<div style='font-weight:700;font-size:0.88rem;color:#0f172a;'>{theme}</div>"
                f"<div style='color:#475569;font-size:0.82rem;margin-top:0.15rem;line-height:1.5;'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    themes = brief.get("recurring_themes", [])
    if themes:
        st.markdown("#### Recurring themes")
        for t in themes:
            st.markdown(f"- {t}")

    watch = brief.get("what_to_watch_next_week", [])
    if watch:
        st.markdown("#### What to watch next week")
        for w in watch:
            st.markdown(f"- {w}")


# ---------- Theme synthesis renderer (Phase 2) ----------

def render_theme_synthesis(synthesis: dict):
    """Render a single theme synthesis card."""
    theme = _html.escape(synthesis.get("theme", "").replace("_", " ").title())
    summary = _html.escape(synthesis.get("summary", ""))
    direction = synthesis.get("overall_direction", "mixed")
    confidence = synthesis.get("confidence", "medium")
    dir_color = {"positive": "#059669", "negative": "#dc2626", "mixed": "#d97706"}.get(direction, "#94a3b8")
    conf_badge = {"high": "#059669", "medium": "#d97706", "low": "#94a3b8"}.get(confidence, "#94a3b8")

    dir_rgb = {"positive": "5,150,105", "negative": "220,38,38", "mixed": "217,119,6"}.get(direction, "148,163,184")
    st.markdown(
        f"<div style='background:white;border:1px solid #e2e8f0;border-left:4px solid {dir_color};"
        f"border-radius:14px;padding:1rem 1.2rem;margin-bottom:0.8rem;"
        f"box-shadow:0 1px 4px rgba(0,0,0,0.05);'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;'>"
        f"<div style='font-weight:800;font-size:1rem;color:#0f172a;'>{theme}</div>"
        f"<div>"
        f"<span style='background:rgba({dir_rgb},0.1);"
        f"color:{dir_color};font-size:0.7rem;padding:2px 8px;border-radius:999px;font-weight:600;"
        f"margin-right:0.3rem;'>{direction}</span>"
        f"<span style='background:rgba(148,163,184,0.1);color:{conf_badge};font-size:0.7rem;"
        f"padding:2px 8px;border-radius:999px;font-weight:600;'>{confidence} confidence</span>"
        f"</div></div>"
        f"<div style='color:#334155;font-size:0.86rem;line-height:1.6;margin-bottom:0.5rem;'>{summary}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        changes = synthesis.get("key_changes", [])
        if changes:
            st.markdown("**Key changes**")
            for c in changes:
                st.markdown(f"- {c}")
        risks = synthesis.get("risks", [])
        if risks:
            st.markdown("**Risks**")
            for r in risks:
                st.markdown(f"- {r}")
    with col2:
        opps = synthesis.get("opportunities", [])
        if opps:
            st.markdown("**Opportunities**")
            for o in opps:
                st.markdown(f"- {o}")
        watch = synthesis.get("what_to_watch", [])
        if watch:
            st.markdown("**What to watch**")
            for w in watch:
                st.markdown(f"- {w}")


# ---------- Sector sentiment renderer (Phase 2) ----------

def render_sector_sentiments(sentiments: list):
    """Render sector sentiment badges."""
    if not sentiments:
        st.info("No sector sentiments available for this article.")
        return
    for s in sentiments:
        sector_name = _html.escape(s.get("sector", ""))
        direction = s.get("direction", "mixed")
        confidence = s.get("confidence", "medium")
        horizon = s.get("horizon", "medium_term").replace("_", " ")
        reason = _html.escape(s.get("reason", ""))
        dir_color = {"positive": "#059669", "negative": "#dc2626", "mixed": "#d97706"}.get(direction, "#94a3b8")
        st.markdown(
            f"<div style='background:white;border:1px solid #e2e8f0;border-left:3px solid {dir_color};"
            f"border-radius:8px;padding:0.5rem 0.8rem;margin-bottom:0.4rem;'>"
            f"<div style='display:flex;align-items:center;gap:0.5rem;'>"
            f"<span style='font-weight:700;font-size:0.84rem;color:#0f172a;'>{sector_name}</span>"
            f"<span style='color:{dir_color};font-size:0.72rem;font-weight:600;'>{direction}</span>"
            f"<span style='color:#94a3b8;font-size:0.68rem;'>{confidence} · {horizon}</span>"
            f"</div>"
            f"<div style='color:#475569;font-size:0.78rem;margin-top:0.15rem;'>{reason}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


# ---------- Main App ----------
def render_home(user):
    onboarding = user.get("onboarding", {})
    sectors = onboarding.get("main_sectors", [])
    sub_interests = onboarding.get("sub_interests", {})
    watchlist = get_watchlist(user["email"])
    geography = user.get("geography", "India")

    if st.session_state.post_login_message:
        st.success(st.session_state.post_login_message)
        st.session_state.post_login_message = None

    # ── Load bookmarked URLs into session ──
    if not st.session_state.bookmarked_urls:
        st.session_state.bookmarked_urls = get_bookmarked_urls(user["email"])

    # ── Clean old cache on each session ──
    clear_old_cache(user["email"])

    # ── Sidebar ──
    with st.sidebar:
        st.success(f"Signed in as {user['full_name']}")
        st.write(f"**Persona:** {user['persona']}")
        st.write(f"**Experience:** {user['years_experience']}")
        st.write(f"**Geography:** {user['geography']}")
        if sectors:
            st.markdown("**Tracking:**")
            for s in sectors:
                subs = sub_interests.get(s, [])
                label = f"{s}" + (f" ({', '.join(subs[:2])}{'…' if len(subs)>2 else ''})" if subs else "")
                st.markdown(f"- {label}")
        if watchlist:
            st.markdown("**Watchlist:**")
            st.markdown(", ".join(watchlist))

        # Signal legend
        st.markdown("---")
        st.markdown("**Signal legend**")
        st.markdown(
            "<div style='font-size:0.78rem;line-height:1.7;'>"
            "&#x1F525; <strong>High Impact</strong> (8-10)<br>"
            "&#x26A1; <strong>Developing</strong> (5-7)<br>"
            "&#x1F440; <strong>Watch</strong> (3-4)<br>"
            "&#x1F9CA; <strong>Low Urgency</strong> (1-2)<br>"
            "<span style='color:#059669;'>&#x25CF;</span> Positive &nbsp;"
            "<span style='color:#dc2626;'>&#x25CF;</span> Negative &nbsp;"
            "<span style='color:#d97706;'>&#x25CF;</span> Mixed"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        if st.button("Log out", use_container_width=True):
            # Clear persistent session
            saved_token = _load_session_token()
            if saved_token:
                delete_login_session(saved_token)
            _clear_session_token()
            st.session_state.auth_user = None
            st.session_state.auth_mode = "signin"
            for k in ["for_you_feed", "for_you_feed_date", "company_feed", "company_feed_date",
                       "bookmarked_urls", "daily_brief", "daily_brief_date",
                       "weekly_brief", "weekly_brief_date", "theme_syntheses"]:
                st.session_state[k] = None
            st.rerun()

    # ── Market Ticker (top of page) ──
    render_market_ticker(watchlist)

    # ── Tabs ──
    tab_news, tab_company, tab_daily, tab_weekly, tab_saved, tab_insights, tab_summarize, tab_settings = st.tabs(
        ["News", "Company News", "Daily Brief", "Weekly Brief", "Saved", "Insights", "Summarize", "Settings"]
    )

    # ── Tab 1 : News ─────────────────────────────────────────────────────────
    with tab_news:
        today = date.today()

        col_title, col_btn = st.columns([4, 1])
        with col_title:
            st.markdown(
                f"<h3 style='margin:0;color:#0f172a;'>Your feed — {today.strftime('%b %d, %Y')}</h3>",
                unsafe_allow_html=True,
            )
            if sectors:
                chips = "".join(f"<span class='profile-chip'>{_html.escape(s)}</span>" for s in sectors)
                st.markdown(chips, unsafe_allow_html=True)

        feed = st.session_state.for_you_feed
        if feed is None:
            cached = load_news_cache(user["email"], cache_type="sector")
            if cached:
                st.session_state.for_you_feed = cached
                st.session_state.for_you_feed_date = str(today)
                feed = cached

        with col_btn:
            refresh = st.button(
                "Refresh" if feed else "Load feed",
                type="primary", use_container_width=True,
            )

        if refresh:
            if not sectors:
                st.warning("Complete onboarding to set your sectors first.")
            else:
                with st.spinner(f"SoWhatDaily is Searching news across {len(sectors)} sector(s) · running impact analysis…"):
                    feed = run_for_you_pipeline(user)
                save_news_cache(user["email"], feed, cache_type="sector")
                st.session_state.for_you_feed = feed
                st.session_state.for_you_feed_date = str(today)
                # Auto-generate daily brief in the background
                if feed:
                    try:
                        daily = run_daily_brief_pipeline(feed, geography, str(today))
                        save_brief(user["email"], "daily", geography, str(today), daily)
                        st.session_state.daily_brief = daily
                        st.session_state.daily_brief_date = str(today)
                    except Exception:
                        pass
                st.rerun()

        if not feed:
            st.markdown(
                "<div style='color:#94a3b8; padding:2rem 0; text-align:center;'>"
                "Click <strong style='color:#475569;'>Load feed</strong> to fetch "
                "this week's personalised news with structured insights and impact signals."
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.caption(f"{len(feed)} articles · last 7 days · sorted by India impact")

            sector_filter, score_filter, sort_by = render_filter_bar(feed, key_prefix="fy")
            displayed = _apply_filters(feed, sector_filter, score_filter, sort_by)

            if not displayed:
                st.info("No articles match the current filters.")
            else:
                st.caption(f"Showing {len(displayed)} of {len(feed)} articles")
                render_feed_with_bookmarks(displayed, user["email"], "fy")

    # ── Tab 2 : Company News ─────────────────────────────────────────────────
    with tab_company:
        if not watchlist:
            st.markdown(
                "<div style='color:#94a3b8; padding:2rem 0; text-align:center;'>"
                "Add stock symbols in the <strong style='color:#475569;'>Settings</strong> tab "
                "to see company-specific news and impact analysis here."
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<h3 style='margin:0;color:#0f172a;'>Company News — {', '.join(watchlist)}</h3>",
                unsafe_allow_html=True,
            )

            cfeed = st.session_state.company_feed
            if cfeed is None:
                cached_company = load_news_cache(user["email"], cache_type="company")
                if cached_company:
                    st.session_state.company_feed = cached_company
                    st.session_state.company_feed_date = str(date.today())
                    cfeed = cached_company

            col_info, col_cbtn = st.columns([4, 1])
            with col_info:
                chips = "".join(f"<span class='profile-chip'>{_html.escape(s)}</span>" for s in watchlist)
                st.markdown(chips, unsafe_allow_html=True)
            with col_cbtn:
                c_refresh = st.button(
                    "Refresh" if cfeed else "Load company news",
                    type="primary", use_container_width=True, key="company_refresh",
                )

            if c_refresh:
                with st.spinner(f"Fetching news for {len(watchlist)} companies…"):
                    cfeed = run_company_news_pipeline(watchlist)
                save_news_cache(user["email"], cfeed, cache_type="company")
                st.session_state.company_feed = cfeed
                st.session_state.company_feed_date = str(date.today())
                st.rerun()

            if not cfeed:
                st.markdown(
                    "<div style='color:#94a3b8; padding:2rem 0; text-align:center;'>"
                    "Click <strong style='color:#475569;'>Load company news</strong> to fetch "
                    "recent news for your tracked companies."
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.caption(f"{len(cfeed)} articles · last 7 days · sorted by impact")

                c_sector_f, c_score_f, c_sort = render_filter_bar(cfeed, key_prefix="co")
                c_displayed = _apply_filters(cfeed, c_sector_f, c_score_f, c_sort)

                if not c_displayed:
                    st.info("No articles match the current filters.")
                else:
                    st.caption(f"Showing {len(c_displayed)} of {len(cfeed)} articles")
                    render_feed_with_bookmarks(
                        c_displayed, user["email"], "co",
                        badge_label_fn=lambda item: item.get("symbol", item.get("sector", "Impact")),
                    )

    # ── Tab 3 : Daily Brief ──────────────────────────────────────────────────
    with tab_daily:
        today = date.today()
        st.markdown(
            f"<h3 style='margin:0;color:#0f172a;'>Today's {geography} Brief — {today.strftime('%b %d, %Y')}</h3>",
            unsafe_allow_html=True,
        )

        # Try loading cached brief
        brief = st.session_state.daily_brief
        if brief is None:
            brief = load_brief(user["email"], "daily", geography, str(today))
            if brief:
                st.session_state.daily_brief = brief
                st.session_state.daily_brief_date = str(today)

        col_db_info, col_db_btn = st.columns([4, 1])
        with col_db_info:
            st.caption("A synthesized intelligence brief from today's top stories.")
        with col_db_btn:
            gen_daily = st.button(
                "Regenerate" if brief else "Generate brief",
                type="primary", use_container_width=True, key="gen_daily",
            )

        if gen_daily:
            feed = st.session_state.for_you_feed
            if not feed:
                cached = load_news_cache(user["email"], cache_type="sector")
                feed = cached if cached else []
            if not feed:
                st.warning("Load your news feed first (News tab) to generate a daily brief.")
            else:
                with st.spinner("Synthesizing daily brief…"):
                    brief = run_daily_brief_pipeline(feed, geography, str(today))
                save_brief(user["email"], "daily", geography, str(today), brief)
                st.session_state.daily_brief = brief
                st.session_state.daily_brief_date = str(today)
                st.rerun()

        if brief:
            render_daily_brief_content(brief)
        else:
            st.markdown(
                "<div style='color:#94a3b8; padding:2rem 0; text-align:center;'>"
                "Generate your daily brief to see a synthesized view of today's key developments, "
                "signals, and what to watch."
                "</div>",
                unsafe_allow_html=True,
            )

    # ── Tab 4 : Weekly Brief ─────────────────────────────────────────────────
    with tab_weekly:
        from datetime import timedelta
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_key = f"{week_start}_{week_end}"

        st.markdown(
            f"<h3 style='margin:0;color:#0f172a;'>This Week in {geography}</h3>",
            unsafe_allow_html=True,
        )
        st.caption(f"{week_start.strftime('%b %d')} — {week_end.strftime('%b %d, %Y')}")

        wbrief = st.session_state.weekly_brief
        if wbrief is None:
            wbrief = load_brief(user["email"], "weekly", geography, week_key)
            if wbrief:
                st.session_state.weekly_brief = wbrief
                st.session_state.weekly_brief_date = week_key

        col_wb_info, col_wb_btn = st.columns([4, 1])
        with col_wb_info:
            st.caption("A weekly synthesis: what changed, recurring themes, and what's next.")
        with col_wb_btn:
            gen_weekly = st.button(
                "Regenerate" if wbrief else "Generate brief",
                type="primary", use_container_width=True, key="gen_weekly",
            )

        if gen_weekly:
            feed = st.session_state.for_you_feed
            if not feed:
                cached = load_news_cache(user["email"], cache_type="sector")
                feed = cached if cached else []
            if not feed:
                st.warning("Load your news feed first (News tab) to generate a weekly brief.")
            else:
                with st.spinner("Synthesizing weekly brief…"):
                    wbrief = run_weekly_brief_pipeline(feed, geography, str(week_start), str(week_end))
                save_brief(user["email"], "weekly", geography, week_key, wbrief)
                st.session_state.weekly_brief = wbrief
                st.session_state.weekly_brief_date = week_key
                st.rerun()

        if wbrief:
            render_weekly_brief_content(wbrief)
        else:
            st.markdown(
                "<div style='color:#94a3b8; padding:2rem 0; text-align:center;'>"
                "Generate your weekly brief to see the biggest shifts, recurring themes, "
                "and what to watch next week."
                "</div>",
                unsafe_allow_html=True,
            )

    # ── Tab 5 : Saved / Bookmarks ────────────────────────────────────────────
    with tab_saved:
        st.markdown("<h3 style='margin:0;color:#0f172a;'>Saved articles</h3>", unsafe_allow_html=True)

        bookmarks = get_bookmarks(user["email"])
        if not bookmarks:
            st.markdown(
                "<div style='color:#94a3b8; padding:2rem 0; text-align:center;'>"
                "No saved articles yet. Use the <strong style='color:#475569;'>\U0001F90D</strong> button "
                "on any article to bookmark it for later."
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            # Filters for saved articles
            bm_dir_filter = st.selectbox(
                "Filter by signal", ["All", "Positive only", "Negative only", "Mixed only"],
                key="bm_dir_filter",
            )
            filtered_bm = bookmarks
            if bm_dir_filter == "Positive only":
                filtered_bm = [b for b in filtered_bm if b.get("impact_score", 0) > 0]
            elif bm_dir_filter == "Negative only":
                filtered_bm = [b for b in filtered_bm if b.get("impact_score", 0) < 0]
            elif bm_dir_filter == "Mixed only":
                filtered_bm = [b for b in filtered_bm if b.get("signal_direction") == "mixed"]

            st.caption(f"{len(filtered_bm)} saved articles")
            for idx, item in enumerate(filtered_bm):
                render_news_card(item, card_key=f"bm_{idx}")
                url = item.get("url", "")
                if url and st.button("Remove bookmark", key=f"rm_bm_{idx}"):
                    remove_bookmark(user["email"], url)
                    st.session_state.bookmarked_urls.discard(url)
                    st.rerun()

    # ── Tab 6 : Insights (Phase 2) ───────────────────────────────────────────
    with tab_insights:
        st.markdown("<h3 style='margin:0;color:#0f172a;'>Intelligence insights</h3>", unsafe_allow_html=True)

        insight_view = st.radio(
            "View", ["Theme synthesis", "Personalized insights", "Sector sentiment"],
            horizontal=True, key="insight_view", label_visibility="collapsed",
        )

        feed = st.session_state.for_you_feed
        if not feed:
            cached = load_news_cache(user["email"], cache_type="sector")
            feed = cached if cached else []

        if insight_view == "Theme synthesis":
            st.markdown("#### Multi-article theme synthesis")
            st.caption("Articles grouped by theme with synthesized analysis of changes, risks, and opportunities.")

            if not feed:
                st.warning("Load your news feed first (News tab).")
            else:
                syntheses = st.session_state.theme_syntheses
                col_ts_info, col_ts_btn = st.columns([4, 1])
                with col_ts_btn:
                    gen_themes = st.button(
                        "Regenerate" if syntheses else "Generate",
                        type="primary", use_container_width=True, key="gen_themes",
                    )
                if gen_themes:
                    with st.spinner("Classifying articles and synthesizing themes…"):
                        syntheses = run_theme_synthesis_pipeline(feed, geography)
                    st.session_state.theme_syntheses = syntheses
                    st.rerun()

                if syntheses:
                    st.caption(f"{len(syntheses)} themes identified")
                    for syn in syntheses:
                        render_theme_synthesis(syn)
                else:
                    st.info("Click Generate to cluster articles by theme and produce synthesis reports.")

        elif insight_view == "Personalized insights":
            st.markdown("#### Why this matters to you")
            st.caption("AI-generated personalized relevance for each article based on your profile.")

            if not feed:
                st.warning("Load your news feed first (News tab).")
            else:
                # Show top 5 articles by impact with personalization
                top_articles = sorted(feed, key=lambda x: abs(x.get("impact_score", 0)), reverse=True)[:5]
                for idx, item in enumerate(top_articles):
                    title = _html.escape(item.get("title", "Untitled"))
                    score = item.get("impact_score", 0)
                    score_label = f"+{score}" if score > 0 else str(score)
                    st.markdown(f"**{score_label}** — {title}")

                    p_key = f"personalize_{idx}"
                    if st.button("Why this matters to me", key=p_key):
                        with st.spinner("Generating personalized insight…"):
                            insight = run_personalization_for_article(item, user)
                        if insight:
                            st.markdown(
                                f"<div style='background:rgba(99,102,241,0.04);border:1px solid rgba(99,102,241,0.12);"
                                f"border-radius:10px;padding:0.7rem 1rem;margin:0.3rem 0 0.8rem;'>"
                                f"<div style='color:#334155;font-size:0.86rem;line-height:1.6;'>{_html.escape(insight)}</div>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.info("Could not generate personalized insight for this article.")
                    st.markdown("---")

        elif insight_view == "Sector sentiment":
            st.markdown("#### Sector sentiment mapping")
            st.caption("How news maps to sector-level sentiment signals — not investment advice.")

            if not feed:
                st.warning("Load your news feed first (News tab).")
            else:
                top_articles = sorted(feed, key=lambda x: abs(x.get("impact_score", 0)), reverse=True)[:5]
                for idx, item in enumerate(top_articles):
                    title = _html.escape(item.get("title", "Untitled"))
                    score = item.get("impact_score", 0)
                    score_label = f"+{score}" if score > 0 else str(score)
                    st.markdown(f"**{score_label}** — {title}")

                    ss_key = f"sector_sent_{idx}"
                    if st.button("Show sector sentiment", key=ss_key):
                        with st.spinner("Analyzing sector sentiment…"):
                            sentiments = run_sector_sentiment_for_article(item)
                        render_sector_sentiments(sentiments)
                    st.markdown("---")

    # ── Tab 7 : Summarize Article ────────────────────────────────────────────
    with tab_summarize:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Article to summary")
        article_title = st.text_input("Article title (optional)")
        article_text = st.text_area("Paste article text", height=260)

        if st.button("Generate summary", type="primary", use_container_width=True):
            if not article_text.strip():
                st.warning("Please paste article text first.")
            else:
                output = generate_ai_outputs(article_text, user)
                save_summary(
                    user_email=user["email"],
                    article_title=article_title or output["title"],
                    article_text=article_text,
                    summary_payload=output,
                )
                st.success("Done.")
                st.markdown("### Summary")
                st.write(output["summary"])
                st.markdown("### Key points")
                for point in output["key_points"]:
                    st.write(f"- {point}")
                st.markdown("### Why it matters for you")
                st.write(output["why_it_matters"])

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Tab 8 : Settings ─────────────────────────────────────────────────────
    with tab_settings:
        render_settings(user)


# ---------- Router ----------
# Check for missing configuration
if _missing_config:
    st.error(f"❌ Configuration Error - Missing API Keys: {', '.join(_missing_config)}")
    st.markdown("""
    ### How to Fix
    
    1. Go to your Streamlit app settings on [share.streamlit.io](https://share.streamlit.io)
    2. Click **"Secrets"** in the sidebar
    3. Add these secrets:
    
    ```
    OPENAI_API_KEY = "your-key-here"
    EXA_API_KEY = "your-key-here"
    ```
    
    4. Reboot the app
    
    **Get API Keys:**
    - [OpenAI](https://platform.openai.com/api-keys)
    - [Exa](https://dashboard.exa.ai)
    """)
    st.stop()

# Auto-login from persisted session token (45-day remember me)
if st.session_state.auth_user is None:
    saved_token = _load_session_token()
    if saved_token:
        restored_user = validate_login_session(saved_token)
        if restored_user:
            st.session_state.auth_user = restored_user
        else:
            _clear_session_token()

if st.session_state.auth_user is None:
    render_sidebar_logged_out()
    if st.session_state.auth_mode == "signup":
        render_signup()
    elif st.session_state.auth_mode == "signup_onboarding":
        render_signup_onboarding()
    else:
        render_signin()
else:
    render_home(st.session_state.auth_user)

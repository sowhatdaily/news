import streamlit as st
from db import init_db, get_all_users, delete_user, clear_user_preferences

init_db()

st.set_page_config(page_title="SoWhat Admin", page_icon="🛠", layout="wide")

# ── Admin auth ──
_ADMIN_USER = "admin@tans"
_ADMIN_PASS = "Babysaisha@123"

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.markdown("<h2 style='text-align:center;margin-top:3rem;'>SoWhat Admin</h2>", unsafe_allow_html=True)
    with st.form("admin_login"):
        col = st.columns([1, 2, 1])[1]
        with col:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)
            if submitted:
                if username == _ADMIN_USER and password == _ADMIN_PASS:
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
    st.stop()

# ── CSS ──
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; color: #1e293b; }
    .admin-header {
        font-size: 2rem; font-weight: 800; color: #0f172a;
        letter-spacing: -0.03em; margin-bottom: 0.2rem;
    }
    .admin-subtitle { color: #64748b; font-size: 0.95rem; margin-bottom: 1.5rem; }
    .stat-card {
        background: white; border: 1px solid #e2e8f0; border-radius: 14px;
        padding: 1.2rem 1.5rem; text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .stat-number { font-size: 2.4rem; font-weight: 800; color: #6366f1; }
    .stat-label { color: #64748b; font-size: 0.82rem; text-transform: uppercase;
                  letter-spacing: 0.06em; margin-top: 0.2rem; }
    .user-row {
        background: white; border: 1px solid #e2e8f0; border-radius: 12px;
        padding: 1rem 1.2rem; margin-bottom: 0.6rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.success("Signed in as admin")
    if st.button("Log out", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.rerun()

st.markdown("<div class='admin-header'>SoWhat Admin</div>", unsafe_allow_html=True)
st.markdown("<div class='admin-subtitle'>Manage users, preferences, and data</div>", unsafe_allow_html=True)

# ── Stats ──
users = get_all_users()
total = len(users)

with_prefs = sum(1 for u in users if u["onboarding"].get("main_sectors"))
without_prefs = total - with_prefs

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        f"<div class='stat-card'><div class='stat-number'>{total}</div>"
        f"<div class='stat-label'>Total Users</div></div>",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"<div class='stat-card'><div class='stat-number'>{with_prefs}</div>"
        f"<div class='stat-label'>With Preferences</div></div>",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"<div class='stat-card'><div class='stat-number'>{without_prefs}</div>"
        f"<div class='stat-label'>No Preferences</div></div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── User list ──
if not users:
    st.info("No users found.")
else:
    st.subheader(f"All users ({total})")

    # Search
    search = st.text_input("Search by name or email", placeholder="Type to filter…")
    filtered = users
    if search.strip():
        q = search.strip().lower()
        filtered = [u for u in users if q in u["full_name"].lower() or q in u["email"].lower()]

    for user in filtered:
        with st.container():
            st.markdown(f"<div class='user-row'>", unsafe_allow_html=True)

            col_info, col_meta, col_actions = st.columns([3, 3, 2])

            with col_info:
                st.markdown(f"**{user['full_name']}**")
                st.caption(user["email"])

            with col_meta:
                persona = user.get("persona") or "—"
                geo = user.get("geography") or "—"
                sectors = user["onboarding"].get("main_sectors", [])
                sector_str = ", ".join(sectors[:3]) + ("…" if len(sectors) > 3 else "") if sectors else "None"
                st.caption(f"Persona: {persona} · Geo: {geo}")
                st.caption(f"Sectors: {sector_str}")
                st.caption(f"Joined: {user.get('created_at', '—')[:10]}")

            with col_actions:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("Clear prefs", key=f"clear_{user['email']}", help="Reset preferences & watchlist"):
                        clear_user_preferences(user["email"])
                        st.rerun()
                with btn_col2:
                    if st.button("Remove", key=f"del_{user['email']}", type="primary", help="Delete user permanently"):
                        st.session_state[f"confirm_del_{user['email']}"] = True

                # Confirmation step for delete
                if st.session_state.get(f"confirm_del_{user['email']}"):
                    st.warning(f"Delete **{user['full_name']}**? This cannot be undone.")
                    yes_col, no_col = st.columns(2)
                    with yes_col:
                        if st.button("Yes, delete", key=f"yes_del_{user['email']}", type="primary"):
                            delete_user(user["email"])
                            del st.session_state[f"confirm_del_{user['email']}"]
                            st.rerun()
                    with no_col:
                        if st.button("Cancel", key=f"no_del_{user['email']}"):
                            del st.session_state[f"confirm_del_{user['email']}"]
                            st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

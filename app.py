"""Helixis Solar Yield Maps - partner app.

A password-protected Streamlit app. After sign-in the partner sees a start
page with one card per country they have access to; each card opens an
interactive map of expected thermal yield for the Helixis LC10 HW and LC20 HW.

Add a country:
  1. put its map file in maps/ (for example maps/kenya.html)
  2. put its outline in assets/outlines/ (for example assets/outlines/kenya.svg)
  3. add one entry to COUNTRIES below

Who sees what is set in the app secrets (see secrets.toml.example):
  [passwords]  user name = password
  [access]     user name = list of country keys, or ["*"] for all countries
"""
import base64
import hmac
import time
from pathlib import Path

import streamlit as st

HERE = Path(__file__).parent
LOGO_FILE = HERE / "assets" / "logo_dark.png"            # full logo, for light backgrounds
LOGO_WHITE = HERE / "assets" / "helixis_logo_white.png"  # full logo, for dark backgrounds
MARK_FILE = HERE / "assets" / "mark_blue.png"            # blue symbol

MAX_ATTEMPTS = 5          # failed logins before a short lock
LOCK_SECONDS = 60         # lock time after too many failed attempts

# -------------------------------------------------
# Countries: one entry per map. Key figures are for one unit with
# 74.5 % optical efficiency and no loop losses (10th / 50th / 90th
# percentile of the country's grid points).
# -------------------------------------------------
COUNTRIES = {
    "italy": {
        "name": "Italy",
        "map": "maps/italy.html",
        "outline": "assets/outlines/italy.svg",
        "height": 2650,
        "dni": "1,270 – 1,750",
        "lc10": "9.7 – 13.3",
        "lc20": "19.3 – 26.6",
        "note": "Best in Sicily, Puglia and Sardinia",
        "grid": "969 points, 0.2° grid",
    },
    "rwanda": {
        "name": "Rwanda",
        "map": "maps/rwanda.html",
        "outline": "assets/outlines/rwanda.svg",
        "height": 1950,
        "dni": "1,060 – 1,380",
        "lc10": "8.1 – 10.5",
        "lc20": "16.1 – 21.0",
        "note": "Best in the east and around Lake Kivu",
        "grid": "904 points, 0.05° grid",
    },
}

st.set_page_config(
    page_title="Helixis · Solar Yield Maps",
    page_icon=str(MARK_FILE) if MARK_FILE.exists() else None,
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode() if path.exists() else ""


# -------------------------------------------------
# Helixis look (Style Guide 4): blue #1444E2, navy #222F4D, dark #1A252C,
# yellow #FECB02, light yellow #FED581, light grey #DFDADC.
# Brand font Suisse Intl, with Inter as fallback.
# -------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
html, body, .stApp, input, button, textarea, select {
  font-family: "Suisse Intl", "Inter", "Helvetica Neue", Arial, sans-serif !important;
}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], [data-testid="stHeader"] { display: none !important; }
.block-container { padding-top: 1.4rem; padding-bottom: 1rem; max-width: 1240px; }
.hx-hero { background: #1A252C; color: #F2F1F1; border-radius: 14px; min-height: 460px;
  padding: 32px 34px 26px; display: flex; flex-direction: column; justify-content: space-between; }
.hx-hero .mark { height: 42px; width: auto; align-self: flex-start; margin: 0 !important; }
.hx-hero h1 { font-weight: 300; font-size: clamp(40px, 5vw, 60px); line-height: 1.02;
  letter-spacing: -0.02em; margin: 0 0 14px; color: #F2F1F1; padding: 0; }
.hx-hero p { color: #C3C8D2; font-size: 16px; max-width: 34ch; margin: 0 0 26px; }
.hx-hero .foot { display: flex; justify-content: space-between; align-items: center;
  font-size: 11px; letter-spacing: .08em; color: #C3C8D2; }
.hx-hero .foot img { height: 14px; width: auto; }
.hx-formtitle { font-weight: 500; font-size: 22px; color: #1A252C; margin: 6px 0 2px; }
.hx-formsub { color: #4B5560; font-size: 14.5px; margin: 0 0 14px; }
.hx-login-foot { color: #7F878F; font-size: 12.5px; margin-top: 12px; }
[data-testid="stForm"] { background: #fff; border: 1px solid #DFDADC; border-radius: 14px; padding: 24px 24px 10px; }
.stButton button, [data-testid="stFormSubmitButton"] button {
  border-radius: 999px; font-weight: 500; padding: 0.5rem 1.2rem; }
.hx-user { color: #4B5560; font-size: 14px; text-align: right; padding-top: 6px; }
.hx-title { font-weight: 300; font-size: clamp(34px, 4.4vw, 48px); line-height: 1.05;
  letter-spacing: -0.02em; color: #1A252C; margin: 18px 0 6px; }
.hx-sub { color: #4B5560; font-size: 16px; max-width: 62ch; margin: 0 0 22px; }
.hx-card { background: #1A252C; color: #F2F1F1; border-radius: 14px; padding: 22px 24px 20px; margin-bottom: 10px;
  display: grid; grid-template-columns: minmax(0, 1fr) 96px; gap: 6px 16px; }
.hx-card h2 { font-weight: 300; font-size: 34px; letter-spacing: -0.02em; margin: 0; color: #F2F1F1; padding: 0; }
.hx-card .note { color: #C3C8D2; font-size: 14px; margin: 0 0 10px; }
.hx-card .shape { grid-row: 1 / span 3; grid-column: 2; align-self: start; width: 96px; height: 96px; object-fit: contain; }
.hx-card dl { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px; margin: 8px 0 4px; }
.hx-card dl div { border-top: 1px solid #33405F; padding-top: 8px; }
.hx-card dt { font-size: 11px; letter-spacing: .06em; text-transform: uppercase; color: #8E97A8; }
.hx-card dd { margin: 2px 0 0; font-size: 18px; font-variant-numeric: tabular-nums; color: #F2F1F1; }
.hx-card dd small { color: #8E97A8; font-size: 12px; }
.hx-card .meta { grid-column: 1 / -1; font-size: 12px; color: #8E97A8; margin-top: 4px; }
.hx-mapname { font-weight: 400; font-size: 20px; color: #1A252C; padding-top: 6px; }
.hx-foot { color: #7F878F; font-size: 12.5px; margin-top: 18px; }
</style>
""",
    unsafe_allow_html=True,
)


# -------------------------------------------------
# Authentication and access
# -------------------------------------------------
def _passwords() -> dict:
    try:
        return dict(st.secrets["passwords"])
    except Exception:
        return {}


def allowed_countries(user: str) -> list:
    """Country keys this user may open.

    No [access] section in the secrets: everyone sees every country.
    With an [access] section: only what is listed for the user; ["*"] means all.
    """
    try:
        access = dict(st.secrets["access"])
    except Exception:
        return list(COUNTRIES)
    wanted = access.get(user)
    if wanted is None:
        return []
    if isinstance(wanted, str):
        wanted = [wanted]
    wanted = [str(w).strip().lower() for w in wanted]
    if "*" in wanted or "all" in wanted:
        return list(COUNTRIES)
    return [k for k in COUNTRIES if k in wanted]


def _try_login() -> None:
    ss = st.session_state
    now = time.time()
    if ss.get("locked_until", 0) > now:
        return
    user = ss.get("login_user", "").strip()
    pwd = ss.get("login_pwd", "")
    users = _passwords()
    ok = (
        bool(user)
        and bool(pwd)
        and user in users
        and hmac.compare_digest(str(pwd).encode(), str(users[user]).encode())
    )
    ss["login_pwd"] = ""  # never keep the password in session state
    if ok:
        ss["auth_user"] = user
        ss["failed"] = 0
        ss["login_error"] = None
    else:
        ss["failed"] = ss.get("failed", 0) + 1
        if ss["failed"] >= MAX_ATTEMPTS:
            ss["locked_until"] = now + LOCK_SECONDS
            ss["failed"] = 0
            ss["login_error"] = f"Too many attempts. Try again in {LOCK_SECONDS} seconds."
        else:
            ss["login_error"] = "Wrong user name or password."


def login_screen() -> None:
    st.write("")
    hero, form = st.columns([1.15, 1], gap="large")
    with hero:
        st.markdown(
            f"""
<div class="hx-hero">
  <img class="mark" src="data:image/png;base64,{_b64(MARK_FILE)}" alt="">
  <div>
    <h1>Solar<br>Yield Maps</h1>
    <p>Expected annual solar heat from the Helixis LC10 HW and LC20 HW, site by site.</p>
    <div class="foot"><img src="data:image/png;base64,{_b64(LOGO_WHITE)}" alt="Helixis"><span>HELIXIS.SE</span></div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
    with form:
        st.markdown('<div class="hx-formtitle">Partner sign-in</div>', unsafe_allow_html=True)
        st.markdown('<p class="hx-formsub">Use the user name and password you received from Helixis.</p>',
                    unsafe_allow_html=True)
        if not _passwords():
            st.error("Login is not set up yet. Add user names and passwords under [passwords] in the app secrets.")
            return
        locked = st.session_state.get("locked_until", 0) > time.time()
        with st.form("login", clear_on_submit=False):
            st.text_input("User name", key="login_user", autocomplete="username")
            st.text_input("Password", type="password", key="login_pwd", autocomplete="current-password")
            st.form_submit_button("Sign in", type="primary", on_click=_try_login,
                                  use_container_width=True, disabled=locked)
        if st.session_state.get("login_error"):
            st.error(st.session_state["login_error"])
        st.markdown(
            '<div class="hx-login-foot">No account yet? Contact Helixis at info@helixis.se</div>',
            unsafe_allow_html=True,
        )


def logout() -> None:
    for k in ("auth_user", "login_error", "failed", "locked_until"):
        st.session_state.pop(k, None)
    st.query_params.clear()


def open_country(key: str) -> None:
    st.query_params["country"] = key


def go_home() -> None:
    st.query_params.clear()


# -------------------------------------------------
# Pages
# -------------------------------------------------
def header() -> None:
    left, right = st.columns([3, 2])
    with left:
        if LOGO_FILE.exists():
            st.image(str(LOGO_FILE), width=140)
    with right:
        u, b = st.columns([3, 1.3])
        with u:
            st.markdown(f'<div class="hx-user">Signed in as <b>{st.session_state["auth_user"]}</b></div>',
                        unsafe_allow_html=True)
        with b:
            st.button("Sign out", on_click=logout, use_container_width=True)


def start_page(keys: list) -> None:
    st.markdown('<div class="hx-title">Solar yield maps</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hx-sub">Choose a country to see the expected annual heat output of the '
        "Helixis LC10 HW and LC20 HW anywhere in it. Figures below are the range across each "
        "country, per unit and year.</p>",
        unsafe_allow_html=True,
    )
    cols = st.columns(2, gap="medium")
    for i, key in enumerate(keys):
        c = COUNTRIES[key]
        with cols[i % 2]:
            st.markdown(
                f"""
<div class="hx-card">
  <h2>{c['name']}</h2>
  <img class="shape" src="data:image/svg+xml;base64,{_b64(HERE / c['outline'])}" alt="">
  <p class="note">{c['note']}</p>
  <dl>
    <div><dt>DNI</dt><dd>{c['dni']} <small>kWh/m²</small></dd></div>
    <div><dt>LC10 HW</dt><dd>{c['lc10']} <small>MWh</small></dd></div>
    <div><dt>LC20 HW</dt><dd>{c['lc20']} <small>MWh</small></dd></div>
  </dl>
  <div class="meta">Global Solar Atlas · {c['grid']}</div>
</div>
""",
                unsafe_allow_html=True,
            )
            st.button(f"Open {c['name']} map", key=f"open_{key}", type="primary",
                      on_click=open_country, args=(key,), use_container_width=True)
            st.write("")
    st.markdown(
        '<div class="hx-foot">Range = 10th to 90th percentile of the grid points, 74.5 % optical '
        "efficiency, no loop losses. Each map lets you change these assumptions.</div>",
        unsafe_allow_html=True,
    )


def map_page(key: str, show_back: bool) -> None:
    c = COUNTRIES[key]
    if show_back:
        back, name = st.columns([1, 5])
        with back:
            st.button("← All maps", on_click=go_home, use_container_width=True)
        with name:
            st.markdown(f'<div class="hx-mapname">{c["name"]}</div>', unsafe_allow_html=True)
    path = HERE / c["map"]
    if not path.exists():
        st.error(f"Map file missing: {c['map']}.")
        return
    if hasattr(st, "iframe"):  # Streamlit 1.50 and newer
        st.iframe(path, height=c["height"])
    else:  # older Streamlit versions
        import streamlit.components.v1 as components

        components.html(path.read_text(encoding="utf-8"), height=c["height"], scrolling=True)


# -------------------------------------------------
# App
# -------------------------------------------------
if not st.session_state.get("auth_user"):
    login_screen()
    st.stop()

header()
keys = allowed_countries(st.session_state["auth_user"])
if not keys:
    st.info("Your account has no maps yet. Contact Helixis at info@helixis.se.")
    st.stop()

chosen = st.query_params.get("country")
if len(keys) == 1:
    map_page(keys[0], show_back=False)
elif chosen in keys:
    map_page(chosen, show_back=True)
else:
    start_page(keys)

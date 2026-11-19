"""NewsSignal – Streamlit dashboard.  Run with:  streamlit run app.py"""

import base64
import html
from datetime import datetime, timezone

import plotly.graph_objects as go
import requests
import streamlit as st

import config
from signals import analyse

st.set_page_config(
    page_title="NewsSignal · News-driven stock signals",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------- colours
C = {
    "surface": "#151922", "border": "#252a36", "grid": "#232733",
    "text": "#eef0f3", "text2": "#a3a9b5", "muted": "#6f7684",
    "pos": "#3987e5", "neg": "#e66767", "neu": "#5b5f68",      # sentiment (diverging)
    "buy": "#0ca30c", "sell": "#d03b3b", "hold": "#8a8f99",    # signal (status)
    "s1": "#3987e5", "s2": "#d95926",                          # chart series
}
SIGNAL_ICON = {"BUY": "▲", "SELL": "▼", "HOLD": "●"}
LABEL_ICON = {"positive": "▲", "negative": "▼", "neutral": "●"}

# ---------------------------------------------------------------- styles
st.markdown("""
<style>
.block-container, [data-testid="stMainBlockContainer"] { padding-top: 1.2rem !important; max-width: 1400px; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, .stAppDeployButton { visibility: hidden; }
[data-testid="stSidebar"] { background: #10131a; border-right: 1px solid #252a36; }
[data-testid="stSidebarUserContent"] { padding-top: 0.5rem !important; }
[data-testid="stSidebarHeader"] { height: 2.2rem !important; padding-top: .4rem !important; }
[data-testid="stForm"] { border: none; padding: 0; }

/* hero header */
.ns-hero { border-radius:16px; border:1px solid #252a36; overflow:hidden; margin-bottom:18px;
  background: radial-gradient(900px 220px at 0% 0%, rgba(57,135,229,.20), transparent 60%),
              radial-gradient(700px 220px at 100% 0%, rgba(47,198,160,.12), transparent 60%), #10141d; }
.ns-hero-main { display:flex; align-items:center; justify-content:space-between; gap:18px; padding:18px 22px; flex-wrap:wrap; }
.ns-logo { display:flex; align-items:center; gap:14px; }
.ns-logo img { display:block; filter:drop-shadow(0 4px 14px rgba(57,135,229,.35)); }
.ns-kicker { font-size:.66rem; letter-spacing:.24em; text-transform:uppercase; color:#7f8796; margin-bottom:5px; }
.ns-word { font-size:2rem; line-height:1; letter-spacing:-.02em; color:#eef0f3; }
.ns-word .light { font-weight:300; }
.ns-word .bold { font-weight:800; background:linear-gradient(90deg,#3987e5,#2fc6a0);
  -webkit-background-clip:text; background-clip:text; color:transparent; }
.ns-hero-right { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.ns-live { display:inline-flex; align-items:center; gap:7px; font-size:.72rem; font-weight:700; letter-spacing:.14em;
  color:#eef0f3; padding:5px 11px; border-radius:6px; background:rgba(208,59,59,.18); border:1px solid rgba(208,59,59,.55); }
.ns-live .pulse { width:8px; height:8px; border-radius:50%; background:#ff5a5a; animation:nsPulse 1.6s infinite; }
@keyframes nsPulse { 0% { box-shadow:0 0 0 0 rgba(255,90,90,.7); } 70% { box-shadow:0 0 0 8px rgba(255,90,90,0); }
  100% { box-shadow:0 0 0 0 rgba(255,90,90,0); } }
.ns-stat { font-size:.76rem; color:#a3a9b5; padding-left:10px; border-left:1px solid #2a3042; }
.ns-stat b { color:#eef0f3; font-weight:600; }
.ns-tape { display:flex; border-top:1px solid #222838; background:rgba(8,10,15,.6); overflow:hidden; white-space:nowrap; }
.ns-tape-label { flex:none; z-index:1; padding:8px 14px; font-size:.7rem; font-weight:800; letter-spacing:.14em;
  color:#0b0e14; background:linear-gradient(90deg,#3987e5,#2fc6a0); }
.ns-tape-view { overflow:hidden; flex:1; }
.ns-tape-track { display:inline-block; padding:8px 0 8px 16px; animation:nsScroll 120s linear infinite; }
.ns-tape:hover .ns-tape-track { animation-play-state:paused; }
.ns-tape-item { display:inline-block; margin:0 28px 0 0; font-size:.82rem; color:#c9cdd4; }
.ns-tape-item b { color:#eef0f3; margin-right:6px; }
.ns-tape-item .up { color:#5b9df0; } .ns-tape-item .down { color:#ff7b7b; } .ns-tape-item .flat { color:#8a8f99; }
@keyframes nsScroll { from { transform:translateX(0); } to { transform:translateX(-50%); } }

/* old top bar classes (still used for small labels) */
.ns-top { display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap;
  padding:16px 22px; margin-bottom:18px; border-radius:14px; border:1px solid #252a36;
  background:linear-gradient(110deg,#161b28 0%,#111520 60%,#0f1a2c 100%); }
.ns-brand { font-size:1.55rem; font-weight:750; color:#eef0f3; letter-spacing:-.01em; }
.ns-brand span { color:#3987e5; }
.ns-tagline { color:#a3a9b5; font-size:.88rem; margin-top:2px; }
.ns-meta { display:flex; gap:8px; flex-wrap:wrap; }
.ns-pill { font-size:.78rem; color:#c9cdd4; padding:5px 11px; border-radius:999px;
  background:#1b2030; border:1px solid #2a3042; white-space:nowrap; }
.ns-pill .dot { display:inline-block; width:7px; height:7px; border-radius:50%; background:#0ca30c; margin-right:6px; }

/* KPI tiles */
.ns-kpi { background:#151922; border:1px solid #252a36; border-radius:12px; padding:14px 16px; height:100%; }
.ns-kpi-label { color:#8b919c; font-size:.72rem; text-transform:uppercase; letter-spacing:.07em; }
.ns-kpi-value { color:#eef0f3; font-size:1.65rem; font-weight:700; margin-top:4px; line-height:1.2; }
.ns-kpi-sub { color:#6f7684; font-size:.78rem; margin-top:2px; }
.ns-kpi-bar { height:3px; border-radius:2px; margin-top:10px; }

/* signal cards */
.ns-card { background:#151922; border:1px solid #252a36; border-radius:14px; padding:16px 18px;
  margin-bottom:14px; transition:border-color .15s, transform .15s; }
.ns-card:hover { border-color:#3a4256; transform:translateY(-1px); }
.ns-card-head { display:flex; justify-content:space-between; align-items:flex-start; gap:10px; }
.ns-ident { display:flex; align-items:center; gap:12px; min-width:0; }
.ns-avatar { position:relative; flex:none; width:40px; height:40px; border-radius:10px; overflow:hidden;
  background:#f2f4f7; display:flex; align-items:center; justify-content:center;
  color:#1f2534; font-weight:800; font-size:.8rem; letter-spacing:.02em; box-shadow:0 0 0 1px #2a3042; }
.ns-avatar img { position:absolute; inset:0; width:100%; height:100%; object-fit:contain; padding:5px; }
.ns-avatar.lg { width:46px; height:46px; border-radius:12px; font-size:.9rem; }
.ns-name { color:#eef0f3; font-weight:650; font-size:1.05rem; }
.ns-sub { color:#8b919c; font-size:.8rem; margin-top:2px; }
.ns-badge { font-size:.78rem; font-weight:700; letter-spacing:.04em; color:#eef0f3;
  padding:5px 11px; border-radius:8px; white-space:nowrap; border:1px solid; }
.ns-badge.BUY  { background:rgba(12,163,12,.16);  border-color:rgba(12,163,12,.6); }
.ns-badge.SELL { background:rgba(208,59,59,.16);  border-color:rgba(208,59,59,.65); }
.ns-badge.HOLD { background:rgba(138,143,153,.14); border-color:rgba(138,143,153,.5); }
.ns-badge.BUY .i { color:#3ccf3c; } .ns-badge.SELL .i { color:#ff6b6b; } .ns-badge.HOLD .i { color:#a3a9b5; }
.ns-row { display:flex; justify-content:space-between; align-items:baseline; margin-top:14px; }
.ns-label { color:#8b919c; font-size:.75rem; text-transform:uppercase; letter-spacing:.06em; }
.ns-score { color:#eef0f3; font-weight:700; font-size:1.25rem; font-variant-numeric:tabular-nums; }
.ns-meter { position:relative; height:8px; background:#1f2430; border-radius:4px; margin-top:6px; overflow:hidden; }
.ns-meter-fill { position:absolute; top:0; height:100%; border-radius:4px; }
.ns-meter-mid { position:absolute; z-index:1; left:50%; top:-2px; width:2px; height:12px; background:#6f7684; }
.ns-split { display:flex; gap:14px; color:#a3a9b5; font-size:.8rem; margin-top:12px; }
.ns-reason { color:#8b919c; font-size:.8rem; margin-top:8px; border-top:1px solid #222734; padding-top:8px; }

/* news list */
.ns-news { background:#151922; border:1px solid #252a36; border-left:3px solid; border-radius:10px;
  padding:10px 14px; margin-bottom:8px; }
.ns-news a { color:#eef0f3 !important; text-decoration:none; font-weight:550; font-size:.93rem; }
.ns-news a:hover { text-decoration:underline; }
.ns-news-meta { color:#8b919c; font-size:.76rem; margin-bottom:4px; display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
.ns-tag { background:#1f2534; color:#c9cdd4; padding:1px 7px; border-radius:5px; font-weight:600; font-size:.72rem; }

/* tabs */
.stTabs [data-baseweb="tab-list"] { gap:6px; border-bottom:1px solid #252a36; }
.stTabs [data-baseweb="tab"] { padding:8px 16px; border-radius:8px 8px 0 0; }
.stTabs [aria-selected="true"] { background:#151922; }

.ns-section { color:#eef0f3; font-weight:650; font-size:1.05rem; margin:6px 0 10px; }
.ns-footer { color:#6f7684; font-size:.75rem; text-align:center; margin-top:40px; padding-top:14px; border-top:1px solid #1f2430; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------- helpers
def esc(x) -> str:
    return html.escape(str(x))


def name_of(ticker: str) -> str:
    return NAME_BY_TICKER.get(ticker, ticker)


def initials(name: str) -> str:
    words = [w for w in name.replace("(", " ").replace("-", " ").split() if w[0].isalnum()]
    return "".join(w[0] for w in words[:2]).upper() or "?"


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def logo_data(ticker: str) -> str | None:
    """Download the company logo once a day. Returns a data URI, or None if there is no logo."""
    try:
        resp = requests.get(config.LOGO_URL.format(ticker=ticker), timeout=4)
        kind = resp.headers.get("content-type", "")
        if resp.status_code == 200 and kind.startswith("image") and len(resp.content) > 200:
            return f"data:{kind};base64,{base64.b64encode(resp.content).decode()}"
    except Exception:
        pass
    return None


def avatar(ticker: str, size: str = "") -> str:
    """Company logo, or the company's initials if no logo is available."""
    data = logo_data(ticker)
    inner = (f'<img src="{data}" alt="">' if data
             else f'<span>{esc(initials(name_of(ticker)))}</span>')
    return f'<div class="ns-avatar {size}">{inner}</div>'

def time_ago(dt: datetime) -> str:
    mins = int((datetime.now(timezone.utc) - dt).total_seconds() // 60)
    if mins < 60:
        return f"{max(mins, 1)} min ago"
    if mins < 60 * 24:
        return f"{mins // 60} h ago"
    return f"{mins // (60 * 24)} d ago"


def fmt_price(r) -> str:
    if r["price"] is None:
        return "Price n/a"
    return f"{r['price']:,.2f} {r['currency']}".strip()


def meter(score: float) -> str:
    width = min(abs(score), 1) * 50
    side = f"left:50%;" if score >= 0 else f"right:50%;"
    col = C["pos"] if score >= 0 else C["neg"]
    return (f'<div class="ns-meter"><div class="ns-meter-fill" style="{side}width:{width:.1f}%;'
            f'background:{col}"></div><div class="ns-meter-mid"></div></div>')


def badge(signal: str) -> str:
    return f'<span class="ns-badge {signal}"><span class="i">{SIGNAL_ICON[signal]}</span> {signal}</span>'


def kpi(label, value, sub="", bar_color=None) -> str:
    bar = f'<div class="ns-kpi-bar" style="background:{bar_color}"></div>' if bar_color else ""
    return (f'<div class="ns-kpi"><div class="ns-kpi-label">{label}</div>'
            f'<div class="ns-kpi-value">{value}</div><div class="ns-kpi-sub">{sub}</div>{bar}</div>')


def signal_card(r) -> str:
    chg = ""
    if r["change_pct"] is not None:
        arrow = "▲" if r["change_pct"] >= 0 else "▼"
        chg = f" · {arrow} {r['change_pct']:+.2f}% today"
    c = r["counts"]
    return (
        f'<div class="ns-card"><div class="ns-card-head"><div class="ns-ident">{avatar(r["ticker"])}<div>'
        f'<div class="ns-name">{esc(name_of(r["ticker"]))}</div>'
        f'<div class="ns-sub">{esc(r["ticker"])} · {esc(fmt_price(r))}{chg}</div></div></div>'
        f'{badge(r["signal"])}</div>'
        f'<div class="ns-row"><span class="ns-label">News sentiment</span>'
        f'<span class="ns-score">{r["score"]:+.2f}</span></div>{meter(r["score"])}'
        f'<div class="ns-split"><span>▲ {c["positive"]} positive</span>'
        f'<span>● {c["neutral"]} neutral</span><span>▼ {c["negative"]} negative</span></div>'
        f'<div class="ns-reason">{esc(r["reason"])}</div></div>'
    )


def news_item(a, ticker=None) -> str:
    col = {"positive": C["pos"], "negative": C["neg"]}.get(a["label"], C["neu"])
    tag = f'<span class="ns-tag">{esc(ticker)}</span>' if ticker else ""
    when = a["published"].astimezone().strftime("%d %b %H:%M")
    return (
        f'<div class="ns-news" style="border-left-color:{col}">'
        f'<div class="ns-news-meta">{tag}<span>{esc(a["source"])}</span><span>·</span>'
        f'<span title="{when}">{time_ago(a["published"])}</span><span>·</span>'
        f'<span>{LABEL_ICON[a["label"]]} {a["label"].capitalize()} {a["sentiment"]:+.2f}</span></div>'
        f'<a href="{esc(a["url"])}" target="_blank">{esc(a["title"])}</a></div>'
    )


def base_layout(fig, height):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C["text2"], size=12),
        hoverlabel=dict(bgcolor="#1b2030", bordercolor="#2a3042", font_color=C["text"]),
    )
    fig.update_xaxes(gridcolor=C["grid"], zeroline=False, linecolor=C["border"])
    fig.update_yaxes(gridcolor=C["grid"], zeroline=False, linecolor=C["border"])
    return fig


def sentiment_chart(results):
    rs = sorted(results, key=lambda r: r["score"])
    fig = go.Figure(go.Bar(
        x=[r["score"] for r in rs],
        y=[name_of(r["ticker"]) for r in rs],
        orientation="h",
        marker=dict(color=[C["pos"] if r["score"] >= 0 else C["neg"] for r in rs]),
        customdata=[[r["ticker"], r["signal"], r["headlines"]] for r in rs],
        hovertemplate="<b>%{y}</b> (%{customdata[0]})<br>Score %{x:+.2f}<br>"
                      "Signal %{customdata[1]} · %{customdata[2]} headlines<extra></extra>",
        width=0.55,
    ))
    fig.add_vline(x=0, line_color=C["muted"], line_width=1)
    for x, label in ((config.BUY_THRESHOLD, "BUY level"), (config.SELL_THRESHOLD, "SELL level")):
        fig.add_vline(x=x, line_dash="dot", line_color=C["muted"], line_width=1,
                      annotation_text=label, annotation_font_color=C["text2"],
                      annotation_font_size=11, annotation_position="top")
    lim = max(0.6, max(abs(r["score"]) for r in rs) + 0.1)
    fig.update_xaxes(range=[-lim, lim], title_text="Recency-weighted news sentiment")
    fig.update_layout(barcornerradius=4, showlegend=False)
    return base_layout(fig, 90 + 38 * len(rs))


def price_chart(r):
    h = r["history"]
    fig = go.Figure()
    fig.add_scatter(x=h.index, y=h["Close"], name="Price", mode="lines",
                    line=dict(color=C["s1"], width=2))
    fig.add_scatter(x=h.index, y=h["MA50"], name="50-day average", mode="lines",
                    line=dict(color=C["s2"], width=2))
    fig.update_layout(hovermode="x unified",
                      legend=dict(orientation="h", y=1.08, x=0, font=dict(color=C["text2"])))
    fig.update_xaxes(showspikes=True, spikecolor=C["muted"], spikethickness=1, spikedash="dot")
    fig.update_yaxes(title_text=r["currency"] or "Price")
    return base_layout(fig, 340)


LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="SIZE" height="SIZE" viewBox="0 0 48 48">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#3987e5"/><stop offset="1" stop-color="#2fc6a0"/></linearGradient></defs>
<rect width="48" height="48" rx="13" fill="url(#g)"/>
<rect x="10" y="11" width="16" height="3.2" rx="1.6" fill="#0b0e14" opacity=".85"/>
<rect x="10" y="17.5" width="11" height="3.2" rx="1.6" fill="#0b0e14" opacity=".55"/>
<path d="M33 9.5a9 9 0 0 1 0 12.7M36.6 6a14 14 0 0 1 0 19.8" fill="none" stroke="#0b0e14"
 stroke-width="2.4" stroke-linecap="round" opacity=".7"/>
<polyline points="10,37 17,30.5 23,33.5 30,24.5 37.5,18" fill="none" stroke="#fff" stroke-width="3.2"
 stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="37.5" cy="18" r="3.3" fill="#fff"/></svg>"""


def logo(size=48) -> str:
    data = base64.b64encode(LOGO_SVG.replace("SIZE", str(size)).encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{data}" width="{size}" height="{size}" alt="NewsSignal logo">'


def hero(results=None) -> str:
    n_comp = len(results) if results else len(S.tickers)
    n_news = sum(r["headlines"] for r in results) if results else 0
    stats = (f'<span class="ns-stat"><b>{n_comp}</b> companies</span>'
             f'<span class="ns-stat"><b>{n_news or "–"}</b> headlines</span>'
             f'<span class="ns-stat">FinBERT · last {config.LOOKBACK_DAYS} days</span>'
             f'<span class="ns-stat">Updated <b>{S.updated:%H:%M}</b></span>')
    top = (f'<div class="ns-hero-main"><div class="ns-logo">{logo(50)}<div>'
           f'<div class="ns-kicker">AI news intelligence for stocks</div>'
           f'<div class="ns-word"><span class="light">News</span><span class="bold">Signal</span></div>'
           f'</div></div><div class="ns-hero-right"><span class="ns-live"><span class="pulse"></span>LIVE</span>'
           f'{stats}</div></div>')
    tape = ""
    if results:
        latest = sorted(((r["ticker"], a) for r in results for a in r["articles"]),
                        key=lambda x: x[1]["published"], reverse=True)[:25]
        if latest:
            cls = {"positive": ("up", "▲"), "negative": ("down", "▼")}
            items = "".join(
                f'<span class="ns-tape-item"><span class="{cls.get(a["label"], ("flat", "●"))[0]}">'
                f'{cls.get(a["label"], ("flat", "●"))[1]}</span> <b>{esc(t)}</b>{esc(a["title"])}</span>'
                for t, a in latest)
            tape = (f'<div class="ns-tape"><div class="ns-tape-label">LATEST</div>'
                    f'<div class="ns-tape-view"><div class="ns-tape-track">{items}{items}</div></div></div>')
    return f'<div class="ns-hero">{top}{tape}</div>'


@st.cache_data(ttl=900, show_spinner=False)  # re-fetch news at most every 15 min
def cached_analyse(ticker, require_trend, buy, sell):
    config.BUY_THRESHOLD, config.SELL_THRESHOLD = buy, sell
    return analyse(ticker, require_trend)


NAME_BY_TICKER = {t: n for n, t in config.COMPANIES.items()}

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown(f'<div class="ns-logo" style="gap:10px;margin-bottom:6px">{logo(34)}'
                '<div><div class="ns-word" style="font-size:1.3rem"><span class="light">News</span>'
                '<span class="bold">Signal</span></div>'
                '<div class="ns-tagline" style="font-size:.75rem">Control panel</div></div></div>',
                unsafe_allow_html=True)
    with st.form("controls"):
        st.markdown("##### Watchlist")
        companies = st.multiselect(
            "Select companies", options=list(config.COMPANIES.keys()),
            default=config.DEFAULT_COMPANIES, placeholder="Choose companies")
        extra_text = st.text_input(
            "Or enter tickers", placeholder="e.g. AMD, RHM.DE",
            help="Yahoo Finance tickers, separated by commas. German stocks end in .DE")
        st.markdown("##### Strategy")
        require_trend = st.toggle("Confirm with price trend (MA50)", value=True)
        buy_t = st.slider("BUY when score above", 0.05, 0.8, config.BUY_THRESHOLD, 0.05)
        sell_t = st.slider("SELL when score below −", 0.05, 0.8, -config.SELL_THRESHOLD, 0.05)
        submitted = st.form_submit_button("Analyse", type="primary", use_container_width=True)
    st.caption("Educational tool – not financial advice.")

if submitted or "tickers" not in st.session_state:
    tickers = [config.COMPANIES[c] for c in companies]
    tickers += [t.strip().upper() for t in extra_text.split(",") if t.strip()]
    st.session_state.update(
        tickers=list(dict.fromkeys(tickers)), require_trend=require_trend,
        buy=buy_t, sell=-sell_t, updated=datetime.now())

S = st.session_state
config.BUY_THRESHOLD, config.SELL_THRESHOLD = S.buy, S.sell

# ---------------------------------------------------------------- header
header = st.empty()
header.markdown(hero(), unsafe_allow_html=True)

if not S.tickers:
    st.info("Select companies or enter tickers in the sidebar, then press **Analyse**.")
    st.stop()

# ---------------------------------------------------------------- analysis
results, failed = [], []
progress = st.progress(0.0, text="Reading the news…")
for i, t in enumerate(S.tickers):
    progress.progress(i / len(S.tickers), text=f"Analysing {name_of(t)}…")
    try:
        results.append(cached_analyse(t, S.require_trend, S.buy, S.sell))
    except Exception as e:
        failed.append(f"{t} ({e.__class__.__name__})")
progress.empty()

if failed:
    st.warning("Could not analyse: " + ", ".join(failed))
problems = {r["ticker"]: r.get("news_errors", []) for r in results if r.get("news_errors")}
if problems:
    with st.expander(f"⚠️ Some news sources failed for {len(problems)} companies – details"):
        for t, errs in problems.items():
            st.markdown(f"**{esc(name_of(t))} ({t})**  \n" + "  \n".join(esc(e) for e in errs))
if not results:
    st.stop()

header.markdown(hero(results), unsafe_allow_html=True)

# ---------------------------------------------------------------- KPI row
n_buy = sum(r["signal"] == "BUY" for r in results)
n_sell = sum(r["signal"] == "SELL" for r in results)
n_hold = len(results) - n_buy - n_sell
avg = sum(r["score"] for r in results) / len(results)
total_news = sum(r["headlines"] for r in results)
mood = "Positive" if avg > 0.1 else "Negative" if avg < -0.1 else "Neutral"

k = st.columns(5)
k[0].markdown(kpi("Companies", len(results), "in watchlist"), unsafe_allow_html=True)
k[1].markdown(kpi("▲ Buy signals", n_buy, "positive news", C["buy"]), unsafe_allow_html=True)
k[2].markdown(kpi("▼ Sell signals", n_sell, "negative news", C["sell"]), unsafe_allow_html=True)
k[3].markdown(kpi("● Hold", n_hold, "mixed or unconfirmed", C["hold"]), unsafe_allow_html=True)
k[4].markdown(kpi("Market mood", f"{avg:+.2f}", f"{mood} · {total_news} headlines read"),
              unsafe_allow_html=True)
st.write("")

# ---------------------------------------------------------------- tabs
tab_over, tab_detail, tab_news, tab_method = st.tabs(
    ["📊 Overview", "🏢 Company detail", "📰 News feed", "ℹ️ How it works"])

with tab_over:
    order = {"BUY": 0, "SELL": 1, "HOLD": 2}
    ranked = sorted(results, key=lambda r: (order[r["signal"]], -abs(r["score"])))
    cols = st.columns(3)
    for i, r in enumerate(ranked):
        cols[i % 3].markdown(signal_card(r), unsafe_allow_html=True)

    st.markdown('<div class="ns-section">Sentiment ranking</div>', unsafe_allow_html=True)
    st.plotly_chart(sentiment_chart(results), use_container_width=True,
                    config={"displayModeBar": False})

with tab_detail:
    pick = st.selectbox("Company", [r["ticker"] for r in results],
                        format_func=lambda t: f"{name_of(t)} ({t})")
    r = next(x for x in results if x["ticker"] == pick)

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:14px;margin:6px 0 14px">{avatar(pick, "lg")}'
        f'<div class="ns-brand" style="font-size:1.4rem">{esc(name_of(pick))}</div>'
        f'{badge(r["signal"])}<span class="ns-sub">{esc(r["reason"])}</span></div>',
        unsafe_allow_html=True)

    m = st.columns(4)
    m[0].markdown(kpi("Price", fmt_price(r).replace("Price n/a", "–"),
                      f"{r['change_pct']:+.2f}% today" if r["change_pct"] is not None else ""),
                  unsafe_allow_html=True)
    m[1].markdown(kpi("50-day average", f"{r['ma50']:,.2f}" if r["ma50"] else "–",
                      {"up": "▲ price above average", "down": "▼ price below average"}
                      .get(r["trend"], "not enough data")), unsafe_allow_html=True)
    m[2].markdown(kpi("News score", f"{r['score']:+.2f}", "range −1 to +1"),
                  unsafe_allow_html=True)
    m[3].markdown(kpi("Headlines", r["headlines"],
                      f"▲ {r['counts']['positive']} · ● {r['counts']['neutral']} · ▼ {r['counts']['negative']}"),
                  unsafe_allow_html=True)
    st.write("")

    left, right = st.columns([3, 2])
    with left:
        st.markdown('<div class="ns-section">Price · last 6 months</div>', unsafe_allow_html=True)
        if r["history"] is not None:
            st.plotly_chart(price_chart(r), use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("No price history available for this ticker.")
    with right:
        st.markdown('<div class="ns-section">Latest headlines</div>', unsafe_allow_html=True)
        if r["articles"]:
            items = "".join(news_item(a) for a in r["articles"][:8])
            st.markdown(f'<div style="max-height:360px;overflow-y:auto;padding-right:4px">{items}</div>',
                        unsafe_allow_html=True)
        else:
            st.info("No recent headlines found.")

with tab_news:
    f1, f2 = st.columns([2, 3])
    mood_filter = f1.radio("Sentiment", ["All", "Positive", "Neutral", "Negative"], horizontal=True)
    comp_filter = f2.multiselect("Companies", [r["ticker"] for r in results],
                                 format_func=name_of, placeholder="All companies")
    feed = [(r["ticker"], a) for r in results for a in r["articles"]
            if (not comp_filter or r["ticker"] in comp_filter)
            and (mood_filter == "All" or a["label"] == mood_filter.lower())]
    feed.sort(key=lambda x: x[1]["published"], reverse=True)
    st.caption(f"{len(feed)} headlines")
    if feed:
        st.markdown("".join(news_item(a, t) for t, a in feed[:150]), unsafe_allow_html=True)
    else:
        st.info("No headlines match these filters.")

with tab_method:
    st.markdown(f"""
#### How NewsSignal works
1. **Collect news** – recent headlines from Yahoo Finance (and Finnhub, if an API key is set),
   from the last **{config.LOOKBACK_DAYS} days**. Duplicates are removed.
2. **Read the news with AI** – each headline is scored by **FinBERT**, a language model trained
   on financial text: positive, neutral or negative, with a confidence level.
3. **Combine** – scores are averaged, and newer news counts more
   (a headline {config.HALF_LIFE_HOURS} hours old counts half as much).
4. **Decide** – score above **{S.buy:+.2f}** → BUY, below **{S.sell:+.2f}** → SELL, otherwise HOLD.
   With trend confirmation on, a BUY also needs the price above its 50-day average
   (and a SELL needs it below). At least {config.MIN_HEADLINES} headlines are required.

#### Limitations
- Markets react to news within minutes; free news feeds are often slower.
- Headlines alone can be misleading; the model does not read full articles.
- Past signals have not been backtested in this version.

*NewsSignal is an educational project and does not provide financial advice.*
""")

st.markdown(
    '<div class="ns-footer">NewsSignal · Built with Python, Streamlit, FinBERT & yfinance · '
    'Data may be delayed · Not financial advice</div>', unsafe_allow_html=True)
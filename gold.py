"""Gold & Forex deep-dive page — tailored for Fahad's XAUUSDz / EURUSDz trading."""

import streamlit as st
from utils.data import (
    get_quotes, get_ohlcv, get_ticker_info,
    fetch_gold_news, fetch_forex_news,
    GOLD_SYMBOLS, FOREX_PAIRS,
)
from utils.charts import candlestick_chart, line_chart


def _badge(pct: float) -> str:
    cls  = "up" if pct > 0 else ("down" if pct < 0 else "flat")
    sign = "+" if pct > 0 else ""
    return f'<span class="{cls}">{sign}{pct:.2f}%</span>'


def _news_html(articles: list, limit: int = 8) -> str:
    html = ""
    for a in articles[:limit]:
        src_cls = f"news-source-{a['source'].lower().replace(' ', '-')}"
        title   = a["title"][:90] + ("…" if len(a["title"]) > 90 else "")
        link    = a["link"]
        html += f"""
        <div class="news-card">
          <a href="{link}" target="_blank" style="text-decoration:none;">
            <div class="news-title">{title}</div>
          </a>
          <div class="news-meta">
            <span class="{src_cls}">{a['source']}</span>
            &nbsp;·&nbsp;{a['published']}
          </div>
        </div>"""
    return html or '<div class="apex-card">No news loaded.</div>'


def render():
    tab_gold, tab_fx = st.tabs(["🥇 Gold", "💱 Forex"])

    # ── GOLD ────────────────────────────────────────────────────
    with tab_gold:
        with st.spinner(""):
            gold_q = get_quotes(GOLD_SYMBOLS)

        # Quick stats row
        if gold_q:
            g = next((x for x in gold_q if "XAUUSD" in x["label"]), gold_q[0])
            price = g["price"]
            pct   = g["pct"]
            chg   = g["change"]

            sign = "+" if chg > 0 else ""
            col_cls = "up" if pct > 0 else "down"
            st.markdown(f"""
            <div class="apex-card apex-card-accent">
              <div style="font-family:var(--mono);font-size:11px;color:var(--text-dim)">XAUUSD SPOT</div>
              <div style="font-family:var(--mono);font-size:28px;font-weight:600;color:var(--text)">${price:,.2f}</div>
              <div class="{col_cls}" style="font-family:var(--mono);font-size:13px">
                {sign}{chg:.2f} &nbsp; {sign}{pct:.2f}%
              </div>
            </div>""", unsafe_allow_html=True)

        # All gold symbols
        for r in gold_q:
            p   = r["price"]
            ps  = f"${p:,.2f}" if p > 100 else f"${p:.3f}"
            sig = "+" if r["pct"] > 0 else ""
            cls = "up" if r["pct"] > 0 else ("down" if r["pct"] < 0 else "flat")
            st.markdown(f"""
            <div class="ticker-row">
              <span class="ticker-sym">{r['label']}</span>
              <span class="ticker-price">{ps}</span>
              <span class="{cls}">{sig}{r['pct']:.2f}%</span>
            </div>""", unsafe_allow_html=True)

        # Timeframe selector
        st.markdown('<div class="apex-header" style="margin-top:10px">Chart</div>', unsafe_allow_html=True)
        col1, col2 = st.columns([2, 2])
        with col1:
            tf = st.selectbox("Timeframe", ["15m", "1h", "4h", "1d"], key="gold_tf", label_visibility="collapsed")
        with col2:
            period_map = {"15m": "2d", "1h": "5d", "4h": "10d", "1d": "60d"}
            period = period_map[tf]
            if st.button("🔄 Refresh", key="gold_ref"):
                st.cache_data.clear()

        with st.spinner("Loading chart…"):
            df = get_ohlcv("GC=F", period=period, interval=tf)
        if not df.empty:
            fig = candlestick_chart(df, title=f"Gold (GC=F) · {tf}", height=280)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Gold news
        st.markdown('<div class="apex-header" style="margin-top:6px">Gold News</div>', unsafe_allow_html=True)
        with st.spinner(""):
            gnews = fetch_gold_news(limit=12)
        st.markdown(_news_html(gnews, limit=10), unsafe_allow_html=True)

    # ── FOREX ────────────────────────────────────────────────────
    with tab_fx:
        with st.spinner(""):
            fx_q = get_quotes(FOREX_PAIRS)

        # Ticker list
        for r in fx_q:
            cls  = "up" if r["pct"] > 0 else ("down" if r["pct"] < 0 else "flat")
            sign = "+" if r["pct"] > 0 else ""
            st.markdown(f"""
            <div class="ticker-row">
              <span class="ticker-sym">{r['label']}</span>
              <span class="ticker-price">{r['price']:.5f}</span>
              <span class="{cls}">{sign}{r['pct']:.3f}%</span>
            </div>""", unsafe_allow_html=True)

        # Chart
        st.markdown('<div class="apex-header" style="margin-top:10px">Pair Chart</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            pair_label = st.selectbox("Pair", list(FOREX_PAIRS.keys()), key="fx_pair", label_visibility="collapsed")
        with col2:
            tf_fx = st.selectbox("TF", ["15m", "1h", "4h", "1d"], key="fx_tf", label_visibility="collapsed")
        with col3:
            if st.button("🔄", key="fx_ref"):
                st.cache_data.clear()

        period_map = {"15m": "2d", "1h": "5d", "4h": "10d", "1d": "60d"}
        ticker_fx  = FOREX_PAIRS[pair_label]
        with st.spinner("Loading chart…"):
            df_fx = get_ohlcv(ticker_fx, period=period_map[tf_fx], interval=tf_fx)
        if not df_fx.empty:
            fig_fx = candlestick_chart(df_fx, title=f"{pair_label} · {tf_fx}", height=260)
            st.plotly_chart(fig_fx, use_container_width=True, config={"displayModeBar": False})

        # Forex news
        st.markdown('<div class="apex-header" style="margin-top:6px">Forex News</div>', unsafe_allow_html=True)
        with st.spinner(""):
            fxnews = fetch_forex_news(limit=12)
        st.markdown(_news_html(fxnews, limit=10), unsafe_allow_html=True)

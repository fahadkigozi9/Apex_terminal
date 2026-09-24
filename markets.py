"""Markets overview page — indices, commodities, crypto."""

import streamlit as st
from utils.data import get_quotes, get_ohlcv, INDICES, COMMODITIES, CRYPTO, now_utc_str
from utils.charts import candlestick_chart, line_chart


def _color(pct: float) -> str:
    if pct > 0: return "up"
    if pct < 0: return "down"
    return "flat"


def _ticker_html(rows: list) -> str:
    html = ""
    for r in rows:
        cls  = _color(r["pct"])
        sign = "+" if r["pct"] > 0 else ""
        p    = r["price"]
        # Format price
        if p > 1000:
            ps = f"{p:,.0f}"
        elif p > 10:
            ps = f"{p:,.2f}"
        else:
            ps = f"{p:.4f}"
        html += f"""
        <div class="ticker-row">
          <span class="ticker-sym">{r['label']}</span>
          <span class="ticker-price">{ps}</span>
          <span class="{cls}">{sign}{r['pct']:.2f}%</span>
        </div>"""
    return html


def render():
    st.markdown(f'<div class="time-badge">⏱ {now_utc_str()}</div>', unsafe_allow_html=True)

    # ── Indices ──────────────────────────────────────────────────
    st.markdown('<div class="apex-header">Global Indices</div>', unsafe_allow_html=True)
    with st.spinner(""):
        idx_quotes = get_quotes(INDICES)
    if idx_quotes:
        st.markdown(_ticker_html(idx_quotes), unsafe_allow_html=True)
    else:
        st.markdown('<div class="apex-card">Unable to load index data.</div>', unsafe_allow_html=True)

    # ── Commodities ──────────────────────────────────────────────
    st.markdown('<div class="apex-header" style="margin-top:10px">Commodities</div>', unsafe_allow_html=True)
    with st.spinner(""):
        com_quotes = get_quotes(COMMODITIES)
    if com_quotes:
        st.markdown(_ticker_html(com_quotes), unsafe_allow_html=True)

    # ── Crypto ───────────────────────────────────────────────────
    st.markdown('<div class="apex-header" style="margin-top:10px">Crypto</div>', unsafe_allow_html=True)
    with st.spinner(""):
        cry_quotes = get_quotes(CRYPTO)
    if cry_quotes:
        st.markdown(_ticker_html(cry_quotes), unsafe_allow_html=True)

    # ── S&P 500 sparkline ────────────────────────────────────────
    st.markdown('<div class="apex-header" style="margin-top:10px">S&P 500 — 5 Day</div>', unsafe_allow_html=True)
    with st.spinner(""):
        spx_df = get_ohlcv("^GSPC", period="5d", interval="30m")
    if not spx_df.empty:
        fig = line_chart(spx_df, col="Close", title="S&P 500 30m", height=180)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── VIX ──────────────────────────────────────────────────────
    st.markdown('<div class="apex-header" style="margin-top:4px">VIX — Fear Index</div>', unsafe_allow_html=True)
    with st.spinner(""):
        vix_df = get_ohlcv("^VIX", period="5d", interval="30m")
    if not vix_df.empty:
        fig = line_chart(vix_df, col="Close", title="VIX", color="#ff4757", height=150)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

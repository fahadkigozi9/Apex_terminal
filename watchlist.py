"""Watchlist page — user can add/remove custom symbols."""

import streamlit as st
from utils.data import get_quotes, get_ohlcv
from utils.charts import line_chart

DEFAULT_WATCHLIST = ["GC=F", "EURUSD=X", "GBPUSD=X", "^GSPC", "BTC-USD", "CL=F"]

def render():
    st.markdown('<div class="apex-header">Watchlist</div>', unsafe_allow_html=True)

    if "watchlist" not in st.session_state:
        st.session_state.watchlist = list(DEFAULT_WATCHLIST)

    # Add symbol
    col1, col2 = st.columns([3, 1])
    with col1:
        new_sym = st.text_input("Add symbol (yfinance format)", placeholder="e.g. AAPL, MSFT, GC=F", label_visibility="collapsed", key="wl_input")
    with col2:
        if st.button("＋ Add", key="wl_add"):
            sym = new_sym.strip().upper()
            if sym and sym not in st.session_state.watchlist:
                st.session_state.watchlist.append(sym)
                st.rerun()

    if not st.session_state.watchlist:
        st.markdown('<div class="apex-card">Your watchlist is empty. Add symbols above.</div>', unsafe_allow_html=True)
        return

    sym_dict = {s: s for s in st.session_state.watchlist}
    with st.spinner(""):
        quotes = get_quotes(sym_dict)

    quote_map = {q["ticker"]: q for q in quotes}

    for sym in list(st.session_state.watchlist):
        q = quote_map.get(sym)
        if q:
            p   = q["price"]
            pct = q["pct"]
            cls = "up" if pct > 0 else ("down" if pct < 0 else "flat")
            sgn = "+" if pct > 0 else ""
            ps  = f"{p:,.5f}" if p < 10 else (f"{p:,.2f}" if p < 10000 else f"{p:,.0f}")
            price_html = f'<span class="ticker-price">{ps}</span> <span class="{cls}">{sgn}{pct:.2f}%</span>'
        else:
            price_html = '<span class="flat">—</span>'

        col_a, col_b, col_c = st.columns([3, 4, 1])
        with col_a:
            st.markdown(f'<div style="font-family:var(--mono);font-size:13px;font-weight:600;padding:8px 0">{sym}</div>', unsafe_allow_html=True)
        with col_b:
            st.markdown(f'<div style="padding:8px 0;font-family:var(--mono)">{price_html}</div>', unsafe_allow_html=True)
        with col_c:
            if st.button("✕", key=f"rm_{sym}"):
                st.session_state.watchlist.remove(sym)
                st.rerun()

    st.markdown("---")

    # Mini chart for selected symbol
    st.markdown('<div class="apex-header">Quick Chart</div>', unsafe_allow_html=True)
    sel = st.selectbox("Symbol", st.session_state.watchlist, key="wl_chart_sym", label_visibility="collapsed")
    tf  = st.selectbox("Timeframe", ["1h", "15m", "4h", "1d"], key="wl_tf", label_visibility="collapsed")
    period_map = {"15m": "2d", "1h": "5d", "4h": "10d", "1d": "60d"}

    if sel:
        with st.spinner(""):
            df = get_ohlcv(sel, period=period_map[tf], interval=tf)
        if not df.empty:
            fig = line_chart(df, col="Close", title=f"{sel} · {tf}", height=200)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<div class="apex-card">No chart data available.</div>', unsafe_allow_html=True)

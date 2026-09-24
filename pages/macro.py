"""Macro page — economic calendar, DXY, yields, central bank news."""

import streamlit as st
from utils.data import get_quotes, get_ohlcv, fetch_economic_calendar, fetch_news, now_utc_str
from utils.charts import line_chart, multi_line_chart
import pandas as pd

MACRO_SYMBOLS = {
    "DXY (Dollar)":  "DX-Y.NYB",
    "10Y US Yield":  "^TNX",
    "2Y US Yield":   "^IRX",
    "Gold":          "GC=F",
    "US Oil WTI":    "CL=F",
}

IMPACT_COLOR = {"High": "#ff4757", "Medium": "#f5a623", "Low": "#4a5568", "": "#4a5568"}
IMPACT_ICON  = {"High": "🔴", "Medium": "🟡", "Low": "⚪", "": "⚪"}


def render():
    st.markdown(f'<div class="time-badge">⏱ {now_utc_str()}</div>', unsafe_allow_html=True)

    tab_cal, tab_dxy, tab_yields = st.tabs(["📅 Calendar", "💵 DXY", "📊 Yields"])

    # ── Economic Calendar ────────────────────────────────────────
    with tab_cal:
        st.markdown('<div class="apex-header">Economic Calendar — This Week</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([2,1])
        with col2:
            if st.button("🔄 Refresh", key="macro_ref"):
                st.cache_data.clear()
                st.rerun()
        with col1:
            impact_filter = st.selectbox("Impact", ["All", "High", "Medium", "Low"],
                                         key="impact_f", label_visibility="collapsed")

        with st.spinner("Loading calendar…"):
            events = fetch_economic_calendar()

        if not events:
            st.markdown("""
            <div class="alert-strip">
              ⚠ Calendar data unavailable — ForexFactory API may be down.
              Check <a href="https://www.forexfactory.com/calendar" target="_blank" style="color:var(--accent)">forexfactory.com</a> directly.
            </div>""", unsafe_allow_html=True)
        else:
            if impact_filter != "All":
                events = [e for e in events if e["impact"] == impact_filter]

            for ev in events:
                imp   = ev.get("impact", "")
                icon  = IMPACT_ICON.get(imp, "⚪")
                color = IMPACT_COLOR.get(imp, "#4a5568")
                actual_html = ""
                if ev.get("actual"):
                    act_color = "var(--green)" if imp == "High" else "var(--text)"
                    actual_html = f'<span style="color:{act_color};font-weight:600">{ev["actual"]}</span>'
                else:
                    actual_html = '<span style="color:var(--text-dim)">Pending</span>'

                st.markdown(f"""
                <div class="apex-card" style="border-left:3px solid {color};padding:8px 10px;margin-bottom:4px">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div>
                      <div style="font-weight:600;font-size:12px;color:var(--text)">{icon} {ev['event']}</div>
                      <div style="font-family:var(--mono);font-size:10px;color:var(--text-dim);margin-top:2px">
                        {ev['currency']} · {ev['date']} {ev['time']}
                      </div>
                    </div>
                    <div style="text-align:right;font-family:var(--mono);font-size:11px">
                      <div>{actual_html}</div>
                      <div style="color:var(--text-dim);font-size:9px">F: {ev['forecast']} &nbsp; P: {ev['previous']}</div>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)

        # Central bank news
        st.markdown('<div class="apex-header" style="margin-top:10px">Central Bank News</div>', unsafe_allow_html=True)
        with st.spinner(""):
            cb_news = fetch_news(["Reuters", "CNBC"], limit=80)
            cb_kw   = ["fed", "federal reserve", "ecb", "european central bank", "boe", "bank of england",
                       "rate", "interest", "inflation", "cpi", "powell", "lagarde", "bailey", "hawkish", "dovish"]
            cb_news = [a for a in cb_news if any(k in a["title"].lower() for k in cb_kw)][:12]

        for a in cb_news[:8]:
            st.markdown(f"""
            <div class="news-card">
              <a href="{a['link']}" target="_blank" style="text-decoration:none;">
                <div class="news-title">{a['title'][:90]}</div>
              </a>
              <div class="news-meta">{a['source']} · {a['published']}</div>
            </div>""", unsafe_allow_html=True)

    # ── DXY ──────────────────────────────────────────────────────
    with tab_dxy:
        st.markdown('<div class="apex-header">US Dollar Index (DXY)</div>', unsafe_allow_html=True)
        with st.spinner(""):
            dxy_quotes = get_quotes({"DXY": "DX-Y.NYB", "Gold": "GC=F", "Oil WTI": "CL=F"})
        for r in dxy_quotes:
            cls = "up" if r["pct"] > 0 else ("down" if r["pct"] < 0 else "flat")
            sgn = "+" if r["pct"] > 0 else ""
            p   = r["price"]
            ps  = f"{p:,.3f}" if p < 200 else f"{p:,.2f}"
            st.markdown(f"""
            <div class="ticker-row">
              <span class="ticker-sym">{r['label']}</span>
              <span class="ticker-price">{ps}</span>
              <span class="{cls}">{sgn}{r['pct']:.2f}%</span>
            </div>""", unsafe_allow_html=True)

        tf_dxy = st.selectbox("Timeframe", ["1h", "4h", "1d"], key="dxy_tf", label_visibility="collapsed")
        period_map = {"1h": "5d", "4h": "10d", "1d": "60d"}
        with st.spinner(""):
            dxy_df = get_ohlcv("DX-Y.NYB", period=period_map[tf_dxy], interval=tf_dxy)
        if not dxy_df.empty:
            fig = line_chart(dxy_df, col="Close", title=f"DXY · {tf_dxy}", height=220)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown("""
        <div class="apex-card" style="margin-top:6px">
          <div style="font-size:11px;color:var(--text-dim);line-height:1.6">
            📌 <strong style="color:var(--accent)">DXY Inverse Rule:</strong><br>
            DXY ↑ → Gold ↓ &nbsp;|&nbsp; DXY ↓ → Gold ↑<br>
            Watch DXY as a leading indicator for XAUUSDz direction.
          </div>
        </div>""", unsafe_allow_html=True)

    # ── Yields ───────────────────────────────────────────────────
    with tab_yields:
        st.markdown('<div class="apex-header">US Treasury Yields</div>', unsafe_allow_html=True)
        with st.spinner(""):
            yield_quotes = get_quotes({"10Y Yield": "^TNX", "2Y Yield": "^IRX", "5Y Yield": "^FVX"})
        for r in yield_quotes:
            cls = "up" if r["pct"] > 0 else ("down" if r["pct"] < 0 else "flat")
            sgn = "+" if r["pct"] > 0 else ""
            st.markdown(f"""
            <div class="ticker-row">
              <span class="ticker-sym">{r['label']}</span>
              <span class="ticker-price">{r['price']:.3f}%</span>
              <span class="{cls}">{sgn}{r['pct']:.2f}%</span>
            </div>""", unsafe_allow_html=True)

        # Yield curve mini chart
        with st.spinner(""):
            t10_df = get_ohlcv("^TNX", period="30d", interval="1d")
            t2_df  = get_ohlcv("^IRX", period="30d", interval="1d")

        if not t10_df.empty and not t2_df.empty:
            if isinstance(t10_df.columns, pd.MultiIndex):
                t10_df.columns = t10_df.columns.get_level_values(0)
            if isinstance(t2_df.columns, pd.MultiIndex):
                t2_df.columns = t2_df.columns.get_level_values(0)
            series_list = [
                {"name": "10Y", "x": t10_df.index, "y": t10_df["Close"], "color": "#f5a623"},
                {"name": "2Y",  "x": t2_df.index,  "y": t2_df["Close"],  "color": "#4a9eff"},
            ]
            fig = multi_line_chart(series_list, title="Yield Curve 30D", height=200)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown("""
        <div class="apex-card" style="margin-top:6px">
          <div style="font-size:11px;color:var(--text-dim);line-height:1.6">
            📌 <strong style="color:var(--accent)">Yield-Gold Rule:</strong><br>
            Yields ↑ → Gold pressure down (higher opportunity cost)<br>
            Yields ↓ → Gold bullish (safe haven / lower USD returns)
          </div>
        </div>""", unsafe_allow_html=True)

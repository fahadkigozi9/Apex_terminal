"""News page — aggregated from Reuters, CNBC, MarketWatch, FXStreet, Yahoo Finance."""

import streamlit as st
from data import get_quotes, get_ohlcv, get_ticker_info, RSS_FEEDS

SOURCE_COLORS = {
    "Reuters":       "#f5a623",
    "CNBC":          "#00d4a4",
    "MarketWatch":   "#4a9eff",
    "Yahoo Finance": "#6c5ecf",
    "FXStreet":      "#ff6b9d",
    "Kitco Gold":    "#ffd700",
    "Investing.com": "#ff4757",
}

def _news_cards(articles):
    if not articles:
        st.markdown('<div class="apex-card">No articles loaded — check your internet connection.</div>', unsafe_allow_html=True)
        return
    for a in articles:
        color   = SOURCE_COLORS.get(a["source"], "#7a8a9e")
        title   = a["title"][:100] + ("…" if len(a["title"]) > 100 else "")
        summary = a["summary"][:140] + ("…" if len(a["summary"]) > 140 else "")
        link    = a["link"]
        age     = a["age_h"]
        age_str = f"{int(age*60)}m ago" if age < 1 else (f"{age:.1f}h ago" if age < 24 else f"{int(age/24)}d ago")

        st.markdown(f"""
        <div class="news-card">
          <a href="{link}" target="_blank" style="text-decoration:none;">
            <div class="news-title">{title}</div>
          </a>
          <div style="font-size:11px;color:var(--text-dim);margin:3px 0 0">{summary}</div>
          <div class="news-meta" style="margin-top:5px">
            <span style="color:{color};font-weight:600">{a['source']}</span>
            &nbsp;·&nbsp;{a['published']}
            &nbsp;·&nbsp;<span style="color:var(--text-dim)">{age_str}</span>
          </div>
        </div>""", unsafe_allow_html=True)


def render():
    # Source filter
    all_sources = list(RSS_FEEDS.keys())
    st.markdown('<div class="apex-header">News Feed</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        selected = st.multiselect(
            "Sources",
            options=all_sources,
            default=all_sources,
            label_visibility="collapsed",
            key="news_sources",
        )
    with col2:
        if st.button("🔄 Refresh", key="news_ref"):
            st.cache_data.clear()
            st.rerun()

    # Keyword filter
    kw = st.text_input("Filter by keyword", placeholder="e.g. gold, fed, inflation", label_visibility="collapsed", key="news_kw")

    with st.spinner("Loading news…"):
        articles = fetch_news(sources=selected if selected else all_sources, limit=60)

    if kw:
        kw_lower = kw.lower()
        articles = [a for a in articles if kw_lower in a["title"].lower() or kw_lower in a["summary"].lower()]

    st.markdown(f'<div class="time-badge">{len(articles)} articles · sorted newest first</div>', unsafe_allow_html=True)
    _news_cards(articles)

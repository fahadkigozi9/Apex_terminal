"""
APEX Terminal — Bloomberg-style mobile trading terminal
Entry point
"""

import streamlit as st

st.set_page_config(
    page_title="APEX Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

# Inject global CSS
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from pages import markets, news, watchlist, forex, gold, macro

tabs = st.tabs(["📈 Markets", "🥇 Gold/FX", "👁 Watch", "📰 News", "🌐 Macro"])

with tabs[0]:
    markets.render()

with tabs[1]:
    gold.render()

with tabs[2]:
    watchlist.render()

with tabs[3]:
    news.render()

with tabs[4]:
    macro.render()

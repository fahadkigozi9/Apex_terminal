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
import os
from pathlib import Path

# Build an absolute path to assets/style.css relative to app.py
css_path = Path(__file__).parent / "assets" / "style.css"

if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

import os
import sys

# Ensure current directory and subdirectories are added to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))



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

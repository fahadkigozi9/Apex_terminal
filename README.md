# 📊 APEX Terminal

A Bloomberg-style mobile trading terminal built with Streamlit.  
Designed for forex & gold traders — optimised for phone screens.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

| Tab | What it shows |
|-----|--------------|
| 📈 Markets | Global indices, commodities, crypto — live quotes + charts |
| 🥇 Gold/FX | XAUUSDz & forex pairs — candlestick charts, gold & forex news |
| 👁 Watchlist | Custom symbol watchlist with mini charts |
| 📰 News | Live RSS from Reuters, CNBC, MarketWatch, FXStreet, Kitco, Yahoo Finance |
| 🌐 Macro | Economic calendar (ForexFactory), DXY, US yield curve |

### Data Sources (all free)
- **yfinance** — price data, OHLCV charts
- **Reuters RSS** — business & finance news
- **CNBC RSS** — markets news
- **MarketWatch RSS** — market pulse
- **FXStreet RSS** — forex-specific news
- **Kitco RSS** — gold & precious metals news
- **Yahoo Finance RSS** — general financial news
- **ForexFactory JSON API** — economic calendar

---

## Quick Start

### 1. Clone
```bash
git clone https://github.com/YOUR_USERNAME/apex-terminal.git
cd apex-terminal
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run
```bash
streamlit run app.py
```

Open `http://localhost:8501` on your phone (connect phone to same WiFi as PC, use your PC's local IP).

---

## Deploy to Streamlit Cloud (free hosting)

1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set **Main file path** to `app.py`
5. Deploy — you get a public URL to open on any phone

---

## Project Structure

```
apex-terminal/
├── app.py                  # Entry point & tab layout
├── requirements.txt
├── .streamlit/
│   └── config.toml         # Dark theme config
├── assets/
│   └── style.css           # Bloomberg-style CSS
├── pages/
│   ├── markets.py          # Global indices, commodities, crypto
│   ├── gold.py             # Gold & Forex with charts + news
│   ├── watchlist.py        # Custom watchlist
│   ├── news.py             # Aggregated news feed
│   └── macro.py            # Economic calendar, DXY, yields
└── utils/
    ├── data.py             # All data fetching (yfinance + RSS)
    └── charts.py           # Plotly chart builders
```

---

## Mobile Tips

- Add the Streamlit Cloud URL to your **Home Screen** (Safari → Share → Add to Home Screen) for a near-native app feel
- The terminal auto-refreshes news every 2 minutes and prices every 30 seconds via Streamlit's cache TTL
- Use the **Gold/FX tab** for XAUUSDz and EURUSDz monitoring — built with Exness traders in mind

---

## Customisation

Edit `utils/data.py` to:
- Add more forex pairs to `FOREX_PAIRS`
- Add more RSS feeds to `RSS_FEEDS`
- Change cache TTLs (`@st.cache_data(ttl=...)`)

---

## License
MIT

"""
Data fetching utilities — yfinance, RSS feeds (Reuters, CNBC, FXStreet, Kitco, MarketWatch)
All functions cached with TTL to avoid rate limits.
"""

import streamlit as st
import yfinance as yf
import feedparser
import requests
import pandas as pd
from datetime import datetime, timezone

# ── Symbol maps ──────────────────────────────────────────────────

FOREX_PAIRS = {
    "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X", "USDCAD": "USDCAD=X", "USDCHF": "USDCHF=X",
    "NZDUSD": "NZDUSD=X", "EURGBP": "EURGBP=X", "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X",
}
GOLD_SYMBOLS = {
    "XAUUSD Spot": "GC=F", "XAGUSD Silver": "SI=F",
    "GLD ETF": "GLD", "IAU ETF": "IAU",
}
INDICES = {
    "S&P 500": "^GSPC", "NASDAQ": "^IXIC", "DOW": "^DJI",
    "FTSE 100": "^FTSE", "DAX": "^GDAXI", "Nikkei": "^N225",
    "VIX": "^VIX",
}
COMMODITIES = {
    "Gold": "GC=F", "Silver": "SI=F", "Crude WTI": "CL=F",
    "Brent": "BZ=F", "Nat Gas": "NG=F", "Copper": "HG=F",
}
CRYPTO = {
    "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD",
    "BNB": "BNB-USD", "Solana": "SOL-USD",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 Safari/604.1"
    )
}

# ── Price fetching ────────────────────────────────────────────────

@st.cache_data(ttl=30)
def get_quotes(symbols: dict) -> list:
    """Fetch latest quotes for {label: yf_ticker}."""
    results = []
    tickers = list(symbols.values())
    labels  = list(symbols.keys())
    try:
        if len(tickers) == 1:
            data = yf.download(tickers[0], period="5d", interval="1d",
                               auto_adjust=True, progress=False)
            closes_map = {tickers[0]: data["Close"].dropna() if "Close" in data else pd.Series()}
        else:
            data = yf.download(tickers, period="5d", interval="1d",
                               group_by="ticker", auto_adjust=True,
                               progress=False, threads=True)
            closes_map = {}
            for t in tickers:
                try:
                    closes_map[t] = data[t]["Close"].dropna()
                except Exception:
                    closes_map[t] = pd.Series()

        for label, ticker in zip(labels, tickers):
            closes = closes_map.get(ticker, pd.Series())
            if len(closes) >= 2:
                prev = float(closes.iloc[-2])
                curr = float(closes.iloc[-1])
                chg  = curr - prev
                pct  = (chg / prev) * 100
            elif len(closes) == 1:
                curr = float(closes.iloc[-1])
                chg = pct = 0.0
            else:
                continue
            results.append({
                "label": label, "ticker": ticker,
                "price": curr, "change": chg, "pct": pct,
            })
    except Exception:
        pass
    return results


@st.cache_data(ttl=60)
def get_ohlcv(ticker: str, period: str = "5d", interval: str = "15m") -> pd.DataFrame:
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_ticker_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}


# ── News RSS feeds ────────────────────────────────────────────────

RSS_FEEDS = {
    "Reuters": [
        "https://feeds.reuters.com/reuters/businessNews",
        "https://feeds.reuters.com/reuters/financialServicesAndRealEstateNews",
    ],
    "CNBC": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    ],
    "MarketWatch": [
        "https://feeds.marketwatch.com/marketwatch/topstories",
        "https://feeds.marketwatch.com/marketwatch/marketpulse",
    ],
    "Yahoo Finance": [
        "https://finance.yahoo.com/rss/headline",
    ],
    "FXStreet": [
        "https://www.fxstreet.com/rss",
    ],
    "Kitco Gold": [
        "https://www.kitco.com/rss/kitco-news.xml",
    ],
    "Investing.com": [
        "https://www.investing.com/rss/news_25.rss",
    ],
}


@st.cache_data(ttl=120)
def fetch_news(sources=None, limit: int = 50) -> list:
    if sources is None:
        sources = list(RSS_FEEDS.keys())
    articles = []
    for source in sources:
        for url in RSS_FEEDS.get(source, []):
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:12]:
                    pub = entry.get("published_parsed") or entry.get("updated_parsed")
                    if pub:
                        pub_dt = datetime(*pub[:6], tzinfo=timezone.utc)
                        age_h  = (datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600
                        pub_str = pub_dt.strftime("%H:%M UTC")
                    else:
                        age_h, pub_str = 999, "—"
                    articles.append({
                        "title":     entry.get("title", "").strip(),
                        "link":      entry.get("link", ""),
                        "source":    source,
                        "published": pub_str,
                        "age_h":     age_h,
                        "summary":   entry.get("summary", "")[:220],
                    })
            except Exception:
                continue
    articles.sort(key=lambda x: x["age_h"])
    return articles[:limit]


@st.cache_data(ttl=120)
def fetch_gold_news(limit: int = 25) -> list:
    all_news = fetch_news(["Kitco Gold", "FXStreet", "Reuters", "CNBC"], limit=80)
    kw = ["gold", "xau", "silver", "bullion", "precious", "fed", "rates", "inflation", "dxy"]
    return [a for a in all_news if any(k in a["title"].lower() for k in kw)][:limit]


@st.cache_data(ttl=120)
def fetch_forex_news(limit: int = 25) -> list:
    all_news = fetch_news(["FXStreet", "Reuters", "CNBC", "Investing.com"], limit=80)
    kw = ["forex", "currency", "usd", "eur", "gbp", "jpy", "aud", "dollar",
          "euro", "pound", "yen", "fed", "ecb", "boe", "rba", "central bank", "pips"]
    return [a for a in all_news if any(k in a["title"].lower() for k in kw)][:limit]


# ── Economic calendar ─────────────────────────────────────────────

@st.cache_data(ttl=1800)
def fetch_economic_calendar() -> list:
    """ForexFactory JSON calendar — best free source."""
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            return [
                {
                    "date":     ev.get("date", ""),
                    "time":     ev.get("time", ""),
                    "currency": ev.get("country", ""),
                    "impact":   ev.get("impact", ""),
                    "event":    ev.get("title", ""),
                    "forecast": ev.get("forecast") or "—",
                    "previous": ev.get("previous") or "—",
                    "actual":   ev.get("actual") or "",
                }
                for ev in r.json()
            ]
    except Exception:
        pass
    return []


def now_utc_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

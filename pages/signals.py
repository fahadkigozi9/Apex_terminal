import json
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import streamlit as st
import yfinance as yf
from groq import Groq, APIError

# Import shared terminal functions if available
try:
    from data import get_quotes, get_ohlcv
except ImportError:
    pass

STATE_FILE = "trade_state.json"

ASSET_MAP = {
    "Gold (XAU/USD)": "GC=F",
    "GBP/USD": "GBPUSD=X",
    "EUR/USD": "EURUSD=X",
    "Bitcoin (BTC/USD)": "BTC-USD"
}

# ------------------------------------------------------------------------------
# Session State & Persistence
# ------------------------------------------------------------------------------
if "groq_key" not in st.session_state:
    st.session_state["groq_key"] = st.secrets.get("GROQ_API_KEY", "")
if "telegram_token" not in st.session_state:
    st.session_state["telegram_token"] = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
if "telegram_chat_id" not in st.session_state:
    st.session_state["telegram_chat_id"] = st.secrets.get("TELEGRAM_CHAT_ID", "")

def load_trade_history() -> list:
    if "trade_history" in st.session_state:
        return st.session_state["trade_history"]
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                history = json.load(f)
                if isinstance(history, list):
                    st.session_state["trade_history"] = history
                    return history
        except Exception:
            pass
    st.session_state["trade_history"] = []
    return []

def save_new_signal(signal_data: dict):
    history = load_trade_history()
    history.append(signal_data)
    st.session_state["trade_history"] = history
    with open(STATE_FILE, "w") as f:
        json.dump(history, f, indent=4)

def save_all_trades(history: list):
    st.session_state["trade_history"] = history
    with open(STATE_FILE, "w") as f:
        json.dump(history, f, indent=4)

# ------------------------------------------------------------------------------
# Data Scraping & Market Operations
# ------------------------------------------------------------------------------
def fetch_live_price(ticker_symbol: str) -> dict:
    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period="1d", interval="1m")
        if data.empty:
            return {"price": 0.0, "change": 0.0, "status": "No Data"}
        
        latest_price = float(data["Close"].iloc[-1])
        open_price = float(data["Open"].iloc[0])
        pct_change = ((latest_price - open_price) / open_price) * 100
        
        return {"price": latest_price, "change": pct_change, "status": "Success"}
    except Exception as e:
        return {"price": 0.0, "change": 0.0, "status": str(e)}

def scrape_forex_factory_news() -> list:
    url = "https://www.forexfactory.com/calendar"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    events = []
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.find_all("tr", class_="calendar__row")
            for row in rows:
                impact = row.find("td", class_="calendar__impact")
                if impact and impact.find("span", class_="icon--ff-impact-red"):
                    currency = row.find("td", class_="calendar__currency")
                    title = row.find("td", class_="calendar__event")
                    time_elem = row.find("td", class_="calendar__time")
                    events.append({
                        "time": time_elem.text.strip() if time_elem else "",
                        "currency": currency.text.strip() if currency else "",
                        "title": title.text.strip() if title else ""
                    })
    except Exception:
        pass
    return events

def send_telegram_alert(bot_token: str, chat_id: str, message: str) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

# ------------------------------------------------------------------------------
# Signal Generation Engine
# ------------------------------------------------------------------------------
def determine_order_type(action: str, entry_price: float, current_price: float) -> str:
    if action == "BUY":
        return "BUY STOP" if entry_price > current_price else "BUY LIMIT"
    else:
        return "SELL STOP" if entry_price < current_price else "SELL LIMIT"

MODEL_FALLBACKS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
    "openai/gpt-oss-20b"
]

def generate_groq_signal(asset: str, price_data: dict, news_data: list, timeframe: str, api_key: str) -> dict:
    if not api_key:
        return {"signal": "ERROR", "confidence": 0, "reasons": ["Groq API key missing"]}

    client = Groq(api_key=api_key)
    current_price = price_data.get("price", 0.0)

    prompt = f"""
You are an institutional trading analyst. Analyze parameters for {asset}:
- Timeframe: {timeframe}
- Current Price: {current_price}
- Daily Change (%): {price_data.get('change')}
- High-Impact News: {json.dumps(news_data, indent=2)}

Return ONLY a raw JSON object matching this schema without markdown formatting:
{{
    "signal": "BUY",
    "entry_price": 0.0,
    "stop_loss": 0.0,
    "take_profit_1": 0.0,
    "take_profit_2": 0.0,
    "risk_reward_ratio": "1:2.5",
    "confidence": 85,
    "reasons": ["Key structure level sweep", "News sentiment aligned"]
}}
"""

    for model in MODEL_FALLBACKS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            raw_content = response.choices[0].message.content.strip()
            if raw_content.startswith("```json"): raw_content = raw_content[7:]
            if raw_content.startswith("```"): raw_content = raw_content[3:]
            if raw_content.endswith("```"): raw_content = raw_content[:-3]
                
            signal_obj = json.loads(raw_content.strip())
            sig_action = signal_obj.get("signal", "BUY").upper()
            entry_p = float(signal_obj.get("entry_price", current_price))
            signal_obj["order_type"] = determine_order_type(sig_action, entry_p, current_price)
            return signal_obj
        except APIError as e:
            if e.status_code in [400, 404] or "decommissioned" in str(e).lower():
                continue
            return {"signal": "ERROR", "confidence": 0, "reasons": [str(e)]}
        except Exception:
            continue

    return {"signal": "ERROR", "confidence": 0, "reasons": ["All AI model fallbacks failed."]}

# ------------------------------------------------------------------------------
# Backtesting & Trade Status Engine
# ------------------------------------------------------------------------------
def run_strategy_backtest(ticker_symbol: str, timeframe: str, lookback_days: int, signal_data: dict) -> dict:
    yf_interval_map = {"15m": "15m", "1h": "1h", "4h": "1h", "1D": "1d"}
    interval = yf_interval_map.get(timeframe, "1h")
    
    try:
        df = yf.download(ticker_symbol, period=f"{lookback_days}d", interval=interval)
        if df.empty:
            return {"error": "Failed to fetch historical data for backtesting."}
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        action = signal_data.get("signal", "BUY").upper()
        entry = float(signal_data.get("entry_price", 0.0))
        sl = float(signal_data.get("stop_loss", 0.0))
        tp = float(signal_data.get("take_profit_1", 0.0))
        
        if entry == 0.0 or sl == 0.0 or tp == 0.0:
            return {"error": "Invalid target price levels for strategy backtest."}
            
        point = 0.1 if "GC=F" in ticker_symbol or "Gold" in ticker_symbol else (1.0 if "BTC" in ticker_symbol else 0.0001)
        
        trades = []
        in_position = False
        
        for i in range(len(df)):
            high_val = df["High"].iloc[i]
            low_val = df["Low"].iloc[i]
            high = float(high_val.iloc[0]) if isinstance(high_val, pd.Series) else float(high_val)
            low = float(low_val.iloc[0]) if isinstance(low_val, pd.Series) else float(low_val)
            
            if not in_position:
                if (action == "BUY" and low <= entry <= high) or (action == "SELL" and low <= entry <= high):
                    in_position = True
                continue

            if in_position:
                if action == "BUY":
                    if low <= sl:
                        trades.append({"result": "LOSS", "pips": (sl - entry) / point})
                        in_position = False
                    elif high >= tp:
                        trades.append({"result": "WIN", "pips": (tp - entry) / point})
                        in_position = False
                else:
                    if high >= sl:
                        trades.append({"result": "LOSS", "pips": (entry - sl) / point})
                        in_position = False
                    elif low <= tp:
                        trades.append({"result": "WIN", "pips": (entry - tp) / point})
                        in_position = False

        if not trades:
            return {"error": "No completed trade cycles triggered in this historical window."}

        total_trades = len(trades)
        wins = sum(1 for t in trades if t["result"] == "WIN")
        losses = total_trades - wins
        win_rate = (wins / total_trades) * 100
        net_pips = sum(t["pips"] for t in trades)

        return {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2),
            "net_pips": round(net_pips, 1)
        }
    except Exception as e:
        return {"error": f"Backtest failure: {str(e)}"}

def evaluate_trade_status(saved_signal: dict, current_price: float) -> dict:
    action = saved_signal.get("signal", "BUY").upper()
    entry = float(saved_signal.get("entry_price", 0.0))
    sl = float(saved_signal.get("stop_loss", 0.0))
    tp1 = float(saved_signal.get("take_profit_1", 0.0))

    if entry == 0.0 or sl == 0.0:
        return {"recommendation": "UNKNOWN", "analysis": "Invalid levels."}

    ticker_str = saved_signal.get("ticker", "")
    point = 0.1 if "GC=F" in ticker_str else (1.0 if "BTC" in ticker_str else 0.0001)

    pnl_pips = (current_price - entry) / point if "BUY" in action else (entry - current_price) / point
    risk_pips = (entry - sl) / point if "BUY" in action else (sl - entry) / point
    hit_sl = current_price <= sl if "BUY" in action else current_price >= sl
    rr_achieved = pnl_pips / risk_pips if risk_pips > 0 else 0

    if hit_sl:
        recommendation = "STOP LOSS HIT"
        analysis = f"❌ Trade invalidated. Hit SL ({sl}). PnL: {pnl_pips:.1f} pips."
    elif rr_achieved >= 1.0:
        recommendation = "TRAIL SL TO BREAKEVEN"
        analysis = f"🎯 1:1 R:R achieved (+{pnl_pips:.1f} pips). Lock SL to entry ({entry})."
    else:
        recommendation = "HOLD POSITION"
        analysis = f"⏳ Setup intact. PnL: {pnl_pips:+.1f} pips. TP: {tp1}."

    return {
        "asset": saved_signal.get("asset"),
        "order_type": saved_signal.get("order_type"),
        "entry": entry,
        "current_price": current_price,
        "pnl_pips": round(pnl_pips, 1),
        "rr_achieved": round(rr_achieved, 2),
        "recommendation": recommendation,
        "analysis": analysis,
        "hit_sl": hit_sl
    }

# ------------------------------------------------------------------------------
# Terminal Page Render
# ------------------------------------------------------------------------------
def render():
    st.markdown("## 📡 Signals Engine")

    with st.sidebar:
        st.subheader("🔑 Credentials & Settings")
        st.session_state["groq_key"] = st.text_input("Groq API Key", value=st.session_state["groq_key"], type="password")
        st.session_state["telegram_token"] = st.text_input("Telegram Bot Token", value=st.session_state["telegram_token"], type="password")
        st.session_state["telegram_chat_id"] = st.text_input("Telegram Chat ID", value=st.session_state["telegram_chat_id"])
        
        selected_asset_label = st.selectbox("Select Asset", list(ASSET_MAP.keys()))
        selected_ticker = ASSET_MAP[selected_asset_label]
        selected_timeframe = st.selectbox("Timeframe", ["15m", "1h", "4h", "1D"])

    news_list = scrape_forex_factory_news()

    tab1, tab2, tab3 = st.tabs(["⚡ Live Signals", "🔍 Active Status", "🧪 Backtest"])

    with tab1:
        st.subheader(f"Market Analysis: {selected_asset_label}")
        price_data = fetch_live_price(selected_ticker)
        
        if price_data["status"] == "Success":
            st.metric("Live Price", f"{price_data['price']:.4f}", f"{price_data['change']:.2f}%")
        
        if st.button("Generate Signal & Dispatch Alert", type="primary"):
            if not st.session_state["groq_key"]:
                st.error("Missing Groq API Key!")
            else:
                with st.spinner("Evaluating market setup..."):
                    setup = generate_groq_signal(selected_asset_label, price_data, news_list, selected_timeframe, st.session_state["groq_key"])
                    sig = setup.get("signal", "NEUTRAL")
                    if sig in ["BUY", "SELL"]:
                        setup["id"] = f"TRADE-{pd.Timestamp.now().strftime('%M%S')}"
                        setup["timestamp"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                        setup["asset"] = selected_asset_label
                        setup["ticker"] = selected_ticker
                        setup["timeframe"] = selected_timeframe
                        setup["status"] = "ACTIVE"
                        
                        save_new_signal(setup)

                        st.success(f"### {setup.get('order_type')} ({sig}) — {setup.get('confidence')}% Confidence")
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Entry Price", setup.get("entry_price"))
                        m2.metric("Stop Loss", setup.get("stop_loss"))
                        m3.metric("Take Profit 1", setup.get("take_profit_1"))
                        m4.metric("Take Profit 2", setup.get("take_profit_2"))

                        if st.session_state["telegram_token"] and st.session_state["telegram_chat_id"]:
                            msg = (
                                f"📲 *NEW AI SIGNAL DISPATCH*\n\n"
                                f"📌 *Asset:* {selected_asset_label}\n"
                                f"⚡ *Order Type:* `{setup.get('order_type')}`\n"
                                f"🎯 *Entry:* `{setup.get('entry_price')}`\n"
                                f"🛑 *SL:* `{setup.get('stop_loss')}` | 🟢 *TP:* `{setup.get('take_profit_1')}`"
                            )
                            send_telegram_alert(st.session_state["telegram_token"], st.session_state["telegram_chat_id"], msg)

    with tab2:
        st.subheader("Active Trade Tracker")
        trade_history = load_trade_history()
        if not trade_history:
            st.info("No saved trades found.")
        else:
            for trade in reversed(trade_history):
                live_data = fetch_live_price(trade.get("ticker", selected_ticker))
                if live_data["status"] == "Success":
                    rep = evaluate_trade_status(trade, live_data["price"])
                    with st.expander(f"📌 {rep['asset']} | {rep['order_type']} @ {rep['entry']}", expanded=True):
                        st.write(f"**PnL:** {rep['pnl_pips']:+} pips | **Action:** `{rep['recommendation']}`")
                        st.write(rep["analysis"])

    with tab3:
        st.subheader("Strategy Backtester")
        trade_history = load_trade_history()
        if trade_history:
            selected_trade_id = st.selectbox("Select Signal", options=[t.get("id") for t in reversed(trade_history)])
            target_trade = next((t for t in trade_history if t.get("id") == selected_trade_id), None)
            if target_trade and st.button("Run Backtest"):
                res = run_strategy_backtest(target_trade.get("ticker", selected_ticker), target_trade.get("timeframe", "1h"), 30, target_trade)
                if "error" not in res:
                    st.success(f"Win Rate: {res['win_rate']}% | Total Pips: {res['net_pips']}")

if __name__ == "__main__":
    render()

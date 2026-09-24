"""
Plotly chart builders styled for APEX Terminal dark theme.
"""

import plotly.graph_objects as go
import pandas as pd

THEME = dict(
    bg       = "#0a0c0f",
    bg2      = "#111418",
    border   = "#1e2430",
    accent   = "#f5a623",
    green    = "#00d4a4",
    red      = "#ff4757",
    blue     = "#4a9eff",
    text     = "#d4dce8",
    text_dim = "#7a8a9e",
    grid     = "#1a1f28",
)

LAYOUT_BASE = dict(
    paper_bgcolor = THEME["bg"],
    plot_bgcolor  = THEME["bg"],
    font          = dict(family="IBM Plex Mono, monospace", size=10, color=THEME["text_dim"]),
    margin        = dict(l=4, r=4, t=28, b=4),
    xaxis         = dict(
        gridcolor     = THEME["grid"],
        showgrid      = True,
        zeroline      = False,
        tickfont      = dict(size=9),
        showline      = True,
        linecolor     = THEME["border"],
    ),
    yaxis         = dict(
        gridcolor     = THEME["grid"],
        showgrid      = True,
        zeroline      = False,
        tickfont      = dict(size=9),
        showline      = True,
        linecolor     = THEME["border"],
        side          = "right",
    ),
    legend        = dict(
        bgcolor      = "rgba(0,0,0,0)",
        font         = dict(size=9),
        orientation  = "h",
        x=0, y=1.05,
    ),
    hoverlabel    = dict(
        bgcolor    = THEME["bg2"],
        bordercolor= THEME["border"],
        font       = dict(family="IBM Plex Mono", size=10),
    ),
)


def candlestick_chart(df: pd.DataFrame, title: str = "", height: int = 280) -> go.Figure:
    """OHLCV candlestick chart."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(**LAYOUT_BASE, height=height,
                          title=dict(text="No data", font=dict(size=10)))
        return fig

    # Flatten MultiIndex columns if needed
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    up   = df["Close"] >= df["Open"]
    down = ~up

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x     = df.index,
        open  = df["Open"],
        high  = df["High"],
        low   = df["Low"],
        close = df["Close"],
        increasing_line_color = THEME["green"],
        decreasing_line_color = THEME["red"],
        increasing_fillcolor  = THEME["green"],
        decreasing_fillcolor  = THEME["red"],
        name  = title,
        showlegend = False,
    ))

    layout = dict(**LAYOUT_BASE)
    layout["height"] = height
    layout["title"]  = dict(text=title, font=dict(size=10, color=THEME["accent"]), x=0, xanchor="left")
    layout["xaxis"]["rangeslider"] = dict(visible=False)
    fig.update_layout(**layout)
    return fig


def line_chart(df: pd.DataFrame, col: str = "Close", title: str = "",
               color: str = "#4a9eff", height: int = 200) -> go.Figure:
    """Simple line chart for a single series."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(**LAYOUT_BASE, height=height)
        return fig

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    series = df[col].dropna() if col in df else pd.Series()
    if series.empty:
        fig = go.Figure()
        fig.update_layout(**LAYOUT_BASE, height=height)
        return fig

    chg = series.iloc[-1] - series.iloc[0] if len(series) > 1 else 0
    line_color = THEME["green"] if chg >= 0 else THEME["red"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x    = df.index,
        y    = series,
        mode = "lines",
        line = dict(color=line_color, width=1.5),
        fill = "tozeroy",
        fillcolor = f"rgba({int(line_color[1:3],16)},{int(line_color[3:5],16)},{int(line_color[5:7],16)},0.08)",
        name = col,
        showlegend = False,
    ))
    layout = dict(**LAYOUT_BASE)
    layout["height"] = height
    layout["title"]  = dict(text=title, font=dict(size=10, color=THEME["accent"]), x=0, xanchor="left")
    fig.update_layout(**layout)
    return fig


def multi_line_chart(series_list: list, title: str = "", height: int = 220) -> go.Figure:
    """
    series_list: [{"name": str, "x": index, "y": series, "color": hex}, ...]
    """
    fig = go.Figure()
    colors = [THEME["accent"], THEME["blue"], THEME["green"], THEME["red"]]
    for i, s in enumerate(series_list):
        c = s.get("color") or colors[i % len(colors)]
        fig.add_trace(go.Scatter(
            x    = s["x"],
            y    = s["y"],
            mode = "lines",
            name = s["name"],
            line = dict(color=c, width=1.5),
        ))
    layout = dict(**LAYOUT_BASE)
    layout["height"] = height
    layout["title"]  = dict(text=title, font=dict(size=10, color=THEME["accent"]), x=0, xanchor="left")
    fig.update_layout(**layout)
    return fig

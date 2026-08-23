import sqlite3
import numpy as np
import pandas as pd


def get_rsi(data, window=14):
    diff = data.diff()
    gain = diff.clip(lower=0)
    loss = -1 * diff.clip(upper=0)
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()

    for idx in range(window, len(data)):
        avg_gain.iloc[idx] = (
            avg_gain.iloc[idx - 1] * (window - 1) + gain.iloc[idx]
        ) / window
        avg_loss.iloc[idx] = (
            avg_loss.iloc[idx - 1] * (window - 1) + loss.iloc[idx]
        ) / window

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


conn = sqlite3.connect("stock_market.db")
df = pd.read_sql_query(
    "SELECT * FROM raw_stock_prices ORDER BY Ticker, Date", conn
)

df["Date"] = pd.to_datetime(df["Date"])
processed_frames = []

for ticker, group in df.groupby("Ticker"):
    g = group.sort_values("Date").copy()

    g["SMA_20"] = g["Close"].rolling(20).mean()
    g["SMA_50"] = g["Close"].rolling(50).mean()
    g["RSI_14"] = get_rsi(g["Close"], 14)
    g["Volatility_20"] = g["Close"].pct_change().rolling(20).std()

    g["Signal"] = 0
    g["Signal"] = np.where(g["SMA_20"] > g["SMA_50"], 1, 0)
    g["Position"] = g["Signal"].shift(1).fillna(0)

    g["Market_Return"] = g["Close"].pct_change()
    g["Strategy_Return"] = g["Market_Return"] * g["Position"]

    g["Cum_Market"] = (1 + g["Market_Return"].fillna(0)).cumprod()
    g["Cum_Strategy"] = (1 + g["Strategy_Return"].fillna(0)).cumprod()

    peak = g["Cum_Strategy"].cummax()
    g["Drawdown"] = (g["Cum_Strategy"] - peak) / peak

    processed_frames.append(g)

res = pd.concat(processed_frames)
res["Date"] = res["Date"].dt.strftime("%Y-%m-%d")

res.to_sql("processed_stock_analytics", conn, if_exists="replace", index=False)
conn.close()

print("Technical analytics processed successfully.")
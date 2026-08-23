import sqlite3
import numpy as np
import pandas as pd

def get_rsi(series, period=14):
    """Calculates standard 14-period Wilder's RSI using Pandas EWM."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    
    # Wilder's Exponential Moving Average (alpha = 1 / period)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi

def main():
    conn = sqlite3.connect("stock_market.db")
    df = pd.read_sql_query("SELECT * FROM raw_stock_prices ORDER BY Ticker, Date", conn)
    
    if df.empty:
        print("Warning: raw_stock_prices table is empty.")
        conn.close()
        return

    df["Date"] = pd.to_datetime(df["Date"])
    processed_frames = []
    
    for ticker, group in df.groupby("Ticker"):
        g = group.sort_values("Date").copy()
    
        # Trend & Technical Indicators
        g["SMA_20"] = g["Close"].rolling(20).mean()
        g["SMA_50"] = g["Close"].rolling(50).mean()
        g["RSI_14"] = get_rsi(g["Close"], 14)
        g["Volatility_20"] = g["Close"].pct_change().rolling(20).std()
    
        # Trading Signals (SMA Crossover)
        g["Signal"] = np.where(g["SMA_20"] > g["SMA_50"], 1, 0)
        g["Position"] = g["Signal"].shift(1).fillna(0)
    
        # Signal status text expected by app.py
        g["Signal_Status"] = np.where(
            g["Signal"] == 1, 
            "BUY (Golden Cross)", 
            "SELL / HOLD (Death Cross)"
        )
    
        # Performance Returns
        g["Market_Return"] = g["Close"].pct_change()
        g["Strategy_Return"] = g["Market_Return"] * g["Position"]
    
        # Cumulative returns as decimal growth ratios
        g["Cum_Market_Return"] = (1 + g["Market_Return"].fillna(0)).cumprod() - 1
        g["Cum_Strategy_Return"] = (1 + g["Strategy_Return"].fillna(0)).cumprod() - 1
    
        peak = (1 + g["Cum_Strategy_Return"]).cummax()
        g["Drawdown"] = ((1 + g["Cum_Strategy_Return"]) - peak) / peak
    
        processed_frames.append(g)
    
    res = pd.concat(processed_frames, ignore_index=True)
    res["Date"] = res["Date"].dt.strftime("%Y-%m-%d")
    
    # Save directly to the exact table name app.py queries
    res.to_sql("technical_stock_analytics", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    
    print("Technical analytics processed successfully into 'technical_stock_analytics' table.")

if __name__ == "__main__":
    main()

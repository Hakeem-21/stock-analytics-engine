import sqlite3
import numpy as np
import pandas as pd

def main():
    def get_rsi(data, window=14):
        diff = data.diff()
        gain = diff.clip(lower=0)
        loss = -1 * diff.clip(upper=0)
        avg_gain = gain.rolling(window=window, min_periods=window).mean()
        avg_loss = loss.rolling(window=window, min_periods=window).mean()
    
        # Exponential smoothing for RSI (Wilder's RSI)
        avg_gain_vals = avg_gain.to_numpy(dtype=float)
        avg_loss_vals = avg_loss.to_numpy(dtype=float)
        gain_vals = gain.to_numpy(dtype=float)
        loss_vals = loss.to_numpy(dtype=float)

        for idx in range(window, len(data)):
            if not np.isnan(avg_gain_vals[idx - 1]):
                avg_gain_vals[idx] = (avg_gain_vals[idx - 1] * (window - 1) + gain_vals[idx]) / window
            if not np.isnan(avg_loss_vals[idx - 1]):
                avg_loss_vals[idx] = (avg_loss_vals[idx - 1] * (window - 1) + loss_vals[idx]) / window
    
        rs = pd.Series(avg_gain_vals, index=data.index) / pd.Series(avg_loss_vals, index=data.index)
        return 100 - (100 / (1 + rs))

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
    
        g["SMA_20"] = g["Close"].rolling(20).mean()
        g["SMA_50"] = g["Close"].rolling(50).mean()
        g["RSI_14"] = get_rsi(g["Close"], 14)
        g["Volatility_20"] = g["Close"].pct_change().rolling(20).std()
    
        # Trading Signals
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
    
        # Match column names expected by app.py
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

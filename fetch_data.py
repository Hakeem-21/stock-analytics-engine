import sqlite3
import yfinance as yf
import pandas as pd

def main():
    # Use standard NSE ticker symbols
    tickers = ["TATAMOTORS", "HDFCBANK", "SUNPHARMA", "TCS", "RELIANCE"]
    
    conn = sqlite3.connect("stock_market.db")
    
    all_data = []
    
    for symbol in tickers:
        ns_symbol = f"{symbol}.NS"
        print(f"Fetching data for {symbol} ({ns_symbol})...")
        
        # Download 5 years of daily data
        df = yf.download(ns_symbol, period="5y", interval="1d", progress=False)
        
        if df.empty:
            print(f"Warning: No data returned for {ns_symbol}")
            continue
        
        # Flatten MultiIndex columns if yfinance returns them
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = df.reset_index()
        df["Ticker"] = symbol
        
        # Keep standard OHLCV columns
        keep_cols = ["Date", "Ticker", "Open", "High", "Low", "Close", "Volume"]
        df = df[[c for c in keep_cols if c in df.columns]]
        
        # Convert Date to string YYYY-MM-DD
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
        
        all_data.append(df)
        
    if all_data:
        master_df = pd.concat(all_data, ignore_index=True)
        # Write directly to SQLite table
        master_df.to_sql("raw_stock_prices", conn, if_exists="replace", index=False)
        conn.commit()
        print(f"Data fetch complete. Inserted {len(master_df)} rows into raw_stock_prices.")
    else:
        print("Error: No data was fetched for any ticker.")
        
    conn.close()

if __name__ == "__main__":
    main()

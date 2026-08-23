import sqlite3
import yfinance as yf


def main():
# Replaced TATAMOTORS with TMPV (Tata Motors Passenger Vehicles)
    raw_tickers = ["TMPV", "HDFCBANK", "SUNPHARMA", "TCS", "RELIANCE"]
    ticker_map = {t: f"{t}.NS" for t in raw_tickers}
    
    conn = sqlite3.connect("stock_market.db")
    cursor = conn.cursor()
    
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS raw_stock_prices (
        Date TEXT,
        Ticker TEXT,
        Open REAL,
        High REAL,
        Low REAL,
        Close REAL,
        Volume REAL,
        PRIMARY KEY (Date, Ticker)
    )
    """
    )
    conn.commit()
    
    for display_name, ns_symbol in ticker_map.items():
        print(f"Fetching data for {display_name}...")
        df = yf.download(ns_symbol, period="5y", interval="1d", progress=False)
    
        if df.empty:
            print(f"Warning: No data returned for {ns_symbol}")
            continue
    
        if isinstance(df.columns, tuple) or getattr(
            df.columns, "nlevels", 1
        ) > 1:
            df.columns = [col[0] for col in df.columns]
    
        df = df.reset_index()
        df["Ticker"] = display_name
    
        keep_cols = ["Date", "Ticker", "Open", "High", "Low", "Close", "Volume"]
        df = df[keep_cols]
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    
        records = df.to_records(index=False)
        cursor.executemany(
            """
        INSERT OR REPLACE INTO raw_stock_prices (Date, Ticker, Open, High, Low, Close, Volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            list(records),
        )
        conn.commit()
    
    conn.close()
    print("Data fetch complete.")
    
if __name__ == "__main__":
    main()

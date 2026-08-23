# Stock_Market_analysis_automation_using_SMA20-50

Stock Market Technical Analytics & Backtest Engine

Business & Technical Overview
An interactive quantitative finance tool designed to perform technical analysis and strategy backtesting on stock market data. The application fetches daily OHLCV (Open, High, Low, Close, Volume) data, processes technical indicators using Pandas, stores historical data in SQLite, and provides an interactive visual frontend via Streamlit.

Tech Stack & Concepts
Frontend: Streamlit, Plotly (Interactive Candlestick & Indicator Charts)
Backend & Analytics: Python, Pandas, NumPy
Database: SQLite
Key Features:
Technical Indicators: Moving Averages (SMA/EMA), Relative Strength Index (RSI).
Backtesting Engine: Simulates crossover trading strategies and calculates total returns vs. buy-and-hold benchmarks.
Modular Architecture: Clean database schema separation from frontend rendering logic.

Key Output & Results
Automated historical data fetching and local caching in SQLite to optimize API calls.
Interactive strategy backtesting engine comparing SMA crossovers against buy-and-hold baseline performance.

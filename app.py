import sqlite3
import importlib
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set up full-width page configuration with financial icon
st.set_page_config(
    page_title="Stock Market Technical Analytics Engine",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# PIPELINE AUTO-INITIALIZATION & DATABASE HANDLERS
# ==============================================================================
DB_PATH = "stock_market.db"

def run_pipeline():
    """Executes Step 1 (Data Ingestion) and Step 2 (Technical Analytics)."""
    fetch_mod = importlib.import_module("1_fetch_data_to_sql")
    analytics_mod = importlib.import_module("2_technical_analysis")
    
    # Run Step 1
    if hasattr(fetch_mod, "main"):
        fetch_mod.main()
        
    # Run Step 2
    if hasattr(analytics_mod, "main"):
        analytics_mod.main()

def check_and_initialize_db():
    """Checks if the required analytics table exists. If not, auto-generates it."""
    table_exists = 0
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT count(name) FROM sqlite_master 
            WHERE type='table' AND name='technical_stock_analytics'
        """)
        table_exists = cursor.fetchone()[0]
        conn.close()
    except Exception:
        table_exists = 0

    if not table_exists:
        with st.spinner("🚀 Setting up database: Fetching market data & calculating indicators..."):
            run_pipeline()

# Run database verification prior to loading queries
check_and_initialize_db()

# ==============================================================================
# DATA LOADING & CACHING
# ==============================================================================
@st.cache_data
def load_data_from_sql():
    """
    Connects to the local SQLite database created in Step 1 & 2
    and fetches enriched stock indicator records.
    """
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM technical_stock_analytics ORDER BY Ticker, Date ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Ensure Date column is in proper datetime format for Plotly filtering
    df['Date'] = pd.to_datetime(df['Date'])
    return df

# Attempt data load with error boundary
try:
    df_master = load_data_from_sql()
except Exception as e:
    st.error(f"❌ Error loading SQL Database '{DB_PATH}'. Details: {e}")
    st.stop()

# ==============================================================================
# SIDEBAR CONTROLS & MANUAL REFRESH
# ==============================================================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2422/2422796.png", width=60)
st.sidebar.title("📊 Control Panel")

# Manual Data Refresh Button
if st.sidebar.button("🔄 Refresh / Update Market Data"):
    with st.spinner("Pulling latest data and recalculating indicators..."):
        run_pipeline()
        st.cache_data.clear()  # Clear cache so fresh SQL data loads immediately
    st.sidebar.success("Database updated successfully!")
    st.rerun()

st.sidebar.markdown("---")

# Ticker Selector
tickers = sorted(df_master['Ticker'].unique().tolist())
selected_ticker = st.sidebar.selectbox(
    "Select Stock Ticker:",
    options=tickers,
    index=0
)

# Date Range Filter Slider
min_date = df_master['Date'].min().to_pydatetime()
max_date = df_master['Date'].max().to_pydatetime()

start_date, end_date = st.sidebar.slider(
    "Select Date Filter Range:",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD"
)

# Technical Indicator Overlay Checkboxes
st.sidebar.markdown("### 🎛️ Indicator Overlays")
show_sma20 = st.sidebar.checkbox("Show SMA 20 (Short-Term Trend)", value=True)
show_sma50 = st.sidebar.checkbox("Show SMA 50 (Medium-Term Trend)", value=True)
show_rsi = st.sidebar.checkbox("Show RSI 14 Sub-Chart", value=True)
show_volume = st.sidebar.checkbox("Show Volume Sub-Chart", value=True)

# ==============================================================================
# DATA FILTERING & METRICS CALCULATION
# ==============================================================================
df_filtered = df_master[
    (df_master['Ticker'] == selected_ticker) &
    (df_master['Date'] >= pd.to_datetime(start_date)) &
    (df_master['Date'] <= pd.to_datetime(end_date))
].copy()

# Get latest recorded row for selected stock
latest_row = df_filtered.iloc[-1]
latest_close = latest_row['Close']
latest_date_str = latest_row['Date'].strftime('%Y-%m-%d')
signal_status = latest_row['Signal_Status']

# Compute returns over selected date window
buy_hold_return = ((latest_row['Cum_Market_Return'] - df_filtered.iloc[0]['Cum_Market_Return']) * 100)
strategy_return = ((latest_row['Cum_Strategy_Return'] - df_filtered.iloc[0]['Cum_Strategy_Return']) * 100)
max_drawdown = df_filtered['Drawdown'].min() * 100

# ==============================================================================
# DASHBOARD DISPLAY & METRIC TILES
# ==============================================================================
company_clean_name = selected_ticker.replace(".NS", "")
st.title(f"📈 {company_clean_name} Market Analytics & Backtest Engine")
st.caption(f"Showing historical daily price data & technical signals up to **{latest_date_str}**")

st.markdown("### 🏛️ Executive Summary & Signal Status")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Latest Close Price", f"₹{latest_close:,.2f}")

with col2:
    st.metric("Buy & Hold Return", f"{buy_hold_return:+.2f}%")

with col3:
    st.metric("Strategy Return", f"{strategy_return:+.2f}%", 
              delta=f"{(strategy_return - buy_hold_return):+.2f}% vs Market")

with col4:
    st.metric("Max Drawdown", f"{max_drawdown:.2f}%")

with col5:
    st.write("**Current Trading Signal**")
    if "BUY" in signal_status:
        st.markdown(f'<span style="color: #22c55e; font-weight: bold;">🟢 {signal_status}</span>', unsafe_allow_html=True)
    elif "SELL" in signal_status:
        st.markdown(f'<span style="color: #ef4444; font-weight: bold;">🔴 {signal_status}</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span style="color: #f59e0b; font-weight: bold;">⚠️ {signal_status}</span>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# MULTI-ROW TECHNICAL PLOTLY CHART
# ==============================================================================
subplot_rows = 2
row_heights = [0.7, 0.3]

if show_rsi and show_volume:
    subplot_rows = 3
    row_heights = [0.55, 0.2, 0.25]

fig = make_subplots(
    rows=subplot_rows, 
    cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.04, 
    row_heights=row_heights
)

# 1. Candlestick Main Chart
fig.add_trace(
    go.Candlestick(
        x=df_filtered['Date'],
        open=df_filtered['Open'],
        high=df_filtered['High'],
        low=df_filtered['Low'],
        close=df_filtered['Close'],
        name="OHLC Price"
    ),
    row=1, col=1
)

# 2. Simple Moving Average Overlays
if show_sma20:
    fig.add_trace(
        go.Scatter(
            x=df_filtered['Date'],
            y=df_filtered['SMA_20'],
            mode='lines',
            line=dict(color='#38bdf8', width=1.5),
            name="SMA 20 (Short Term)"
        ),
        row=1, col=1
    )

if show_sma50:
    fig.add_trace(
        go.Scatter(
            x=df_filtered['Date'],
            y=df_filtered['SMA_50'],
            mode='lines',
            line=dict(color='#f59e0b', width=1.5),
            name="SMA 50 (Medium Term)"
        ),
        row=1, col=1
    )

current_row = 2

# Volume Bar Chart
if show_volume:
    colors = ['#22c55e' if cl >= op else '#ef4444' for op, cl in zip(df_filtered['Open'], df_filtered['Close'])]
    fig.add_trace(
        go.Bar(
            x=df_filtered['Date'],
            y=df_filtered['Volume'],
            marker_color=colors,
            name="Trading Volume"
        ),
        row=current_row, col=1
    )
    current_row += 1

# RSI Oscillator Chart
if show_rsi:
    fig.add_trace(
        go.Scatter(
            x=df_filtered['Date'],
            y=df_filtered['RSI_14'],
            mode='lines',
            line=dict(color='#a855f7', width=1.5),
            name="RSI 14"
        ),
        row=current_row, col=1
    )
    # Overbought Line (70)
    fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=current_row, col=1)
    # Oversold Line (30)
    fig.add_hline(y=30, line_dash="dash", line_color="#22c55e", row=current_row, col=1)

fig.update_layout(
    title=f"Technical Chart: {selected_ticker} (Candlestick + Indicators)",
    template="plotly_dark",
    height=750,
    xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# BENCHMARK COMPARISON CHART
# ==============================================================================
st.markdown("### 📊 Backtest Performance: Buying & Holding vs Golden Cross Strategy")

fig_perf = go.Figure()

# Buy & Hold Return Curve
fig_perf.add_trace(
    go.Scatter(
        x=df_filtered['Date'],
        y=df_filtered['Cum_Market_Return'] * 100,
        mode='lines',
        name='Buy & Hold Benchmark (%)',
        line=dict(color='#64748b', width=2)
    )
)

# Moving Average Crossover Strategy Curve
fig_perf.add_trace(
    go.Scatter(
        x=df_filtered['Date'],
        y=df_filtered['Cum_Strategy_Return'] * 100,
        mode='lines',
        name='SMA Crossover Strategy (%)',
        line=dict(color='#10b981', width=2.5)
    )
)

fig_perf.update_layout(
    title="Cumulative Growth of ₹100 Investment Over Time",
    xaxis_title="Date",
    yaxis_title="Return (%)",
    template="plotly_dark",
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig_perf, use_container_width=True)

# ==============================================================================
# DATA EXPORT & AUDIT TRAIL
# ==============================================================================
with st.expander("📂 View Raw Enriched Data Table"):
    st.dataframe(df_filtered.tail(100), use_container_width=True)
    
    csv_data = df_filtered.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv_data,
        file_name=f"{selected_ticker}_analytics_data.csv",
        mime="text/csv"
    )

st.markdown("---")
    mime="text/csv"
    )

st.markdown("---")

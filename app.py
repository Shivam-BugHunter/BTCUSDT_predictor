import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import plotly.graph_objects as go
import os
from data import get_aligned_data
from model import predict_next_bar

st.set_page_config(page_title="BTCUSDT Predictor", layout="wide")

st.title("Bitcoin 1-Hour Price Range Predictor")

try:
    with open("backtest_results.jsonl", "r") as f:
        results = [json.loads(line) for line in f]
    if results:
        df_bt = pd.DataFrame(results)
        coverage = df_bt['coverage'].mean()
        avg_width = df_bt['width'].mean()
        avg_winkler = df_bt['winkler'].mean()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Backtest Coverage (Target: ~95%)", f"{coverage:.2%}")
        col2.metric("Avg Range Width", f"${avg_width:.2f}")
        col3.metric("Avg Winkler Score", f"{avg_winkler:.2f}")
    else:
        st.warning("Backtest running...")
except FileNotFoundError:
    st.warning("Backtest results not found. Please run backtest.py first.")

st.markdown("---")

HISTORY_FILE = "prediction_history.jsonl"

def save_prediction(date_str, current_price, low_95, high_95):
    res = {
        "date": date_str,
        "current_price": current_price,
        "low_95": low_95,
        "high_95": high_95
    }
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(res) + "\n")

with st.spinner("Fetching latest data and running model..."):
    prices, macro_data = get_aligned_data(total_bars=500)
    current_price = prices.iloc[-1]
    last_time = prices.index[-1]
    
    low_95, high_95 = predict_next_bar(prices, macro_data=macro_data, n_sims=10000)
    
    next_time = last_time + pd.Timedelta(hours=1)
    duplicate = False
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                if json.loads(line).get("date") == str(next_time):
                    duplicate = True
                    break
    if not duplicate:
        save_prediction(str(next_time), current_price, low_95, high_95)

st.header(f"Current BTC Price: ${current_price:,.2f}")
st.subheader("Predicted 95% Range for Next Hour:")
st.success(f"**${low_95:,.2f} — ${high_95:,.2f}**")

next_time_ist = next_time.tz_localize('UTC').tz_convert('Asia/Kolkata')
st.info(f"⏳ This prediction is valid until **{next_time_ist.strftime('%Y-%m-%d %I:%M %p')} IST**")

history = []
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        for line in f:
            history.append(json.loads(line))
hist_df = pd.DataFrame(history)
if not hist_df.empty:
    hist_df['date'] = pd.to_datetime(hist_df['date'])
    # Need to drop duplicates on date in case of edge cases
    hist_df = hist_df.drop_duplicates(subset=['date'])
    hist_df.set_index('date', inplace=True)

last_50 = prices.iloc[-50:]
plot_dates = list(last_50.index) + [next_time]
plot_prices = list(last_50.values) + [None]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=plot_dates,
    y=plot_prices,
    mode='lines+markers',
    name='Historical Price',
    line=dict(color='white')
))

upper_bounds = []
lower_bounds = []

for dt in plot_dates:
    if not hist_df.empty and dt in hist_df.index:
        upper_bounds.append(hist_df.loc[dt, 'high_95'])
        lower_bounds.append(hist_df.loc[dt, 'low_95'])
    elif dt == next_time:
        upper_bounds.append(high_95)
        lower_bounds.append(low_95)
    else:
        upper_bounds.append(None)
        lower_bounds.append(None)

x_ribbon = []
y_upper = []
y_lower = []
for i in range(len(plot_dates)):
    if upper_bounds[i] is not None and lower_bounds[i] is not None:
        x_ribbon.append(plot_dates[i])
        y_upper.append(upper_bounds[i])
        y_lower.append(lower_bounds[i])

if x_ribbon:
    fig.add_trace(go.Scatter(
        x=x_ribbon + x_ribbon[::-1],
        y=y_upper + y_lower[::-1],
        fill='toself',
        fillcolor='rgba(0,176,246,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Predicted 95% Range'
    ))

fig.update_layout(
    title='BTC/USDT 1-Hour Chart with 95% Predicted Range',
    xaxis_title='Time (UTC)',
    yaxis_title='Price (USDT)',
    template='plotly_dark',
    height=600
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("Real-Time BTC/USDT Live Chart")

tradingview_html = """
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container" style="height:100%;width:100%">
  <div id="tradingview_btc" style="height:500px;width:100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget(
  {
  "autosize": true,
  "symbol": "BINANCE:BTCUSDT",
  "interval": "1",
  "timezone": "Etc/UTC",
  "theme": "dark",
  "style": "1",
  "locale": "en",
  "enable_publishing": false,
  "backgroundColor": "rgba(14, 17, 23, 1)",
  "gridColor": "rgba(42, 46, 57, 1)",
  "hide_top_toolbar": false,
  "hide_legend": false,
  "save_image": false,
  "container_id": "tradingview_btc"
}
  );
  </script>
</div>
<!-- TradingView Widget END -->
"""

components.html(tradingview_html, height=500)

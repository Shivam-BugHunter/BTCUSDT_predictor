# Bitcoin 1-Hour Price Range Predictor

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://btcusdtpredictor-4jjdmbtv7er4fqpxxjprrk.streamlit.app/)

A real-time Streamlit dashboard and backtesting framework that forecasts the 95% confidence interval for the next 1-hour Bitcoin (BTC/USDT) price using a Geometric Brownian Motion (GBM) model with volatility clustering and fat tails.

**[🚀 View Live Dashboard Here](https://btcusdtpredictor-4jjdmbtv7er4fqpxxjprrk.streamlit.app/)**

## Features

- **Real-Time Forecasting**: Live predictions for the next hour's price range based on current market conditions.
- **Strict Backtesting**: Framework to validate the model using 720 hours of historical data without lookahead bias.
- **Interactive Dashboard**: Built with Streamlit and Plotly to visualize historical predictions alongside live market data.
- **Live TradingView Integration**: Integrated interactive TradingView chart for real-time market monitoring.

## Project Structure

- `app.py`: Streamlit dashboard for real-time forecasting and visualization.
- `backtest.py`: Script to run the historical 720-bar backtest.
- `model.py`: Core mathematical forecasting logic.
- `data.py`: Data fetching pipeline utilizing the Binance API.
- `requirements.txt`: Python dependencies required for the project.

## Installation & Usage

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Backtest**:
   ```bash
   python backtest.py
   ```
   This generates `backtest_results.jsonl` containing historical predictions and outputs key model metrics: Coverage (Target: ~95%), Average Width, and Winkler Score.

3. **Launch the Dashboard**:
   ```bash
   streamlit run app.py
   ```
   Open the provided local URL (usually `http://localhost:8501`) to view the dashboard. The application will fetch the latest price, compute the next hour's prediction, and display the performance of past predictions.

## Deployment

The app is deployed live on Streamlit Community Cloud: **[Live Demo](https://btcusdtpredictor-4jjdmbtv7er4fqpxxjprrk.streamlit.app/)**

This application is designed to be easily deployed on platforms like [Streamlit Community Cloud](https://share.streamlit.io/). 

1. Push this repository to GitHub.
2. Log in to Streamlit Community Cloud and click "New app".
3. Select your repository and specify `app.py` as the main file path.
4. Click "Deploy".
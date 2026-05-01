# BTCUSDT Predictor

This project contains a 1-hour Bitcoin price range forecaster based on a Geometric Brownian Motion (GBM) with volatility clustering and fat tails.

## Files
- `model.py`: Core forecasting logic extracted from the starter Colab.
- `data.py`: Functions to fetch historical 1-hour bars from Binance API.
- `backtest.py`: Script to run the 720-bar backtest (Part A).
- `app.py`: Streamlit dashboard for real-time forecasting (Part B & C).
- `requirements.txt`: Dependencies for the project.

## How to use

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Backtest (Part A)**:
   ```bash
   python backtest.py
   ```
   This will generate `backtest_results.jsonl` containing the 720 predictions and print out the Coverage, Average Width, and Winkler Score.

3. **Run the Dashboard (Part B & C)**:
   ```bash
   streamlit run app.py
   ```
   This will launch a local dashboard. The dashboard will show the latest price, the 95% predicted range for the next hour, historical predictions, and the backtest metrics.

## Deploying to Streamlit Community Cloud

1. Commit these files to a public or private GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io/).
3. Click "New app".
4. Select the repository, branch, and specify `app.py` as the main file path.
5. Click "Deploy".
6. Copy the URL of your deployed app and paste it into your submission form!
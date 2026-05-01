import requests
import pandas as pd
import yfinance as yf

def get_binance_data_extended(symbol="BTCUSDT", interval="1h", total_bars=1300):
    bars = []
    end_time = None
    while len(bars) < total_bars:
        limit = min(1000, total_bars - len(bars))
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        if end_time:
            url += f"&endTime={end_time}"
        response = requests.get(url)
        data = response.json()
        if not data:
            break
        bars = data + bars
        end_time = data[0][0] - 1
    
    df = pd.DataFrame(bars, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df = df.drop_duplicates(subset=['open_time'])
    df.set_index('open_time', inplace=True)
    df['close'] = df['close'].astype(float)
    df.sort_index(inplace=True)
    return df['close'].iloc[-total_bars:]

def get_aligned_data(symbol="BTCUSDT", total_bars=1300):
    btc_close = get_binance_data_extended(symbol, "1h", total_bars)
    
    start_time = btc_close.index[0]
    end_time = btc_close.index[-1] + pd.Timedelta(hours=1)
    
    tickers = ["^GSPC", "^IXIC", "^DJI", "^VIX", "GC=F", "CL=F", "DX-Y.NYB"]
    try:
        macro_df = yf.download(tickers, start=start_time, end=end_time, interval="1h", progress=False)['Close']
        if not macro_df.empty:
            if macro_df.index.tz is not None:
                macro_df.index = macro_df.index.tz_convert('UTC').tz_localize(None)
            macro_df = macro_df.reindex(btc_close.index).ffill().bfill()
        else:
            macro_df = pd.DataFrame(index=btc_close.index, columns=tickers).fillna(1.0)
    except Exception as e:
        macro_df = pd.DataFrame(index=btc_close.index, columns=tickers).fillna(1.0)
        
    return btc_close, macro_df


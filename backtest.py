import json
import pandas as pd
from tqdm import tqdm
from data import get_aligned_data
from model import predict_next_bar

def run_backtest():
    total_bars = 500 + 720
    print(f"Fetching last {total_bars} bars and macro data...")
    prices, macro_data = get_aligned_data(total_bars=total_bars)
    
    results = []
    
    for i in tqdm(range(500, len(prices))):
        train_prices = prices.iloc[i-500:i]
        train_macro = macro_data.iloc[i-500:i]
        actual = prices.iloc[i]
        
        # predict the 95% range
        low_95, high_95 = predict_next_bar(train_prices, macro_data=train_macro, n_sims=5000)
        
        width = high_95 - low_95
        alpha = 0.05
        winkler = (width + (2/alpha)*(low_95 - actual)) if actual < low_95 else \
                  (width + (2/alpha)*(actual - high_95)) if actual > high_95 else \
                  width
                  
        res = {
            "date": str(prices.index[i]),
            "actual": actual,
            "low_95": low_95,
            "high_95": high_95,
            "coverage": 1 if low_95 <= actual <= high_95 else 0,
            "width": width,
            "winkler": winkler
        }
        results.append(res)
        
        # Save incrementally
        with open("backtest_results.jsonl", "a") as f:
            f.write(json.dumps(res) + "\n")
            
    df = pd.DataFrame(results)
    print(f"Coverage: {df['coverage'].mean():.2%}")
    print(f"Avg Width: {df['width'].mean():.2f}")
    print(f"Avg Winkler: {df['winkler'].mean():.2f}")

if __name__ == "__main__":
    open("backtest_results.jsonl", "w").close()
    run_backtest()

# compute_metrics.py
import pandas as pd
import numpy as np
import json
import os

def compute_stock_metrics():
    """Compute all metrics from CSV data"""
    
    # Load combined data
    df = pd.read_csv("data/all_stocks.csv", index_col=0, parse_dates=True)
    
    results = {}
    
    # Process each stock
    for symbol in df['Symbol'].unique():
        stock_data = df[df['Symbol'] == symbol].copy()
        stock_data.sort_index(inplace=True)
        
        # Get stock info
        name = stock_data['Name'].iloc[0]
        prices = stock_data['Close']
        
        # Calculate annual returns
        yearly_prices = prices.resample('Y').last()
        
        annual_returns = []
        years = []
        
        for i in range(1, len(yearly_prices)):
            prev_price = yearly_prices.iloc[i-1]
            curr_price = yearly_prices.iloc[i]
            
            if prev_price > 0:
                ret = (curr_price - prev_price) / prev_price
                annual_returns.append(ret)
                years.append(yearly_prices.index[i].year)
        
        if len(annual_returns) < 3:
            continue
        
        # Calculate metrics
        returns_array = np.array(annual_returns)
        exp_return = float(np.mean(returns_array))
        variance = float(np.var(returns_array))
        std_dev = float(np.std(returns_array))
        
        # Current price
        current_price = float(prices.iloc[-1])
        
        # Store results
        results[symbol] = {
            'symbol': symbol,
            'name': name,
            'expected_return': round(exp_return * 100, 2),
            'std_deviation': round(std_dev * 100, 2),
            'variance': round(variance, 6),
            'current_price': round(current_price, 2),
            'annual_returns': [round(r * 100, 2) for r in annual_returns],
            'years': years,
            'data_points': len(annual_returns)
        }
        
        print(f"Processed {symbol}: Return={results[symbol]['expected_return']}%, Risk={results[symbol]['std_deviation']}%")
    
    # Save to JSON
    with open('data/stock_metrics.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nSaved metrics for {len(results)} stocks to data/stock_metrics.json")
    return results

if __name__ == "__main__":
    compute_stock_metrics()
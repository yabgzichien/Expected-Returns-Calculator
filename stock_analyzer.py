import yfinance as yf
import pandas as pd
import numpy as np
import json
import gc  # Garbage collection
from datetime import datetime

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types"""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return super().default(obj)

class StockAnalyzer:
    def __init__(self):
        pass
    
    def _safe_float(self, value):
        """Safely convert value to float"""
        try:
            if value is None or pd.isna(value):
                return None
            return float(value)
        except:
            return None
    
    def analyze_stock(self, stock_symbol, start_date="2020-01-01", end_date="2026-01-01", min_years=3):
        """
        Memory-optimized version - uses minimal RAM
        Using 2020 as start date to reduce data by 50%
        """
        try:
            print(f"Analyzing: {stock_symbol}")
            
            # Use period='5y' instead of dates - more memory efficient
            data = yf.download(
                stock_symbol, 
                period='5y',  # Changed from date range to period
                interval='1mo', 
                progress=False,
                repair=True
            )
            
            if data.empty:
                # Try with shorter period
                data = yf.download(
                    stock_symbol, 
                    period='3y', 
                    interval='1mo', 
                    progress=False
                )
            
            if data.empty:
                return {'success': False, 'error': 'No data'}
            
            # Get only closing prices - free memory for rest of data
            prices = data['Close'].copy()
            
            # Explicitly delete data to free memory
            del data
            gc.collect()
            
            # Convert to numpy for faster processing
            if isinstance(prices, pd.DataFrame):
                prices = prices.iloc[:, 0]
            
            # Calculate yearly returns using numpy (faster than pandas resample)
            price_array = prices.values
            date_index = prices.index
            
            # Simple annual returns (last price of each year)
            years = {}
            for i, date in enumerate(date_index):
                year = date.year
                years[year] = price_array[i]  # Keep last value of each year
            
            if len(years) < min_years + 1:
                return {'success': False, 'error': 'Insufficient years'}
            
            # Calculate returns
            sorted_years = sorted(years.items())
            annual_returns = []
            year_list = []
            
            for i in range(1, len(sorted_years)):
                prev_year, prev_price = sorted_years[i-1]
                curr_year, curr_price = sorted_years[i]
                
                if prev_price and curr_price and prev_price > 0:
                    total_return = (curr_price - prev_price) / prev_price
                    annual_returns.append(float(total_return))
                    year_list.append(curr_year)
            
            if len(annual_returns) < min_years:
                return {'success': False, 'error': 'Insufficient returns'}
            
            # Calculate metrics
            returns_array = np.array(annual_returns)
            n = len(annual_returns)
            
            exp_return = float(np.mean(returns_array))
            variance = float(np.var(returns_array))
            std_dev = float(np.std(returns_array))
            
            # Current price
            current_price = self._safe_float(prices.iloc[-1])
            
            # Convert to percentages
            annual_returns_pct = [round(r * 100, 2) for r in annual_returns]
            
            # Minimal calculation steps
            calculation_steps = {
                'annual_returns': [
                    {'year': y, 'result': f"{r}%"} 
                    for y, r in zip(year_list, annual_returns_pct)
                ],
                'expected_return': {
                    'formula': 'Average of annual returns',
                    'result': f"{round(exp_return * 100, 2)}%"
                },
                'variance': {
                    'result': f"{round(variance, 6)}"
                },
                'std_deviation': {
                    'result': f"{round(std_dev * 100, 2)}%"
                }
            }
            
            result = {
                'success': True,
                'symbol': str(stock_symbol),
                'name': stock_symbol,  # Skip fetching name
                'expected_return': round(exp_return * 100, 2),
                'variance': round(variance, 6),
                'std_deviation': round(std_dev * 100, 2),
                'current_price': round(current_price, 2) if current_price else None,
                'annual_returns': annual_returns_pct,
                'years': year_list,
                'data_points': n,
                'calculation_steps': calculation_steps
            }
            
            # Clean up
            del prices, returns_array, annual_returns
            gc.collect()
            
            return result
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def analyze_multiple_stocks(self, stock_list, weights=None, start_date="2020-01-01", end_date="2026-01-01"):
        """Process stocks sequentially with memory cleanup"""
        results = []
        errors = []
        
        for stock in stock_list:
            # Analyze one stock at a time
            result = self.analyze_stock(stock, start_date, end_date)
            
            if result and result.get('success'):
                results.append(result)
            else:
                errors.append(f"{stock}: {result.get('error', 'Unknown')}")
            
            # Force garbage collection after each stock
            gc.collect()
        
        if len(results) == 0:
            return {'success': False, 'error': 'No valid stocks', 'errors': errors}
        
        response = {
            'success': True,
            'stocks': results,
            'total_stocks': len(results),
            'is_portfolio': len(results) > 1
        }
        
        if len(results) > 1:
            if not weights:
                weights = [1.0/len(results)] * len(results)
            
            portfolio_return = 0
            for w, r in zip(weights, results):
                portfolio_return += w * (r['expected_return'] / 100)
            
            response['weights'] = [round(w * 100, 1) for w in weights]
            response['portfolio_return'] = round(portfolio_return * 100, 2)
        
        if errors:
            response['errors'] = errors
        
        return response
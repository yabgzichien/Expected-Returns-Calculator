# stock_analyzer.py
import pandas as pd
import numpy as np
import os
import glob
import json
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
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return str(obj)
        elif pd.isna(obj):
            return None
        return super().default(obj)

class StockAnalyzer:
    def __init__(self):
        self.data_dir = 'data'
        self.stock_info = self._load_stock_info()
        print(f"Initialized StockAnalyzer with {len(self.stock_info)} stocks")
    
    def _load_stock_info(self):
        """Load basic stock information from CSV files"""
        stock_info = {}
        csv_files = glob.glob(f"{self.data_dir}/*.csv")
        
        for file in csv_files:
            try:
                # Read only the first row to get symbol and name
                df = pd.read_csv(file, nrows=1)
                if 'Symbol' in df.columns and 'Name' in df.columns:
                    symbol = df['Symbol'].iloc[0]
                    name = df['Name'].iloc[0]
                    stock_info[symbol] = {
                        'symbol': symbol,
                        'name': name,
                        'file': file
                    }
                    print(f"Loaded stock: {symbol} - {name}")
            except Exception as e:
                print(f"Error reading {file}: {e}")
        
        return stock_info
    
    def get_all_stocks(self):
        """Return list of all available stocks"""
        stocks = []
        for symbol, info in self.stock_info.items():
            stocks.append({
                'symbol': symbol,
                'name': info['name'],
                'sector': self._get_sector(symbol)
            })
        return stocks
    
    def _get_sector(self, symbol):
        """Get sector for a stock"""
        banking = ['1155.KL', '1295.KL', '1023.KL', '5819.KL', '1066.KL', '1015.KL']
        oil_gas = ['5681.KL', '6033.KL', '5183.KL', '5285.KL']
        telecom = ['6012.KL', '6947.KL', '4863.KL', '6888.KL']
        utilities = ['5347.KL', '6742.KL', '4677.KL']
        plantation = ['1961.KL', '2445.KL', '4197.KL', '3816.KL']
        consumer = ['5296.KL', '5326.KL', '4707.KL']
        healthcare = ['5225.KL']
        construction = ['5398.KL', '5211.KL']
        industrial = ['7084.KL', '8869.KL', '4065.KL']
        
        if symbol in banking:
            return 'Banking & Finance'
        elif symbol in oil_gas:
            return 'Oil & Gas'
        elif symbol in telecom:
            return 'Telecommunications'
        elif symbol in utilities:
            return 'Utilities & Power'
        elif symbol in plantation:
            return 'Plantation & Agriculture'
        elif symbol in consumer:
            return 'Consumer & Retail'
        elif symbol in healthcare:
            return 'Healthcare'
        elif symbol in construction:
            return 'Construction & Property'
        elif symbol in industrial:
            return 'Industrial'
        else:
            return 'Others'
    
    def _fix_date(self, date_str):
        """Fix date format (add day if missing)"""
        try:
            if isinstance(date_str, str):
                # If date is like "2011-04-0", convert to "2011-04-01"
                if date_str.endswith('-0'):
                    return date_str[:-1] + '1'
                # If date is like "2011-4-1", ensure two digits for month and day
                parts = date_str.split('-')
                if len(parts) == 3:
                    year = parts[0].zfill(4)
                    month = parts[1].zfill(2)
                    day = parts[2].zfill(2)
                    return f"{year}-{month}-{day}"
            return date_str
        except:
            return date_str
    
    def _load_stock_data(self, symbol):
        """Load stock data from CSV file with proper date parsing"""
        if symbol not in self.stock_info:
            return None
        
        file_path = self.stock_info[symbol]['file']
        try:
            # Read CSV
            df = pd.read_csv(file_path)
            
            # Fix dates
            df['Date'] = df['Date'].astype(str).apply(self._fix_date)
            
            # Convert to datetime
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            # Drop rows with invalid dates
            df = df.dropna(subset=['Date'])
            
            # Set index
            df.set_index('Date', inplace=True)
            
            # Remove timezone if present
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            # Sort by date
            df.sort_index(inplace=True)
            
            print(f"Loaded {len(df)} rows for {symbol}")
            return df
        except Exception as e:
            print(f"Error loading {symbol}: {e}")
            return None
    
    def analyze_stock(self, symbol, start_date, end_date):
        """Calculate metrics for a single stock with calculation steps"""
        
        print(f"Analyzing {symbol} from {start_date} to {end_date}")
        
        # Load data
        df = self._load_stock_data(symbol)
        if df is None or df.empty:
            return {'success': False, 'error': f'No data found for {symbol}'}
        
        # Convert dates
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Filter by date range
        mask = (df.index >= start) & (df.index <= end)
        df_filtered = df.loc[mask].copy()
        
        if len(df_filtered) < 12:
            return {'success': False, 'error': f'Insufficient data. Only {len(df_filtered)} months found.'}
        
        # Get prices and dividends
        prices = df_filtered['Close']
        dividends = df_filtered['Dividends'] if 'Dividends' in df_filtered.columns else pd.Series(0, index=prices.index)
        
        # Calculate annual returns using December prices
        yearly_prices = prices.resample('Y').last()
        yearly_dividends = dividends.resample('Y').sum()
        
        annual_returns = []
        years = []
        return_calculations = []
        
        # Stop one year before the end to exclude current year
        for i in range(1, len(yearly_prices) - 1):
            try:
                prev_price = float(yearly_prices.iloc[i-1])
                curr_price = float(yearly_prices.iloc[i])
                div = float(yearly_dividends.iloc[i]) if i < len(yearly_dividends) else 0
                
                if prev_price > 0 and curr_price > 0:
                    total_return = (curr_price - prev_price + div) / prev_price
                    annual_returns.append(total_return)
                    year = yearly_prices.index[i].year
                    years.append(year)
                    
                    # Store calculation steps
                    return_calculations.append({
                        'year': year,
                        'formula': 'Rate of Return = (P<sub>t</sub> - P<sub>t-1</sub> + D<sub>t</sub>) / P<sub>t-1</sub>',
                        'values': f"= (RM{curr_price:.2f} - RM{prev_price:.2f} + RM{div:.2f}) / RM{prev_price:.2f}",
                        'result': f"= {total_return*100:.2f}%"
                    })
                    
                    print(f"Year {year}: Return={total_return*100:.2f}%")
            except Exception as e:
                continue
        
        if len(annual_returns) < 2:
            return {'success': False, 'error': f'Insufficient yearly data. Only {len(annual_returns)} years found.'}
        
        # Calculate metrics
        returns_array = np.array(annual_returns)
        n = len(annual_returns)
        
        # Expected return
        exp_return = float(np.sum(returns_array) / n)
        
        # Variance (population variance)
        squared_deviations = [(r - exp_return) ** 2 for r in returns_array]
        variance = float(np.sum(squared_deviations) / n)
        
        # Standard deviation
        std_dev = float(np.sqrt(variance))
        
        # Current price
        current_price = float(prices.iloc[-1])
        
        # Annual returns as percentages
        annual_returns_pct = [round(r * 100, 2) for r in annual_returns]
        
        # Create detailed calculation steps
        calculation_steps = {
            'annual_returns': return_calculations,
            'expected_return': {
                'formula': 'E(r) = (1/n) × Σ rᵢ',
                'steps': [
                    f"Step 1: Sum all annual returns",
                    f"Σ rᵢ = {' + '.join([f'{r}%' for r in annual_returns_pct])} = {sum(annual_returns)*100:.2f}%",
                    f"Step 2: Divide by number of years (n = {n})",
                    f"E(r) = {sum(annual_returns)*100:.2f}% / {n} = {exp_return*100:.2f}%"
                ],
                'result': f"{exp_return*100:.2f}%"
            },
            'variance': {
                'formula': 'σ² = (1/n) × Σ (rᵢ - E(r))²',
                'steps': [
                    "Step 1: Calculate deviations from expected return",
                    *[f"Year {years[j]}: {annual_returns_pct[j]}% - {exp_return*100:.2f}% = {(annual_returns[j] - exp_return)*100:.2f}%" 
                    for j in range(min(3, n))],
                    "Step 2: Square each deviation",
                    *[f"({(annual_returns[j] - exp_return)*100:.2f}%)² = {(annual_returns[j] - exp_return)**2:.6f}" 
                    for j in range(min(3, n))],
                    f"Step 3: Sum squared deviations and divide by {n}",
                    f"σ² = {variance:.6f}"
                ],
                'result': f"{variance:.6f}"
            },
            'std_deviation': {
                'formula': 'σ = √σ²',
                'steps': [
                    f"σ = √{variance:.6f} = {std_dev*100:.2f}%"
                ],
                'result': f"{std_dev*100:.2f}%"
            }
        }
        
        result = {
            'success': True,
            'symbol': symbol,
            'name': self.stock_info[symbol]['name'],
            'expected_return': round(exp_return * 100, 2),
            'variance': round(variance, 6),
            'std_deviation': round(std_dev * 100, 2),
            'current_price': round(current_price, 2),
            'annual_returns': annual_returns_pct,
            'years': years,
            'data_points': n,
            'start_date': start_date,
            'end_date': end_date,
            'calculation_steps': calculation_steps  # This is crucial!
        }
        
        print(f"Results: Return={exp_return*100:.2f}%, Variance={variance:.6f}, StdDev={std_dev*100:.2f}%")
        return result
    
    def analyze_multiple_stocks(self, stock_list, weights=None, start_date="2014-01-01", end_date="2026-01-01"):
        """Analyze multiple stocks and calculate portfolio metrics"""
        results = []
        errors = []
        
        for symbol in stock_list:
            result = self.analyze_stock(symbol, start_date, end_date)
            if result.get('success'):
                results.append(result)
            else:
                errors.append(f"{symbol}: {result.get('error', 'Unknown error')}")
        
        if len(results) == 0:
            return {
                'success': False,
                'error': 'No valid stocks could be analyzed',
                'errors': errors
            }
        
        response = {
            'success': True,
            'stocks': results,
            'total_stocks': len(results),
            'is_portfolio': len(results) > 1,
            'analysis_period': {
                'start': start_date,
                'end': end_date
            }
        }
        
        if len(results) > 1:
            if not weights:
                weights = [1.0/len(results)] * len(results)
            else:
                weights = [float(w) for w in weights]
                weight_sum = sum(weights)
                if abs(weight_sum - 1.0) > 0.01:
                    weights = [w/weight_sum for w in weights]
            
            # Calculate portfolio return (matches Jupyter notebook)
            portfolio_return = 0
            for w, stock in zip(weights, results):
                portfolio_return += w * (stock['expected_return'] / 100)
            
            response['weights'] = [round(w * 100, 1) for w in weights]
            response['portfolio_return'] = round(portfolio_return * 100, 2)
            
            # Portfolio calculation steps
            portfolio_calculation_steps = [
                {'step': 1, 'description': 'Portfolio Expected Return Formula', 'formula': 'E(Rp) = w₁ × E(R₁) + w₂ × E(R₂)'},
                {'step': 2, 'description': 'Portfolio Weights', 'details': [f"{stock['symbol']}: {round(w*100,1)}%" for w, stock in zip(weights, results)]},
                {'step': 3, 'description': 'Individual Expected Returns', 'details': [f"{stock['symbol']}: {stock['expected_return']}%" for stock in results]},
                {'step': 4, 'description': 'Apply Formula', 'calculation': f"E(Rp) = {round(weights[0]*100,1)}% × {results[0]['expected_return']}% + {round(weights[1]*100,1)}% × {results[1]['expected_return']}%"},
                {'step': 5, 'description': 'Calculate', 'calculation': f"= {round(weights[0]*results[0]['expected_return']/100*100, 2)}% + {round(weights[1]*results[1]['expected_return']/100*100, 2)}%"},
                {'step': 6, 'description': 'Final Result', 'result': f"Expected Portfolio Return = {round(portfolio_return * 100, 2)}%"}
            ]
            response['portfolio_calculation_steps'] = portfolio_calculation_steps
        
        if errors:
            response['errors'] = errors
        
        return response
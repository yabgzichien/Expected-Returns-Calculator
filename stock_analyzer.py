import yfinance as yf
import pandas as pd
import numpy as np
import json
import time
import random
import requests
from datetime import datetime, timedelta

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
        self.stocks = {}
        self.available_stocks = {
            '1155.KL': 'Maybank',
            '6033.KL': 'Petronas'
        }
        # Rotating user agents to avoid blocking
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
    def _safe_float(self, value):
        """Safely convert value to float"""
        try:
            if value is None or pd.isna(value):
                return None
            if isinstance(value, pd.Series):
                value = value.iloc[0] if len(value) > 0 else None
            return float(value)
        except:
            return None
    
    def _safe_int(self, value):
        """Safely convert value to int"""
        try:
            if value is None or pd.isna(value):
                return None
            if isinstance(value, pd.Series):
                value = value.iloc[0] if len(value) > 0 else None
            return int(value)
        except:
            return None
    
    def _create_requests_session(self):
        """Create a requests session with custom headers"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        return session
    
    def analyze_stock(self, stock_symbol, start_date="2015-01-01", end_date="2026-01-01", min_years=3):
        """Analyze a single stock with Render-specific fixes"""
        max_retries = 5  # Increased retries for cloud environment
        
        for attempt in range(max_retries):
            try:
                print(f"Analyzing stock: {stock_symbol} (attempt {attempt + 1}/{max_retries})")
                
                # Add increasing delay between retries
                if attempt > 0:
                    delay = 2 ** attempt + random.uniform(1, 3)
                    print(f"Waiting {delay:.1f} seconds before retry...")
                    time.sleep(delay)
                
                # Method 1: Try with repair=True and auto_adjust=False
                try:
                    data = yf.download(
                        stock_symbol, 
                        start=start_date, 
                        end=end_date, 
                        interval='1mo', 
                        actions=True, 
                        progress=False,
                        repair=True,
                        auto_adjust=False,
                        timeout=60  # Longer timeout for cloud
                    )
                    
                    if not data.empty:
                        print(f"Method 1 succeeded for {stock_symbol}")
                        return self._process_stock_data(data, stock_symbol, start_date, end_date)
                except Exception as e:
                    print(f"Method 1 failed: {str(e)}")
                
                # Method 2: Try with different interval
                try:
                    data = yf.download(
                        stock_symbol, 
                        start=start_date, 
                        end=end_date, 
                        interval='1mo',
                        actions=True,
                        progress=False,
                        timeout=60
                    )
                    
                    if not data.empty:
                        print(f"Method 2 succeeded for {stock_symbol}")
                        return self._process_stock_data(data, stock_symbol, start_date, end_date)
                except Exception as e:
                    print(f"Method 2 failed: {str(e)}")
                
                # Method 3: Try using Ticker object directly
                try:
                    ticker = yf.Ticker(stock_symbol)
                    data = ticker.history(start=start_date, end=end_date, interval='1mo')
                    
                    if not data.empty:
                        print(f"Method 3 succeeded for {stock_symbol}")
                        # Manually add dividends (not available in history)
                        dividends = pd.Series(index=data.index, data=0)
                        return self._process_stock_data_with_dividends(data, dividends, stock_symbol, start_date, end_date)
                except Exception as e:
                    print(f"Method 3 failed: {str(e)}")
                
                # Method 4: Try with period instead of dates
                try:
                    data = yf.download(
                        stock_symbol,
                        period='10y',
                        interval='1mo',
                        actions=True,
                        progress=False,
                        timeout=60
                    )
                    
                    if not data.empty:
                        print(f"Method 4 succeeded for {stock_symbol}")
                        return self._process_stock_data(data, stock_symbol, start_date, end_date)
                except Exception as e:
                    print(f"Method 4 failed: {str(e)}")
                
                print(f"All methods failed for {stock_symbol} on attempt {attempt + 1}")
                
            except Exception as e:
                print(f"Error analyzing {stock_symbol} (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    return {
                        'success': False,
                        'error': f"Failed after {max_retries} attempts: {str(e)}"
                    }
        
        return {
            'success': False,
            'error': f"Failed to analyze {stock_symbol} after {max_retries} attempts"
        }
    
    def _process_stock_data(self, data, stock_symbol, start_date, end_date):
        """Process downloaded stock data"""
        try:
            # Extract prices and dividends
            if isinstance(data['Close'], pd.DataFrame):
                prices = data['Close'].iloc[:, 0]
                dividends = data['Dividends'].iloc[:, 0] if 'Dividends' in data else pd.Series(index=data.index, data=0)
            else:
                prices = data['Close']
                dividends = data['Dividends'] if 'Dividends' in data else pd.Series(index=data.index, data=0)
            
            return self._calculate_metrics(prices, dividends, stock_symbol, start_date, end_date)
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            raise
    
    def _process_stock_data_with_dividends(self, data, dividends, stock_symbol, start_date, end_date):
        """Process stock data with manual dividends"""
        try:
            prices = data['Close']
            return self._calculate_metrics(prices, dividends, stock_symbol, start_date, end_date)
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            raise
    
    def _calculate_metrics(self, prices, dividends, stock_symbol, start_date, end_date):
        """Calculate all metrics from price and dividend data"""
        # Calculate annual returns
        yearly_prices = prices.resample('Y').last()
        yearly_dividends = dividends.resample('Y').sum()
        
        # Calculate annual returns including dividends
        annual_returns = []
        years = []
        return_calculations = []
        
        for i in range(1, len(yearly_prices)):
            try:
                P_t = self._safe_float(yearly_prices.iloc[i])
                P_t1 = self._safe_float(yearly_prices.iloc[i-1])
                D_t = self._safe_float(yearly_dividends.iloc[i])
                
                if P_t is not None and P_t1 is not None and P_t1 > 0:
                    if D_t is None:
                        D_t = 0.0
                        
                    total_return = (P_t - P_t1 + D_t) / P_t1
                    annual_returns.append(float(total_return))
                    
                    year = yearly_prices.index[i].year
                    years.append(int(year))
                    
                    return_calculations.append({
                        'year': year,
                        'formula': f"Rate of Return = (P<sub>t</sub> - P<sub>t-1</sub> + D<sub>t</sub>) / P<sub>t-1</sub>",
                        'values': f"= (RM{P_t:.2f} - RM{P_t1:.2f} + RM{D_t:.2f}) / RM{P_t1:.2f}",
                        'result': f"= {total_return*100:.2f}%"
                    })
            except Exception as e:
                print(f"Error processing year {i}: {e}")
                continue
        
        if len(annual_returns) < 3:
            raise Exception(f"Insufficient data: only {len(annual_returns)} years found")
        
        # Calculate metrics
        returns_array = np.array(annual_returns)
        n = len(annual_returns)
        
        # Expected Return
        exp_return = float(np.mean(returns_array))
        
        # Expected return steps
        expected_return_steps = {
            'formula': 'E(r) = Σ (r<sub>i</sub> × p<sub>i</sub>)',
            'components': [
                {
                    'description': f'With {n} years of data, assign equal probability p = 1/{n}',
                    'calculation': f'E(r) = (1/{n}) × Σ r<sub>i</sub>'
                },
                {
                    'description': 'Sum of annual returns:',
                    'values': ' + '.join([f'{r*100:.2f}%' for r in annual_returns]),
                    'sum': f'= {sum(annual_returns)*100:.2f}%'
                },
                {
                    'description': 'Final calculation:',
                    'calculation': f'E(r) = (1/{n}) × {sum(annual_returns)*100:.2f}%',
                    'result': f'= {exp_return*100:.2f}%'
                }
            ]
        }
        
        # Variance
        variance = float(np.var(annual_returns))
        
        # Variance steps
        variance_steps = {
            'formula': 'σ² = Σ [(r<sub>i</sub> - E(r))² × p<sub>i</sub>]',
            'components': [
                {
                    'description': 'Step 1: Calculate deviations [r<sub>i</sub> - E(r)]',
                    'values': [f'{r*100:.2f}% - {exp_return*100:.2f}% = {(r - exp_return)*100:.2f}%' for r in annual_returns[:3]]
                },
                {
                    'description': 'Step 2: Square each deviation',
                    'values': [f'({(r - exp_return)*100:.2f}%)² = {(r - exp_return)**2:.6f}' for r in annual_returns[:3]]
                },
                {
                    'description': f'Step 3: Multiply by probability (1/{n}) and sum',
                    'calculation': 'σ² = (1/' + str(n) + ') × [' + ' + '.join([f'{(r - exp_return)**2:.6f}' for r in annual_returns]) + ']',
                    'result': f'= {variance:.6f}'
                }
            ]
        }
        
        # Standard Deviation
        std_dev = float(np.std(annual_returns))
        
        std_dev_steps = {
            'formula': 'σ = √σ² = √variance',
            'calculation': f'σ = √{variance:.6f}',
            'result': f'= {std_dev*100:.2f}%'
        }
        
        # Get stock info
        try:
            ticker = yf.Ticker(stock_symbol)
            info = ticker.info
            stock_name = str(info.get('longName', stock_symbol))
        except:
            stock_name = stock_symbol
        
        # Get current price
        current_price = self._safe_float(prices.iloc[-1])
        
        # Convert annual returns to percentages
        annual_returns_pct = [round(r * 100, 2) for r in annual_returns]
        
        result = {
            'success': True,
            'symbol': str(stock_symbol),
            'name': stock_name,
            'expected_return': round(exp_return * 100, 2),
            'variance': round(variance, 6),
            'std_deviation': round(std_dev * 100, 2),
            'current_price': round(current_price, 2) if current_price else None,
            'annual_returns': annual_returns_pct,
            'years': [int(y) for y in years],
            'data_points': int(len(annual_returns)),
            'start_date': start_date,
            'end_date': end_date,
            'calculation_steps': {
                'annual_returns': return_calculations,
                'expected_return': expected_return_steps,
                'variance': variance_steps,
                'std_deviation': std_dev_steps
            }
        }
        
        return result
    
    def analyze_multiple_stocks(self, stock_list, weights=None, start_date="2015-01-01", end_date="2026-01-01"):
        """Analyze multiple stocks with portfolio calculation"""
        results = []
        errors = []
        
        print(f"Analyzing multiple stocks: {stock_list}")
        
        for stock in stock_list:
            result = self.analyze_stock(stock, start_date=start_date, end_date=end_date)
            if result and result.get('success'):
                results.append(result)
                print(f"Successfully analyzed {stock}")
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No result'
                errors.append(f"{stock}: {error_msg}")
                print(f"Failed to analyze {stock}: {error_msg}")
        
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
        
        # Calculate portfolio metrics if multiple stocks
        if len(results) > 1:
            if not weights:
                weights = [1.0/len(results)] * len(results)
            else:
                weights = [float(w) for w in weights]
                weight_sum = sum(weights)
                if abs(weight_sum - 1.0) > 0.01:
                    weights = [w/weight_sum for w in weights]
            
            # Calculate portfolio return
            portfolio_return = 0.0
            portfolio_calculation_steps = [
                {'step': 1, 'description': 'Portfolio Expected Return Formula', 'formula': 'E(Rp) = Σ wᵢ × E(Rᵢ)'},
                {'step': 2, 'description': 'Portfolio Weights', 'details': [f"{stock['symbol']}: {round(w*100,1)}%" for w, stock in zip(weights, results)]},
                {'step': 3, 'description': 'Individual Expected Returns', 'details': [f"{stock['symbol']}: {stock['expected_return']}%" for stock in results]},
                {'step': 4, 'description': 'Apply Formula', 'calculation': 'E(Rp) = ' + ' + '.join([f"({round(w*100,1)}% × {stock['expected_return']}%)" for w, stock in zip(weights, results)])}
            ]
            
            for w, stock in zip(weights, results):
                portfolio_return += w * stock['expected_return']
            
            portfolio_calculation_steps.append({'step': 5, 'description': 'Final Result', 'result': f'Expected Portfolio Return = {round(portfolio_return, 2)}%'})
            
            response['weights'] = [round(w * 100, 1) for w in weights]
            response['portfolio_return'] = round(portfolio_return, 2)
            response['portfolio_calculation_steps'] = portfolio_calculation_steps
        
        if errors:
            response['errors'] = errors
        
        return response
import yfinance as yf
import pandas as pd
import numpy as np
import json
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
    
    def _safe_float(self, value):
        """Safely convert value to float"""
        try:
            if value is None or pd.isna(value):
                return None
            # Handle Series objects
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
            # Handle Series objects
            if isinstance(value, pd.Series):
                value = value.iloc[0] if len(value) > 0 else None
            return int(value)
        except:
            return None
    
    def analyze_stock(self, stock_symbol, start_date="2010-01-01", end_date="2026-01-01", min_years=3):
        """Analyze a single stock and return its metrics with calculation steps"""
        try:
            print(f"Analyzing stock: {stock_symbol} from {start_date} to {end_date}")
            
            # Download data
            data = yf.download(stock_symbol, start=start_date, end=end_date, 
                              interval='1mo', actions=True, progress=False)
            
            if data.empty:
                print(f"No data found for {stock_symbol}")
                return {
                    'success': False,
                    'error': f'No data found for {stock_symbol}'
                }
            
            # Extract prices and dividends
            if isinstance(data['Close'], pd.DataFrame):
                prices = data['Close'].iloc[:, 0]
                dividends = data['Dividends'].iloc[:, 0] if 'Dividends' in data else pd.Series(index=data.index, data=0)
            else:
                prices = data['Close']
                dividends = data['Dividends'] if 'Dividends' in data else pd.Series(index=data.index, data=0)
            
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
                        
                        # Store calculation steps for display
                        return_calculations.append({
                            'year': year,
                            'formula': f"Rate of Return = (P<sub>t</sub> - P<sub>t-1</sub> + D<sub>t</sub>) / P<sub>t-1</sub>",
                            'values': f"= (RM{P_t:.2f} - RM{P_t1:.2f} + RM{D_t:.2f}) / RM{P_t1:.2f}",
                            'result': f"= {total_return*100:.2f}%"
                        })
                except Exception as e:
                    print(f"Error processing year {i}: {e}")
                    continue
            
            if len(annual_returns) < min_years:
                print(f"Insufficient data for {stock_symbol}. Found {len(annual_returns)} years, need {min_years}")
                return {
                    'success': False,
                    'error': f'Insufficient historical data. Only {len(annual_returns)} years found.',
                    'data_points': len(annual_returns)
                }
            
            # Calculate metrics
            returns_array = np.array(annual_returns)
            n = len(annual_returns)
            prob = 1.0 / n  # Equal probability for each year
            
            # Expected Return Calculation (Equation 7-3 from slides)
            exp_return = float(np.mean(returns_array))
            
            # Create expected return calculation steps
            expected_return_steps = {
                'formula': 'E(r) = Σ (r<sub>i</sub> × p<sub>i</sub>)',
                'components': [
                    {
                        'description': f'With {n} years of data, we assign equal probability p = 1/{n} to each year',
                        'calculation': f'E(r) = (1/{n}) × Σ r<sub>i</sub>'
                    },
                    {
                        'description': 'Sum of annual returns:',
                        'values': ' + '.join([f'{r*100:.2f}%' for r in annual_returns]),
                        'sum': f'= {sum(annual_returns)*100:.2f}%'
                    },
                    {
                        'description': 'Multiply by probability:',
                        'calculation': f'E(r) = (1/{n}) × {sum(annual_returns)*100:.2f}%',
                        'result': f'= {exp_return*100:.2f}%'
                    }
                ]
            }
            
            # Variance Calculation (Equation 7-5 from slides)
            squared_deviations = [(r - exp_return)**2 for r in annual_returns]
            variance = float(np.var(annual_returns))
            
            # Create variance calculation steps
            variance_steps = {
                'formula': 'σ² = Σ [(r<sub>i</sub> - E(r))² × p<sub>i</sub>]',
                'components': [
                    {
                        'description': 'Step 1: Calculate deviations from expected return [r<sub>i</sub> - E(r)]',
                        'values': [f'{r*100:.2f}% - {exp_return*100:.2f}% = {(r - exp_return)*100:.2f}%' for r in annual_returns]
                    },
                    {
                        'description': 'Step 2: Square each deviation',
                        'values': [f'({(r - exp_return)*100:.2f}%)² = {(r - exp_return)**2:.6f}' for r in annual_returns]
                    },
                    {
                        'description': f'Step 3: Multiply by probability (1/{n}) and sum',
                        'calculation': 'σ² = (1/' + str(n) + ') × [' + ' + '.join([f'{(r - exp_return)**2:.6f}' for r in annual_returns]) + ']',
                        'result': f'= {variance:.6f}'
                    }
                ]
            }
            
            # Standard Deviation Calculation
            std_dev = float(np.std(annual_returns))
            
            # Create standard deviation steps
            std_dev_steps = {
                'formula': 'σ = √σ² = √variance',
                'calculation': f'σ = √{variance:.6f}',
                'result': f'= {std_dev*100:.2f}%'
            }
            
            # Get stock info
            ticker = yf.Ticker(stock_symbol)
            info = ticker.info
            
            # Get current price
            current_price = self._safe_float(prices.iloc[-1])
            
            # Convert annual returns to percentages
            annual_returns_pct = [round(r * 100, 2) for r in annual_returns]
            
            result = {
                'success': True,
                'symbol': str(stock_symbol),
                'name': str(info.get('longName', stock_symbol)),
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
            
            json.dumps(result, cls=NumpyEncoder)
            print(f"Successfully analyzed {stock_symbol}")
            
            return result
            
        except Exception as e:
            print(f"Error analyzing {stock_symbol}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_multiple_stocks(self, stock_list, weights=None, start_date="2010-01-01", end_date="2026-01-01"):
        """Analyze multiple stocks - returns individual results and portfolio if multiple"""
        results = []
        errors = []
        
        print(f"Analyzing multiple stocks: {stock_list} from {start_date} to {end_date}")
        
        for stock in stock_list:
            print(f"Analyzing {stock}...")
            result = self.analyze_stock(stock, start_date=start_date, end_date=end_date, min_years=3)
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
        
        # If we have multiple stocks, calculate portfolio metrics
        if len(results) > 1:
            # Use provided weights or equal weights
            if not weights:
                weights = [1.0/len(results)] * len(results)
                weight_type = "equal"
            else:
                weights = [float(w) for w in weights]
                weight_type = "custom"
                weight_sum = sum(weights)
                if abs(weight_sum - 1.0) > 0.01:
                    weights = [w/weight_sum for w in weights]
            
            # Calculate portfolio return
            portfolio_return = 0.0
            portfolio_calculation_steps = []
            
            # Build calculation steps
            portfolio_calculation_steps.append({
                'step': 1,
                'description': 'Portfolio Expected Return Formula',
                'formula': 'E(R<sub>p</sub>) = w₁ × E(R₁) + w₂ × E(R₂) + ... + w<sub>n</sub> × E(R<sub>n</sub>)'
            })
            
            # Show weights
            weight_details = []
            for i, (w, stock) in enumerate(zip(weights, results)):
                weight_pct = round(w * 100, 1)
                weight_details.append(f"w{i+1} = {weight_pct}%")
                portfolio_return += w * stock['expected_return']
            
            portfolio_calculation_steps.append({
                'step': 2,
                'description': 'Portfolio Weights',
                'details': weight_details
            })
            
            # Show individual stock returns
            return_details = []
            for i, stock in enumerate(results):
                return_details.append(f"E(R{i+1}) = {stock['expected_return']}%")
            
            portfolio_calculation_steps.append({
                'step': 3,
                'description': 'Individual Stock Expected Returns',
                'details': return_details
            })
            
            # Show the full calculation
            calc_parts = []
            for i, (w, stock) in enumerate(zip(weights, results)):
                w_pct = round(w * 100, 1)
                calc_parts.append(f"({w_pct}% × {stock['expected_return']}%)")
            
            portfolio_calculation_steps.append({
                'step': 4,
                'description': 'Apply the Formula',
                'calculation': 'E(R<sub>p</sub>) = ' + ' + '.join(calc_parts)
            })
            
            # Calculate intermediate products
            intermediate = []
            for i, (w, stock) in enumerate(zip(weights, results)):
                product = w * stock['expected_return']
                intermediate.append(f"{round(product, 2)}%")
            
            portfolio_calculation_steps.append({
                'step': 5,
                'description': 'Calculate each term',
                'calculation': ' = ' + ' + '.join(intermediate)
            })
            
            # Final result
            portfolio_calculation_steps.append({
                'step': 6,
                'description': 'Sum all terms',
                'calculation': f'= {round(portfolio_return, 2)}%',
                'result': f'Expected Portfolio Return = {round(portfolio_return, 2)}%'
            })
            
            response['weights'] = [round(w * 100, 1) for w in weights]
            response['portfolio_return'] = round(portfolio_return, 2)
            response['weight_type'] = weight_type
            response['portfolio_calculation_steps'] = portfolio_calculation_steps
        
        if errors:
            response['errors'] = errors
        
        json.dumps(response, cls=NumpyEncoder)
        print(f"Analysis complete. Valid stocks: {len(results)}")
        
        return response
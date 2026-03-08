# app.py
import os
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from stock_analyzer import StockAnalyzer, NumpyEncoder

app = Flask(__name__)
# Allow all origins for Render
CORS(app, origins=["*"], supports_credentials=True)

# Initialize the stock analyzer
analyzer = StockAnalyzer()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/stocks', methods=['GET'])
def get_all_stocks():
    """Return the complete list of available stocks"""
    try:
        stocks = analyzer.get_all_stocks()
        return json.dumps(stocks, cls=NumpyEncoder), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"Error in get_all_stocks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_stocks():
    """Search for stocks by symbol or name"""
    try:
        query = request.args.get('q', '').upper()
        all_stocks = analyzer.get_all_stocks()
        
        results = []
        for stock in all_stocks:
            if query in stock['symbol'] or query in stock['name'].upper():
                results.append(stock)
        
        return json.dumps(results[:10], cls=NumpyEncoder), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"Error in search_stocks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-multiple', methods=['POST'])
def analyze_multiple_stocks():
    """Analyze multiple stocks and return portfolio metrics"""
    try:
        data = request.json
        stocks = data.get('stocks', [])
        weights = data.get('weights')
        start_date = data.get('start_date', '2015-01-01')
        end_date = data.get('end_date', '2026-01-01')
        
        if not stocks or len(stocks) == 0:
            return jsonify({'error': 'Please select at least 1 stock'}), 400
        
        print(f"Analyzing stocks: {stocks} from {start_date} to {end_date}")
        result = analyzer.analyze_multiple_stocks(stocks, weights, start_date, end_date)
        
        return json.dumps(result, cls=NumpyEncoder), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"Error in analyze_multiple_stocks: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/analyze-single', methods=['POST'])
def analyze_single_stock():
    """Analyze a single stock (for testing)"""
    try:
        data = request.json
        symbol = data.get('symbol')
        start_date = data.get('start_date', '2015-01-01')
        end_date = data.get('end_date', '2026-01-01')
        
        if not symbol:
            return jsonify({'error': 'No stock symbol provided'}), 400
        
        print(f"Analyzing single stock: {symbol} from {start_date} to {end_date}")
        result = analyzer.analyze_stock(symbol, start_date, end_date)
        
        return json.dumps(result, cls=NumpyEncoder), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"Error in analyze_single_stock: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    stocks_count = len(analyzer.stock_info)
    return jsonify({
        'status': 'healthy',
        'message': 'Stock analyzer API is running',
        'stocks_available': stocks_count,
        'data_directory_exists': os.path.exists('data')
    })

@app.route('/api/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to check data availability"""
    try:
        data_dir = 'data'
        files = []
        if os.path.exists(data_dir):
            files = os.listdir(data_dir)
        
        # Get first few rows of first CSV for debugging
        sample_data = None
        if files and len(files) > 0:
            try:
                sample_df = pd.read_csv(os.path.join(data_dir, files[0]), nrows=5)
                sample_data = sample_df.to_dict('records')
            except:
                pass
        
        return jsonify({
            'data_directory_exists': os.path.exists(data_dir),
            'data_files_count': len(files),
            'data_files': files[:10],  # First 10 files
            'stocks_in_memory': len(analyzer.stock_info),
            'stock_symbols': list(analyzer.stock_info.keys()),
            'sample_data': sample_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """Force refresh of stock data from CSV files"""
    try:
        global analyzer
        analyzer = StockAnalyzer()  # Re-initialize to reload data
        return jsonify({
            'success': True,
            'message': 'Data refreshed',
            'stocks_loaded': len(analyzer.stock_info)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
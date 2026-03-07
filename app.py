from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from stock_analyzer import StockAnalyzer, NumpyEncoder
import traceback
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)
analyzer = StockAnalyzer()

# Complete list of top 30 Malaysian companies
MALAYSIAN_STOCKS = {
    '1155.KL': 'Malayan Banking Berhad (Maybank)',
    '1295.KL': 'Public Bank Berhad',
    '1023.KL': 'CIMB Group Holdings Berhad',
    '5819.KL': 'Hong Leong Bank Berhad',
    '1066.KL': 'RHB Bank Berhad',
    '1015.KL': 'AMMB Holdings Berhad',
    
    # Oil & Gas
    '5681.KL': 'PETRONAS Dagangan Berhad',
    '6033.KL': 'PETRONAS Gas Berhad',
    '5183.KL': 'PETRONAS Chemicals Group Berhad',
    '5285.KL': 'SD Guthrie Berhad',
    
    # Telecommunications
    '6012.KL': 'Maxis Berhad',
    '6947.KL': 'Celcomdigi Berhad',
    '4863.KL': 'Telekom Malaysia Berhad',
    '6888.KL': 'Axiata Group Berhad',
    
    # Utilities & Power
    '5347.KL': 'Tenaga Nasional Berhad',
    '6742.KL': 'YTL Power International Berhad',
    '4677.KL': 'YTL Corporation Berhad',
    
    # Plantation & Agriculture
    '1961.KL': 'IOI Corporation Berhad',
    '2445.KL': 'Kuala Lumpur Kepong Berhad',
    '4197.KL': 'Sime Darby Berhad',
    '3816.KL': 'MISC Berhad',
    
    # Consumer & Retail
    '5296.KL': 'Mr D.I.Y. Group (M) Berhad',
    '5326.KL': '99 Speed Mart Retail Holdings Berhad',
    '4707.KL': 'Nestlé (Malaysia) Berhad',
    
    # Healthcare
    '5225.KL': 'IHH Healthcare Berhad',
    
    # Construction & Property
    '5398.KL': 'Gamuda Berhad',
    '5211.KL': 'Sunway Berhad',
    
    # Industrial
    '7084.KL': 'QL Resources Berhad',
    '8869.KL': 'Press Metal Aluminium Holdings Berhad',
    '4065.KL': 'PPB Group Berhad'
}

@app.route('/')
def index():
    return render_template('index.html')

import logging
import sys

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

@app.errorhandler(500)
def handle_500(error):
    return jsonify({'error': 'Internal server error', 'success': False}), 500

@app.route('/api/stocks', methods=['GET'])
def get_all_stocks():
    try:
        stocks = []
        for symbol, name in MALAYSIAN_STOCKS.items():
            stocks.append({
                'symbol': symbol,
                'name': name,
                'sector': get_sector(symbol)
            })
        return json.dumps(stocks, cls=NumpyEncoder), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"Error in get_all_stocks: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def get_sector(symbol):
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

@app.route('/api/analyze', methods=['POST'])
def analyze_stock():
    try:
        data = request.json
        stock_symbol = data.get('symbol')
        start_date = data.get('start_date', '2010-01-01')
        end_date = data.get('end_date', '2026-01-01')
        
        if not stock_symbol:
            return jsonify({'error': 'No stock symbol provided'}), 400
        
        print(f"Analyzing stock: {stock_symbol} from {start_date} to {end_date}")
        result = analyzer.analyze_stock(stock_symbol, start_date=start_date, end_date=end_date)
        
        return json.dumps(result, cls=NumpyEncoder), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"Error in analyze_stock: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/analyze-multiple', methods=['POST'])
def analyze_multiple_stocks():
    try:
        data = request.json
        stocks = data.get('stocks', [])
        weights = data.get('weights')
        start_date = data.get('start_date', '2010-01-01')
        end_date = data.get('end_date', '2026-01-01')
        
        print(f"Analyze multiple request - Stocks: {stocks}, Period: {start_date} to {end_date}")
        
        if not stocks or len(stocks) == 0:
            return jsonify({'error': 'Please select at least 1 stock'}), 400
        
        result = analyzer.analyze_multiple_stocks(stocks, weights, start_date=start_date, end_date=end_date)
        
        return json.dumps(result, cls=NumpyEncoder), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"Error in analyze_multiple_stocks: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/search', methods=['GET'])
def search_stocks():
    try:
        query = request.args.get('q', '').upper()
        
        results = []
        for symbol, name in MALAYSIAN_STOCKS.items():
            if query in symbol or query in name.upper():
                results.append({
                    'symbol': symbol,
                    'name': name,
                    'sector': get_sector(symbol)
                })
        
        return json.dumps(results[:10], cls=NumpyEncoder), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"Error in search_stocks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Stock analyzer API is running'})

if __name__ == '__main__':
    app.run(debug=True, port=5000) 

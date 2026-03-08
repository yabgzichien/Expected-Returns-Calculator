# download_data.py
import yfinance as yf
import pandas as pd
import time
import os

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# List of Malaysian stocks
STOCKS = {
    '1155.KL': 'Maybank',
    '1295.KL': 'Public Bank',
    '1023.KL': 'CIMB',
    '5819.KL': 'Hong Leong Bank',
    '1066.KL': 'RHB Bank',
    '1015.KL': 'AMMB Holdings',
    '5681.KL': 'PETRONAS Dagangan',
    '6033.KL': 'PETRONAS Gas',
    '5183.KL': 'PETRONAS Chemicals',
    '5285.KL': 'SD Guthrie',
    '6012.KL': 'Maxis',
    '6947.KL': 'Celcomdigi',
    '4863.KL': 'Telekom Malaysia',
    '6888.KL': 'Axiata',
    '5347.KL': 'Tenaga Nasional',
    '6742.KL': 'YTL Power',
    '4677.KL': 'YTL Corporation',
    '1961.KL': 'IOI Corporation',
    '2445.KL': 'Kuala Lumpur Kepong',
    '4197.KL': 'Sime Darby',
    '3816.KL': 'MISC',
    '5296.KL': 'Mr D.I.Y.',
    '5326.KL': '99 Speed Mart',
    '4707.KL': 'Nestlé Malaysia',
    '5225.KL': 'IHH Healthcare',
    '5398.KL': 'Gamuda',
    '5211.KL': 'Sunway',
    '7084.KL': 'QL Resources',
    '8869.KL': 'Press Metal',
    '4065.KL': 'PPB Group'
}

def download_stock_data(symbol, name):
    """Download stock data and save to CSV"""
    print(f"Downloading {symbol} - {name}...")
    
    try:
        # Download 15 years of monthly data
        stock = yf.Ticker(symbol)
        df = stock.history(period="15y", interval="1mo")
        
        if df.empty:
            print(f"No data for {symbol}")
            return False
        
        # Add symbol column
        df['Symbol'] = symbol
        df['Name'] = name
        
        # Save to CSV
        filename = f"data/{symbol.replace('.', '_')}.csv"
        df.to_csv(filename)
        print(f"Saved to {filename}")
        
        # Add small delay to avoid rate limiting
        time.sleep(1)
        return True
        
    except Exception as e:
        print(f"Error downloading {symbol}: {e}")
        return False

def download_all_stocks():
    """Download all stocks"""
    successful = []
    failed = []
    
    for symbol, name in STOCKS.items():
        if download_stock_data(symbol, name):
            successful.append(symbol)
        else:
            failed.append(symbol)
    
    print("\n=== Download Summary ===")
    print(f"Successful: {len(successful)} stocks")
    print(f"Failed: {len(failed)} stocks")
    
    if failed:
        print("\nFailed stocks:", failed)

if __name__ == "__main__":
    download_all_stocks()
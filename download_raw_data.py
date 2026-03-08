# download_raw_data.py
import yfinance as yf
import pandas as pd
import time
import os
from datetime import datetime

# Create data directory
os.makedirs('data', exist_ok=True)

# Complete list of top 30 Malaysian companies
MALAYSIAN_STOCKS = {
    # Banking & Finance
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

def download_stock_csv(symbol, name):
    """Download stock data and save as CSV"""
    print(f"Downloading {symbol} - {name}...")
    
    try:
        # Download 15 years of monthly data
        stock = yf.Ticker(symbol)
        df = stock.history(period="15y", interval="1mo")
        
        if df.empty:
            print(f"  ⚠️ No data for {symbol}")
            return False
        
        # Add symbol and name columns
        df['Symbol'] = symbol
        df['Name'] = name
        
        # Reset index to make Date a column
        df.reset_index(inplace=True)
        
        # Save to CSV
        filename = f"data/{symbol.replace('.', '_')}.csv"
        df.to_csv(filename, index=False)
        print(f"  ✅ Saved {len(df)} rows to {filename}")
        
        # Small delay to avoid rate limiting
        time.sleep(1)
        return True
        
    except Exception as e:
        print(f"  ❌ Error downloading {symbol}: {e}")
        return False

def download_all_stocks():
    """Download all stocks to CSV files"""
    print("=" * 60)
    print("DOWNLOADING RAW STOCK DATA")
    print("=" * 60)
    
    successful = []
    failed = []
    
    for i, (symbol, name) in enumerate(MALAYSIAN_STOCKS.items(), 1):
        print(f"\n[{i}/{len(MALAYSIAN_STOCKS)}] ", end="")
        if download_stock_csv(symbol, name):
            successful.append(symbol)
        else:
            failed.append(symbol)
    
    print("\n" + "=" * 60)
    print(f"✅ SUCCESSFUL: {len(successful)} stocks")
    print(f"❌ FAILED: {len(failed)} stocks")
    
    if failed:
        print("\nFailed stocks:")
        for symbol in failed:
            print(f"  - {symbol}")
    
    print("\n📁 CSV files saved in 'data/' directory")

if __name__ == "__main__":
    download_all_stocks()
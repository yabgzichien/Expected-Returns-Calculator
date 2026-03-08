# combine_data.py
import pandas as pd
import os
import glob

def combine_all_data():
    """Combine all individual CSV files into one master file"""
    
    # Get all CSV files
    csv_files = glob.glob("data/*.csv")
    
    all_data = []
    
    for file in csv_files:
        df = pd.read_csv(file, index_col=0)
        df.index = pd.to_datetime(df.index)
        all_data.append(df)
    
    # Combine all data
    combined = pd.concat(all_data)
    combined.sort_index(inplace=True)
    
    # Save combined data
    combined.to_csv("data/all_stocks.csv")
    print(f"Combined {len(csv_files)} files into data/all_stocks.csv")
    print(f"Total rows: {len(combined)}")

if __name__ == "__main__":
    combine_all_data()
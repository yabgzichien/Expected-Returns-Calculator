# setup_data.py
import subprocess
import os

def setup():
    """Run all data download and processing scripts"""
    
    print("=" * 50)
    print("Setting up stock data...")
    print("=" * 50)
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Step 1: Download individual stock data
    print("\n1. Downloading stock data...")
    subprocess.run(['python', 'download_data.py'])
    
    # Step 2: Combine all data
    print("\n2. Combining data...")
    subprocess.run(['python', 'combine_data.py'])
    
    # Step 3: Compute metrics
    print("\n3. Computing metrics...")
    subprocess.run(['python', 'compute_metrics.py'])
    
    print("\n" + "=" * 50)
    print("Setup complete! Data saved to data/ directory")
    print("=" * 50)

if __name__ == "__main__":
    setup()
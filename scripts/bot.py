import argparse
import os
from dotenv import load_dotenv
from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager
from gmx_python_sdk.scripts.v2.order.create_increase_order import IncreaseOrder
from gmx_python_sdk.scripts.v2.order.create_decrease_order import DecreaseOrder
from gmx_python_sdk.scripts.v2.order.create_swap_order import SwapOrder
from get_gmx_stats import GetGMXv2Stats
import pandas as pd
import numpy as np
import talib as ta
from datetime import datetime
import time
import yfinance as yf
from web3 import Web3
import requests

# Load environment variables from .env file
load_dotenv()

# Access environment variables
rpc_url = os.getenv("RPC_URL")
private_key = os.getenv("PRIVATE_KEY")
wallet_address = os.getenv("WALLET_ADDRESS")

# Setup configuration
print("Setting up configuration for GMX...")
config = ConfigManager("arbitrum")
config.set_config(filepath="config.yaml")
print("Configuration setup complete.")

w3 = Web3(Web3.HTTPProvider(rpc_url))


def initialize_historical_data():
    print("Initializing historical data...")
    eth_data = yf.download("ETH-USD", period="1mo", interval="15m").tail(200)
    eth_data = eth_data.reset_index()[['Datetime', 'Close', 'Volume']]
    eth_data.columns = ['Timestamp', 'Close', 'Volume']
    eth_data['Volume_MA'] = ta.SMA(eth_data['Volume'], timeperiod=200)
    print("Historical data initialized.")
    return eth_data


def generate_signals(data, rsi_period, rsi_buy_threshold, rsi_sell_threshold):
    print("Generating RSI-based trading signals...")
    data['RSI'] = ta.RSI(data['Close'], timeperiod=rsi_period)
    data['Long'] = np.where(data['RSI'] < rsi_buy_threshold, 1, 0)
    data['Short'] = np.where(data['RSI'] > rsi_sell_threshold, -1, 0)
    data['Position'] = data['Long'] + data['Short']
    signal = data.iloc[-1]
    print(f"Generated signal - RSI: {signal['RSI']}, Position: {signal['Position']}")
    return signal


def run_trading_bot(rsi_period, rsi_buy_threshold, rsi_sell_threshold, open_percentage, close_percentage):
    print("Starting trading bot...")
    historical_data = initialize_historical_data()
    current_position = 0

    while True:
        print("Running bot iteration...")
        eth_price = fetch_market_data()  # Add your fetch_market_data function here

        # Ensure eth_price is valid before continuing
        if eth_price is None:
            print("Error fetching market data. Retrying in 1 minute.")
            time.sleep(60)
            continue

        # Update historical data and calculate RSI signals
        latest_signal = generate_signals(historical_data, rsi_period, rsi_buy_threshold, rsi_sell_threshold)

        # Fetch wallet balance and calculate position sizes
        wallet_balance_usd = get_wallet_balance()  # Add your get_wallet_balance function here
        size_delta_usd = wallet_balance_usd * open_percentage
        close_size_delta = current_position * close_percentage

        # Implement your trading logic here based on signals and position size

        print("Sleeping for 5 minutes...")
        time.sleep(300)


if __name__ == "__main__":
    # Define and parse command-line arguments
    parser = argparse.ArgumentParser(description="Run the GMX trading bot with custom RSI and position parameters.")
    parser.add_argument("--rsi_period", type=int, default=14, help="RSI period for trading signals")
    parser.add_argument("--rsi_buy_threshold", type=int, default=41, help="RSI buy threshold")
    parser.add_argument("--rsi_sell_threshold", type=int, default=60, help="RSI sell threshold")
    parser.add_argument("--open_percentage", type=float, default=0.1, help="Percentage of wallet balance to use for opening positions")
    parser.add_argument("--close_percentage", type=float, default=0.1, help="Percentage of position to close when closing")

    args = parser.parse_args()

    # Run the bot with parsed arguments
    run_trading_bot(
        rsi_period=args.rsi_period,
        rsi_buy_threshold=args.rsi_buy_threshold,
        rsi_sell_threshold=args.rsi_sell_threshold,
        open_percentage=args.open_percentage,
        close_percentage=args.close_percentage
    )

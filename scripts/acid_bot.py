from utils import _set_paths, load_yaml, setup_config, download_ta_lib

download_ta_lib()

from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager, create_connection, convert_to_checksum_address
from gmx_python_sdk.scripts.v2.order.create_increase_order import IncreaseOrder
from gmx_python_sdk.scripts.v2.order.create_decrease_order import DecreaseOrder
from gmx_python_sdk.scripts.v2.order.create_decrease_order import Order
from get_gmx_stats import GetGMXv2Stats
from gmx_python_sdk.scripts.v2.order.order_argument_parser import OrderArgumentParser
from utils import _set_paths, load_yaml, setup_config, download_ta_lib
import pandas as pd
import numpy as np
import talib as ta
import requests
import time
from datetime import datetime
import yfinance as yf
from web3 import Web3
from hexbytes import HexBytes
from web3.exceptions import ValidationError
import json
import os
import yaml
import sys
import subprocess
import argparse

# Set paths for relative imports
_set_paths()

rpc_url = None
w3 = None
stats = None
bb_length = None
bb_multiplier = None
rsi_length = None
rsi_overbought = None
rsi_oversold = None
stats = None
market = None

def get_config():
    """
    Parse command-line arguments and load configurations.

    Returns
    -------
    strategy : dict
        The trading strategy configuration loaded from YAML.
    config : ConfigManager
        The GMX configuration object.
    """
    parser = argparse.ArgumentParser(
        description="Run GMX trading bot - ACID."
    )
    parser.add_argument(
        "--config",
        help="Path to the configuration YAML file.",
        default=os.path.join("utils", "config.yaml"),
    )
    parser.add_argument(
        "--strategy",
        help="Path to the strategy YAML file.",
        default=os.path.join("utils", "strategy.yaml"),
    )

    args = parser.parse_args()

    # Load configurations
    print("[DEBUG] Loading configuration files...")
    strategy_path = args.strategy
    config_path = args.config

    strategy = load_yaml(strategy_path)
    config = setup_config(config_path)
    
    return strategy, config
    
strategy, config = get_config()

def setup(config, strategy):
   """
    Set up the bot environment, including the RPC connection and strategy trading parameters.
   """
    global rpc_url, w3, stats
    
    print("[DEBUG] Setting up configuration...")
    rpc_url = config.rpc
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    print(f"[DEBUG] RPC URL: {rpc_url}")
    
    # Access specific strategy parameters
    bb_length = strategy["bollinger_bands"]["length"]
    bb_multiplier = strategy["bollinger_bands"]["multiplier"]
    rsi_length = strategy["rsi"]["length"]
    rsi_overbought = strategy["rsi"]["overbought"]
    rsi_oversold = strategy["rsi"]["oversold"]
    print(f"[DEBUG] Bollinger Bands Length: {bb_length}, RSI Length: {rsi_length}")

    # Modify the instantiation of GetGMXv2Stats with additional arguments
    stats = GetGMXv2Stats(config, to_json=True, to_csv=False)  # Adjust these flags as needed
    print("[DEBUG] GMX Stats initialized.")
    
def get_market_data():
    """
    Fetch and display market data for ETH.

    Returns
    -------
    dict
        ETH market data, including token addresses and collateral details.
    """
    print("[DEBUG] Fetching available markets...")
    # Assuming markets is a dictionary where keys are addresses and values contain market details
    try:
        markets = stats.get_available_markets()
        eth_market = next((details for address, details in markets.items() if details.get("market_symbol") == "ETH"), None)
    except AttributeError as e:
        print(f"[ERROR] Error accessing market details: {e}")
        return None

    if eth_market:
        print("[DEBUG] ETH market details fetched successfully.")
        MARKET_KEY = eth_market["gmx_market_address"]
        INDEX_TOKEN_ADDRESS = eth_market["index_token_address"]
        LONG_TOKEN_ADDRESS = eth_market["long_token_address"]
        SHORT_TOKEN_ADDRESS = eth_market["short_token_address"]
        COLLATERAL_ADDRESS = eth_market["short_token_address"]
        print(f"Market Key for ETH: {MARKET_KEY}")
        print(f"Index Token Address: {INDEX_TOKEN_ADDRESS}")
        print(f"Long Token Address: {LONG_TOKEN_ADDRESS}")
        print(f"Short Token Address: {SHORT_TOKEN_ADDRESS}")
        print(f"Collateral Address: {COLLATERAL_ADDRESS}")
    else:
        print("[ERROR] ETH market not found in GMX markets.")
        exit()

# Function to get the ETH to USD conversion rate using CoinGecko's API
def get_eth_to_usd_price():
    """
    Fetch the current price of ETH in USD from the CoinGecko API.

    Returns
    -------
    float
        The current ETH price in USD.
    """
    print("[DEBUG] Fetching ETH price from CoinGecko...")
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {
        'ids': 'ethereum',
        'vs_currencies': 'usd'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()
        eth_price_usd = data['ethereum']['usd']
        print(f"[DEBUG] ETH price: ${eth_price_usd}")
        return eth_price_usd
    except requests.exceptions.HTTPError as http_err:
        print(f"[ERROR] HTTP error: {http_err}")
    except Exception as err:
        print(f"[ERROR] General error: {err}")
    return None

# Function to fetch wallet balance in USD
def get_wallet_balance():
    """
    Fetch the user's wallet balance in ETH and its USD equivalent.

    Returns
    -------
    tuple
        A tuple containing the wallet balance in ETH and USD.
    """
    print("[DEBUG] Fetching wallet balance...")
    print("Connecting to RPC URL:", config.rpc)
    try:
        wallet_address = config.user_wallet_address
        print("Fetching balance for wallet address")

        # Step 1: Get balance in native token (ETH)
        native_balance_wei = w3.eth.get_balance(wallet_address)
        print("Native balance (in Wei):", native_balance_wei)

        # Step 2: Convert Wei to ETH manually
        native_balance_eth = native_balance_wei / 1e18
        print("Native balance (in ETH):", native_balance_eth)

        # Ensure balance is in a compatible format
        native_balance_eth = float(native_balance_eth)
        print("Native balance (converted to float):", native_balance_eth, "ETH")

        # Step 3: Fetch ETH to USD conversion rate from CoinGecko
        max_price_in_usd = get_eth_to_usd_price()  # Fetch ETH price in USD equivalent
        if max_price_in_usd is None:
            print("Error: Unable to fetch ETH price for USD conversion.")
            return None

        # Step 4: Calculate wallet balance in USD
        wallet_balance = native_balance_eth * max_price_in_usd
        print(f"Wallet balance in USD: ${wallet_balance:.2f}")
        return native_balance_eth, wallet_balance

    except AttributeError as e:
        print("[ERROR] fetching balance or price from oracle:", e)
        return None
    except Exception as e:
        print(f"[ERROR] fetching wallet balance: {e}")
        return None


# Helper function to calculate size_delta_usd for opening position
def calculate_open_position_amount(wallet_balance, open_percentage):
    if wallet_balance is None:
        print("[ERROR]: Wallet balance is None. Skipping position calculation.")
        return None
    return wallet_balance * open_percentage

# Helper function to calculate size_delta_usd for closing position
def calculate_close_position_amount(current_position_value, close_percentage):
    if current_position_value is None:
        print("[ERROR]: Current position value is None. Skipping position calculation.")
        return None
    return current_position_value * (1 - close_percentage)

# Initialize historical data
def initialize_historical_data():
    """
    Fetch historical ETH price data and calculate moving averages.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing historical data with Bollinger Band indicators.
    """
    print("[DEBUG] Fetching historical price data for ETH...")
    eth_data = yf.download("ETH-USD", period="1mo", interval="15m").tail(200)
    eth_data = eth_data.reset_index()[['Datetime', 'Close', 'Volume']]
    eth_data.columns = ['Timestamp', 'Close', 'Volume']

    # Calculate the moving average explicitly using .loc
    eth_data.loc[:, 'Volume_MA'] = ta.SMA(eth_data['Volume'], timeperiod=200)

    print("Historical data initialized.")
    return eth_data


# Generate trading signals based on Bollinger Bands, RSI, and Volume
def generate_signals(data, strategy):
    """
    Generate trading signals based on technical indicators: Bollinger Bands, RSI, and Volume.

    Parameters
    ----------
    data : pandas.DataFrame
        Historical data containing at least 'Close' and 'Volume' columns.
    strategy : dict
        Strategy configuration dictionary containing parameters for Bollinger Bands, RSI, and Volume.

    Returns
    -------
    pandas.Series
        A row of the DataFrame with the latest generated signal and indicator values.
    """
    print("[DEBUG] Generating trading signals...")

    # Bollinger Bands setup
    bb_length = strategy["bollinger_bands"]["length"]
    bb_multiplier = strategy["bollinger_bands"]["multiplier"]
    print(f"[DEBUG] Bollinger Bands parameters: Length={bb_length}, Multiplier={bb_multiplier}")
    data['BB_MA'] = ta.SMA(data['Close'], timeperiod=bb_length)
    data['BB_Upper'] = data['BB_MA'] + bb_multiplier * ta.STDDEV(data['Close'], timeperiod=bb_length, nbdev=1)
    data['BB_Lower'] = data['BB_MA'] - bb_multiplier * ta.STDDEV(data['Close'], timeperiod=bb_length, nbdev=1)

    # RSI setup
    rsi_length = strategy["rsi"]["length"]
    rsi_overbought = strategy["rsi"]["overbought"]
    rsi_oversold = strategy["rsi"]["oversold"]
    print(f"[DEBUG] RSI parameters: Length={rsi_length}, Overbought={rsi_overbought}, Oversold={rsi_oversold}")
    data['RSI'] = ta.RSI(data['Close'], timeperiod=rsi_length)

    # Volume setup
    vol_ma_length = strategy["volume"]["moving_avg_length"]
    print(f"[DEBUG] Volume moving average length: {vol_ma_length}")
    data['Volume_MA'] = ta.SMA(data['Volume'], timeperiod=vol_ma_length)
    data['High_Volume'] = data['Volume'] > data['Volume_MA']

    # Long condition: Price touches lower Bollinger Band, RSI < Oversold, Volume > MA
    data['Long_Signal'] = (data['Close'] <= data['BB_Lower']) & (data['RSI'] < rsi_oversold) & (data['High_Volume'])

    # Short condition: Price touches upper Bollinger Band, RSI > Overbought, Volume > MA
    data['Short_Signal'] = (data['Close'] >= data['BB_Upper']) & (data['RSI'] > rsi_overbought) & (data['High_Volume'])

    # Generate signals
    data['Position'] = 0
    data.loc[data['Long_Signal'], 'Position'] = 1
    data.loc[data['Short_Signal'], 'Position'] = -1

    # Extract the latest signal
    latest_signal = data.iloc[-1]
    print(f"[DEBUG] Latest Signal: RSI={latest_signal['RSI']}, Position={latest_signal['Position']}")
    return latest_signal

#Function to build order parser
def build_order(leverage, is_long, size_delta, percentage, increase):
    """
    Build order parameters for submitting a trade order.

    Parameters
    ----------
    leverage : float
        The leverage factor for the trade (e.g., 5 for 5x leverage).
    is_long : bool
        True for a long position, False for a short position.
    size_delta : float
        The size of the position in units (e.g., ETH).
    percentage : float
        Slippage percentage as a decimal (e.g., 0.003 for 0.3%).
    increase : bool
        True if this is an increase order, False for a decrease order.

    Returns
    -------
    dict
        Order parameters dictionary ready for submission.
    """
    size_delta_usd = size_delta * leverage
    # Initialize and submit the IncreaseOrder
    parameters = {
        "chain": 'arbitrum',
        # the market you want to trade on
        "index_token_symbol": "ETH",
        # token to use as collateral. Start token swaps into collateral token
        # if different
        "collateral_token_symbol": "ETH",

        # the token to start with - WETH not supported yet
        "start_token_symbol": "USDC",

        # True for long, False for short
        "is_long": is_long,

        # Position size in in USD
        "size_delta_usd": size_delta_usd,

        # if leverage is passed, will calculate number of tokens in
        # start_token_symbol amount
        "leverage": leverage,

        # as a decimal ie 0.003 == 0.3%
        "slippage_percent": percentage
    }
    print(f"The parameters for this order is the following: {parameters}")

    order_parameters = OrderArgumentParser(
    config,
    is_increase=True
    ).process_parameters_dictionary(
    parameters
    )
    print(f"Order Parser: {order_parameters}")

    return order_parameters

# Function to open position based on a percentage of wallet balance in USD
def open_position(is_long, eth_price, leverage, size_delta_usd, percentage):
    """
    Open a trading position (long or short) based on the given parameters.

    Parameters
    ----------
    is_long : bool
        True for a long position, False for a short position.
    eth_price : float
        Current ETH price in USD.
    leverage : float
        Leverage factor (e.g., 5 for 5x leverage).
    size_delta_usd : float
        Position size in USD.
    percentage : float
        Slippage percentage as a decimal (e.g., 0.003 for 0.3%).
    """
    print(f"[DEBUG] Initiating open_position: Is_Long={is_long}, ETH_Price={eth_price}, Leverage={leverage}, Size_Delta_USD={size_delta_usd}")

    order_parameters = build_order(leverage, is_long, size_delta_usd, percentage, True)

    order = IncreaseOrder(
        config=config,
        market_key=order_parameters['market_key'],
        collateral_address=order_parameters['start_token_address'],
        index_token_address=order_parameters['index_token_address'],
        is_long=order_parameters['is_long'],
        size_delta=order_parameters['size_delta'],
        initial_collateral_delta_amount=(
            order_parameters['initial_collateral_delta']
        ),
        slippage_percent=order_parameters['slippage_percent'],
        swap_path=order_parameters['swap_path'],
        debug_mode=True,
        execution_buffer=1.5
    )

    # Calculate gas limits and submit the transaction
    print("[DEBUG] Calculating gas limits for transaction...")
    order.determine_gas_limits()
    print(f"[DEBUG] Gas limits determined: {order._gas_limits}")

    print("[DEBUG] Checking token approval...")
    order.check_for_approval()

    print("[DEBUG] Submitting transaction to open position...")
    order._submit_transaction(
        user_wallet_address=config.user_wallet_address,
        value_amount=order_parameters["initial_collateral_delta"],  # Collateral amount in Wei
        multicall_args=[
          #HexBytes(order._send_wnt(order_parameters['initial_collateral_delta'])),  # Ensure this matches value_amount
          #HexBytes(order._create_order((config.user_wallet_address,)))
        ],
        gas_limits=order._gas_limits,
    )
    print(f"[DEBUG] Position opened with ETH amount: {eth_amount_to_use:.6f} ETH")

def close_position(is_long, eth_price, leverage, size_delta_usd, percentage):
    """
    Function to close a position using similar logic to opening a position.

    Parameters
    ----------
    is_long : bool
        True if closing a long position, False for short position.
    eth_price : float
        Current price of ETH in USD.
    leverage : float
        Leverage used in the position.
    size_delta_usd : float
        Size of the position to close in USD.
    percentage : float
        Percentage for slippage and initial collateral delta.
    """
    print(f"[DEBUG] Starting close_position. Parameters - is_long: {is_long}, eth_price: {eth_price}, leverage: {leverage}, size_delta_usd: {size_delta_usd}, percentage: {percentage}")

    # Calculate the size of the position to close
    size_delta = size_delta_usd / leverage

    # Build order parameters for decreasing the position
    order_parameters = build_order(leverage, is_long, size_delta, percentage, increase=False)

    print(f"[DEBUG] Processed order parameters for closing position: {order_parameters}")

    # Instantiate and configure DecreaseOrder
    order = DecreaseOrder(
        config=config,
        market_key=order_parameters['market_key'],
        collateral_address=order_parameters['start_token_address'],
        index_token_address=order_parameters['index_token_address'],
        is_long=order_parameters['is_long'],
        size_delta=order_parameters['size_delta'],
        initial_collateral_delta_amount=(
            order_parameters['initial_collateral_delta']
        ),
        slippage_percent=order_parameters['slippage_percent'],
        swap_path=order_parameters['swap_path'],
        debug_mode=True,
        execution_buffer=1.5
    )

    print("[DEBUG] DecreaseOrder instantiated successfully.")

    # Determine gas limits for the transaction
    print("[DEBUG] Determining gas limits...")
    order.determine_gas_limits()
    print(f"[DEBUG] Gas limits determined: {order._gas_limits}")

    # Submit transaction
    print("[DEBUG] Preparing to submit transaction for closing position...")
    order._submit_transaction(
        user_wallet_address=config.user_wallet_address,
        value_amount=order_parameters['initial_collateral_delta'],  # Collateral amount in Wei
        multicall_args=[
            # HexBytes(order._send_wnt(order_parameters['initial_collateral_delta'])),  # Ensure this matches value_amount
            # HexBytes(order._create_order((config.user_wallet_address,)))
        ],
        gas_limits=order._gas_limits
    )
    print(f"[DEBUG] Position closed. Long position: {is_long}, Size: {size_delta_usd} USD.")

def check_risk_management(is_long, entry_price, current_price, take_profit_percent, stop_loss_percent):
    """
    Check if the current price has hit take-profit or stop-loss levels.

    Parameters
    ----------
    is_long : bool
        True if the position is a long position, False if short.
    entry_price : float
        The price at which the position was entered.
    current_price : float
        The current market price of the asset.
    take_profit_percent : float
        The percentage increase (for long) or decrease (for short) to take profit.
    stop_loss_percent : float
        The percentage decrease (for long) or increase (for short) to trigger a stop loss.

    Returns
    -------
    str
        "take_profit" if the take-profit level is hit,
        "stop_loss" if the stop-loss level is hit,
        None if neither condition is met.
    """

    if is_long:
        # Long position: Check if current price exceeds take-profit or falls below stop-loss
        take_profit_price = entry_price * (1 + take_profit_percent / 100)
        stop_loss_price = entry_price * (1 - stop_loss_percent / 100)
        if current_price >= take_profit_price:
            return "take_profit"
        elif current_price <= stop_loss_price:
            return "stop_loss"
    else:
        # Short position: Check if current price falls below take-profit or rises above stop-loss
        take_profit_price = entry_price * (1 - take_profit_percent / 100)
        stop_loss_price = entry_price * (1 + stop_loss_percent / 100)
        if current_price <= take_profit_price:
            return "take_profit"
        elif current_price >= stop_loss_price:
            return "stop_loss"

    return None

def run_trading_bot():
    global current_position
    print("Starting trading bot...")
    current_position = 0
    current_position_value = 0  # Track the value of the current position
    entry_price = 0  # Track the entry price of the position

    while True:
        print("Running bot iteration...")

        # Update historical data and calculate signals
        historical_data = initialize_historical_data()
        latest_signal = generate_signals(historical_data, strategy)

        # Get wallet balance and calculate appropriate size_delta_usd for open/close
        wallet_balance_eth, wallet_balance_usd = get_wallet_balance()
        open_percentage = strategy["trade_settings"]["open_position_percentage"]
        close_percentage = strategy["trade_settings"]["close_position_percentage"]
        take_profit_percent = strategy["risk_management"]["take_profit_percent"]
        stop_loss_percent = strategy["risk_management"]["stop_loss_percent"]

        # Fetch current ETH price
        eth_price_usd = get_eth_to_usd_price()
        if eth_price_usd is None:
            print("Error fetching ETH price. Retrying in the next iteration.")
            time.sleep(60)
            continue

        # Check risk management for open positions
        if current_position != 0:
            risk_event = check_risk_management(
                is_long=(current_position == 1),
                entry_price=entry_price,
                current_price=eth_price_usd,
                take_profit_percent=take_profit_percent,
                stop_loss_percent=stop_loss_percent
            )

            if risk_event == "take_profit":
                print(f"Take profit hit! Closing position. Current Price: ${eth_price_usd}, Entry Price: ${entry_price}")
                size_delta_usd = calculate_close_position_amount(current_position_value, close_percentage)
                close_position(is_long=(current_position == 1), eth_price=eth_price_usd, size_delta_usd=size_delta_usd, percentage=0.01)
                current_position = 0
                current_position_value = 0  # Reset position value after closing
                print("Position closed after hitting take profit.")
                continue

            elif risk_event == "stop_loss":
                print(f"Stop loss hit! Closing position. Current Price: ${eth_price_usd}, Entry Price: ${entry_price}")
                size_delta_usd = calculate_close_position_amount(current_position_value, close_percentage)
                close_position(is_long=(current_position == 1), eth_price=eth_price_usd, size_delta_usd=size_delta_usd, percentage=0.01)
                current_position = 0
                current_position_value = 0  # Reset position value after closing
                print("Position closed after hitting stop loss.")
                continue

        # Open a Long Position
        if latest_signal['Position'] == 1 and current_position == 0:
            size_delta_usd = calculate_open_position_amount(wallet_balance_usd, open_percentage)
            print(f"Opening position with amount: ${size_delta_usd}")
            open_position(is_long=True, eth_price=eth_price_usd, leverage=5, size_delta_usd=size_delta_usd, percentage=0.01)
            current_position = 1
            current_position_value = size_delta_usd  # Track the initial position value
            entry_price = eth_price_usd  # Record entry price
            print(f"Long position opened with size {size_delta_usd} USD.")

        # Open a Short Position
        elif latest_signal['Position'] == -1 and current_position == 0:
            size_delta_usd = calculate_open_position_amount(wallet_balance_usd, open_percentage)
            print(f"Opening position with amount: ${size_delta_usd}")
            open_position(is_long=False, eth_price=eth_price_usd, leverage=5, size_delta_usd=size_delta_usd, percentage=0.01)
            current_position = -1
            current_position_value = size_delta_usd  # Track the initial position value
            entry_price = eth_price_usd  # Record entry price
            print(f"Short position opened with size {size_delta_usd} USD.")

        # Close Long Position
        elif current_position == 1 and latest_signal['Position'] == 0:
            size_delta_usd = calculate_close_position_amount(current_position_value, close_percentage)
            close_position(is_long=True, eth_price=eth_price_usd, size_delta_usd=size_delta_usd, percentage=0.01)
            current_position = 0
            current_position_value = 0  # Reset position value after closing
            print(f"Long position closed with size {size_delta_usd} USD.")

        # Close Short Position
        elif current_position == -1 and latest_signal['Position'] == 0:
            size_delta_usd = calculate_close_position_amount(current_position_value, close_percentage)
            close_position(is_long=False, eth_price=eth_price_usd, size_delta_usd=size_delta_usd, percentage=0.01)
            current_position = 0
            current_position_value = 0  # Reset position value after closing
            print(f"Short position closed with size {size_delta_usd} USD.")

        # Wait for the next iteration
        print("Sleeping for 5 minutes...")
        time.sleep(300)
        print("\n")
    
def main():    
    setup()
    # Run the trading bot
    run_trading_bot()
    
# Run the bot
if __name__ == "__main__":
    main()
    #run_trading_bot()
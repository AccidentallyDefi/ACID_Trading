# Download and extract TA-Lib libraries
print("Downloading and extracting TA-Lib libraries...")
url = 'https://anaconda.org/conda-forge/libta-lib/0.4.0/download/linux-64/libta-lib-0.4.0-h166bdaf_1.tar.bz2'
!curl -L $url | tar xj -C /usr/lib/x86_64-linux-gnu/ lib --strip-components=1
url = 'https://anaconda.org/conda-forge/ta-lib/0.4.19/download/linux-64/ta-lib-0.4.19-py310hde88566_4.tar.bz2'
!curl -L $url | tar xj -C /usr/local/lib/python3.10/dist-packages/ lib/python3.10/site-packages/talib --strip-components=3
print("TA-Lib libraries downloaded and extracted.")

from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager
from gmx_python_sdk.scripts.v2.order.create_increase_order import IncreaseOrder
from gmx_python_sdk.scripts.v2.order.create_decrease_order import DecreaseOrder
from gmx_python_sdk.scripts.v2.order.create_swap_order import SwapOrder
from get_gmx_stats import GetGMXv2Stats
from gmx_python_sdk.scripts.v2.order.order_argument_parser import OrderArgumentParser
import pandas as pd
import numpy as np
import talib as ta
import os
from datetime import datetime
import time
import yfinance as yf
from web3 import Web3
import requests
from dotenv import load_dotenv

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


# Modify the instantiation of GetGMXv2Stats with additional arguments
stats = GetGMXv2Stats(config, to_json=True, to_csv=False)  # Adjust these flags as needed
print("GetGMXv2Stats initialized.")

# Fetch max and min prices for ETH
def get_eth_prices(oracle_prices, symbol="ETH"):
    for entry_data in oracle_prices.values():
        if entry_data.get("tokenSymbol") == symbol:
            max_price = int(entry_data.get("maxPriceFull")) / 1e18  # Convert from Wei to Ether
            min_price = int(entry_data.get("minPriceFull")) / 1e18  # Convert from Wei to Ether
            return max_price, min_price
    return None, None  # Return None if the symbol is not found

# Fetch oracle prices
def fetch_market_data():
    oracle_prices = stats.get_oracle_prices()
    max_price, min_price = get_eth_prices(oracle_prices, "ETH")

    if max_price and min_price:
        print(f"Fetched Max Price for ETH: {max_price} ETH")
        print(f"Fetched Min Price for ETH: {min_price} ETH")
        # You might want to choose either max or min price depending on your logic
        eth_price = (max_price + min_price) / 2  # Take the average price as an example
        return eth_price
    else:
        print("ETH data not found in oracle prices.")
        return None

# Fetch available markets and inspect structure
markets = stats.get_available_markets()
#print("Markets data structure:", markets)  # Print the structure of markets for debugging

# Assuming markets is a dictionary where keys are addresses and values contain market details
try:
    eth_market = next((details for address, details in markets.items() if details.get("market_symbol") == "ETH"), None)
except AttributeError as e:
    print("Error accessing market details:", e)
    eth_market = None

if eth_market:
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
    print("ETH market not found in GMX markets.")
    exit()

# Function to get the ETH to USD conversion rate using CoinGecko's API
def get_eth_to_usd_price():
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
        print(f"Fetched ETH price from CoinGecko: ${eth_price_usd} USD.")
        return eth_price_usd
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred while fetching ETH price: {http_err}")
    except Exception as err:
        print(f"An error occurred while fetching ETH price: {err}")
    return None

# Function to fetch wallet balance in USD
def get_wallet_balance():
    try:
        #wallet_address = config.user_wallet_address
        print("Fetching balance for wallet address:", wallet_address)

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
        wallet_balance_usd = native_balance_eth * max_price_in_usd
        print(f"Wallet balance in USD: ${wallet_balance_usd:.2f}")
        return wallet_balance_usd

    except AttributeError as e:
        print("Error fetching balance or price from oracle:", e)
        return None
    except Exception as e:
        print(f"Error fetching wallet balance: {e}")
        return None


# Helper function to calculate size_delta_usd for opening position
def calculate_open_position_amount(wallet_balance, open_percentage):
    if wallet_balance is None:
        print("Error: Wallet balance is None. Skipping position calculation.")
        return None
    return wallet_balance * open_percentage

# Helper function to calculate size_delta_usd for closing position
def calculate_close_position_amount(current_position_value, close_percentage):
    if current_position_value is None:
        print("Error: Current position value is None. Skipping position calculation.")
        return None
    return current_position_value * (1 - close_percentage)

# Initialize historical data
def initialize_historical_data():
    print("Initializing historical data...")
    eth_data = yf.download("ETH-USD", period="1mo", interval="15m").tail(200)
    eth_data = eth_data.reset_index()[['Datetime', 'Close', 'Volume']]
    eth_data.columns = ['Timestamp', 'Close', 'Volume']

    # Calculate the moving average explicitly using .loc
    eth_data.loc[:, 'Volume_MA'] = ta.SMA(eth_data['Volume'], timeperiod=200)

    print("Historical data initialized.")
    return eth_data


# Generate trading signals based on RSI
def generate_signals(data):
    print("Generating RSI-based trading signals...")
    data['RSI'] = ta.RSI(data['Close'], timeperiod=14)
    data['Long'] = np.where(data['RSI'] < 41, 1, 0)
    data['Short'] = np.where(data['RSI'] > 60, -1, 0)
    data['Position'] = data['Long'] + data['Short']
    signal = data.iloc[-1]
    print(f"Generated signal - RSI: {signal['RSI']}, Position: {signal['Position']}")
    return signal

# Increase Position
def open_position(is_long, eth_price, leverage, size_delta_usd, percentage):
    if eth_price is None:
        print("Invalid ETH price; cannot open position.")
        return

    # Determine collateral and index token based on position type
    if is_long:
        collateral_address = COLLATERAL_ADDRESS  # Assume stablecoin (e.g., USDC) as collateral
        index_token_address = INDEX_TOKEN_ADDRESS  # ETH as the index token
    else:
        collateral_address = LONG_TOKEN_ADDRESS  # ETH as collateral
        index_token_address = SHORT_TOKEN_ADDRESS  # Stablecoin (e.g., USDC) as the index token

    print(f"Opening {'long' if is_long else 'short'} position...")

    # Initialize the order with parameters as per the Order class requirements
    order = IncreaseOrder(
        config=config,
        market_key=MARKET_KEY,
        collateral_address=collateral_address,
        index_token_address=index_token_address,
        is_long=is_long,
        size_delta=int(size_delta_usd * leverage * 1e30),
        initial_collateral_delta_amount=int(eth_price * 1e6 * percentage),  # Collateral in USD scaled
        slippage_percent=percentage,
        swap_path=[collateral_address, index_token_address],
        debug_mode=True  # Set to False to execute for real; True for simulation
    )

    # Call order_builder to set up the transaction details
    order.order_builder(is_open=True)  # Indicate this is an opening order

    # Fetch the gas limits using the determine_gas_limits method
    order.determine_gas_limits()  # This method should set self._gas_limits within the order instance

    # Assuming that `user_wallet_address` and `private_key` are set in the config
    user_wallet_address = wallet_address

    # Setting multicall_args based on the order details
    value_amount = int(eth_price * 1e6 * percentage)  # Value amount in Wei or smallest unit if needed
    multicall_args = [
        HexBytes(order._send_wnt(value_amount)),
        HexBytes(order._create_order((user_wallet_address,)))  # Replace with correct arguments if needed
    ]

    # Submit the transaction with dynamically fetched gas limits
    order._submit_transaction(
        user_wallet_address=user_wallet_address,
        value_amount=value_amount,
        multicall_args=multicall_args,
        gas_limits=order._gas_limits  # Uses the dynamically set gas limits
    )
    print(f"{'Long' if is_long else 'Short'} position opened.")



# Decrease Position
def close_position(is_long, eth_price, size_delta_usd, percentage):
    if eth_price is None:
        print("Invalid ETH price; cannot close position.")
        return

    # Determine collateral and index token based on position type
    if is_long:
        collateral_address = COLLATERAL_ADDRESS  # Assume stablecoin (e.g., USDC) as collateral
        index_token_address = INDEX_TOKEN_ADDRESS  # ETH as the index token
    else:
        collateral_address = LONG_TOKEN_ADDRESS  # ETH as collateral
        index_token_address = SHORT_TOKEN_ADDRESS  # Stablecoin (e.g., USDC) as the index token

    print(f"Closing {'long' if is_long else 'short'} position...")

    # Initialize the order with parameters as per the Order class requirements
    order = DecreaseOrder(
        config=config,
        market_key=MARKET_KEY,
        collateral_address=collateral_address,
        index_token_address=index_token_address,
        is_long=is_long,
        size_delta=int(size_delta_usd * 1e30),
        initial_collateral_delta_amount=int(eth_price * 1e6 * percentage),  # Collateral in USD scaled
        slippage_percent=percentage,
        swap_path=[index_token_address, collateral_address],
        debug_mode=True  # Set to False to execute for real; True for simulation
    )

    # Call order_builder to set up the transaction details
    order.order_builder(is_close=True)  # Indicate this is a closing order

    # Fetch the gas limits using the determine_gas_limits method
    order.determine_gas_limits()  # This method should set self._gas_limits within the order instance

    # Assuming that `user_wallet_address` and `private_key` are set in the config
    user_wallet_address = wallet_address

    # Setting multicall_args based on the order details
    value_amount = int(eth_price * 1e6 * percentage)  # Value amount in Wei or smallest unit if needed
    multicall_args = [
        HexBytes(order._send_wnt(value_amount)),
        HexBytes(order._create_order((user_wallet_address,)))  # Replace with correct arguments if needed
    ]

    # Submit the transaction with dynamically fetched gas limits
    order._submit_transaction(
        user_wallet_address=user_wallet_address,
        value_amount=value_amount,
        multicall_args=multicall_args,
        gas_limits=order._gas_limits  # Uses the dynamically set gas limits
    )
    print(f"{'Long' if is_long else 'Short'} position closed.")


# Main trading loop
def run_trading_bot():
    global current_position
    print("Starting trading bot...")
    historical_data = initialize_historical_data()
    current_position = 0
    current_position_value = 0  # Track the value of the current position

    while True:
        print("Running bot iteration...")
        eth_price = fetch_market_data()

        # Ensure eth_price is valid before continuing
        if eth_price is None:
            print("Error fetching market data. Retrying in 1 minute.")
            time.sleep(60)
            continue

        # Update historical data and calculate RSI signals
        latest_signal = generate_signals(historical_data)

        # Get wallet balance and calculate appropriate size_delta_usd for open/close
        wallet_balance_usd = get_wallet_balance()
        open_percentage = 0.1  # Example: Use 10% of wallet balance for opening positions
        close_percentage = 0.1  # Example: Close 90% of the current position, retaining 10%

        # Open a Long Position
        if latest_signal['Position'] == 1 and current_position == 0:
            size_delta_usd = calculate_open_position_amount(wallet_balance_usd, open_percentage)
            open_position(is_long=True, eth_price=eth_price, leverage=5, size_delta_usd=size_delta_usd, percentage=.01)
            current_position = 1
            current_position_value = size_delta_usd  # Track the initial position value
            print(f"Long position opened with size {size_delta_usd} USD.")

        # Open a Short Position
        elif latest_signal['Position'] == -1 and current_position == 0:
            size_delta_usd = calculate_open_position_amount(wallet_balance_usd, open_percentage)
            open_position(is_long=False, eth_price=eth_price, leverage=5, size_delta_usd=size_delta_usd, percentage=.01)
            current_position = -1
            current_position_value = size_delta_usd  # Track the initial position value
            print(f"Short position opened with size {size_delta_usd} USD.")

        # Close Long Position
        elif current_position == 1 and latest_signal['Position'] == 0:
            # Calculate size_delta_usd for closing the position
            size_delta_usd = calculate_close_position_amount(current_position_value, close_percentage)
            close_position(is_long=True, eth_price=eth_price, size_delta_usd=size_delta_usd, percentage=.01)
            current_position = 0
            current_position_value = 0  # Reset position value after closing
            print(f"Long position closed with size {size_delta_usd} USD.")

        # Close Short Position
        elif current_position == -1 and latest_signal['Position'] == 0:
            # Calculate size_delta_usd for closing the position
            size_delta_usd = calculate_close_position_amount(current_position_value, close_percentage)
            close_position(is_long=False, eth_price=eth_price, size_delta_usd=size_delta_usd, percentage=.01)
            current_position = 0
            current_position_value = 0  # Reset position value after closing
            print(f"Short position closed with size {size_delta_usd} USD.")

        # Wait for the next iteration
        print("Sleeping for 5 minutes...")
        time.sleep(300)
        print("\n")

# Run the bot
if __name__ == "__main__":
    run_trading_bot()
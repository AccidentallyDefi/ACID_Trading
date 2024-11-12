url = 'https://anaconda.org/conda-forge/libta-lib/0.4.0/download/linux-64/libta-lib-0.4.0-h166bdaf_1.tar.bz2'
!curl -L $url | tar xj -C /usr/lib/x86_64-linux-gnu/ lib --strip-components=1
url = 'https://anaconda.org/conda-forge/ta-lib/0.4.19/download/linux-64/ta-lib-0.4.19-py310hde88566_4.tar.bz2'
!curl -L $url | tar xj -C /usr/local/lib/python3.10/dist-packages/ lib/python3.10/site-packages/talib --strip-components=3
# Import the required libraries
import yfinance as yf  # Library for downloading historical data
import pandas as pd  # Library for data manipulation
import talib as ta  # Library for technical indicators like RSI, Bollinger Bands
import numpy as np  # Library for numerical operations
import matplotlib.pyplot as plt  # Library for plotting graphs

# Fetch historical data using yfinance
symbol = 'ETH-USD'  # You can change this to another asset (e.g., 'ETH-USD' or 'AAPL')
data = yf.download(symbol, start='2024-09-01', end='2024-10-12', interval='15m')

# Ensure there are no missing values in the dataset
data.dropna(inplace=True)

# Calculate Bollinger Bands
data['upperband'], data['middleband'], data['lowerband'] = ta.BBANDS(
    data['Close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

# Calculate RSI (Relative Strength Index)
data['RSI'] = ta.RSI(data['Close'], timeperiod=14)

# Calculate the 200-period moving average for volume
data['Volume_MA'] = ta.SMA(data['Volume'], timeperiod=200)

# Define the strategy: Long when price touches lower Bollinger Band, RSI < 20, and volume > 200-period MA
def apply_strategy(df):
    """
    This function applies the trading strategy to the given DataFrame.
    It sets conditions for entering long and short positions based on
    Bollinger Bands, RSI, and Volume.

    Parameters:
    df (pd.DataFrame): DataFrame containing historical price, volume, and technical indicators

    Returns:
    None
    """
    # Long condition: RSI < 20, price <= lower Bollinger Band, and volume > volume moving average
    df['Long'] = np.where(
        (df['RSI'] < 40) &
        (df['Close'] <= df['lowerband']) &
        (df['Volume'] > df['Volume_MA']),
        1,  # 1 indicates a Buy signal
        0   # 0 indicates no Buy signal
    )

    # Short condition: RSI > 80, price >= upper Bollinger Band, and volume > volume moving average
    df['Short'] = np.where(
        (df['RSI'] > 60) &
        (df['Close'] >= df['upperband']) &
        (df['Volume'] > df['Volume_MA']),
        -1,  # -1 indicates a Sell signal
        0    # 0 indicates no Sell signal
    )

    # Combine Long and Short signals into a single column
    df['Position'] = df['Long'] + df['Short']

    # Shift the position column to ensure trades are made AFTER the signal appears
    df['Position'] = df['Position'].shift(1)

# Apply the strategy to the data
apply_strategy(data)

# Plot the historical prices, Bollinger Bands, and the strategy signals (buy/sell)
plt.figure(figsize=(14, 8))
plt.plot(data.index, data['Close'], label='Close Price')
plt.plot(data.index, data['upperband'], label='Upper Bollinger Band', linestyle='--', color='red')
plt.plot(data.index, data['lowerband'], label='Lower Bollinger Band', linestyle='--', color='green')
plt.scatter(data.index[data['Position'] == 1], data['Close'][data['Position'] == 1], label='Buy Signal', marker='^', color='green', lw=3)
plt.scatter(data.index[data['Position'] == -1], data['Close'][data['Position'] == -1], label='Sell Signal', marker='v', color='red', lw=3)
plt.title(f"{symbol} Price and Bollinger Bands with Strategy Signals")
plt.legend()
plt.show()

# Backtest the strategy to evaluate its performance
initial_balance = 10000  # Initial balance in USD
balance = initial_balance
position = 0  # 1 = long, -1 = short, 0 = no position
entry_price = 0  # Entry price for the position

# Trade settings
leverage = 5  # Leverage to use for each trade (e.g., 5x)
trade_size_percentage = 0.1  # Use 10% of balance for each trade

# Loop through the historical data to simulate the trading strategy
for i, row in data.iterrows():
    # Determine how much of the balance is used for each trade
    trade_size = balance * trade_size_percentage  # Use 10% of balance
    position_size = trade_size * leverage  # Apply leverage to the trade size

    if row['Position'] == 1 and position == 0:
        # Enter a long position if currently not in any position
        position = 1
        entry_price = row['Close']
        print(f"Entering long with {position_size} at {entry_price} on {i}")

    elif row['Position'] == -1 and position == 0:
        # Enter a short position if currently not in any position
        position = -1
        entry_price = row['Close']
        print(f"Entering short with {position_size} at {entry_price} on {i}")

    elif position == 1 and row['Position'] == 0:
        # Exit the long position if a sell signal appears
        profit = (row['Close'] - entry_price) * position_size / entry_price  # Calculate profit from leveraged position
        balance += profit
        print(f"Exiting long at {row['Close']} on {i}, Profit: {profit}, New Balance: {balance}")
        position = 0

    elif position == -1 and row['Position'] == 0:
        # Exit the short position if a buy signal appears
        profit = (entry_price - row['Close']) * position_size / entry_price  # Calculate profit from leveraged position
        balance += profit
        print(f"Exiting short at {row['Close']} on {i}, Profit: {profit}, New Balance: {balance}")
        position = 0

# Print final balance and performance metrics
profit_percent = ((balance - initial_balance) / initial_balance) * 100
print(f"Initial Balance: ${initial_balance}")
print(f"Final Balance: ${balance}")
print(f"Total Profit: {profit_percent:.2f}%")
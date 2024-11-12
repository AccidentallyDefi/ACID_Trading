# ACID Trading Bot

This project is a GMX trading bot designed to automate trades on the GMX platform using market data and signals derived from technical analysis indicators. The bot leverages RSI (Relative Strength Index) and Oracle price data to open and close positions for Ethereum (ETH) on the Arbitrum network. This README provides detailed setup instructions, usage guidance, and security recommendations.

---

## Table of Contents
1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Environment Configuration](#environment-configuration)
5. [Running the Bot](#running-the-bot)
6. [Technical Details](#technical-details)
7. [Security Considerations](#security-considerations)
8. [Troubleshooting](#troubleshooting)

---

## Features

- **Automated Trading on GMX:** Opens and closes long and short positions based on RSI signals.
- **ETH Price Fetching:** Uses Oracle price data and CoinGecko API for ETH-USD conversion.
- **Risk Management:** Configurable position size and leverage based on wallet balance.
- **Customizable Technical Indicators:** Supports RSI-based trading signals, with flexibility to integrate additional indicators.

## Requirements

- **Operating System:** Linux, macOS, or Windows
- **Python Version:** 3.8+
- **Dependencies:** Listed in `requirements.txt`

## Installation

1. **Clone the Repository**

   ```bash
   git clone <repo-url>
   cd trading-bot
   ```

2. **Set Up the Python Environment**

   - It is recommended to use a virtual environment:
   
     ```bash
     python3 -m venv venv
     source venv/bin/activate   # On Windows use `venv\Scripts\activate`
     ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Download and Extract TA-Lib (Technical Analysis Library)**

   **Note:** The following commands are for Linux. For Windows, see [TA-Lib Installation](https://mrjbq7.github.io/ta-lib/install.html).

   ```python
   # Download and extract the TA-Lib library files
   url = 'https://anaconda.org/conda-forge/libta-lib/0.4.0/download/linux-64/libta-lib-0.4.0-h166bdaf_1.tar.bz2'
   !curl -L $url | tar xj -C /usr/lib/x86_64-linux-gnu/ lib --strip-components=1
   url = 'https://anaconda.org/conda-forge/ta-lib/0.4.19/download/linux-64/ta-lib-0.4.19-py310hde88566_4.tar.bz2'
   !curl -L $url | tar xj -C /usr/local/lib/python3.10/dist-packages/ lib/python3.10/site-packages/talib --strip-components=3
   ```

5. **Install Web3 for Blockchain Interactions**

   ```bash
   pip install web3
   ```

## Environment Configuration

To protect sensitive information like wallet addresses, private keys, and API keys, use environment variables:

1. **Create a `.env` File**

   In the root directory, create a `.env` file with the following structure:

   ```plaintext
   RPC_URL=https://your-arbitrum-rpc-url
   PRIVATE_KEY=your-private-key
   WALLET_ADDRESS=your-wallet-address
   ```

2. **Set Up Environment Variables**

   - Load the environment variables in the bot script using `dotenv`:

     ```python
     from dotenv import load_dotenv
     load_dotenv()
     ```

3. **Update Configuration Files**

   Update `config.yaml` or other configuration files as necessary, using the environment variables where applicable.

## Running the Bot

1. **Start the Bot**

   To run the bot, simply execute:

   ```bash
   python trading_bot.py
   ```

   This will start an infinite loop where the bot fetches market data, analyzes it, and opens/closes positions based on RSI signals.

2. **Command-Line Arguments**

   You may add command-line arguments to modify the bot’s behavior (e.g., changing the trading interval or adjusting the position size). Update `OrderArgumentParser` to accept custom arguments.

## Technical Details

### 1. **RSI-Based Signal Generation**

   The bot uses the 14-period RSI indicator to generate trade signals:
   - **Long Signal**: Opens a position when RSI < 41.
   - **Short Signal**: Opens a position when RSI > 60.
   - **Neutral Signal**: Closes the position when RSI moves back to the middle range.

### 2. **Price Fetching**
   - **Oracle Prices**: Uses GMX’s Oracle data to fetch max and min prices for ETH.
   - **USD Conversion**: Uses CoinGecko’s API to get ETH-USD conversion rates, which are used to calculate the USD value of wallet balances.

### 3. **Position Management**
   - **Position Size**: Dynamically calculated as a percentage of the wallet balance.
   - **Leverage**: Configurable, allowing for higher exposure.
   - **Execution**: Uses `IncreaseOrder` and `DecreaseOrder` from the GMX Python SDK to submit orders.

### 4. **Error Handling**
   - Includes error handling for failed API requests, unavailable data, and Web3 connection issues.

## Security Considerations

1. **Never Hardcode Private Keys**: Always load keys from environment variables or secure vaults.
2. **Set `.gitignore`**:
   - Add `.env` and `config.yaml` to `.gitignore` to prevent accidental commits.
3. **Use Debug Mode for Testing**: Run the bot in debug mode (if supported) to simulate trades before deploying with real funds.

## Troubleshooting

1. **Web3 Connection Issues**:
   - Ensure the `RPC_URL` is correct and the Arbitrum node is responsive.

2. **TA-Lib Not Found**:
   - Verify the correct installation of TA-Lib for your platform (Linux, macOS, or Windows).

3. **CoinGecko API Rate Limits**:
   - CoinGecko imposes rate limits. Minimize API calls by caching the ETH price if possible.

4. **Bot Stops Unexpectedly**:
   - Check for Python exceptions or network issues, especially if running over a long period. Add retry logic as needed.

---

## Contributing

Contributions are welcome! If you find bugs, have feature requests, or want to improve the code, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

### Disclaimer

This bot is intended for educational purposes only. Trading and investment in cryptocurrencies carry significant risk. The authors are not responsible for any financial losses incurred. Always trade responsibly.

# ACID Trading Bot

## Overview

The **ACID Trading Bot** is a Python-based automated trading solution designed to interact with the GMX decentralized exchange on the **Arbitrum blockchain**. It leverages popular technical indicators such as **Bollinger Bands**, **RSI**, and **Volume Moving Averages** to generate trading signals and execute trades.

This bot allows users to define their custom trading strategies via a YAML configuration file (`strategy.yaml`), making it flexible and adaptable to a variety of trading approaches.

---

## Features

- **Technical Indicators**:
  - **Bollinger Bands** for detecting price volatility.
  - **RSI (Relative Strength Index)** for gauging market momentum.
  - **Volume Moving Average** for confirming trends.
- **Automated Trade Execution**:
  - Opens and closes long or short positions on GMX based on trading signals.
- **Customizable Trading Strategy**:
  - Fully configurable through `strategy.yaml`.
- **Risk Management**:
  - Configurable **take-profit** and **stop-loss** levels.
- **Blockchain Integration**:
  - Powered by **Web3**, ensuring smooth interaction with the Arbitrum blockchain.

---

## File Structure

```
ACID_Trading/
├── scripts/
│   ├── acid_bot.py         # Main trading bot script
│   ├── backtest.py         # Backtesting utility script
│   ├── get_gmx_stats.py    # GMX statistics fetching utility
│   ├── utils.py            # Utility functions for configuration and setup
│   └── __init__.py         # Module initializer
├── utils/
│   ├── config.yaml         # Configuration file (RPC, wallet details, etc.)
│   ├── strategy.yaml       # Strategy configuration file (technical indicators)
│   ├── token_approval.json # Token contract ABI for approvals
├── LICENSE                 # Project license
└── README.md               # Project documentation
```

---

## Getting Started

### Step 1: Clone the Repository

Begin by cloning the repository:

```bash
git clone https://github.com/your-username/ACID_Trading.git
cd ACID_Trading
```

---

### Step 2: Install Dependencies

Install all required Python packages by running:

```bash
pip install -r requirements.txt
```

If you encounter issues installing **TA-Lib**, you can download the necessary binaries for your operating system and run:

```bash
python -c "from utils import download_ta_lib; download_ta_lib()"
```

---

### Step 3: Configure the Bot

#### 1. **Configuration File (`config.yaml`)**

Update the `utils/config.yaml` file with your RPC endpoint and wallet details:

```yaml
rpc: "https://arb1.arbitrum.io/rpc"
private_key: "your-wallet-private-key"
user_wallet_address: "your-wallet-address"
chain_id: 42161
```

- Replace `"your-wallet-private-key"` and `"your-wallet-address"` with your wallet information.
- Ensure the RPC URL is correct for the Arbitrum network.

---

#### 2. **Strategy File (`strategy.yaml`)**

Define your trading strategy in `utils/strategy.yaml`. Below is the structure of the file with descriptions of each parameter:

```yaml
strategy:
  bollinger_bands:
    length: {INTEGER NUMBER, WHOLE NUMBER}            # Length of the Bollinger Bands moving average (e.g., 20)
    multiplier: {PERCENTAGE * 100, EX: 1.0 FOR 1%}    # Multiplier for the Bollinger Bands (e.g., 2.0)

  rsi:
    length: {INTEGER NUMBER, WHOLE NUMBER}            # RSI look-back period (e.g., 14)
    overbought: {INTEGER NUMBER, WHOLE NUMBER}        # RSI value indicating overbought conditions (e.g., 70)
    oversold: {INTEGER NUMBER, WHOLE NUMBER}          # RSI value indicating oversold conditions (e.g., 30)

  volume:
    moving_avg_length: {INTEGER NUMBER, WHOLE NUMBER} # Period for the Volume Moving Average (e.g., 50)

  risk_management:
    take_profit_percent: {PERCENTAGE * 100, EX: 1.0 FOR 1%}  # Percentage to take profit (e.g., 10 for 10%)
    stop_loss_percent: {PERCENTAGE * 100, EX: 1.0 FOR 1%}    # Percentage to stop loss (e.g., 5 for 5%)

  trade_settings:
    open_position_percentage: {PERCENTAGE * 100, EX: 1.0 FOR 1%}  # Percentage of wallet balance for opening positions (e.g., 0.1 for 10%)
    close_position_percentage: {PERCENTAGE * 100, EX: 1.0 FOR 1%} # Percentage of the current position for closing (e.g., 0.9 for 90%)
```

---

## Running the Bot

The main script is `acid_bot.py` located in the `scripts/` folder. To start the bot, run the following command:

```bash
python scripts/acid_bot.py --config utils/config.yaml --strategy utils/strategy.yaml
```

### Command-Line Arguments

- `--config`: Path to the configuration YAML file (default: `utils/config.yaml`).
- `--strategy`: Path to the strategy YAML file (default: `utils/strategy.yaml`).

---

## How It Works

1. **Setup**:
   - Reads `config.yaml` and connects to the Arbitrum blockchain.
   - Loads the trading strategy from `strategy.yaml`.

2. **Signal Generation**:
   - Fetches historical price and volume data for **ETH-USD** using Yahoo Finance.
   - Computes Bollinger Bands, RSI, and Volume indicators.
   - Generates trading signals based on the strategy.

3. **Trade Execution**:
   - Opens **long** or **short** positions when signals are triggered.
   - Monitors open positions for **take-profit** or **stop-loss** conditions.
   - Closes positions automatically when thresholds are met.

4. **Continuous Loop**:
   - Runs every 5 minutes to fetch new data, generate signals, and manage trades.

---

## Example Outputs

### 1. Signal Generation

```
[DEBUG] Latest Signal: RSI=45.2, Position=1 (LONG)
```

### 2. Trade Execution

```
[DEBUG] Opening Long Position: Size=0.1 ETH, Leverage=5x
[DEBUG] Transaction Hash: 0xabc123...
```

### 3. Position Closure

```
[DEBUG] Stop Loss Triggered. Closing Position.
[DEBUG] Position Closed. Transaction Hash: 0xdef456...
```

---

## Troubleshooting

### Common Issues

1. **TA-Lib Installation Issues**:
   - Ensure you have the required dependencies installed. For Ubuntu:
     ```bash
     sudo apt-get install build-essential libta-lib0-dev
     ```

2. **RPC Connection Issues**:
   - Verify the `rpc` URL in `config.yaml`. It should point to the Arbitrum network:
     ```yaml
     rpc: "https://arb1.arbitrum.io/rpc"
     ```

3. **Insufficient Gas**:
   - Ensure your wallet has sufficient ETH for gas fees on the Arbitrum network.

---

## Backtesting

The `backtest.py` script allows you to test your strategy on historical data:

```bash
python scripts/backtest.py
```

---

## Contributing

We welcome contributions! Follow these steps:

1. Fork the repository.
2. Create a new branch (`feature/your-feature-name`).
3. Submit a pull request.

---

## License

This project is licensed under the **Apache 2.0 License**. See the `LICENSE` file for details.

---

## Contact

Created by **AccidentallyDeFi**  
For support or inquiries, email: `your-email@example.com`.

# Strategy Backtester

A modular Streamlit web application for backtesting trading strategies using the `backtesting.py` library.

## Features

- **CSV File Upload**: Upload OHLCV data in standard format
- **Modular Strategy System**: Easy to add new strategies without touching the main app
- **Multiple Trade Modes**: Only_Buy, Only_Sell, or Both_Buy_Sell
- **Comprehensive Results**: Summary statistics, trade details, and equity curves
- **Data Export**: Download trade results as CSV

## Setup

### Prerequisites
- Python 3.10 or higher

### Installation
1. Create virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate virtual environment:
   - **Windows**: `.venv\Scripts\activate`
   - **Linux/Mac**: `source .venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   streamlit run app.py
   ```

## CSV Format Requirements

Your CSV file must contain the following columns:
- `date`: Date and time in format `DD-MM-YYYY HH:MM`
- `open`: Opening price
- `high`: High price
- `low`: Low price
- `close`: Closing price
- `volume`: Trading volume

Example:
```csv
date,open,high,low,close,volume
01-01-2023 09:00,100.0,101.0,99.0,100.5,1000
01-01-2023 09:01,100.5,102.0,100.0,101.5,1200
```

## Available Strategies

### EMA Crossover
- **Fast EMA**: Shorter period moving average
- **Slow EMA**: Longer period moving average
- **Signal**: Buy when fast EMA crosses above slow EMA, sell when fast EMA crosses below slow EMA

## Trade Modes

1. **Only_Buy**: Take long positions only, exit on sell signals
2. **Only_Sell**: Take short positions only, exit on buy signals  
3. **Both_Buy_Sell**: Flip between long and short positions

## Adding New Strategies

To add a new strategy:

1. Create a new file in the `strategies/` directory (e.g., `rsi_strategy.py`)
2. Implement the `StrategyAdapter` interface:
   ```python
   class RSIStrategyAdapter(StrategyAdapter):
       name = "RSI Strategy"
       params_schema = {
           "rsi_period": {"type": "int", "default": 14, "min": 1, "max": 100},
           "oversold": {"type": "float", "default": 30.0, "min": 0.0, "max": 100.0},
           "overbought": {"type": "float", "default": 70.0, "min": 0.0, "max": 100.0}
       }
       
       def get_bt_strategy_class(self):
           return RSIStrategy
   ```

3. Create the backtesting.py Strategy class:
   ```python
   class RSIStrategy(Strategy):
       rsi_period = 14
       oversold = 30
       overbought = 70
       
       def init(self):
           # Strategy logic here
           pass
   ```

4. Register the strategy in `core/registry.py`:
   ```python
   from strategies.rsi_strategy import RSIStrategyAdapter
   
   # In the register_default_strategies function
   registry.register(RSIStrategyAdapter())
   ```

## Project Structure

```
backtester/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .streamlit/
│   └── config.toml      # Streamlit configuration
├── core/
│   ├── strategy_base.py  # Base classes and interfaces
│   └── registry.py       # Strategy registry
├── strategies/
│   └── ema_crossover.py # EMA Crossover strategy
└── utils/
    ├── io_utils.py       # CSV loading and validation
    └── ui_utils.py       # Streamlit UI helpers
```

## Usage

1. Upload your OHLCV CSV file
2. Select a strategy from the dropdown
3. Configure strategy parameters
4. Choose your trade mode
5. Click "Run Backtest"
6. View results and download trade data

## Troubleshooting

- **CSV Error**: Ensure your CSV has the correct column names and date format
- **Strategy Error**: Check that all required parameters are within valid ranges
- **Memory Error**: Try using smaller datasets or reduce the date range

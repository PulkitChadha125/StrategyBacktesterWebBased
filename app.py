import streamlit as st
import pandas as pd
import numpy as np
from backtesting import Backtest

import io

# Import our modules
from core.registry import registry
from core.strategy_base import StrategyConfig
from utils.io_utils import load_and_validate_csv, prepare_data_for_backtest
from utils.ui_utils import (
    create_strategy_selector, create_parameter_inputs, create_trade_mode_selector,
    display_summary_stats, display_trades_table, display_equity_curve,
    show_error_message, show_success_message, show_info_message
)


# Page configuration
st.set_page_config(
    page_title="Strategy Backtester",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)





def run_backtest(data, strategy_name, params, trade_mode, initial_cash, indicator_engine):
    """Run the backtest with the specified parameters."""
    try:
        strategy_adapter = registry.get(strategy_name)
        if not strategy_adapter:
            raise ValueError(f"Strategy '{strategy_name}' not found")

        if not strategy_adapter.validate_params(params):
            raise ValueError("Invalid strategy parameters")

        # extra guard
        if int(params.get("fast_ema", 12)) >= int(params.get("slow_ema", 26)):
            raise ValueError("Fast EMA must be smaller than Slow EMA.")

        StrategyClass = strategy_adapter.get_bt_strategy_class()

        bt = Backtest(
            data,
            StrategyClass,
            cash=float(initial_cash),   # Use user-defined cash value
            commission=0.001,
            exclusive_orders=True,
        )

        # Build run kwargs for strategy params
        run_kwargs = dict(
            fast_ema=int(params["fast_ema"]),
            slow_ema=int(params["slow_ema"]),
            trade_mode=trade_mode,
            indicator_engine=indicator_engine,   # pass engine to Strategy
        )

        results = bt.run(**run_kwargs)
        return results, bt

    except Exception as e:
        raise Exception(f"Backtest failed: {str(e)}")


def main():
    """Main application function."""
    
    # Header
    st.markdown('<h1 class="main-header">📈 Strategy Backtester</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown('<h2 class="sidebar-header">⚙️ Configuration</h2>', unsafe_allow_html=True)
        
        # File upload
        st.subheader("📁 Data Upload")
        uploaded_file = st.file_uploader(
            "Upload OHLCV CSV file",
            type=['csv'],
            help="Upload a CSV file with columns: date, open, high, low, close, volume"
        )
        
        # Strategy selection
        st.subheader("🎯 Strategy")
        available_strategies = registry.list_all()
        selected_strategy = create_strategy_selector(available_strategies)
        
        # Parameter inputs
        if selected_strategy:
            strategy_adapter = registry.get(selected_strategy)
            st.subheader("🔧 Parameters")
            params = create_parameter_inputs(strategy_adapter)
            
            # Initial Balance input
            st.subheader("💰 Initial Balance")
            initial_cash = st.number_input(
                "Initial Balance (Cash)",
                min_value=1000,
                max_value=1_000_000_000,
                value=100000,
                step=1000,
                help="Starting equity for the backtest"
            )
            
            # Indicator Engine selection
            st.subheader("⚙️ Indicator Engine")
            indicator_engine = st.selectbox(
                "Indicator Engine",
                options=["pandas", "TA-Lib"],
                index=0,
                help="Use pandas (portable) or TA-Lib (fast, requires native library) for EMA"
            )
            
            # Trade mode selection
            st.subheader("💼 Trade Mode")
            trade_mode = create_trade_mode_selector()
            
            # Run button
            st.markdown("---")
            run_button = st.button("🚀 Run Backtest", type="primary", use_container_width=True)
        else:
            params = {}
            trade_mode = None
            initial_cash = 100000
            indicator_engine = "pandas"
            run_button = False
    
    # Main content area
    if uploaded_file is not None:
        try:
            # Load and validate CSV
            with st.spinner("Loading and validating CSV data..."):
                data, error_msg = load_and_validate_csv(uploaded_file)
                
                if error_msg:
                    show_error_message(error_msg)
                    return
                
                if data is None:
                    show_error_message("Failed to load CSV data")
                    return
            
            # Show data preview
            st.subheader("📊 Data Preview")
            st.write(f"**Dataset:** {len(data)} rows from {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**First 5 rows:**")
                st.dataframe(data.head(), use_container_width=True)
            
            with col2:
                st.write("**Data Info:**")
                buffer = io.StringIO()
                data.info(buf=buffer)
                st.text(buffer.getvalue())
            
            # Run backtest if button is clicked
            if run_button and selected_strategy and params and trade_mode:
                try:
                    with st.spinner("Running backtest..."):
                        # Prepare data for backtesting
                        backtest_data = prepare_data_for_backtest(data)
                        
                        # Run the backtest
                        results, bt = run_backtest(backtest_data, selected_strategy, params, trade_mode, initial_cash, indicator_engine)
                        
                        # Display results
                        st.markdown("---")
                        st.subheader("🎯 Backtest Results")
                        
                        # Summary statistics
                        display_summary_stats(results)
                        
                        # Trades table with explicit DataFrame checks to avoid truthiness ambiguity
                        trades = getattr(results, "_trades", None)
                        if isinstance(trades, pd.DataFrame) and not trades.empty:
                            trades = trades.copy()

                            # Add EntryType based on Size (verified on sample CSV: Size>0 → Long, Size<0 → Short)
                            if "Size" in trades.columns:
                                trades["EntryType"] = np.where(trades["Size"] > 0, "Long", "Short")
                            else:
                                trades["EntryType"] = "Long"  # fallback; should not happen if Size exists

                            # Optional: reorder columns to surface EntryType early
                            preferred_order = [
                                "EntryTime", "ExitTime", "EntryType", "Size",
                                "EntryPrice", "ExitPrice", "PnL", "ReturnPct", "Commission",
                                "Duration", "SL", "TP", "Tag"
                            ]
                            rest = [c for c in trades.columns if c not in preferred_order]
                            trades = trades[[c for c in preferred_order if c in trades.columns] + rest]

                            # Show table and provide download
                            display_trades_table(trades)
                            
                            # Add Download Trades CSV button right below the table
                            csv_bytes = trades.to_csv(index=False).encode("utf-8")
                            st.download_button(
                                label="📥 Download Trades CSV",
                                data=csv_bytes,
                                file_name="trades_backtest.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        else:
                            st.info("No trades were executed during the backtest period.")
                        
                        # Equity curve with explicit DataFrame checks
                        equity = getattr(bt, "_equity_curve", None)
                        if isinstance(equity, (pd.Series, pd.DataFrame)) and len(equity) > 0:
                            equity_df = pd.DataFrame({"Equity": equity})
                            display_equity_curve(equity_df)
                        
                        show_success_message("Backtest completed successfully!")
                        
                        # If user selected TA-Lib but it's not installed, show a one-time warning after the run
                        # (Strategy falls back automatically; we surface UX feedback here.)
                        if indicator_engine == "TA-Lib":
                            try:
                                import talib  # noqa
                            except Exception:
                                st.warning("TA-Lib not found in this environment. Fell back to pandas EMA.", icon="⚠️")
                        
                except Exception as e:
                    show_error_message(str(e))
                    st.error(f"Backtest failed: {str(e)}")
                    
        except Exception as e:
            show_error_message(f"Error processing file: {str(e)}")
    
    else:
        # Welcome message and instructions
        st.subheader("🚀 Welcome to Strategy Backtester!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **How to get started:**
            
            1. **Upload Data**: Use the sidebar to upload your OHLCV CSV file
            2. **Select Strategy**: Choose from available trading strategies
            3. **Configure Parameters**: Adjust strategy-specific parameters
            4. **Choose Trade Mode**: Select how to handle buy/sell signals
            5. **Run Backtest**: Click the run button to execute the backtest
            6. **Analyze Results**: View statistics, trades, and equity curves
            """)
        
        with col2:
            st.markdown("""
            **CSV Format Requirements:**
            
            Your CSV must contain these columns:
            - `date`: Date/time in DD-MM-YYYY HH:MM format
            - `open`: Opening price
            - `high`: High price  
            - `low`: Low price
            - `close`: Closing price
            - `volume`: Trading volume
            
            **Available Strategies:**
            - **EMA Crossover**: Fast vs Slow Exponential Moving Average
            """)
        
        # Example data
        st.subheader("📋 Example CSV Format")
        example_data = pd.DataFrame({
            'date': ['01-01-2023 09:00', '01-01-2023 09:01', '01-01-2023 09:02'],
            'open': [100.0, 100.5, 101.0],
            'high': [101.0, 102.0, 102.5],
            'low': [99.0, 100.0, 100.5],
            'close': [100.5, 101.5, 102.0],
            'volume': [1000, 1200, 1100]
        })
        st.dataframe(example_data, use_container_width=True)
        
        # Download example
        csv = example_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Example CSV",
            data=csv,
            file_name="example_ohlcv.csv",
            mime="text/csv"
        )


if __name__ == "__main__":
    main()

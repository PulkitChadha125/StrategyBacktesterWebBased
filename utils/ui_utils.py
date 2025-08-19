import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from core.strategy_base import StrategyAdapter


def create_strategy_selector(strategies: List[str], default_strategy: str = None) -> str:
    """Create a strategy selector dropdown."""
    if not strategies:
        st.error("No strategies available")
        return None
    
    if default_strategy is None:
        default_strategy = strategies[0]
    
    selected_strategy = st.selectbox(
        "Select Strategy",
        options=strategies,
        index=strategies.index(default_strategy) if default_strategy in strategies else 0,
        help="Choose the trading strategy to backtest"
    )
    
    return selected_strategy


def create_parameter_inputs(strategy: StrategyAdapter, current_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create dynamic parameter input fields based on strategy schema."""
    if current_params is None:
        current_params = strategy.get_default_params()
    
    params = {}
    
    for param_name, param_info in strategy.params_schema.items():
        param_type = param_info["type"]
        default_value = current_params.get(param_name, param_info.get("default"))
        description = param_info.get("description", param_name.replace("_", " ").title())
        
        if param_type == "int":
            min_val = param_info.get("min", 0)
            max_val = param_info.get("max", 1000)
            params[param_name] = st.number_input(
                description,
                min_value=min_val,
                max_value=max_val,
                value=default_value,
                step=1,
                help=f"Enter {description.lower()} (range: {min_val}-{max_val})"
            )
        elif param_type == "float":
            min_val = param_info.get("min", 0.0)
            max_val = param_info.get("max", 1000.0)
            step = param_info.get("step", 0.1)
            params[param_name] = st.number_input(
                description,
                min_value=min_val,
                max_value=max_val,
                value=float(default_value) if default_value is not None else 0.0,
                step=step,
                format="%.2f",
                help=f"Enter {description.lower()} (range: {min_val}-{max_val})"
            )
        elif param_type == "str":
            options = param_info.get("options", [])
            if options:
                params[param_name] = st.selectbox(
                    description,
                    options=options,
                    index=options.index(default_value) if default_value in options else 0
                )
            else:
                params[param_name] = st.text_input(
                    description,
                    value=default_value or "",
                    help=f"Enter {description.lower()}"
                )
    
    return params


def create_trade_mode_selector() -> str:
    """Create a trade mode selector."""
    trade_modes = {
        "Only_Buy": "Only Buy - Take long positions only",
        "Only_Sell": "Only Sell - Take short positions only", 
        "Both_Buy_Sell": "Both Buy & Sell - Flip between long and short"
    }
    
    selected_mode = st.selectbox(
        "Trade Mode",
        options=list(trade_modes.keys()),
        format_func=lambda x: trade_modes[x],
        help="Choose how the strategy should handle buy/sell signals"
    )
    
    return selected_mode


def display_summary_stats(stats: Dict[str, Any]) -> None:
    """Display backtest summary statistics."""
    st.subheader("📊 Backtest Summary")
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Return", f"{stats.get('Return [%]', 0):.2f}%")
        st.metric("Buy & Hold Return", f"{stats.get('Buy & Hold Return [%]', 0):.2f}%")
    
    with col2:
        st.metric("Max Drawdown", f"{stats.get('Max. Drawdown [%]', 0):.2f}%")
        st.metric("Sharpe Ratio", f"{stats.get('Sharpe Ratio', 0):.2f}")
    
    with col3:
        st.metric("Total Trades", stats.get('# Trades', 0))
        st.metric("Win Rate", f"{stats.get('Win Rate [%]', 0):.1f}%")
    
    with col4:
        st.metric("Profit Factor", f"{stats.get('Profit Factor', 0):.2f}")
        st.metric("Avg. Trade", f"{stats.get('Avg. Trade', 0):.2f}")
    
    # Additional details
    st.subheader("📈 Performance Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Start Date:** {stats.get('Start', 'N/A')}")
        st.write(f"**End Date:** {stats.get('End', 'N/A')}")
        st.write(f"**Duration:** {stats.get('Duration', 'N/A')}")
        st.write(f"**Exposure Time:** {stats.get('Exposure Time [%]', 0):.1f}%")
    
    with col2:
        st.write(f"**Best Trade:** {stats.get('Best Trade [%]', 0):.2f}%")
        st.write(f"**Worst Trade:** {stats.get('Worst Trade [%]', 0):.2f}%")
        st.write(f"**Avg. Win:** {stats.get('Avg. Win', 0):.2f}")
        st.write(f"**Avg. Loss:** {stats.get('Avg. Loss', 0):.2f}")


def display_trades_table(trades_df: pd.DataFrame) -> None:
    """Display trades table with download functionality."""
    st.subheader("📋 Trade Details")
    
    if trades_df.empty:
        st.info("No trades were executed during the backtest period.")
        return
    
    # Format the trades dataframe for display
    display_df = trades_df.copy()
    
    # Format percentage columns
    if 'PnL [%]' in display_df.columns:
        display_df['PnL [%]'] = display_df['PnL [%]'].apply(lambda x: f"{x:.2f}%")
    
    # Format datetime columns
    datetime_columns = ['Entry Time', 'Exit Time']
    for col in datetime_columns:
        if col in display_df.columns:
            display_df[col] = pd.to_datetime(display_df[col]).dt.strftime('%Y-%m-%d %H:%M')
    
    # Display the table
    st.dataframe(display_df, use_container_width=True)
    
    # Download button
    csv = trades_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Trades CSV",
        data=csv,
        file_name="trades_backtest.csv",
        mime="text/csv"
    )


def display_equity_curve(equity_curve: pd.DataFrame) -> None:
    """Display the equity curve plot."""
    st.subheader("📈 Equity Curve")
    
    if equity_curve.empty:
        st.info("No equity curve data available.")
        return
    
    # Create the plot
    st.line_chart(equity_curve)
    
    # Show some statistics about the equity curve
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Peak Value", f"${equity_curve['Equity'].max():.2f}")
    
    with col2:
        st.metric("Final Value", f"${equity_curve['Equity'].iloc[-1]:.2f}")
    
    with col3:
        st.metric("Total Change", f"${equity_curve['Equity'].iloc[-1] - equity_curve['Equity'].iloc[0]:.2f}")


def show_error_message(error_msg: str) -> None:
    """Display an error message in a user-friendly way."""
    st.error(f"❌ Error: {error_msg}")
    st.info("Please check your data and try again.")


def show_success_message(message: str) -> None:
    """Display a success message."""
    st.success(f"✅ {message}")


def show_info_message(message: str) -> None:
    """Display an info message."""
    st.info(f"ℹ️ {message}")

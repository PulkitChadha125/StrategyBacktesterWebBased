import pandas as pd
from typing import Tuple, Optional
import streamlit as st


def validate_csv_columns(df: pd.DataFrame) -> Tuple[bool, str]:
    """Validate that CSV has required columns."""
    required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"
    
    return True, ""


def parse_date_column(df: pd.DataFrame) -> Tuple[bool, str]:
    """Parse and validate the date column."""
    try:
        # Try different date formats
        date_formats = [
            '%d-%m-%Y %H:%M',
            '%d/%m/%Y %H:%M',
            '%Y-%m-%d %H:%M',
            '%Y/%m/%d %H:%M',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%Y/%m/%d'
        ]
        
        date_parsed = False
        for fmt in date_formats:
            try:
                df['date'] = pd.to_datetime(df['date'], format=fmt)
                date_parsed = True
                break
            except ValueError:
                continue
        
        if not date_parsed:
            # Try automatic parsing
            df['date'] = pd.to_datetime(df['date'])
        
        return True, ""
    except Exception as e:
        return False, f"Error parsing date column: {str(e)}"


def validate_numeric_columns(df: pd.DataFrame) -> Tuple[bool, str]:
    """Validate that OHLCV columns contain numeric data."""
    numeric_columns = ['open', 'high', 'low', 'close', 'volume']
    
    for col in numeric_columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except:
                return False, f"Column '{col}' contains non-numeric data"
    
    return True, ""


def load_and_validate_csv(uploaded_file) -> Tuple[Optional[pd.DataFrame], str]:
    """Load CSV file and validate its contents."""
    try:
        # Read CSV
        df = pd.read_csv(uploaded_file)
        
        # Validate columns
        is_valid, error_msg = validate_csv_columns(df)
        if not is_valid:
            return None, error_msg
        
        # Parse date column
        is_valid, error_msg = parse_date_column(df)
        if not is_valid:
            return None, error_msg
        
        # Validate numeric columns
        is_valid, error_msg = validate_numeric_columns(df)
        if not is_valid:
            return None, error_msg
        
        # Set date as index
        df.set_index('date', inplace=True)
        
        # Rename columns to Title case for backtesting.py
        df.columns = [col.title() for col in df.columns]
        
        # Sort by date
        df.sort_index(inplace=True)
        
        # Remove any rows with NaN values
        df.dropna(inplace=True)
        
        if len(df) == 0:
            return None, "No valid data rows found after processing"
        
        return df, ""
        
    except Exception as e:
        return None, f"Error loading CSV: {str(e)}"


def prepare_data_for_backtest(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare data specifically for backtesting.py library."""
    # Ensure we have the exact column names expected by backtesting.py
    expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    # Check if we have all required columns
    missing_cols = [col for col in expected_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns for backtesting: {missing_cols}")
    
    # Select only the required columns in the correct order
    df_backtest = df[expected_columns].copy()
    
    return df_backtest

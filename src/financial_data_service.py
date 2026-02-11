"""
Financial Data Service Module

Provides functionality to fetch and format financial data from Yahoo Finance.
This module is used by the market server REST API.
"""

import sys
import yfinance as yf
import pandas as pd
from typing import Optional, Dict, Any


def format_number_german(value) -> str:
    """
    Format a number for German Excel with thousand separators and comma as decimal separator.
    German format: 1.234.567,89 (dot as thousand separator, comma as decimal)
    
    Args:
        value: The number to format (can be None, NaN, or numeric)
        
    Returns:
        Formatted string with German number format, or empty string if None/NaN
    """
    if pd.isna(value) or value is None:
        return ""
    
    # Convert to float
    num = float(value)
    
    # Format with 2 decimal places
    formatted = f"{num:,.2f}"
    
    # Replace English separators with German ones
    # English: 1,234,567.89 -> German: 1.234.567,89
    # First replace comma with a temporary placeholder
    formatted = formatted.replace(',', 'TEMP')
    # Replace dot with comma (decimal separator)
    formatted = formatted.replace('.', ',')
    # Replace temporary placeholder with dot (thousand separator)
    formatted = formatted.replace('TEMP', '.')
    
    return formatted


def fetch_financial_data(ticker_symbol: str) -> pd.DataFrame:
    """
    Fetch financial data for a given ticker symbol from Yahoo Finance.
    
    Args:
        ticker_symbol: The Yahoo Finance ticker symbol (e.g., 'AAPL', 'SAP.DE')
        
    Returns:
        DataFrame with financial data organized by year (rows) and metrics (columns)
        
    Raises:
        ValueError: If ticker is invalid or data cannot be fetched
    """
    # Create ticker object
    ticker = yf.Ticker(ticker_symbol)
    
    # Fetch financial statements
    try:
        income_stmt = ticker.income_stmt  # Annual income statement
        balance_sheet = ticker.balance_sheet  # Annual balance sheet
        cash_flow = ticker.cashflow  # Annual cash flow statement
    except Exception as e:
        raise ValueError(f"Error fetching data for {ticker_symbol}: {str(e)}")
    
    # Check if data was retrieved
    if income_stmt is None or income_stmt.empty:
        raise ValueError(f"No financial data available for ticker: {ticker_symbol}")
    
    # Get all available years (columns in the dataframes)
    years = income_stmt.columns
    
    # Initialize result dictionary
    result_data = {
        'Year': [],
        'Total Revenue (mn)': [],
        'Net Income Common Stockholders (mn)': [],
        'Free Cash Flow (mn)': [],
        'Dividend per Share': [],
        'Ordinary Shares Number (mn)': [],
        'Stockholders Equity (mn)': [],
        'Total Assets (mn)': [],
        'Goodwill (mn)': [],
        'Other Intangible Assets (mn)': []
    }
    
    # Map of our desired fields to Yahoo Finance field names
    # Note: Field names may vary, so we try multiple possible names
    field_mappings = {
        'Total Revenue': ['Total Revenue', 'TotalRevenue'],
        'Net Income Common Stockholders': ['Net Income Common Stockholders', 'NetIncomeCommonStockholders', 'Net Income'],
        'Free Cash Flow': ['Free Cash Flow', 'FreeCashFlow'],
        'Cash Dividends Paid': ['Cash Dividends Paid', 'CashDividendsPaid', 'Dividends Paid'],
        'Ordinary Shares Number': ['Ordinary Shares Number', 'OrdinarySharesNumber', 'Share Issued'],
        'Stockholders Equity': ['Stockholders Equity', 'StockholdersEquity', 'Total Equity Gross Minority Interest'],
        'Total Assets': ['Total Assets', 'TotalAssets'],
        'Goodwill': ['Goodwill'],
        'Other Intangible Assets': ['Other Intangible Assets', 'OtherIntangibleAssets']
    }
    
    # Helper function to find value in dataframe
    def get_value(df, possible_names, year):
        """Try to find a value using multiple possible field names."""
        if df is None or df.empty:
            return None
        
        for name in possible_names:
            if name in df.index:
                try:
                    return df.loc[name, year]
                except:
                    pass
        return None
    
    # Extract data for each year
    for year in years:
        # Format year as string (YYYY-MM-DD -> YYYY)
        year_str = str(year.date()) if hasattr(year, 'date') else str(year)
        
        result_data['Year'].append(year_str)
        
        # Get raw values
        total_revenue = get_value(income_stmt, field_mappings['Total Revenue'], year)
        net_income = get_value(income_stmt, field_mappings['Net Income Common Stockholders'], year)
        free_cash_flow = get_value(cash_flow, field_mappings['Free Cash Flow'], year)
        dividends_paid = get_value(cash_flow, field_mappings['Cash Dividends Paid'], year)
        shares_number = get_value(balance_sheet, field_mappings['Ordinary Shares Number'], year)
        stockholders_equity = get_value(balance_sheet, field_mappings['Stockholders Equity'], year)
        total_assets = get_value(balance_sheet, field_mappings['Total Assets'], year)
        goodwill = get_value(balance_sheet, field_mappings['Goodwill'], year)
        other_intangibles = get_value(balance_sheet, field_mappings['Other Intangible Assets'], year)
        
        # Convert amounts to millions (divide by 1 million)
        result_data['Total Revenue (mn)'].append(
            total_revenue / 1e6 if total_revenue is not None and not pd.isna(total_revenue) else None
        )
        result_data['Net Income Common Stockholders (mn)'].append(
            net_income / 1e6 if net_income is not None and not pd.isna(net_income) else None
        )
        result_data['Free Cash Flow (mn)'].append(
            free_cash_flow / 1e6 if free_cash_flow is not None and not pd.isna(free_cash_flow) else None
        )
        
        # Calculate dividend per share (dividends are negative in cash flow, so we negate)
        dividend_per_share = None
        if (dividends_paid is not None and not pd.isna(dividends_paid) and 
            shares_number is not None and not pd.isna(shares_number) and shares_number != 0):
            dividend_per_share = abs(dividends_paid) / shares_number
        result_data['Dividend per Share'].append(dividend_per_share)
        
        # Convert share count to millions
        result_data['Ordinary Shares Number (mn)'].append(
            shares_number / 1e6 if shares_number is not None and not pd.isna(shares_number) else None
        )
        result_data['Stockholders Equity (mn)'].append(
            stockholders_equity / 1e6 if stockholders_equity is not None and not pd.isna(stockholders_equity) else None
        )
        result_data['Total Assets (mn)'].append(
            total_assets / 1e6 if total_assets is not None and not pd.isna(total_assets) else None
        )
        result_data['Goodwill (mn)'].append(
            goodwill / 1e6 if goodwill is not None and not pd.isna(goodwill) else None
        )
        result_data['Other Intangible Assets (mn)'].append(
            other_intangibles / 1e6 if other_intangibles is not None and not pd.isna(other_intangibles) else None
        )
    
    # Create DataFrame
    df = pd.DataFrame(result_data)
    
    return df


def export_to_tsv(df: pd.DataFrame) -> str:
    """
    Export DataFrame to German Excel format (tab-delimited, comma decimal separator).
    
    Args:
        df: DataFrame to export
        
    Returns:
        TSV string with German number formatting
    """
    # Create a copy to avoid modifying original
    df_export = df.copy()
    
    # Format all numeric columns with German decimal separator
    for col in df_export.columns:
        if col != 'Year':
            df_export[col] = df_export[col].apply(format_number_german)
    
    # Export to TSV with tab delimiter
    return df_export.to_csv(sep='\t', index=False, encoding='utf-8')


def export_to_json(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Export DataFrame to JSON format.
    
    Args:
        df: DataFrame to export
        
    Returns:
        Dictionary with years as keys and financial data as values
    """
    # Convert DataFrame to list of dictionaries (one per year)
    records = df.to_dict('records')
    
    # Create structured response
    result = {
        'symbol': None,  # Will be set by caller
        'years': records,
        'count': len(records)
    }
    
    return result

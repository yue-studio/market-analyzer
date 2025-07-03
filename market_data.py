"""market_data.py

This module provides functions for fetching market data from various sources.
It includes:
- get_stock_info: Fetches real-time stock information from Yahoo Finance.
- get_historical_data: Fetches historical stock data from Yahoo Finance.
- get_option_quote: Fetches specific option quotes from Yahoo Finance.
- get_bond_yields: Fetches bond yield data from the Treasury FiscalData API.
"""

import yfinance as yf
import requests
import math
import pandas as pd
from utils import console, TICKER_MAP, debug_print

# Cache for stock information to reduce redundant API calls
_stock_info_cache = {}

def get_stock_info(ticker_symbol: str) -> dict:
    """
    Fetches real-time stock information for a given ticker symbol from Yahoo Finance.
    Results are cached to avoid redundant API calls within a session.

    Args:
        ticker_symbol (str): The ticker symbol (e.g., 'SPY', '^VIX').

    Returns:
        dict: A dictionary containing the stock's information, or an empty dictionary if fetching fails.
    """
    debug_print(f"Fetching stock info for {ticker_symbol}")
    if ticker_symbol in _stock_info_cache:
        debug_print(f"Using cached info for {ticker_symbol}")
        return _stock_info_cache[ticker_symbol]
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        _stock_info_cache[ticker_symbol] = info
        debug_print(f"Successfully fetched info for {ticker_symbol}")
        return info
    except Exception as e:
        console.print(f"[bold red]Could not fetch info for {ticker_symbol}: {e}[/bold red]")
        debug_print(f"Error fetching info for {ticker_symbol}: {e}")
        return {}

def get_historical_data(ticker_symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
    """
    Fetches historical stock data for a given ticker symbol from Yahoo Finance.

    Args:
        ticker_symbol (str): The ticker symbol (e.g., 'SPY', '^GSPC').
        period (str): The period over which to fetch data (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max').
        interval (str): The interval of the data (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo').

    Returns:
        pd.DataFrame: A Pandas DataFrame containing the historical data, or an empty DataFrame if fetching fails.
    """
    debug_print(f"Fetching historical data for {ticker_symbol} (period: {period}, interval: {interval})")
    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period=period, interval=interval)
        debug_print(f"Successfully fetched historical data for {ticker_symbol}. Shape: {data.shape}")
        return data
    except Exception as e:
        console.print(f"[bold red]Could not fetch history for {ticker_symbol}: {e}[/bold red]")
        debug_print(f"Error fetching historical data for {ticker_symbol}: {e}")
        return pd.DataFrame()

def get_option_quote(stock: str, option_type: str, ask_bid: str, price: float, expire_date: str) -> tuple[float, float]:
    """
    Fetches a specific option quote (ask or bid price and delta) for a given stock and option parameters
    from Yahoo Finance.

    Args:
        stock (str): The ticker symbol of the underlying stock (e.g., 'SPY').
        option_type (str): The type of option ('PUT' or 'CALL').
        ask_bid (str): The price type to retrieve ('ask' or 'bid').
        price (float): The strike price of the option.
        expire_date (str): The expiration date of the option in 'YYYY-MM-DD' format.

    Returns:
        tuple[float, float]: A tuple containing the option price (ask or bid) and its delta.
                             Returns (-0.0, -0.0) if the quote cannot be fetched.
    """
    debug_print(f"Fetching option quote for {stock} {option_type} {price} {ask_bid} on {expire_date}")
    try:
        ticker = yf.Ticker(stock)
        opt_chain = ticker.option_chain(expire_date)

        chain = opt_chain.puts if option_type == 'PUT' else opt_chain.calls
        contract = chain[chain['strike'] == price]

        if not contract.empty:
            price_val = contract.iloc[0][ask_bid]
            delta_val = contract.iloc[0].get('delta', 0.0)
            debug_print(f"Successfully fetched option quote: price={price_val}, delta={delta_val}")
            return (price_val, delta_val if not math.isnan(delta_val) else 0.0)
    except Exception as e:
        console.print(f"[bold red]Error fetching option quote for {stock} {price} {option_type} on {expire_date}: {e}[/bold red]")
        debug_print(f"Error fetching option quote: {e}")
    debug_print("Option quote not found or error occurred.")
    return -0.0, -0.0

def get_bond_yields() -> pd.DataFrame:
    """
    Fetches bond yield data from the Treasury FiscalData API.
    Note: The API for 'Daily Treasury Par Yield Curve Rates' (yield_curve_rates) is currently returning 404.
    Using 'Average Interest Rates' as a fallback, which provides different types of rates.

    Returns:
        pd.DataFrame: A Pandas DataFrame containing the bond yield data, or an empty DataFrame if fetching fails.
    """
    console.print("[bold cyan]Fetching Bond Yields...[/bold cyan]")
    debug_print("Attempting to fetch bond yields from Treasury FiscalData API.")
    url = 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates?filter=record_date:gte:2023-01-01&sort=-record_date'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()['data']
        debug_print(f"Successfully fetched bond yields. Number of records: {len(data)}")

        # Extract relevant fields and create a DataFrame
        bond_data = []
        for entry in data:
            bond_data.append({
                'Date': entry.get('record_date'),
                'Security Type': entry.get('security_type_desc'),
                'Security Desc': entry.get('security_desc'),
                'Rate': float(entry.get('avg_interest_rate_amt', 0))
            })
        return pd.DataFrame(bond_data)

    except Exception as e:
        console.print(f"[bold red]Could not fetch Bond Yields: {e}[/bold red]")
        debug_print(f"Error fetching bond yields: {e}")
        return pd.DataFrame()
"""utils.py

This module provides utility functions and shared configurations for the market analysis scripts.
It includes:
- TICKER_MAP: A mapping of common stock/index symbols to their Yahoo Finance equivalents.
- console: An instance of rich.console.Console for formatted terminal output.
- find_day: A function to find the next available option expiration date for a given ticker.
- DEBUG_MODE: A global flag to control debug message output.
- debug_print: A function to print debug messages conditionally.
"""

import datetime
import pytz
import yfinance as yf
from rich.console import Console
from typing import Union

# A mapping of common stock/index symbols to their Yahoo Finance equivalents.
# This helps in standardizing ticker symbols across different data sources.
TICKER_MAP = {
    '$SPX.X': '^GSPC',
    '$VIX.X': '^VIX',
    '$VIX3M.X': '^VIX3M',
    '$VVIX.X': '^VVIX',
    '$SKEW.X': '^SKEW',
    '$VXN.X': '^VXN',
    '$TNX.X': '^TNX',
    '$IRX.X': '^IRX',
    '$FVX.X': '^FVX',
    '$TYX.X': '^TYX',
    '$COMPX': '^IXIC',
    '$NDX.X': '^NDX',
}

# Initialize a rich Console object for consistent and formatted terminal output.
console = Console()

# Global flag for debug mode
DEBUG_MODE = False

def debug_print(*args, **kwargs):
    """
    Prints debug messages only if DEBUG_MODE is True.
    """
    if DEBUG_MODE:
        console.print(f"[bold yellow]DEBUG:[/bold yellow]", *args, **kwargs)

def find_day(ticker_symbol: str, from_date_str: str) -> tuple[Union[str, None], int]:
    """
    Finds the next available option expiration date for a given ticker from a specified date.

    Args:
        ticker_symbol (str): The ticker symbol of the stock or index (e.g., 'SPY', '^GSPC').
        from_date_str (str): The starting date in 'YYYY-MM-DD' format.

    Returns:
        tuple[str | None, int]: A tuple containing the next expiration date in 'YYYY-MM-DD' format
                                 and the number of days to expiration (DTE). Returns (None, 0) if no
                                 suitable expiration date is found.
    """
    debug_print(f"Attempting to find expiration day for {ticker_symbol} from {from_date_str}")
    try:
        from_date = datetime.datetime.strptime(from_date_str, "%Y-%m-%d").date()
        ticker = yf.Ticker(ticker_symbol)
        expirations = ticker.options
        debug_print(f"Found expirations: {expirations}")

        for exp_str in expirations:
            exp_date = datetime.datetime.strptime(exp_str, "%Y-%m-%d").date()
            if exp_date >= from_date:
                dte = (exp_date - from_date).days
                debug_print(f"Found suitable expiration: {exp_str}, DTE: {dte}")
                return exp_str, dte
    except Exception as e:
        console.print(f"[bold red]Error finding expiration day for {ticker_symbol}: {e}[/bold red]")
    debug_print(f"No suitable expiration day found for {ticker_symbol}")
    return None, 0
"""analysis.py

This module defines the MarketAnalyzer class, which encapsulates the logic for performing
various market analyses, including ironfly strategy, market indicators, and pivot point calculations.
"""

import datetime
import pytz
import pandas as pd
from rich.table import Table
import talib
import matplotlib.pyplot as plt
from PIL import Image # Import Pillow
import os

from utils import console, TICKER_MAP, find_day, debug_print
from market_data import get_stock_info, get_historical_data, get_option_quote, get_bond_yields
from openbb_get_spx import get_spx_option_quotes

class MarketAnalyzer:
    """
    A class to analyze market data, including an ironfly strategy,
    market indicators, and bond yields.

    Attributes:
        ticker (str): The primary ticker symbol for analysis (e.g., 'SPY').
        wings (int): The width of the ironfly wings.
        cache (dict): A simple cache to store fetched data.
    """

    def __init__(self, ticker: str, wings: int, display_spx_options: bool = False):
        """
        Initializes the MarketAnalyzer with a ticker symbol and ironfly wings width.

        Args:
            ticker (str): The initial ticker symbol (e.g., '$SPX.X').
            wings (int): The width of the ironfly wings.
            display_spx_options (bool): Whether to display SPX option quotes.
        """
        self.ticker = TICKER_MAP.get(ticker, ticker)
        self.wings = wings
        self.cache = {}
        self.results = {} # Store results for export
        self.display_spx_options = display_spx_options
        debug_print(f"MarketAnalyzer initialized with ticker: {self.ticker}, wings: {self.wings}")

    def analyze_ironfly(self):
        """
        Analyzes and prints the ironfly strategy for the primary ticker.
        If options data is not found for the primary ticker, it falls back to 'SPY'.
        """
        console.print("[bold cyan]Ironfly Analysis[/bold cyan]")
        debug_print("Starting ironfly analysis.")
        
        debug_print("Starting ironfly analysis.")
        
        spx_options_df = get_spx_option_quotes()

        put_ask = 0
        put_bid = 0
        call_bid = 0
        call_ask = 0

        if spx_options_df.empty:
            console.print("[bold red]No SPX option data available for Ironfly analysis.[/bold red]")
            debug_print("Ironfly analysis skipped due to no SPX option data.")
            return

        underlying_price = spx_options_df['underlying_price'].iloc[0]
        spx_quote = underlying_price
        open_quote = underlying_price
        
        # Since get_spx_option_quotes filters for dte == 0, expireddate is always today.
        expireddate = datetime.datetime.now(pytz.timezone('US/Pacific')).strftime("%Y-%m-%d")

        base = 5
        rounded_open = base * round(open_quote / base)
        debug_print(f"SPX Quote: {spx_quote}, Open Quote: {open_quote}, Rounded Open: {rounded_open}")

        debug_print(f"Fetching option quotes for expiration date: {expireddate}")
        
        # Retrieve option prices from the fetched DataFrame
        put_ask_row = spx_options_df[(spx_options_df['option_type'] == 'put') & (spx_options_df['strike'] == (rounded_open - self.wings))]
        put_ask = put_ask_row['ask'].iloc[0] if not put_ask_row.empty else 0

        put_bid_row = spx_options_df[(spx_options_df['option_type'] == 'put') & (spx_options_df['strike'] == rounded_open)]
        put_bid = put_bid_row['bid'].iloc[0] if not put_bid_row.empty else 0

        call_bid_row = spx_options_df[(spx_options_df['option_type'] == 'call') & (spx_options_df['strike'] == rounded_open)]
        call_bid = call_bid_row['bid'].iloc[0] if not call_bid_row.empty else 0

        call_ask_row = spx_options_df[(spx_options_df['option_type'] == 'call') & (spx_options_df['strike'] == (rounded_open + self.wings))]
        call_ask = call_ask_row['ask'].iloc[0] if not call_ask_row.empty else 0

        table = Table(title="Ironfly Strikes")
        table.add_column("Action", style="cyan")
        table.add_column("Price", justify="right", style="magenta")
        table.add_column("Strike", justify="right", style="green")
        table.add_column("Option Price", justify="right", style="yellow")

        table.add_row("Buy", f"{open_quote - self.wings:.2f}", str(rounded_open - self.wings), f"{put_ask:.2f}")
        table.add_row("Sell", f"{open_quote:.2f}", str(rounded_open), f"{put_bid:.2f} / {call_bid:.2f}")
        table.add_row("Buy", f"{open_quote + self.wings:.2f}", str(rounded_open + self.wings), f"{call_ask:.2f}")
        console.print(table)

        console.print(f"Current SPX Quote: [bold green]{spx_quote:.2f}[/bold green]")
        price = put_bid + call_bid - put_ask - call_ask
        console.print(f"Ironfly Price: [bold green]${price:.2f}[/bold green]")
        console.print("\n[bold]Ironfly Explanation:[/bold]")
        console.print("- An Ironfly is a neutral options strategy that profits from low volatility.")
        console.print("- It involves selling a call and a put option at the same strike price (the body) and buying a call and a put option further out-of-the-money (the wings).")
        console.print("- The 'Ironfly Price' represents the net credit received when entering the strategy.")
        console.print("- A positive price indicates a net credit, meaning you receive money upfront.")
        console.print("- The maximum profit is limited to this net credit, achieved if the underlying asset closes exactly at the body strike price at expiration.")
        console.print("- The maximum loss is limited to the difference between the body and wing strikes, minus the net credit, if the price moves beyond the breakeven points.")
        debug_print(f"Calculated Ironfly Price: {price}")
        self.results['ironfly_price'] = price
        self.results['ironfly_details'] = {
            'ticker': self.ticker,
            'mid_strike': rounded_open,
            'wings': self.wings,
            'put_ask': put_ask,
            'put_bid': put_bid,
            'call_bid': call_bid,
            'call_ask': call_ask,
            'expiration_date': expireddate
        }
        console.print()

    def analyze_market_indicators(self):
        """
        Fetches and displays various market indicators like VIX, SKEW, etc.
        """
        console.print("[bold cyan]Market Indicators[/bold cyan]")
        debug_print("Starting market indicators analysis.")
        
        indicators = {
            '$VIX.X': 'VIX',
            '$VIX3M.X': 'VIX3M',
            '$VVIX.X': 'VVIX',
            '$SKEW.X': 'SKEW',
            '$VXN.X': 'NASDAQ VIX',
        }

        table = Table(title="Volatility and Sentiment")
        table.add_column("Indicator", style="cyan")
        table.add_column("Price", justify="right", style="magenta")
        table.add_column("52-Week Range", justify="right", style="green")

        market_indicators_data = []
        for ticker, name in indicators.items():
            debug_print(f"Fetching data for indicator: {name} ({TICKER_MAP[ticker]})")
            info = get_stock_info(TICKER_MAP[ticker])
            price = info.get('regularMarketPrice', 0)
            low = info.get('fiftyTwoWeekLow', 0)
            high = info.get('fiftyTwoWeekHigh', 0)
            table.add_row(name, f"{price:.2f}", f"{low:.2f} - {high:.2f}")
            market_indicators_data.append({
                'Indicator': name,
                'Price': price,
                '52WkLow': low,
                '52WkHigh': high
            })
        
        console.print(table)
        debug_print("Market indicators analysis complete.")
        self.results['market_indicators'] = pd.DataFrame(market_indicators_data)
        console.print()

    def analyze_bond_yields(self):
        """
        Fetches and displays bond yield data from the Treasury FiscalData API.
        """
        console.print("[bold cyan]Bond Yields[/bold cyan]")
        debug_print("Starting bond yields analysis.")
        bond_df = get_bond_yields()

        if not bond_df.empty:
            table = Table(title="Daily Treasury Average Interest Rates")
            table.add_column("Date", style="cyan")
            table.add_column("Security Type", style="magenta")
            table.add_column("Security Desc", style="green")
            table.add_column("Rate", justify="right", style="yellow")

            # Display top 5 recent rates for different security types
            displayed_dates = set()
            for index, entry in bond_df.iterrows():
                if entry['Date'] not in displayed_dates:
                    table.add_row(
                        entry['Date'],
                        entry['Security Type'],
                        entry['Security Desc'],
                        f"{entry['Rate']:.3f}%"
                    )
                    displayed_dates.add(entry['Date'])
                if len(displayed_dates) >= 5: # Limit to 5 unique dates for brevity
                    break
            
            console.print(table)
            debug_print("Bond yields analysis complete.")
            self.results['bond_yields'] = bond_df
            console.print()
        else:
            console.print("[bold red]No bond yield data available.[/bold red]")
            debug_print("Bond yields analysis skipped due to no data.")

    def calculate_pivot_points(self):
        """
        Calculates and prints pivot points for the primary ticker.
        """
        console.print("[bold cyan]Pivot Points Calculation[/bold cyan]")
        debug_print("Starting pivot points calculation.")
        hist_data = get_historical_data(self.ticker, period="5d")

        if not hist_data.empty and len(hist_data) > 1:
            last_day = hist_data.iloc[-2] # Use the most recent full trading day
            pp = (last_day['High'] + last_day['Low'] + last_day['Close']) / 3
            r1 = 2 * pp - last_day['Low']
            s1 = 2 * pp - last_day['High']
            r2 = pp + (last_day['High'] - last_day['Low'])
            s2 = pp - (last_day['High'] - last_day['Low'])
            r3 = pp + 2 * (last_day['High'] - last_day['Low'])
            s3 = pp - 2 * (last_day['High'] - last_day['Low'])

            console.print(f"[bold white]Pivot Points for {self.ticker}:[/bold white]")
            console.print(f"  PP: [green]{pp:.2f}[/green]")
            console.print(f"  R1: [green]{r1:.2f}[/green], S1: [red]{s1:.2f}[/red]")
            console.print(f"  R2: [green]{r2:.2f}[/green], S2: [red]{s2:.2f}[/red]")
            console.print(f"  R3: [green]{r3:.2f}[/green], S3: [red]{s3:.2f}[/red]")
            console.print("\n[bold]Pivot Points Explanation:[/bold]")
            console.print("- [bold]PP[/bold]: Pivot Point - The primary support/resistance level.")
            console.print("- [bold]R1, R2, R3[/bold]: Resistance levels 1, 2, and 3. Potential price ceilings.")
            console.print("- [bold]S1, S2, S3[/bold]: Support levels 1, 2, and 3. Potential price floors.")
            debug_print("Pivot points calculated and displayed.")
            self.results['pivot_points'] = {
                'PP': pp, 'R1': r1, 'S1': s1, 'R2': r2, 'S2': s2, 'R3': r3, 'S3': s3
            }
        else:
            console.print(f"[bold red]Could not calculate pivot points for {self.ticker}. Not enough historical data.[/bold red]")
            debug_print("Pivot points calculation skipped due to insufficient historical data.")
        console.print()

    def calculate_technical_indicators(self):
        """
        Calculates and prints various technical indicators (SMA, EMA, RSI, MACD).
        """
        console.print("[bold cyan]Technical Indicators[/bold cyan]")
        debug_print("Starting technical indicators calculation.")
        # Fetch enough historical data for 200-day moving average
        hist_data = get_historical_data(self.ticker, period="1y") 

        if hist_data.empty or len(hist_data) < 200:
            console.print(f"[bold red]Not enough historical data for {self.ticker} to calculate technical indicators.[/bold red]")
            debug_print("Technical indicators calculation skipped due to insufficient historical data.")
            return

        close_prices = hist_data['Close'].values

        # Simple Moving Averages
        sma_50 = talib.SMA(close_prices, timeperiod=50)
        sma_200 = talib.SMA(close_prices, timeperiod=200)

        # Exponential Moving Averages
        ema_50 = talib.EMA(close_prices, timeperiod=50)
        ema_200 = talib.EMA(close_prices, timeperiod=200)

        # Relative Strength Index (RSI)
        rsi = talib.RSI(close_prices, timeperiod=14)

        # Moving Average Convergence Divergence (MACD)
        macd, macdsignal, macdhist = talib.MACD(close_prices, fastperiod=12, slowperiod=26, signalperiod=9)

        # Bollinger Bands
        upper_band, middle_band, lower_band = talib.BBANDS(close_prices, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

        # Stochastic Oscillator
        slowk, slowd = talib.STOCH(hist_data['High'].values, hist_data['Low'].values, hist_data['Close'].values, 
                                   fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)

        # Average Directional Index (ADX)
        adx = talib.ADX(hist_data['High'].values, hist_data['Low'].values, hist_data['Close'].values, timeperiod=14)

        table = Table(title=f"Technical Indicators for {self.ticker}")
        table.add_column("Indicator", style="cyan")
        table.add_column("Value", justify="right", style="magenta")

        tech_indicators_data = {}
        # Display the latest values
        if not pd.isna(sma_50[-1]):
            table.add_row("SMA (50)", f"{sma_50[-1]:.2f}")
            tech_indicators_data['SMA_50'] = sma_50[-1]
        if not pd.isna(sma_200[-1]):
            table.add_row("SMA (200)", f"{sma_200[-1]:.2f}")
            tech_indicators_data['SMA_200'] = sma_200[-1]
        if not pd.isna(ema_50[-1]):
            table.add_row("EMA (50)", f"{ema_50[-1]:.2f}")
            tech_indicators_data['EMA_50'] = ema_50[-1]
        if not pd.isna(ema_200[-1]):
            table.add_row("EMA (200)", f"{ema_200[-1]:.2f}")
            tech_indicators_data['EMA_200'] = ema_200[-1]
        if not pd.isna(rsi[-1]):
            table.add_row("RSI (14)", f"{rsi[-1]:.2f}")
            tech_indicators_data['RSI_14'] = rsi[-1]
        if not pd.isna(macd[-1]):
            table.add_row("MACD", f"{macd[-1]:.2f}")
            table.add_row("MACD Signal", f"{macdsignal[-1]:.2f}")
            table.add_row("MACD Hist", f"{macdhist[-1]:.2f}")
            tech_indicators_data['MACD'] = macd[-1]
            tech_indicators_data['MACD_Signal'] = macdsignal[-1]
            tech_indicators_data['MACD_Hist'] = macdhist[-1]
        if not pd.isna(upper_band[-1]):
            table.add_row("Bollinger Upper", f"{upper_band[-1]:.2f}")
            table.add_row("Bollinger Middle", f"{middle_band[-1]:.2f}")
            table.add_row("Bollinger Lower", f"{lower_band[-1]:.2f}")
            tech_indicators_data['BB_Upper'] = upper_band[-1]
            tech_indicators_data['BB_Middle'] = middle_band[-1]
            tech_indicators_data['BB_Lower'] = lower_band[-1]
        if not pd.isna(slowk[-1]):
            table.add_row("Stochastic %K", f"{slowk[-1]:.2f}")
            table.add_row("Stochastic %D", f"{slowd[-1]:.2f}")
            tech_indicators_data['STOCH_K'] = slowk[-1]
            tech_indicators_data['STOCH_D'] = slowd[-1]
        if not pd.isna(adx[-1]):
            table.add_row("ADX (14)", f"{adx[-1]:.2f}")
            tech_indicators_data['ADX_14'] = adx[-1]
        
        console.print(table)
        console.print("\n[bold]Technical Indicators Explanation:[/bold]")
        console.print("- [bold]SMA (50/200)[/bold]: Simple Moving Average over 50/200 periods. Shows average price over time.")
        console.print("- [bold]EMA (50/200)[/bold]: Exponential Moving Average over 50/200 periods. Gives more weight to recent prices.")
        console.print("- [bold]RSI (14)[/bold]: Relative Strength Index over 14 periods. Measures the speed and change of price movements (momentum).")
        console.print("- [bold]MACD[/bold]: Moving Average Convergence Divergence. Shows the relationship between two moving averages of a security’s price.")
        console.print("- [bold]Bollinger Bands[/bold]: Volatility bands placed above and below a simple moving average. Upper, Middle, and Lower bands.")
        console.print("- [bold]Stochastic %K/%D[/bold]: Momentum indicators comparing a particular closing price of a security to a range of its prices over a certain period of time.")
        console.print("- [bold]ADX (14)[/bold]: Average Directional Index over 14 periods. Measures the strength of a trend.")
        debug_print("Technical indicators calculation complete.")
        self.results['technical_indicators'] = pd.DataFrame([tech_indicators_data])
        console.print()

    def plot_vix_ratio(self, ax_vix, ax_ratio, period: str = "1y"):
        """
        Fetches historical VIX and VIX3M data, calculates their ratio, and plots them on provided axes.

        Args:
            ax_vix: Matplotlib axes for the VIX plot.
            ax_ratio: Matplotlib axes for the VIX3M/VIX Ratio plot.
            period (str): Historical period for data fetching (e.g., '6mo', '1y').
        """
        debug_print(f"Starting VIX ratio plot generation for period: {period}.")
        vix_ticker = TICKER_MAP['$VIX.X']
        vix3m_ticker = TICKER_MAP['$VIX3M.X']

        # Fetch historical data for the specified period
        vix_hist = get_historical_data(vix_ticker, period=period)
        vix3m_hist = get_historical_data(vix3m_ticker, period=period)

        if vix_hist.empty or vix3m_hist.empty:
            console.print("[bold red]Could not fetch historical VIX or VIX3M data for plotting.[/bold red]")
            debug_print("VIX ratio plot skipped due to insufficient historical data.")
            return False

        # Normalize dates to remove timezone and time components, then convert to plain date objects
        vix_hist.index = vix_hist.index.normalize().map(lambda x: x.date())
        vix3m_hist.index = vix3m_hist.index.normalize().map(lambda x: x.date())

        # Align dataframes by date and calculate ratio
        combined_hist = pd.concat([vix_hist['Close'].rename('vix'), vix3m_hist['Close'].rename('vix3m')], axis=1)
        combined_hist.dropna(inplace=True)
        combined_hist['vix_ratio'] = combined_hist['vix3m'] / combined_hist['vix']

        if combined_hist.empty:
            console.print("[bold red]Not enough overlapping data for VIX ratio plot.[/bold red]")
            debug_print("VIX ratio plot skipped due to no overlapping data after cleaning.")
            return False

        # Plot VIX
        ax_vix.plot(combined_hist.index, combined_hist['vix'], label='VIX', color='green')
        ax_vix.set_title('VIX (Last 6 Months)')
        ax_vix.set_ylabel('Value')
        ax_vix.grid(True)
        ax_vix.legend()

        # Plot VIX3M/VIX Ratio
        ax_ratio.plot(combined_hist.index, combined_hist['vix_ratio'], label='VIX3M/VIX Ratio', color='blue')
        ax_ratio.axhline(y=1, color='red', linestyle='--', label='Ratio = 1')
        ax_ratio.set_title('VIX3M/VIX Ratio (Last 6 Months)')
        ax_ratio.set_xlabel('Date')
        ax_ratio.set_ylabel('Ratio')
        ax_ratio.grid(True)
        ax_ratio.legend()

        debug_print("VIX ratio plot generation complete.")
        return True

    def plot_technical_indicators_plot(self, ax_price, ax_rsi, ax_macd, period: str = "1y"):
        """
        Plots the price and technical indicators (SMA, EMA, RSI, MACD) for the primary ticker
        for the past 12 months on provided axes.

        Args:
            ax_price: Matplotlib axes for the price and moving averages plot.
            ax_rsi: Matplotlib axes for the RSI plot.
            ax_macd: Matplotlib axes for the MACD plot.
            period (str): Historical period for data fetching (e.g., '6mo', '1y').
        """
        debug_print(f"Starting technical indicators plot generation for period: {period}.")

        hist_data = get_historical_data(self.ticker, period=period)

        if hist_data.empty or len(hist_data) < 200: # Need enough data for 200-day SMA
            console.print(f"[bold red]Not enough historical data for {self.ticker} to plot technical indicators.[/bold red]")
            debug_print("Technical indicators plot skipped due to insufficient historical data.")
            return False

        close_prices = hist_data['Close']

        # Calculate indicators
        sma_50 = talib.SMA(close_prices.values, timeperiod=50)
        sma_200 = talib.SMA(close_prices.values, timeperiod=200)

        # Exponential Moving Averages
        ema_50 = talib.EMA(close_prices.values, timeperiod=50)
        ema_200 = talib.EMA(close_prices.values, timeperiod=200)

        # Relative Strength Index (RSI)
        rsi = talib.RSI(close_prices.values, timeperiod=14)

        # Moving Average Convergence Divergence (MACD)
        macd, macdsignal, macdhist = talib.MACD(close_prices.values, fastperiod=12, slowperiod=26, signalperiod=9)

        # Bollinger Bands
        upper_band, middle_band, lower_band = talib.BBANDS(close_prices.values, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

        # Stochastic Oscillator
        slowk, slowd = talib.STOCH(hist_data['High'].values, hist_data['Low'].values, hist_data['Close'].values, 
                                   fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)

        # Average Directional Index (ADX)
        adx = talib.ADX(hist_data['High'].values, hist_data['Low'].values, hist_data['Close'].values, timeperiod=14)

        # Plot Price and Moving Averages
        ax_price.plot(hist_data.index, close_prices, label='Close Price', color='black')
        ax_price.plot(hist_data.index, sma_50, label='SMA (50)', color='blue')
        ax_price.plot(hist_data.index, ema_50, label='EMA (50)', color='orange')
        ax_price.plot(hist_data.index, upper_band, label='Bollinger Upper', color='red', linestyle='--')
        ax_price.plot(hist_data.index, middle_band, label='Bollinger Middle', color='gray', linestyle='--')
        ax_price.plot(hist_data.index, lower_band, label='Bollinger Lower', color='red', linestyle='--')
        ax_price.set_title(f'{self.ticker} Price and Moving Averages')
        ax_price.set_ylabel('Price')
        ax_price.legend()
        ax_price.grid(True)

        # Plot RSI
        ax_rsi.plot(hist_data.index, rsi, label='RSI (14)', color='purple')
        ax_rsi.axhline(70, linestyle='--', alpha=0.5, color='red')
        ax_rsi.axhline(30, linestyle='--', alpha=0.5, color='green')
        ax_rsi.set_title('Relative Strength Index (RSI)')
        ax_rsi.set_ylabel('RSI')
        ax_rsi.legend()
        ax_rsi.grid(True)

        # Plot MACD
        ax_macd.plot(hist_data.index, macd, label='MACD', color='green')
        ax_macd.plot(hist_data.index, macdsignal, label='Signal Line', color='red')
        ax_macd.bar(hist_data.index, macdhist, label='Histogram', color='gray', alpha=0.5)
        ax_macd.set_title('MACD')
        ax_macd.set_xlabel('Date')
        ax_macd.set_ylabel('Value')
        ax_macd.legend()
        ax_macd.grid(True)

        debug_print("Technical indicators plot generation complete.")
        return True

    def analyze_spx_options(self):
        """
        Fetches and displays SPX option quotes using OpenBB.
        """
        console.print("[bold cyan]SPX Option Quotes[/bold cyan]")
        debug_print("Starting SPX option quotes analysis.")
        spx_options_df = get_spx_option_quotes()

        if not spx_options_df.empty:
            table = Table(title="SPX Option Quotes")
            # Dynamically add columns based on DataFrame columns
            for col in spx_options_df.columns:
                table.add_column(col.replace('_', ' ').title(), justify="right", style="magenta")
            
            # Add rows to the table
            for index, row in spx_options_df.iterrows():
                table.add_row(*[str(x) for x in row.values])
            
            console.print(table)
            self.results['spx_options'] = spx_options_df
        else:
            console.print("[bold red]No SPX option data available.[/bold red]")
        debug_print("SPX option quotes analysis complete.")
        console.print()

    def run_analysis(self):
        """
        Runs the full market analysis, including ironfly, market indicators, and bond yields.
        """
        debug_print("Starting full market analysis.")
        self.analyze_ironfly()
        self.analyze_market_indicators()
        self.analyze_bond_yields()
        self.calculate_pivot_points()
        self.calculate_technical_indicators()
        if self.display_spx_options:
            self.analyze_spx_options()
        debug_print("Full market analysis complete.")

def combine_plots_to_png(plot1_filename: str, plot2_filename: str, ticker: str, output_prefix: str = "combined_plots"):
    """
    Combines two PNG image files into a single PNG file, stacking them vertically.
    A timestamp is added to the output filename.

    Args:
        plot1_filename (str): Path to the first PNG image file.
        plot2_filename (str): Path to the second PNG image file.
        ticker (str): The ticker symbol for naming the combined plot.
        output_prefix (str): Prefix for the output combined PNG file.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{output_prefix}_{ticker}_{timestamp}.png"
    debug_print(f"Combining plots: {plot1_filename} and {plot2_filename} into {output_filename}")
    try:
        img1 = Image.open(plot1_filename)
        img2 = Image.open(plot2_filename)

        # Ensure both images have the same width
        if img1.width != img2.width:
            debug_print("Resizing images to match width for combination.")
            max_width = max(img1.width, img2.width)
            img1 = img1.resize((max_width, int(img1.height * (max_width / img1.width))))
            img2 = img2.resize((max_width, int(img2.height * (max_width / img2.width))))

        # Create a new image with combined height
        combined_height = img1.height + img2.height
        combined_image = Image.new('RGB', (img1.width, combined_height))

        # Paste images
        combined_image.paste(img1, (0, 0))
        combined_image.paste(img2, (0, img1.height))

        combined_image.save(output_filename)
        console.print(f"[bold green]Combined plot saved as {output_filename}[/bold green]")
        debug_print("Plot combination complete.")
    except FileNotFoundError:
        console.print("[bold red]Error: One or both plot files not found. Please ensure they are generated first.[/bold red]")
        debug_print(f"File not found during plot combination: {plot1_filename} or {plot2_filename}")
    except Exception as e:
        console.print(f"[bold red]Error combining plots: {e}[/bold red]")
        debug_print(f"Error during plot combination: {e}")

    def export_results(self, output_dir: str = "./analysis_results"):
        """
        Exports the collected analysis results to CSV files.

        Args:
            output_dir (str): The directory where the results will be saved.
        """
        debug_print(f"Starting export of analysis results to {output_dir}")
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        for key, data in self.results.items():
            filename = f"{output_dir}/{key}_{self.ticker}_{timestamp}.csv"
            try:
                if isinstance(data, pd.DataFrame):
                    data.to_csv(filename, index=False)
                    console.print(f"[green]Exported {key} to {filename}[/green]")
                elif isinstance(data, dict):
                    pd.DataFrame([data]).to_csv(filename, index=False)
                    console.print(f"[green]Exported {key} to {filename}[/green]")
                else:
                    debug_print(f"Skipping export for {key}: Unsupported data type.")
            except Exception as e:
                console.print(f"[bold red]Error exporting {key} to {filename}: {e}[/bold red]")
                debug_print(f"Error exporting {key}: {e}")
        debug_print("Analysis results export complete.")
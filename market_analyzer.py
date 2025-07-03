"""td_api_ironfly.py

This is the main script to run the market analysis.
It uses the MarketAnalyzer class from the analysis module to perform
ironfly strategy analysis, market indicator analysis, and bond yield analysis.

Usage:
  python3 td_api_ironfly.py [--ticker TICKER] [--wings WINGS]

Arguments:
  --ticker TICKER  The main ticker to analyze (e.g., $SPX.X, SPY). Default is $SPX.X.
  --wings WINGS    The width of the ironfly wings. Default is 50.
"""

import argparse
from analysis import MarketAnalyzer
from utils import console
import utils
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg') # Explicitly set the backend
from rich.table import Table
from rich.progress import Progress, track

# Install yfinance if it's not already installed
try:
    import yfinance as yf
except ImportError:
    console.print("yfinance not found. Installing...")
    import subprocess
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'yfinance'])
    import yfinance as yf

# Install rich if it's not already installed
try:
    from rich.console import Console
except ImportError:
    console.print("rich not found. Installing...")
    import subprocess
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'rich'])
    from rich.console import Console

# Install prettytable if it's not already installed
try:
    from prettytable import from_html
except ImportError:
    console.print("prettytable not found. Installing...")
    import subprocess
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'prettytable'])
    from prettytable import from_html

# Install requests if it's not already installed
try:
    import requests
except ImportError:
    console.print("requests not found. Installing...")
    import subprocess
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'requests'])
    import requests

# Install pandas if it's not already installed
try:
    import pandas as pd
except ImportError:
    console.print("pandas not found. Installing...")
    import subprocess
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'pandas'])
    import pandas as pd

# Install praw if it's not already installed
try:
    import praw
except ImportError:
    console.print("praw not found. Installing...")
    import subprocess
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'praw'])
    import praw

# Install vaderSentiment if it's not already installed
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:
    console.print("vaderSentiment not found. Installing...")
    import subprocess
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'vaderSentiment'])
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Install newsapi-python if it's not already installed
try:
    from newsapi import NewsApiClient
except ImportError:
    console.print("newsapi-python not found. Installing...")
    import subprocess
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'newsapi-python'])
    from newsapi import NewsApiClient

# Install TA-Lib if it's not already installed
try:
    import talib
except ImportError:
    console.print("TA-Lib not found. Installing...")
    import subprocess
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'TA-Lib'])
    import talib


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Market analysis tool.")
    parser.add_argument("-t", "--ticker", type=str, default="$SPX.X", help="The main ticker to analyze (e.g., $SPX.X).")
    parser.add_argument("-w", "--wings", type=int, default=50, help="The width of the ironfly wings.")
    parser.add_argument("-p", "--plot-vix-ratio", action="store_true", help="Plot VIX and VIX3M ratio.")
    parser.add_argument("--vix-period", type=str, default="1y", help="Historical period for VIX ratio plot (e.g., 6mo, 1y, 5y).")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug messages.")
    parser.add_argument("-ta", "--plot-ta", action="store_true", help="Plot price and technical indicators.")
    parser.add_argument("--ta-period", type=str, default="1y", help="Historical period for TA plot (e.g., 6mo, 1y, 5y).")
    parser.add_argument("-r", "--reddit-analysis", action="store_true", help="Perform Reddit sentiment analysis.")
    parser.add_argument("-a", "--plot-all", action="store_true", help="Plot both VIX ratio and technical indicators.")
    parser.add_argument("-n", "--news-analysis", action="store_true", help="Perform news sentiment analysis.")
    parser.add_argument("-e", "--export-data", action="store_true", help="Export analysis results to CSV/JSON files.")
    parser.add_argument("-top", "--top-headlines", action="store_true", help="Print the top 10 news headlines.")
    args = parser.parse_args()

    if args.debug:
        utils.DEBUG_MODE = True
        utils.debug_print(f"Matplotlib backend: {matplotlib.get_backend()}")

    analyzer = MarketAnalyzer(ticker=args.ticker, wings=args.wings)

    with Progress() as progress:
        task = progress.add_task("[green]Running analysis...[/green]", total=1)
        analyzer.run_analysis()
        progress.update(task, advance=1)

    if args.reddit_analysis:
        console.print("[bold cyan]Reddit Sentiment Analysis[/bold cyan]")
        from reddit_analysis import get_top_mentioned_stocks_with_sentiment
        
        reddit_df, topics = get_top_mentioned_stocks_with_sentiment()

        if topics:
            console.print("[bold green]Top 20 Hot Topics on Wallstreetbets:[/bold green]")
            for i, topic in enumerate(topics, 1):
                console.print(f"{i}. {topic}")
            console.print()

        if not reddit_df.empty:
            table = Table(title="Top Mentioned Stocks on Wallstreetbets")
            table.add_column("Symbol", style="cyan")
            table.add_column("Mentions", justify="right", style="magenta")
            table.add_column("Neg", justify="right", style="red")
            table.add_column("Neu", justify="right", style="yellow")
            table.add_column("Pos", justify="right", style="green")
            table.add_column("Compound", justify="right", style="blue")
            table.add_column("Last Price", justify="right", style="white")

            for symbol, row in reddit_df.iterrows():
                table.add_row(
                    symbol,
                    str(row['mentions']),
                    f"{row['neg']:.2f}",
                    f"{row['neu']:.2f}",
                    f"{row['pos']:.2f}",
                    f"{row['compound']:.2f}",
                    f"{row['last_price']:.2f}"
                )
            console.print(table)
        else:
            console.print("[bold red]No stock mentions found or error during Reddit analysis.[/bold red]")

    if args.news_analysis:
        console.print("[bold cyan]News Sentiment Analysis[/bold cyan]")
        from news_analysis import analyze_news_sentiment
        news_df = analyze_news_sentiment(query=analyzer.ticker) # Use the main ticker for news search

        if not news_df.empty:
            table = Table(title=f"News Sentiment for {analyzer.ticker}")
            table.add_column("Title", style="cyan")
            table.add_column("Neg", justify="right", style="red")
            table.add_column("Neu", justify="right", style="yellow")
            table.add_column("Pos", justify="right", style="green")
            table.add_column("Compound", justify="right", style="blue")
            table.add_column("URL", style="dim")

            for index, row in news_df.iterrows():
                table.add_row(
                    row['Title'],
                    f"{row['Neg']:.2f}",
                    f"{row['Neu']:.2f}",
                    f"{row['Pos']:.2f}",
                    f"{row['Compound']:.2f}",
                    row['URL']
                )
            console.print(table)
        else:
            console.print(f"[bold red]No news articles found or error during news analysis for {analyzer.ticker}.[/bold red]")

    if args.plot_vix_ratio or args.plot_all:
        vix_plot_filename = None
        vix_plot_generated = False # Initialize flag
        if args.plot_all:
            vix_plot_filename = "temp_vix_ratio_plot.png"
        else:
            vix_plot_filename = "vix_ratio_plot.png"

        fig_vix, (ax_vix, ax_ratio) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        plot_success = analyzer.plot_vix_ratio(ax_vix, ax_ratio, args.vix_period)
        if plot_success: # Only save if plotting was successful
            plt.tight_layout()
            plt.savefig(vix_plot_filename)
            vix_plot_generated = True # Set flag only if saved
        plt.close(fig_vix) # Always close the figure

    if args.plot_ta or args.plot_all:
        ta_plot_filename = None
        ta_plot_generated = False # Initialize flag
        if args.plot_all:
            ta_plot_filename = "temp_technical_indicators_plot.png"
        else:
            ta_plot_filename = f"{analyzer.ticker}_technical_indicators_plot.png"

        fig_ta, (ax_price, ax_rsi, ax_macd) = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
        plot_success = analyzer.plot_technical_indicators_plot(ax_price, ax_rsi, ax_macd, args.ta_period)
        if plot_success: # Only save if plotting was successful
            plt.tight_layout()
            plt.savefig(ta_plot_filename)
            ta_plot_generated = True # Set flag only if saved
        plt.close(fig_ta) # Always close the figure

    if args.plot_all and vix_plot_generated and ta_plot_generated:
        from analysis import combine_plots_to_png
        combine_plots_to_png(vix_plot_filename, ta_plot_filename, analyzer.ticker)
        # Clean up temporary files
        import os
        if vix_plot_filename and os.path.exists(vix_plot_filename):
            os.remove(vix_plot_filename)
        if ta_plot_filename and os.path.exists(ta_plot_filename):
            os.remove(ta_plot_filename)

    if args.export_data:
        analyzer.export_results()

    if args.top_headlines:
        from get_top_headlines import run_cli
        run_cli()

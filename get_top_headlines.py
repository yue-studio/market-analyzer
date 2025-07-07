"""
get_top_headlines.py

This script fetches the top 10 news headlines from the NewsAPI and can display them as a Streamlit app or in the console.
It can also search for news based on a stock symbol.
"""

import argparse
import streamlit as st
from news_analysis import initialize_newsapi, _get_news_articles
from utils import console
from rich.table import Table

def run_streamlit_app(symbol=None):
    """
    Runs the Streamlit application.
    """
    st.set_page_config(page_title="Top News Headlines", layout="wide")
    if symbol:
        st.title(f"News for {symbol.upper()}")
    else:
        st.title("Top 10 News Headlines")

    newsapi = initialize_newsapi()
    if not newsapi:
        st.error("Failed to initialize NewsAPI. Please check your API key in config.py.")
        return

    try:
        articles_response = _get_news_articles(newsapi, symbol, None, 10) # from_date is not used for top headlines
        articles = articles_response.get('articles', [])

        if not articles:
            st.warning("No top headlines found.")
            return

        for i, article in enumerate(articles, 1):
            st.subheader(f"{i}. {article['title']}")
            st.markdown(f"[Read more]({article['url']})", unsafe_allow_html=True)
            if article.get('description'):
                st.write(article.get('description'))
            st.markdown("<hr>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error fetching top headlines: {e}")

def run_cli(symbol=None):
    """
    Runs the command-line interface version.
    """
    newsapi = initialize_newsapi()
    if not newsapi:
        return

    try:
        articles_response = _get_news_articles(newsapi, symbol, None, 10) # from_date is not used for top headlines
        articles = articles_response.get('articles', [])

        if not articles:
            console.print("[bold yellow]No top headlines found.[/bold yellow]")
            return

        table = Table(title="Top 10 News Headlines", padding=(0, 1, 1, 1))
        table.add_column("Title", style="cyan")
        table.add_column("Description", style="dim")

        if symbol:
            table.title = f"News for {symbol.upper()}"

        for article in articles:
            table.add_row(
                f"[link={article['url']}]{article['title']}[/link]",
                article.get('description', '')
            )
        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error fetching top headlines: {e}[/bold red]")

def main():
    parser = argparse.ArgumentParser(description="Fetch top news headlines.")
    parser.add_argument("--mode", choices=["streamlit", "cli"], default="cli", help="The mode to run the script in.")
    parser.add_argument("--symbol", help="The stock symbol to search for news.")
    args = parser.parse_args()

    if args.mode == "streamlit":
        run_streamlit_app(args.symbol)
    else:
        run_cli(args.symbol)

if __name__ == "__main__":
    main()

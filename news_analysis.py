"""news_analysis.py

This module provides functionality to fetch news articles related to a given stock
and perform sentiment analysis on their content.
"""

from newsapi import NewsApiClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
from datetime import datetime, timedelta

from utils import console, debug_print
from config import NEWS_API_KEY

def initialize_newsapi():
    """
    Initializes and returns a NewsApiClient instance.
    """
    debug_print("Initializing NewsAPI client.")
    if not NEWS_API_KEY or NEWS_API_KEY == 'YOUR_NEWS_API_KEY':
        console.print("[bold red]Error: NEWS_API_KEY is not set in config.py. Please get one from newsapi.org.[/bold red]")
        return None
    try:
        newsapi = NewsApiClient(api_key=NEWS_API_KEY)
        return newsapi
    except Exception as e:
        console.print(f"[bold red]Error initializing NewsAPI: {e}[/bold red]")
        debug_print(f"Error initializing NewsAPI: {e}")
        return None

def get_sentiment_score(text: str) -> dict:
    """
    Calculates VADER sentiment scores for a given text.
    """
    sia = SentimentIntensityAnalyzer()
    sentiment = sia.polarity_scores(text)
    return sentiment

def _get_news_articles(newsapi, query: str, from_date: str, max_articles: int):
    """Helper to fetch articles from NewsAPI."""
    if query:
        return newsapi.get_everything(
            q=query,
            from_param=from_date,
            language='en',
            sort_by='relevancy',
            page_size=max_articles
        )
    else:
        return newsapi.get_top_headlines(language='en', page_size=max_articles)

def analyze_news_sentiment(query: str, days_ago: int = 7, max_articles: int = 10) -> pd.DataFrame:
    """
    Fetches news articles related to a query, performs sentiment analysis,
    and returns a DataFrame of results.

    Args:
        query (str): The search query (e.g., stock ticker).
        days_ago (int): How many days back to search for articles.
        max_articles (int): Maximum number of articles to process.

    Returns:
        pd.DataFrame: A DataFrame with article titles, sentiment scores, and URLs.
    """
    newsapi = initialize_newsapi()
    if not newsapi:
        return pd.DataFrame()

    sentiment_data = []

    from_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    debug_print(f"Searching news for '{query}' from {from_date} with max {max_articles} articles.")

    try:
        articles_response = _get_news_articles(newsapi, query, from_date, max_articles)
        articles = articles_response.get('articles', [])
        debug_print(f"Found {articles_response.get('totalResults', 0)} articles for '{query}'. Processing up to {max_articles}.")

        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')
            url = article.get('url', '')

            text_to_analyze = f"{title}. {description}"
            if text_to_analyze.strip():
                sentiment = get_sentiment_score(text_to_analyze)
                sentiment_data.append({
                    'Title': title,
                    'URL': url,
                    'Neg': sentiment['neg'],
                    'Neu': sentiment['neu'],
                    'Pos': sentiment['pos'],
                    'Compound': sentiment['compound']
                })
            else:
                debug_print(f"Skipping article with empty title/description: {url}")

    except Exception as e:
        console.print(f"[bold red]Error fetching or analyzing news for '{query}': {e}[/bold red]")
        debug_print(f"Error fetching or analyzing news: {e}")

    return pd.DataFrame(sentiment_data)

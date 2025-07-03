# -*- coding: utf-8 -*-
"""cnbc_analysis.py

This module provides functionality to fetch and analyze CNBC news from RSS feeds.
"""

import feedparser

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
from utils import console, debug_print

def getSIA(text):
  """Get sentiment analysis scores for a given text."""
  sia = SentimentIntensityAnalyzer()
  sentiment = sia.polarity_scores(text)
  return sentiment

def analyze_cnbc_sentiment():
    """
    Fetches news from CNBC RSS feed and performs sentiment analysis.
    Returns a pandas DataFrame with the analysis.
    """
    debug_print("Fetching and analyzing CNBC RSS feed.")
    URL = "https://www.cnbc.com/id/10000664/device/rss/rss.html"
    try:
        NewsFeed = feedparser.parse(URL)
        articles = []
        for entry in NewsFeed.entries[:10]: # Limit to 10 most recent articles
            try:
                sentiment = getSIA(entry.summary)
                articles.append({
                        'Title': entry.title,
                        'URL': entry.link,
                        'Neg': sentiment['neg'],
                        'Neu': sentiment['neu'],
                        'Pos': sentiment['pos'],
                        'Compound': sentiment['compound']
                    })
            except Exception as e:
                debug_print(f"Could not process article {entry.link}: {e}")
                continue
        
        if not articles:
            console.print("[bold yellow]No articles found in CNBC RSS feed.[/bold yellow]")
            return pd.DataFrame()

        return pd.DataFrame(articles)
    except Exception as e:
        console.print(f"[bold red]Error fetching or parsing CNBC RSS feed: {e}[/bold red]")
        debug_print(f"Error in analyze_cnbc_sentiment: {e}")
        return pd.DataFrame()

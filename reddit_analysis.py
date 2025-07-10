"""
This module provides functionality to fetch and analyze Reddit data.
"""

import praw
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import yfinance as yf
from datetime import datetime
import pytz
from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET
from utils import console, debug_print
import pandas as pd

def get_reddit_instance():
    """
    Initializes and returns a PRAW instance.
    """
    debug_print("Initializing PRAW instance.")
    if not REDDIT_CLIENT_ID or REDDIT_CLIENT_ID == 'YOUR_REDDIT_CLIENT_ID' or \
       not REDDIT_CLIENT_SECRET or REDDIT_CLIENT_SECRET == 'YOUR_REDDIT_CLIENT_SECRET':
        console.print("[bold red]Error: Reddit API credentials are not set in config.py.[/bold red]")
        return None
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent="MyBot/0.0.1",
            check_for_async=False
        )
        return reddit
    except Exception as e:
        console.print(f"[bold red]Error initializing PRAW: {e}[/bold red]")
        debug_print(f"Error initializing PRAW: {e}")
        return None

def _get_stock_price(symbol: str) -> float:
    """Helper function to get the last closing price of a stock."""
    try:
        quote = yf.Ticker(symbol).history(interval="1m", period = "1d")
        price = quote['Close'].iloc[-1]
        return price
    except (KeyError, ValueError, ZeroDivisionError, IndexError, TypeError) :
        debug_print(f"Could not fetch price for {symbol}")
        return 0.0

def get_top_mentioned_stocks_with_sentiment():
    """
    Fetches top mentioned stocks from wallstreetbets and performs sentiment analysis.
    """
    reddit = get_reddit_instance()
    if not reddit:
        return pd.DataFrame(), []

    symbols = set([])
    d = {}
    senti = {}
    topics = []

    for submission in reddit.subreddit("wallstreetbets").hot(limit=20):
        topics.append({"title": submission.title, "url": submission.url})
        submission.comments.replace_more(limit=0)
        for top_level_comment in submission.comments:
            s = getSIA(top_level_comment.body.strip())
            res = re.findall(r'\$*[A-Z]{2,4}\s+', top_level_comment.body)
            for i in res:
                w = i.strip().replace("$","")
                symbols.add(w)
                if w in d.keys():
                   d[w] += 1
                   senti[w]['neg'] += s['neg']
                   senti[w]['neu'] += s['neu']
                   senti[w]['pos'] += s['pos']
                   senti[w]['compound'] += s['compound']
                else:
                   d[w] = 1
                   senti[w] = {}
                   senti[w]['neg'] = s['neg']
                   senti[w]['neu'] = s['neu']
                   senti[w]['pos'] = s['pos']
                   senti[w]['compound'] = s['compound']

    junkWords = ['WSB', 'YOLO', 'TO', 'RH', 'AM', 'ER', 'OP', 'GO', 'CEO', 'SEC', 'YOU', 'AND', 'HAVE', 'THEY', 'FOMO', 'TAKE', 'FUD', 'USA', 'CNBC', 'BUY', 'FIRE', 'WE', 'THE', 'ON', 'IS', 'IN', 'IM', 'BUT', 'FOR', 'ARE', 'BE', 'KING', 'HF', 'DFV', 'DD', 'IT', 'HOLD', 'OF', 'US', 'MY', 'LETS', 'GET', 'BACK', 'WEED', 'STOP', 'THAT', 'THIS', 'DO', 'NOT', 'FUCK', 'GANG', 'ALL', 'RIP', 'OTM', 'IV', 'ETF', 'SPDR', 'RIES', 'FTD', 'HSA', 'LIKE', 'HIS', 'SHIT', 'IF', 'HANG', 'SAID', 'HERE', 'IKES', 'HING', 'HE', 'TD', 'JUST', 'HE', 'TD', 'JUST', 'YES', 'WHAT', 'TILL', 'AS', 'VLAD', 'TOCK', 'WHY', 'TING', 'NO', 'OR', 'WHO', 'ANDS', 'MOND', 'HOLY', 'YOUR', 'LOL', 'OH', 'DTCC', 'GUAM', 'ME', 'DONT', 'WITH', 'GOT', 'TIME', 'AOC', 'OULD', 'LLED', 'TION', 'TV', 'WAS', 'MORE', 'OING', 'HAS', 'WANT', 'BS', 'DVF', 'NLP', 'IPO', 'TARD', 'USE', 'PLR', 'FED', 'SELL', 'UP', 'USD', 'KEEP', 'WILL', 'AH', 'ROPE', 'CKIN', 'MEGA', 'JPOW', 'READ', 'IGHT', 'THER', 'EU', 'DOWN', 'VW', 'FD', 'CFO', 'DIP', 'ARK', 'EGME', 'HEIR', 'DING', 'APES', 'UGHT', 'MOON', 'EOD', 'DID', 'DIES', 'NYSE', 'HERS', 'SOLD', 'HODL', 'COME', 'OUR', 'FROM', 'APE', 'YING', 'DIPS', 'WHEN', 'RENT', 'ZERO', 'KNOW', 'HORT', 'LAST', 'LING', 'MING', 'TANT', 'ABLE', 'OVER', 'LIFT', 'EASE', 'BY', 'NING', 'RKET', 'CANT', 'ITS', 'RDAY', 'VIA', 'SNL', 'OOOO', 'DATA', 'NOW', 'STAY', 'OWED', 'ONLY', 'APER', 'NGER', 'ODER', 'ORTS', 'THAN', 'OK', 'ALLS', 'OCKS', 'SDAQ', 'AUSE', 'OUT', 'LET', 'ODAY', 'GING', 'IMIT', 'CASH', 'SEE', 'ALEX', 'LOVE', 'VOTE', 'MF', 'WERE', 'OMG', 'BOYS', 'GOD', 'RAIN', 'GIVE', 'HAND', 'DOOM', 'RED', 'PC', 'WAY', 'CISE', 'VERY', 'ITM', 'EVER', 'ONE', 'HES', 'RE', 'INTO', 'MM', 'ITED', 'RINK', 'PTSD', 'FREE', 'CAP', 'AN', 'NUVO', 'GUYS', 'MAKE', 'LMAO', 'THEM', 'VWAP', 'LION', 'SSR', 'CKET', 'UK', 'HOW', 'ETC', 'TLDR', 'WTF', 'ODOR', 'OASS', 'WARS', 'HINK', 'TUFF', 'TREK', 'BEST', 'STAR', 'XYZ', 'BAN', 'GOOD', 'EADY', 'CUM', 'ASS', 'TITS', 'POOP', 'COCK', 'UI', 'ATM', 'NJ', 'YTD', 'OPEN', 'PM', 'TA', 'BEEN', 'AT', 'LEFT', 'MOVE', 'SAME', 'MANY', 'EACH', 'FORE', 'HIGH', 'OLD', 'CAN', 'RICE', 'BIG', 'RTED', 'DAY', 'GAIN', 'DMV', 'HEAD', 'RONG', 'NEED', 'BABY', 'AVIN', 'LVIN', 'SALE', 'CNN', 'FPS', 'OTC', 'BUYS', 'AINT', 'EIP', 'PFOF', 'MACD', 'MENT', 'LONG', 'IVY', 'WAIT', 'VP', 'AMES', 'TONK', 'HLDG', 'MOLY', 'PMI', 'DJI', 'DTE', 'EV', 'OS', 'CAD', 'QNX', 'RYAN', 'OHEN', 'VIX', 'RMAN', 'CKED', 'NUAL', 'ATED', 'FMR', 'OG', 'NFL', 'IRA', 'FUK', 'QNX', 'XO', 'PR', 'RONK', 'LSD', 'PPI', 'OFF', 'MOLE', 'LFG', 'DA', 'RULE', 'EOW', 'CCP', 'SAYS', 'IRS', 'WFP', 'UN', 'GDP', 'GAS', 'MBS', 'CPI', 'FBI', 'MADE', 'NFT', 'EOM', 'PCE', 'AI', 'MLK', 'LICK', 'INGS', 'IRAN', 'PE', 'FOMC', 'SPX', 'HANK', 'OOGL', 'ATH', 'BBB', 'BLS', 'TACO', 'GUST']

    results = {}
    for w in sorted(d, key=d.get, reverse=True):
        if ((w not in junkWords) and (d[w] > 5)):
           try:
             price = _get_stock_price(w)
             results[w] = {
                 'mentions': d[w],
                 'neg': senti[w]['neg'],
                 'neu': senti[w]['neu'],
                 'pos': senti[w]['pos'],
                 'compound': senti[w]['compound'],
                 'last_price': price
             }
           except (KeyError, ValueError, ZeroDivisionError, IndexError, TypeError) :
               pass
    return pd.DataFrame.from_dict(results, orient='index'), topics

def getSIA(text):
  sia = SentimentIntensityAnalyzer()
  sentiment = sia.polarity_scores(text)
  return sentiment

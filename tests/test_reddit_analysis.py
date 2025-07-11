import unittest
from unittest.mock import patch, MagicMock, call
import pandas as pd

# Import the functions to be tested
from reddit_analysis import get_reddit_instance, get_top_mentioned_stocks_with_sentiment, getSIA

# Mock external dependencies
# Mock console from utils to prevent actual printing during tests
patch('utils.console', MagicMock()).start()

class TestRedditAnalysis(unittest.TestCase):

    @patch('reddit_analysis.praw.Reddit')
    def test_get_reddit_instance_success(self, mock_praw_reddit):
        """Test successful initialization of PRAW instance."""
        with patch('reddit_analysis.REDDIT_CLIENT_ID', 'test_client_id'):
            with patch('reddit_analysis.REDDIT_CLIENT_SECRET', 'test_client_secret'):
                reddit_instance = get_reddit_instance()
                self.assertIsNotNone(reddit_instance)
                mock_praw_reddit.assert_called_once_with(
                    client_id='test_client_id',
                    client_secret='test_client_secret',
                    user_agent="MyBot/0.0.1",
                    check_for_async=False
                )

    @patch('reddit_analysis.praw.Reddit')
    def test_get_reddit_instance_missing_credentials(self, mock_praw_reddit):
        """Test handling of missing Reddit API credentials."""
        with patch('reddit_analysis.REDDIT_CLIENT_ID', 'YOUR_REDDIT_CLIENT_ID'): # Simulate missing ID
            with patch('reddit_analysis.REDDIT_CLIENT_SECRET', 'test_client_secret'):
                reddit_instance = get_reddit_instance()
                self.assertIsNone(reddit_instance)
                mock_praw_reddit.assert_not_called()

    @patch('reddit_analysis.praw.Reddit')
    def test_get_reddit_instance_praw_error(self, mock_praw_reddit):
        """Test handling of PRAW initialization errors."""
        with patch('reddit_analysis.REDDIT_CLIENT_ID', 'test_client_id'):
            with patch('reddit_analysis.REDDIT_CLIENT_SECRET', 'test_client_secret'):
                mock_praw_reddit.side_effect = Exception("PRAW error")
                reddit_instance = get_reddit_instance()
                self.assertIsNone(reddit_instance)

    @patch('reddit_analysis.get_reddit_instance')
    @patch('reddit_analysis.getSIA')
    @patch('yfinance.Ticker')
    def test_get_top_mentioned_stocks_with_sentiment(self, mock_ticker, mock_getSIA, mock_get_reddit_instance):
        """Test fetching top mentioned stocks and sentiment analysis."""
        # Mock Reddit instance and submissions
        mock_reddit = MagicMock()
        mock_submission1 = MagicMock()
        mock_submission1.title = "Hot Topic 1"
        mock_submission1.url = "http://example.com/1"
        mock_submission1.comments = MagicMock()
        mock_submission1.comments.replace_more.return_value = None

        # Create comments to satisfy the > 5 mention threshold for AAPL
        mock_comments = []
        for _ in range(6):
            comment = MagicMock()
            comment.body = "I like $AAPL "
            mock_comments.append(comment)
        
        # Add a comment for another stock that should be filtered out
        comment = MagicMock()
        comment.body = "I like $GME "
        mock_comments.append(comment)

        mock_submission1.comments.__iter__.return_value = mock_comments

        mock_reddit.subreddit.return_value.hot.return_value = [mock_submission1]
        mock_get_reddit_instance.return_value = mock_reddit

        # Mock sentiment analysis for all comments
        mock_getSIA.side_effect = [
            {'neg': 0.0, 'neu': 0.5, 'pos': 0.5, 'compound': 0.6}
        ] * 6 + [{'neg': 0.0, 'neu': 0.5, 'pos': 0.5, 'compound': 0.7}]

        # Mock yfinance Ticker
        mock_aapl_ticker = MagicMock()
        mock_aapl_ticker.history.return_value = pd.DataFrame({'Close': [150.0]}, index=pd.to_datetime(['2023-01-01']))
        mock_gme_ticker = MagicMock()
        mock_gme_ticker.history.return_value = pd.DataFrame({'Close': [25.0]}, index=pd.to_datetime(['2023-01-01']))

        def ticker_side_effect(symbol):
            if symbol == 'AAPL':
                return mock_aapl_ticker
            if symbol == 'GME':
                return mock_gme_ticker
            return MagicMock()

        mock_ticker.side_effect = ticker_side_effect

        df, topics = get_top_mentioned_stocks_with_sentiment()

        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        self.assertIn('AAPL', df.index)
        self.assertNotIn('GME', df.index) # GME should be filtered out

        self.assertEqual(df.loc['AAPL']['mentions'], 6)
        self.assertAlmostEqual(df.loc['AAPL']['compound'], 3.6) # 0.6 * 6
        self.assertEqual(df.loc['AAPL']['last_price'], 150.0)

        self.assertEqual(topics, [{"title": "Hot Topic 1", "url": "http://example.com/1"}])

    def test_getSIA(self):
        """Test VADER sentiment analysis."""
        text = "This is a great day!"
        sentiment = getSIA(text)
        self.assertIn('compound', sentiment)
        self.assertGreater(sentiment['compound'], 0)

if __name__ == '__main__':
    unittest.main()

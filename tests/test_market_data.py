"""test_market_data.py

Unit tests for the market_data.py module.
These tests use unittest.mock to simulate API responses from yfinance and the Treasury FiscalData API,
ensuring that data fetching functions behave as expected without making actual network requests.
"""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import requests

# Import functions from the module to be tested
from market_data import get_stock_info, get_historical_data, get_option_quote, get_bond_yields, _stock_info_cache

class TestMarketData(unittest.TestCase):

    def setUp(self):
        # Clear the cache before each test to ensure isolation
        _stock_info_cache.clear()

    @patch('yfinance.Ticker')
    def test_get_stock_info_success(self, mock_ticker):
        """Test successful fetching of stock info and caching."""
        mock_instance = MagicMock()
        mock_instance.info = {'regularMarketPrice': 150.0, 'open': 149.0}
        mock_ticker.return_value = mock_instance

        info = get_stock_info('AAPL')
        self.assertEqual(info['regularMarketPrice'], 150.0)
        self.assertIn('AAPL', _stock_info_cache)
        mock_ticker.assert_called_once_with('AAPL')

        # Test caching: subsequent call should not call yfinance.Ticker again
        info_cached = get_stock_info('AAPL')
        self.assertEqual(info_cached['regularMarketPrice'], 150.0)
        mock_ticker.assert_called_once_with('AAPL') # Still only one call

    @patch('yfinance.Ticker')
    def test_get_stock_info_failure(self, mock_ticker):
        """Test handling of failure when fetching stock info."""
        mock_ticker.side_effect = Exception("Network error")
        info = get_stock_info('INVALID')
        self.assertEqual(info, {})
        self.assertNotIn('INVALID', _stock_info_cache)

    @patch('yfinance.Ticker')
    def test_get_historical_data_success(self, mock_ticker):
        """Test successful fetching of historical data."""
        mock_instance = MagicMock()
        mock_instance.history.return_value = pd.DataFrame({
            'Close': [100, 101, 102],
            'High': [101, 102, 103],
            'Low': [99, 100, 101],
            'Open': [100, 100, 101]
        })
        mock_ticker.return_value = mock_instance

        df = get_historical_data('AAPL', period="1mo")
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 3)
        mock_ticker.assert_called_once_with('AAPL')
        mock_instance.history.assert_called_once_with(period="1mo", interval="1d")

    @patch('yfinance.Ticker')
    def test_get_historical_data_failure(self, mock_ticker):
        """Test handling of failure when fetching historical data."""
        mock_ticker.side_effect = Exception("API limit reached")
        df = get_historical_data('INVALID')
        self.assertTrue(df.empty)

    @patch('yfinance.Ticker')
    def test_get_option_quote_success(self, mock_ticker):
        """Test successful fetching of an option quote."""
        mock_opt_chain = MagicMock()
        mock_opt_chain.puts = pd.DataFrame({
            'strike': [100, 105, 110],
            'ask': [1.5, 2.0, 2.5],
            'bid': [1.4, 1.9, 2.4],
            'delta': [-0.5, -0.6, -0.7]
        })
        mock_opt_chain.calls = pd.DataFrame({
            'strike': [100, 105, 110],
            'ask': [2.5, 2.0, 1.5],
            'bid': [2.4, 1.9, 1.4],
            'delta': [0.7, 0.6, 0.5]
        })

        mock_instance = MagicMock()
        mock_instance.option_chain.return_value = mock_opt_chain
        mock_ticker.return_value = mock_instance

        # Test PUT option
        price, delta = get_option_quote('SPY', 'PUT', 'bid', 105, '2025-12-31')
        self.assertEqual(price, 1.9)
        self.assertEqual(delta, -0.6)

        # Test CALL option
        price, delta = get_option_quote('SPY', 'CALL', 'ask', 100, '2025-12-31')
        self.assertEqual(price, 2.5)
        self.assertEqual(delta, 0.7)

    @patch('yfinance.Ticker')
    def test_get_option_quote_no_contract(self, mock_ticker):
        """Test handling when no matching option contract is found."""
        mock_opt_chain = MagicMock()
        mock_opt_chain.puts = pd.DataFrame({'strike': [100]})
        mock_opt_chain.calls = pd.DataFrame({'strike': [100]})
        mock_instance = MagicMock()
        mock_instance.option_chain.return_value = mock_opt_chain
        mock_ticker.return_value = mock_instance

        price, delta = get_option_quote('SPY', 'PUT', 'bid', 999, '2025-12-31')
        self.assertEqual(price, -0.0)
        self.assertEqual(delta, -0.0)

    @patch('requests.get')
    def test_get_bond_yields_success(self, mock_requests_get):
        """Test successful fetching of bond yields."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'data': [
                {'record_date': '2025-06-28', 'security_type_desc': 'Marketable', 'security_desc': 'Treasury Bills', 'avg_interest_rate_amt': '4.500'},
                {'record_date': '2025-06-28', 'security_type_desc': 'Non-marketable', 'security_desc': 'Domestic Series', 'avg_interest_rate_amt': '7.000'}
            ]
        }
        mock_requests_get.return_value = mock_response

        df = get_bond_yields()
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['Rate'], 4.500)

    @patch('requests.get')
    def test_get_bond_yields_failure(self, mock_requests_get):
        """Test handling of failure when fetching bond yields."""
        mock_requests_get.side_effect = requests.exceptions.RequestException("API error")
        df = get_bond_yields()
        self.assertTrue(df.empty)

if __name__ == '__main__':
    unittest.main()

"""test_analysis.py

Unit tests for the analysis.py module, specifically the MarketAnalyzer class.
These tests use unittest.mock to isolate the MarketAnalyzer's logic from external dependencies
like yfinance, requests, and TA-Lib, ensuring that its methods behave correctly with mocked data.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import pandas as pd
import datetime
import numpy as np
import pytz

# Import the class to be tested
from analysis import MarketAnalyzer
from utils import TICKER_MAP

# Mock external dependencies
# Mock the console from utils to prevent actual printing during tests
patch('utils.console', MagicMock()).start()

class TestMarketAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = MarketAnalyzer(ticker='$SPX.X', wings=50)

    @patch('analysis.get_stock_info')
    @patch('analysis.find_day')
    @patch('analysis.get_option_quote')
    @patch('datetime.datetime')
    def test_analyze_ironfly_success(self, mock_datetime, mock_get_option_quote, mock_find_day, mock_get_stock_info):
        """Test successful ironfly analysis."""
        mock_datetime.now.return_value = datetime.datetime(2025, 6, 30, 10, 0, 0, tzinfo=pytz.timezone('US/Pacific'))
        mock_datetime.now.return_value.strftime.return_value = '2025-06-30'
        mock_datetime.strptime.side_effect = datetime.datetime.strptime # Keep original strptime functionality
        mock_get_stock_info.return_value = {'regularMarketPrice': 4000.0, 'open': 3990.0}
        mock_find_day.return_value = ('2025-12-31', 100) # expireddate, days
        mock_get_option_quote.side_effect = [
            (0.50, -0.1), # put_ask
            (2.00, -0.5), # put_bid
            (2.10, 0.5),  # call_bid
            (0.60, 0.1)   # call_ask
        ]

        self.analyzer.analyze_ironfly()
        # Assertions to check if the correct methods were called and output is as expected
        mock_get_stock_info.assert_called_with('^GSPC')
        mock_find_day.assert_called_with('^GSPC', '2025-06-30')
        self.assertEqual(mock_get_option_quote.call_count, 4)

    @patch('analysis.get_stock_info')
    @patch('analysis.find_day')
    @patch('analysis.get_option_quote')
    @patch('datetime.datetime')
    def test_analyze_ironfly_fallback(self, mock_datetime, mock_get_option_quote, mock_find_day, mock_get_stock_info):
        """Test ironfly analysis with fallback to SPY."""
        mock_datetime.now.return_value = datetime.datetime(2025, 6, 30, 10, 0, 0, tzinfo=pytz.timezone('US/Pacific'))
        mock_datetime.now.return_value.strftime.return_value = '2025-06-30'
        mock_datetime.strptime.side_effect = datetime.datetime.strptime # Keep original strptime functionality
        # Simulate initial failure for ^GSPC
        mock_get_stock_info.side_effect = [{}, {'regularMarketPrice': 400.0, 'open': 399.0}]
        mock_find_day.side_effect = [(None, 0), ('2025-12-31', 100)]
        mock_get_option_quote.side_effect = [
            (0.50, -0.1), # put_ask
            (2.00, -0.5), # put_bid
            (2.10, 0.5),  # call_bid
            (0.60, 0.1)   # call_ask
        ]

        self.analyzer.analyze_ironfly()
        mock_get_stock_info.assert_any_call('^GSPC')
        mock_get_stock_info.assert_any_call('SPY')
        mock_find_day.assert_any_call('^GSPC', '2025-06-30')
        mock_find_day.assert_any_call('SPY', '2025-06-30')
        self.assertEqual(self.analyzer.ticker, 'SPY') # Ensure ticker was switched

    @patch('analysis.get_stock_info')
    def test_analyze_market_indicators(self, mock_get_stock_info):
        """Test market indicators analysis."""
        mock_get_stock_info.return_value = {
            'regularMarketPrice': 100.0,
            'fiftyTwoWeekLow': 50.0,
            'fiftyTwoWeekHigh': 150.0
        }
        self.analyzer.analyze_market_indicators()
        expected_calls = [
            call(TICKER_MAP['$VIX.X']),
            call(TICKER_MAP['$VIX3M.X']),
            call(TICKER_MAP['$VVIX.X']),
            call(TICKER_MAP['$SKEW.X']),
            call(TICKER_MAP['$VXN.X']),
        ]
        mock_get_stock_info.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_get_stock_info.call_count, len(expected_calls))

    @patch('analysis.get_bond_yields')
    def test_analyze_bond_yields(self, mock_get_bond_yields):
        """Test bond yields analysis."""
        mock_get_bond_yields.return_value = pd.DataFrame({
            'Date': ['2025-01-01', '2025-01-01'],
            'Security Type': ['Marketable', 'Non-marketable'],
            'Security Desc': ['Treasury Bills', 'Domestic Series'],
            'Rate': [4.5, 7.0]
        })
        self.analyzer.analyze_bond_yields()
        mock_get_bond_yields.assert_called_once()

    @patch('analysis.get_historical_data')
    def test_calculate_pivot_points(self, mock_get_historical_data):
        """Test pivot points calculation."""
        mock_get_historical_data.return_value = pd.DataFrame({
            'High': [100, 102, 105],
            'Low': [98, 99, 100],
            'Close': [99, 101, 103],
            'Open': [99, 100, 102]
        })
        self.analyzer.calculate_pivot_points()
        mock_get_historical_data.assert_called_once_with(self.analyzer.ticker, period="5d")

    @patch('analysis.get_historical_data')
    @patch('talib.SMA')
    @patch('talib.EMA')
    @patch('talib.RSI')
    @patch('talib.MACD')
    def test_calculate_technical_indicators(self, mock_macd, mock_rsi, mock_ema, mock_sma, mock_get_historical_data):
        """Test technical indicators calculation."""
        mock_get_historical_data.return_value = pd.DataFrame({
            'High': [float(i) for i in range(200, 400)],
            'Low': [float(i) for i in range(190, 390)],
            'Close': [float(i) for i in range(200, 400)], # Enough data for 200-day SMA
            'Open': [float(i) for i in range(195, 395)]
        })
        # Mock TA-Lib functions to return dummy numpy arrays
        mock_sma.return_value = np.array([1.0, 2.0])
        mock_ema.return_value = np.array([3.0, 4.0])
        mock_rsi.return_value = np.array([50.0, 60.0])
        mock_macd.return_value = (np.array([1.0, 2.0]), np.array([0.5, 1.0]), np.array([0.5, 1.0]))

        self.analyzer.calculate_technical_indicators()
        mock_get_historical_data.assert_called_once_with(self.analyzer.ticker, period="1y")
        mock_sma.assert_called()
        mock_ema.assert_called()
        mock_rsi.assert_called()
        mock_macd.assert_called()

if __name__ == '__main__':
    unittest.main()

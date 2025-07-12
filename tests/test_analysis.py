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

    @patch('analysis.get_spx_option_quotes')
    def test_analyze_ironfly_success(self, mock_get_spx_option_quotes):
        """Test successful ironfly analysis."""
        mock_get_spx_option_quotes.return_value = pd.DataFrame({
            'underlying_price': [4000.0] * 4,
            'option_type': ['put', 'put', 'call', 'call'],
            'strike': [3950, 4000, 4000, 4050],
            'ask': [0.50, 0, 0, 0.60],
            'bid': [0, 2.00, 2.10, 0]
        })

        self.analyzer.analyze_ironfly()
        # Assertions to check if the correct methods were called and output is as expected
        mock_get_spx_option_quotes.assert_called_once()

    

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

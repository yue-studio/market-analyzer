import unittest
from unittest.mock import patch, MagicMock, call
import pandas as pd

# Import the functions to be tested
from get_top_headlines import run_cli, run_streamlit_app

# Mock external dependencies
# Mock console from utils to prevent actual printing during tests
patch('utils.console', MagicMock()).start()

class TestGetTopHeadlines(unittest.TestCase):

    @patch('news_analysis.initialize_newsapi')
    def test_run_cli_top_headlines(self, mock_initialize_newsapi):
        """Test run_cli for top headlines without a symbol."""
        mock_newsapi = MagicMock()
        mock_newsapi.get_top_headlines.return_value = {
            'articles': [
                {'title': 'Headline 1', 'url': 'http://url1.com', 'description': 'Desc 1'},
                {'title': 'Headline 2', 'url': 'http://url2.com', 'description': 'Desc 2'},
            ]
        }
        mock_initialize_newsapi.return_value = mock_newsapi

        with patch('utils.console') as mock_console:
            run_cli()

            mock_newsapi.get_top_headlines.assert_called_once_with(language='en', page_size=10)
            mock_newsapi.get_everything.assert_not_called()
            mock_console.print.assert_any_call("[bold green]Top 10 News Headlines:[/bold green]")
            mock_console.print.assert_any_call("1. Headline 1")
            mock_console.print.assert_any_call("   http://url1.com")
            mock_console.print.assert_any_call("   [dim]Desc 1[/dim]")

    @patch('news_analysis.initialize_newsapi')
    def test_run_cli_symbol_search(self, mock_initialize_newsapi):
        """Test run_cli for news with a stock symbol."""
        mock_newsapi = MagicMock()
        mock_newsapi.get_everything.return_value = {
            'articles': [
                {'title': 'Symbol News 1', 'url': 'http://symbolurl1.com', 'description': 'Symbol Desc 1'},
            ]
        }
        mock_initialize_newsapi.return_value = mock_newsapi

        with patch('utils.console') as mock_console:
            run_cli(symbol='AAPL')

            mock_newsapi.get_everything.assert_called_once_with(q='AAPL', language='en', sort_by='relevancy', page_size=10)
            mock_newsapi.get_top_headlines.assert_not_called()
            mock_console.print.assert_any_call("[bold green]News for AAPL:[/bold green]")
            mock_console.print.assert_any_call("1. Symbol News 1")

    @patch('news_analysis.initialize_newsapi')
    @patch('streamlit.set_page_config')
    @patch('streamlit.title')
    @patch('streamlit.subheader')
    @patch('streamlit.markdown')
    @patch('streamlit.write')
    @patch('streamlit.error')
    @patch('streamlit.warning')
    def test_run_streamlit_app_top_headlines(self, mock_st_warning, mock_st_error, mock_st_write, mock_st_markdown, mock_st_subheader, mock_st_title, mock_st_set_page_config, mock_initialize_newsapi):
        """Test run_streamlit_app for top headlines without a symbol."""
        mock_newsapi = MagicMock()
        mock_newsapi.get_top_headlines.return_value = {
            'articles': [
                {'title': 'ST Headline 1', 'url': 'http://sturl1.com', 'description': 'ST Desc 1'},
            ]
        }
        mock_initialize_newsapi.return_value = mock_newsapi

        run_streamlit_app()

        mock_st_set_page_config.assert_called_once_with(page_title="Top News Headlines", layout="wide")
        mock_st_title.assert_called_once_with("Top 10 News Headlines")
        mock_newsapi.get_top_headlines.assert_called_once_with(language='en', page_size=10)
        mock_st_subheader.assert_called_once_with("1. ST Headline 1")
        mock_st_markdown.assert_any_call("[Read more](http://sturl1.com)", unsafe_allow_html=True)
        mock_st_write.assert_called_once_with("ST Desc 1")
        mock_st_markdown.assert_any_call("<hr>", unsafe_allow_html=True)

    @patch('news_analysis.initialize_newsapi')
    @patch('streamlit.set_page_config')
    @patch('streamlit.title')
    @patch('streamlit.subheader')
    @patch('streamlit.markdown')
    @patch('streamlit.write')
    @patch('streamlit.error')
    @patch('streamlit.warning')
    def test_run_streamlit_app_symbol_search(self, mock_st_warning, mock_st_error, mock_st_write, mock_st_markdown, mock_st_subheader, mock_st_title, mock_st_set_page_config, mock_initialize_newsapi):
        """Test run_streamlit_app for news with a stock symbol."""
        mock_newsapi = MagicMock()
        mock_newsapi.get_everything.return_value = {
            'articles': [
                {'title': 'ST Symbol News 1', 'url': 'http://stsymbolurl1.com', 'description': 'ST Symbol Desc 1'},
            ]
        }
        mock_initialize_newsapi.return_value = mock_newsapi

        run_streamlit_app(symbol='MSFT')

        mock_st_title.assert_called_once_with("News for MSFT")
        mock_newsapi.get_everything.assert_called_once_with(q='MSFT', language='en', sort_by='relevancy', page_size=10)
        mock_newsapi.get_top_headlines.assert_not_called()
        mock_st_subheader.assert_called_once_with("1. ST Symbol News 1")

    @patch('news_analysis.initialize_newsapi')
    @patch('streamlit.error')
    def test_run_streamlit_app_no_newsapi(self, mock_st_error, mock_initialize_newsapi):
        """Test run_streamlit_app when NewsAPI initialization fails."""
        mock_initialize_newsapi.return_value = None
        run_streamlit_app()
        mock_st_error.assert_called_once_with("Failed to initialize NewsAPI. Please check your API key in config.py.")

    @patch('news_analysis.initialize_newsapi')
    @patch('streamlit.warning')
    def test_run_streamlit_app_no_articles(self, mock_st_warning, mock_initialize_newsapi):
        """Test run_streamlit_app when no articles are found."""
        mock_newsapi = MagicMock()
        mock_newsapi.get_top_headlines.return_value = {'articles': []}
        mock_initialize_newsapi.return_value = mock_newsapi
        run_streamlit_app()
        mock_st_warning.assert_called_once_with("No top headlines found.")

if __name__ == '__main__':
    unittest.main()
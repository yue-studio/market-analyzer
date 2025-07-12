import unittest
from unittest.mock import patch, MagicMock, call

# Import the functions to be tested
from get_top_headlines import run_cli, run_streamlit_app

class TestGetTopHeadlines(unittest.TestCase):

    @patch('get_top_headlines.Table')
    @patch('get_top_headlines._get_news_articles')
    @patch('get_top_headlines.initialize_newsapi')
    def test_run_cli_top_headlines(self, mock_initialize_newsapi, mock_get_news_articles, mock_table):
        """Test run_cli for top headlines without a symbol."""
        mock_newsapi = MagicMock()
        mock_initialize_newsapi.return_value = mock_newsapi
        mock_get_news_articles.return_value = {
            'articles': [
                {'title': 'Headline 1', 'url': 'http://url1.com', 'description': 'Desc 1'},
                {'title': 'Headline 2', 'url': 'http://url2.com', 'description': 'Desc 2'},
            ]
        }
        mock_table_instance = mock_table.return_value

        with patch('get_top_headlines.console') as mock_console:
            run_cli()

            mock_get_news_articles.assert_called_once_with(mock_newsapi, None, None, 10)
            
            mock_table.assert_called_once_with(title="Top 10 News Headlines", padding=(0, 1, 1, 1))
            
            calls = [
                call('Title', style='cyan'),
                call('Description', style='dim')
            ]
            mock_table_instance.add_column.assert_has_calls(calls)

            row_calls = [
                call("[link=http://url1.com]Headline 1[/link]", "Desc 1"),
                call("[link=http://url2.com]Headline 2[/link]", "Desc 2")
            ]
            mock_table_instance.add_row.assert_has_calls(row_calls)

            mock_console.print.assert_called_once_with(mock_table_instance)

    @patch('get_top_headlines.Table')
    @patch('get_top_headlines._get_news_articles')
    @patch('get_top_headlines.initialize_newsapi')
    def test_run_cli_symbol_search(self, mock_initialize_newsapi, mock_get_news_articles, mock_table):
        """Test run_cli for news with a stock symbol."""
        mock_newsapi = MagicMock()
        mock_initialize_newsapi.return_value = mock_newsapi
        mock_get_news_articles.return_value = {
            'articles': [
                {'title': 'Symbol News 1', 'url': 'http://symbolurl1.com', 'description': 'Symbol Desc 1'},
            ]
        }
        mock_table_instance = mock_table.return_value
        
        with patch('get_top_headlines.console') as mock_console:
            run_cli(symbol='AAPL')

            mock_get_news_articles.assert_called_once_with(mock_newsapi, 'AAPL', None, 10)
            
            self.assertEqual(mock_table_instance.title, "News for AAPL")
            
            calls = [
                call('Title', style='cyan'),
                call('Description', style='dim')
            ]
            mock_table_instance.add_column.assert_has_calls(calls)

            mock_table_instance.add_row.assert_called_once_with(
                "[link=http://symbolurl1.com]Symbol News 1[/link]",
                "Symbol Desc 1"
            )

            mock_console.print.assert_called_once_with(mock_table_instance)

    @patch('get_top_headlines._get_news_articles')
    @patch('get_top_headlines.initialize_newsapi')
    @patch('streamlit.set_page_config')
    @patch('streamlit.title')
    @patch('streamlit.subheader')
    @patch('streamlit.markdown')
    @patch('streamlit.write')
    @patch('streamlit.error')
    @patch('streamlit.warning')
    def test_run_streamlit_app_top_headlines(self, mock_st_warning, mock_st_error, mock_st_write, mock_st_markdown, mock_st_subheader, mock_st_title, mock_st_set_page_config, mock_initialize_newsapi, mock_get_news_articles):
        """Test run_streamlit_app for top headlines without a symbol."""
        mock_newsapi = MagicMock()
        mock_initialize_newsapi.return_value = mock_newsapi
        mock_get_news_articles.return_value = {
            'articles': [
                {'title': 'ST Headline 1', 'url': 'http://sturl1.com', 'description': 'ST Desc 1'},
            ]
        }

        run_streamlit_app()

        mock_st_set_page_config.assert_called_once_with(page_title="Top News Headlines", layout="wide")
        mock_st_title.assert_called_once_with("Top 10 News Headlines")
        mock_get_news_articles.assert_called_once_with(mock_newsapi, None, None, 10)
        mock_st_subheader.assert_called_once_with("1. ST Headline 1")
        mock_st_markdown.assert_any_call("[Read more](http://sturl1.com)", unsafe_allow_html=True)
        mock_st_write.assert_called_once_with("ST Desc 1")
        mock_st_markdown.assert_any_call("<hr>", unsafe_allow_html=True)

    @patch('get_top_headlines._get_news_articles')
    @patch('get_top_headlines.initialize_newsapi')
    @patch('streamlit.set_page_config')
    @patch('streamlit.title')
    @patch('streamlit.subheader')
    @patch('streamlit.markdown')
    @patch('streamlit.write')
    @patch('streamlit.error')
    @patch('streamlit.warning')
    def test_run_streamlit_app_symbol_search(self, mock_st_warning, mock_st_error, mock_st_write, mock_st_markdown, mock_st_subheader, mock_st_title, mock_st_set_page_config, mock_initialize_newsapi, mock_get_news_articles):
        """Test run_streamlit_app for news with a stock symbol."""
        mock_newsapi = MagicMock()
        mock_initialize_newsapi.return_value = mock_newsapi
        mock_get_news_articles.return_value = {
            'articles': [
                {'title': 'ST Symbol News 1', 'url': 'http://stsymbolurl1.com', 'description': 'ST Symbol Desc 1'},
            ]
        }

        run_streamlit_app(symbol='MSFT')

        mock_st_title.assert_called_once_with("News for MSFT")
        mock_get_news_articles.assert_called_once_with(mock_newsapi, 'MSFT', None, 10)
        mock_st_subheader.assert_called_once_with("1. ST Symbol News 1")

    @patch('get_top_headlines.initialize_newsapi')
    @patch('streamlit.error')
    def test_run_streamlit_app_no_newsapi(self, mock_st_error, mock_initialize_newsapi):
        """Test run_streamlit_app when NewsAPI initialization fails."""
        mock_initialize_newsapi.return_value = None
        run_streamlit_app()
        mock_st_error.assert_called_once_with("Failed to initialize NewsAPI. Please check your API key in config.py.")

    @patch('get_top_headlines._get_news_articles')
    @patch('get_top_headlines.initialize_newsapi')
    @patch('streamlit.warning')
    def test_run_streamlit_app_no_articles(self, mock_st_warning, mock_initialize_newsapi, mock_get_news_articles):
        """Test run_streamlit_app when no articles are found."""
        mock_newsapi = MagicMock()
        mock_initialize_newsapi.return_value = mock_newsapi
        mock_get_news_articles.return_value = {'articles': []}
        run_streamlit_app()
        mock_st_warning.assert_called_once_with("No top headlines found.")

if __name__ == '__main__':
    unittest.main()

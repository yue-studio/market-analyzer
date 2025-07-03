# Market Analyzer

This project provides a comprehensive market analysis tool written in Python. It fetches real-time and historical financial data, performs various market analyses including ironfly options strategy, displays key market indicators, calculates pivot points, and computes technical indicators. It also includes Reddit sentiment analysis and news headline fetching capabilities.

## Features

- **Real-time Data Fetching:** Retrieves stock and options data using the `yfinance` library.
- **Ironfly Options Analysis:** Calculates and displays the strikes and price for an ironfly options strategy, with a fallback to SPY if SPX options data is unavailable.
- **Market Indicators:** Fetches and presents volatility indices (VIX, VIX3M, VVIX, SKEW, VXN).
- **Bond Yields:** Retrieves and displays daily average interest rates from the U.S. Treasury FiscalData API.
- **Technical Analysis:** Calculates and displays popular technical indicators including Simple Moving Averages (SMA), Exponential Moving Averages (EMA), Relative Strength Index (RSI), and Moving Average Convergence Divergence (MACD).
- **Pivot Point Calculation:** Computes and displays classical pivot points.
- **Reddit Sentiment Analysis:** Analyzes sentiment and mentions of stock symbols on r/wallstreetbets, and displays the top 20 hot topics.
- **News Headlines:** Fetches and displays the top 10 news headlines, with options to search by stock symbol and run as a Streamlit application.
- **Modular Design:** The codebase is organized into reusable modules (`market_data.py`, `analysis.py`, `utils.py`, `reddit_analysis.py`, `news_analysis.py`, `get_top_headlines.py`).
- **Command-Line Interface:** Easily configurable via command-line arguments.
- **Formatted Output:** Utilizes the `rich` library for beautiful and readable terminal output.
- **Unit Tests:** Comprehensive unit tests ensure the reliability and correctness of the core logic.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/market-analyzer.git
    cd market-analyzer
    ```

2.  **Install TA-Lib (C Library):**
    The `TA-Lib` Python library requires the underlying C library to be installed on your system. Follow the instructions for your operating system:

    -   **macOS (using Homebrew):**
        ```bash
        brew install ta-lib
        ```

    -   **Debian/Ubuntu (using apt-get):**
        ```bash
        sudo apt-get update
        sudo apt-get install ta-lib
        ```

    -   **Windows:**
        Download the pre-compiled `TA-Lib` library from [Unofficial Windows Binaries for Python Extension Packages](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib). Look for the `.whl` file corresponding to your Python version and system architecture (e.g., `TA_Lib‑0.4.24‑cp39‑cp39‑win_amd64.whl` for Python 3.9 64-bit). Then install it using pip:
        ```bash
        pip install path/to/your/downloaded/TA_Lib‑*.whl
        ```

3.  **Install Python Dependencies:**
    It's recommended to use a virtual environment.
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: .\venv\Scripts\activate
    pip install -r requirements.txt
    ```

## Configuration

This project uses API keys for NewsAPI and Reddit. You need to set these up in `config.py`.

-   **NewsAPI Key:**
    1.  Get a key from [newsapi.org](https://newsapi.org/).
    2.  Open `config.py` and replace `'YOUR_NEWS_API_KEY'` with your actual key.

-   **Reddit API Credentials:**
    1.  Go to [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps).
    2.  Click "are you a developer? create an app..."
    3.  Fill out the form:
        *   **name:** MyBot (or any name you want)
        *   **type:** script
        *   **description:** (leave blank)
        *   **about url:** (leave blank)
        *   **redirect uri:** `http://localhost:8080`
    4.  Click "create app".
    5.  Your `client_id` will be under "personal use script" and your `client_secret` will be next to "secret".
    6.  Open `config.py` and replace `'YOUR_REDDIT_CLIENT_ID'` and `'YOUR_REDDIT_CLIENT_SECRET'` with your actual credentials.

## Usage

Run the main script from the command line:

```bash
python3 market_analyzer.py
```

### Command-Line Arguments

-   `-t`, `--ticker TICKER`: The main ticker symbol to analyze (e.g., `$SPX.X`, `SPY`, `AAPL`).
    -   Default: `$SPX.X`
-   `-w`, `--wings WINGS`: The width of the ironfly options strategy wings.
    -   Default: `50`
-   `-r`, `--reddit-analysis`: Perform Reddit sentiment analysis and display top hot topics.
-   `-n`, `--news-analysis`: Perform news sentiment analysis for the main ticker.
-   `-top`, `--top-headlines`: Print the top 10 news headlines.
-   `--symbol SYMBOL`: Search for news related to a specific stock symbol (used with `get_top_headlines.py` or `--top-headlines`).
-   `-p`, `--plot-vix-ratio`: Plot VIX and VIX3M ratio.
-   `--vix-period VIX_PERIOD`: Historical period for VIX ratio plot (e.g., `6mo`, `1y`, `5y`).
-   `-ta`, `--plot-ta`: Plot price and technical indicators.
-   `--ta-period TA_PERIOD`: Historical period for TA plot (e.g., `6mo`, `1y`, `5y`).
-   `-a`, `--plot-all`: Plot both VIX ratio and technical indicators.
-   `-e`, `--export-data`: Export analysis results to CSV/JSON files.
-   `-d`, `--debug`: Enable debug messages.

**Examples:**

-   Analyze SPY with default ironfly wings:
    ```bash
    python3 market_analyzer.py --ticker SPY
    ```

-   Analyze Apple (AAPL) with custom ironfly wings:
    ```bash
    python3 market_analyzer.py --ticker AAPL --wings 10
    ```

-   Perform Reddit sentiment analysis:
    ```bash
    python3 market_analyzer.py -r
    ```

-   Get top 10 news headlines:
    ```bash
    python3 market_analyzer.py -top
    ```

-   Get news for a specific symbol (e.g., TSLA) using the top headlines option:
    ```bash
    python3 market_analyzer.py -top --symbol TSLA
    ```

-   Run `get_top_headlines.py` as a Streamlit app:
    ```bash
    streamlit run get_top_headlines.py -- --mode streamlit
    ```

-   Run `get_top_headlines.py` as a Streamlit app and search for news about a symbol:
    ```bash
    streamlit run get_top_headlines.py -- --mode streamlit --symbol MSFT
    ```

## Running Tests

To run the unit tests, navigate to the project root directory and execute:

```bash
python3 -m unittest discover -s tests
```

## File Structure

```
market-analyzer/
├── market_analyzer.py      # Main script to run the analysis
├── analysis.py             # Contains the MarketAnalyzer class and analysis logic
├── market_data.py          # Functions for fetching data from yfinance and Treasury API
├── utils.py                # Utility functions and shared configurations
├── requirements.txt        # List of Python dependencies
├── README.md               # Project documentation
├── .gitignore              # Specifies intentionally untracked files to ignore
├── config.py               # Configuration for API keys (NewsAPI, Reddit)
├── news_analysis.py        # Functions for fetching and analyzing news
├── reddit_analysis.py      # Functions for fetching and analyzing Reddit data
├── get_top_headlines.py    # Script to fetch and display top news headlines (CLI/Streamlit)
└── tests/
    ├── test_analysis.py    # Unit tests for analysis.py
    └── test_market_data.py # Unit tests for market_data.py
```
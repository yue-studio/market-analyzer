from openbb import obb
import pandas as pd

def get_spx_option_quotes():
    """
    Fetches SPX option chains, filters for DTE=0, and returns a DataFrame
    with relevant put and call options around the underlying price.
    """
    obb.user.preferences.output_type = "dataframe"
    options = obb.derivatives.options.chains(symbol="SPX", provider="cboe")

    # Filter for dte == 0
    options = options[options['dte'] == 0]

    if options.empty:
        return pd.DataFrame() # Return empty DataFrame if no options found

    underlying_price = options['underlying_price'].iloc[0]

    # Filter for puts below underlying_price
    puts_below = options[(options['strike'] < underlying_price) & (options['option_type'] == 'put')]
    puts_below_selected = puts_below.sort_values(by='strike', ascending=False).head(10)

    # Filter for calls above underlying_price
    calls_above = options[(options['strike'] > underlying_price) & (options['option_type'] == 'call')]
    calls_above_selected = calls_above.sort_values(by='strike', ascending=True).head(10)

    # Filter for at-the-money options (both calls and puts)
    at_the_money = options[options['strike'] == underlying_price]

    # Concatenate and sort by strike
    final_options = pd.concat([puts_below_selected, at_the_money, calls_above_selected]).sort_values(by='strike')

    # Remove specified columns
    columns_to_remove = ['underlying_symbol', 'contract_symbol', 'expiration', 'dte', 'gamma', 'theta', 'vega', 'rho', 'prev_close', 'change_percent', 'last_trade_time', 'bid_size', 'ask_size', 'open', 'high', 'low', 'change', 'implied_volatility']
    final_options = final_options.drop(columns=columns_to_remove, errors='ignore')

    return final_options
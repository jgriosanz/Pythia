"""
Alpha Vantage End-points and Parameters

Documentation:   https://www.alphavantage.co/documentation/
"""

import re
from src.config import crypto_currencies
from src.utils import LOG, get_tabs


ALPHA_VANTAGE_URI = "https://www.alphavantage.co/query"
fx_regex = re.compile("^fx_")
digital_regex = re.compile("^digital_")
fx_data_regex = re.compile(r"\A[A-Z]{3,4}_[A-Z]{3,4}")
fx_crypto_regex = re.compile(r"\ACRYPTO_[A-Z]{3,4}_[A-Z]{3,4}")


def validate_stock_symbol(symbol):
    if not isinstance(symbol, str):
        raise TypeError("Stock symbol must be a string")


def validate_currency_pair(symbol):
    if not isinstance(symbol, (list, tuple)):
        raise TypeError("Currency symbol must be a list of two elements")
    if not len(symbol) == 2:
        raise TypeError("Currency symbol must be a list of two elements")


def get_api_function(category):
    category = category.lower()
    if category == "daily":
        function = "TIME_SERIES_DAILY"
    elif category == "daily-adjusted":
        function = "TIME_SERIES_DAILY_ADJUSTED"
    elif category == "weekly":
        function = "TIME_SERIES_WEEKLY"
    elif category == "weekly-adjusted":
        function = "TIME_SERIES_WEEKLY_ADJUSTED"
    elif category == "monthly":
        function = "TIME_SERIES_MONTHLY"
    elif category == "monthly-adjusted":
        function = "TIME_SERIES_MONTHLY_ADJUSTED"
    elif category in ["fx", "fx_daily"]:
        function = "FX_DAILY"
    elif fx_regex.match(category):
        function = category.upper()
    elif category in ["digital", "digital_fx", "digital_daily"]:
        function = "DIGITAL_CURRENCY_DAILY"
    elif category == "digital_keekly":
        function = "DIGITAL_CURRENCY_WEEKLY"
    elif category == "digital_monthly":
        function = "DIGITAL_CURRENCY_MONTHLY"
    elif category == "sector":
        function = "SECTOR"
    else:
        raise ValueError(f"invalid category {category}")
    return function


def alpha_vantage_query(symbol, category, output_size=None, datatype=None, key=None, **kwargs):
    url = ALPHA_VANTAGE_URI
    datatype = "json" if datatype is None else datatype             # Valid: csv, json
    output_size = "full" if output_size is None else output_size    # Valid: full, compact (only 100 points)
    category = category.lower()

    if category in ["daily", "daily-adjusted", "weekly", "weekly-adjusted", "monthly", "monthly-adjusted"]:
        validate_stock_symbol(symbol)
        # Retrieval of daily time series
        function = get_api_function(category)

        params = {"function": function, "symbol": symbol, "outputsize": output_size,
                  "datatype": datatype, "apikey": key}

    elif category == "search":
        # Retrieval of best-matching symbols (with scores) and market info
        function = "SYMBOL_SEARCH"
        params = {"function": function, "keywords": symbol, "datatype": datatype, "apikey": key}
        # f"{ALPHA_VANTAGE_URI}?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize={outputsize}&apikey={key}"

    elif category in ["fx_exchange", "fx_rate"] or bool(fx_regex.match(category)):
        # FX exchange requires two values, from what symbol and to what symbol
        if isinstance(symbol, dict):        # Process dict
            if not all([k in symbol.keys() for k in ["from_currency", "to_currency"]]):
                raise KeyError("Required parameters (from_currency, to_currency) not provided")
            from_crrn, to_crrn = symbol["from_currency"], symbol["to_currency"]

        elif isinstance(symbol, str):
            if fx_data_regex.match(symbol):
                from_crrn, to_crrn = symbol.split("_")
            else:
                raise ValueError("Not valid values found")

        elif isinstance(symbol, (list, tuple)):                               # Process list
            validate_currency_pair(symbol)
            from_crrn, to_crrn = symbol

        else:
            raise TypeError("Unexpected type in symbol")

        if category in ["fx_exchange", "fx_rate"]:
            # Retrieval of currency exchange rates
            function = "CURRENCY_EXCHANGE_RATE"
            params = {"function": function, "from_currency": from_crrn, "to_currency": to_crrn, "apikey": key}
        else:
            # Retrieval of historical rates
            function = get_api_function(category)
            params = {"function": function, "from_symbol": from_crrn, "to_symbol": to_crrn,
                      "outputsize": output_size, "datatype": datatype, "apikey": key}

    elif category in ["digital", "digital_fx"] or bool(digital_regex.match(category)):
        # Digital requires two values, the symbol and the market
        if isinstance(symbol, dict):        # Process dict
            if not all([k in symbol.keys() for k in ["symbol", "market"]]):
                raise KeyError("Required parameters (symbol, market) not provided")
            symbol, market = symbol["symbol"], symbol["market"]

        elif isinstance(symbol, str):
            if fx_crypto_regex.match(symbol):
                symbol, market = symbol.split("_")
            else:
                raise ValueError("Not valid values found")
        elif isinstance(symbol, (list, tuple)):                               # Process list
            validate_currency_pair(symbol)
            symbol, market = symbol

        else:
            raise TypeError("Unexpected type in symbol")

        if symbol not in crypto_currencies:
            raise ValueError("The symbol must be a valid cryptocurrency. Please introduce the value in the table")

        if category in ["digital_exchange"]:
            # Retrieval of currency exchange rates
            function = "CURRENCY_EXCHANGE_RATE"
            params = {"function": function, "symbol": symbol, "market": market, "apikey": key}
        else:
            # Retrieval of historical rates
            function = get_api_function(category)
            params = {"function": function, "symbol": symbol, "market": market,
                      "outputsize": output_size, "datatype": datatype, "apikey": key}
    elif category == "sector":
        function = get_api_function(category)
        params = {"function": function, "apikey": key}

    else:
        raise Exception(f"Category {category} not found")

    # Use extra parameters provided
    params = {**params, **kwargs}
    return url, params


def manage_vantage_errors(response, symbol):
    if "Error Message" in response.keys():
        LOG.error(f"ERROR: Not possible to retrieve {symbol}. Msg: {response['Error Message']}")
    elif "Note" in response.keys():
        if response["Note"][:111] == 'Thank you for using Alpha Vantage! Our standard API call frequency ' \
                                     'is 5 calls per minute and 500 calls per day.':
            LOG.info(f"Retrieving {symbol}:{get_tabs(symbol, prev=12)}Max frequency reached! Waiting...")
            return "longWait"
    return None

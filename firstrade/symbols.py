from firstrade import urls
from firstrade.account import FTSession
from firstrade.exceptions import QuoteRequestError, QuoteResponseError


class SymbolQuote:
    """
    Data class representing a stock quote for a given symbol.

    Attributes:
        ft_session (FTSession): The session object used for making HTTP requests to Firstrade.
        symbol (str): The symbol for which the quote information is retrieved.
        sec_type (str): The security type of the symbol.
        tick (str): The tick size of the symbol.
        bid (int): The bid price for the symbol.
        bid_size (int): The size of the bid.
        ask (int): The ask price for the symbol.
        ask_size (int): The size of the ask.
        last (float): The last traded price for the symbol.
        change (float): The change in price for the symbol.
        high (float): The highest price for the symbol during the trading day.
        low (float): The lowest price for the symbol during the trading day.
        bid_mmid (str): The market maker ID for the bid.
        ask_mmid (str): The market maker ID for the ask.
        last_mmid (str): The market maker ID for the last trade.
        last_size (int): The size of the last trade.
        change_color (str): The color indicating the change in price.
        volume (str): The volume of shares traded for the symbol.
        today_close (float): The closing price for the symbol today.
        open (str): The opening price for the symbol.
        quote_time (str): The time of the quote.
        last_trade_time (str): The time of the last trade.
        company_name (str): The name of the company associated with the symbol.
        exchange (str): The exchange where the symbol is traded.
        has_option (bool): Indicates if the symbol has options.
        is_etf (bool): Indicates if the symbol is an ETF.
        is_fractional (bool): Indicates if the stock can be traded fractionally.
        realtime (str): Indicates if the quote is real-time.
        nls (str): Nasdaq last sale.
        shares (int): The number of shares.
    """

    def __init__(self, ft_session: FTSession, account: str, symbol: str):
        """
        Initializes a new instance of the SymbolQuote class.

        Args:
            ft_session (FTSession): The session object used for making HTTP requests to Firstrade.
            account (str): The account number for which the quote information is retrieved.
            symbol (str): The symbol for which the quote information is retrieved.

        Raises:
            QuoteRequestError: If the quote request fails with a non-200 status code.
            QuoteResponseError: If the quote response contains an error message.
        """
        self.ft_session = ft_session
        response = self.ft_session.get(url=urls.quote(account, symbol))
        if response.status_code != 200:
            raise QuoteRequestError(response.status_code)
        if response.json().get("error", "") != "":
            raise QuoteResponseError(symbol, response.json()["error"])
        self.symbol = response.json()["result"]["symbol"]
        self.sec_type = response.json()["result"]["sec_type"]
        self.tick = response.json()["result"]["tick"]
        self.bid = response.json()["result"]["bid"]
        self.bid_size = response.json()["result"]["bid_size"]
        self.ask = response.json()["result"]["ask"]
        self.ask_size = response.json()["result"]["ask_size"]
        self.last = response.json()["result"]["last"]
        self.change = response.json()["result"]["change"]
        self.high = response.json()["result"]["high"]
        self.low = response.json()["result"]["low"]
        self.bid_mmid = response.json()["result"]["bid_mmid"]
        self.ask_mmid = response.json()["result"]["ask_mmid"]
        self.last_mmid = response.json()["result"]["last_mmid"]
        self.last_size = response.json()["result"]["last_size"]
        self.change_color = response.json()["result"]["change_color"]
        self.volume = response.json()["result"]["vol"]
        self.today_close = response.json()["result"]["today_close"]
        self.open = response.json()["result"]["open"]
        self.quote_time = response.json()["result"]["quote_time"]
        self.last_trade_time = response.json()["result"]["last_trade_time"]
        self.company_name = response.json()["result"]["company_name"]
        self.exchange = response.json()["result"]["exchange"]
        self.has_option = response.json()["result"]["has_option"]
        self.is_etf = bool(response.json()["result"]["is_etf"])
        self.is_fractional = bool(response.json()["result"]["is_fractional"])
        self.realtime = response.json()["result"]["realtime"]
        self.nls = response.json()["result"]["nls"]
        self.shares = response.json()["result"]["shares"]


class OptionQuote:
    """
    Data class representing an option quote for a given symbol.

    Attributes:
        ft_session (FTSession): The session object used for making HTTP requests to Firstrade.
        symbol (str): The symbol for which the option quote information is retrieved.
        option_dates (dict): A dict of expiration dates for options on the given symbol.
    """

    def __init__(self, ft_session: FTSession, symbol: str):
        """
        Initializes a new instance of the OptionQuote class.

        Args:
            ft_session (FTSession):
                The session object used for making HTTP requests to Firstrade.
            symbol (str): The symbol for which the option quote information is retrieved.
        """
        self.ft_session = ft_session
        self.symbol = symbol
        self.option_dates = self.get_option_dates(symbol)

    def get_option_dates(self, symbol: str):
        """
        Retrieves the expiration dates for options on a given symbol.

        Args:
            symbol (str): The symbol for which the expiration dates are retrieved.

        Returns:
            dict: A dict of expiration dates and other information for options on the given symbol.

        Raises:
            QuoteRequestError: If the request for option dates fails with a non-200 status code.
            QuoteResponseError: If the response for option dates contains an error message.
        """
        response = self.ft_session.get(url=urls.option_dates(symbol))
        return response.json()

    def get_option_quote(self, symbol: str, date: str):
        """
        Retrieves the quote for a given option symbol.

        Args:
            symbol (str): The symbol for which the quote is retrieved.

        Returns:
            dict: A dictionary containing the quote  and other information for the given option symbol.

        Raises:
            QuoteRequestError: If the request for the option quote fails with a non-200 status code.
            QuoteResponseError: If the response for the option quote contains an error message.
        """
        response = self.ft_session.get(url=urls.option_quotes(symbol, date))
        return response.json()

    def get_greek_options(self, symbol: str, exp_date: str):
        """
        Retrieves the greeks for options on a given symbol.

        Args:
            symbol (str): The symbol for which the greeks are retrieved.
            exp_date (str): The expiration date of the options.

        Returns:
            dict: A dictionary containing the greeks for the options on the given symbol.

        Raises:
            QuoteRequestError: If the request for the greeks fails with a non-200 status code.
            QuoteResponseError: If the response for the greeks contains an error message.
        """
        data = {
            "type": "chain",
            "chains_range": "A",
            "root_symbol": symbol,
            "exp_date": exp_date,
        }
        response = self.ft_session.post(url=urls.greek_options(), data=data)
        return response.json()

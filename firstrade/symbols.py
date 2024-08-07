from bs4 import BeautifulSoup

from firstrade import urls
from firstrade.account import FTSession


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
            ft_session (FTSession):
                The session object used for making HTTP requests to Firstrade.
            account (str): The account number for which the quote information is retrieved.
            symbol (str): The symbol for which the quote information is retrieved.
        """
        self.ft_session = ft_session
        response = self.ft_session.get(url=urls.quote(account, symbol))
        if response.status_code != 200 or response.json()["error"] != "":
            raise Exception(f"Failed to get quote for {symbol}. API returned the following error: {response.json()['error']}")
        self.symbol = response.json()["result"]["symbol"]
        self.sec_type = response.json()["result"]["sec_type"]
        self.tick = response.json()["result"]["tick"]
        self.bid = int(response.json()["result"]["bid"].replace(",", ""))
        temp_store = response.json()["result"]["bid_size"].replace(",", "")
        self.bid_size = int(temp_store) if temp_store.isdigit() else 0
        self.ask = int(response.json()["result"]["ask"](",", ""))
        temp_store = response.json()["result"]["ask_size"](",", "")
        self.ask_size = int(temp_store) if temp_store.isdigit() else 0
        self.last = float(response.json()["result"]["last"].replace(",", ""))
        self.change = float(response.json()["result"]["change"].replace(",", ""))
        self.high = float(response.json()["result"]["high"].replace(",", "") if response.json()["result"]["high"] != "N/A" else None)
        self.low = float(response.json()["result"]["low"].replace(",", "") if response.json()["result"]["low"] != "N/A" else None)
        self.bid_mmid = response.json()["result"]["bid_mmid"]
        self.ask_mmid = response.json()["result"]["ask_mmid"]
        self.last_mmid = response.json()["result"]["last_mmid"]
        temp_store = response.json()["result"]["last_size"].replace(",", "")
        self.last_size = int(temp_store) if temp_store.isdigit() else 0
        self.change_color = response.json()["result"]["change_color"]
        self.volume = response.json()["result"]["vol"]
        self.today_close = float(response.json()["result"]["today_close"].replace(",", ""))
        self.open = response.json()["result"]["open"].replace(",", "")
        self.quote_time = response.json()["result"]["quote_time"]
        self.last_trade_time = response.json()["result"]["last_trade_time"]
        self.company_name = response.json()["result"]["company_name"]
        self.exchange = response.json()["result"]["exchange"]
        self.has_option = bool(response.json()["result"]["has_option"])
        self.is_etf = bool(response.json()["result"]["is_etf"])
        self.is_fractional = bool(response.json()["result"]["is_fractional"])
        self.realtime = response.json()["result"]["realtime"]
        self.nls = response.json()["result"]["nls"]
        self.shares = int(response.json()["result"]["shares"].replace(",", ""))

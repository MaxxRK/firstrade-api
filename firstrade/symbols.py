from bs4 import BeautifulSoup

from firstrade import urls
from firstrade.account import FTSession


class SymbolQuote:
    """
    Dataclass containing quote information for a symbol.

    Attributes:
        ft_session (FTSession):
            The session object used for making HTTP requests to Firstrade.
        symbol (str): The symbol for which the quote information is retrieved.
        exchange (str): The exchange where the symbol is traded.
        bid (float): The bid price for the symbol.
        ask (float): The ask price for the symbol.
        last (float): The last traded price for the symbol.
        change (float): The change in price for the symbol.
        high (float): The highest price for the symbol during the trading day.
        low (float): The lowest price for the symbol during the trading day.
        volume (str): The volume of shares traded for the symbol.
        company_name (str): The name of the company associated with the symbol.
        real_time (bool): If the quote is real-time or not
        fractional (bool):  If the stock can be traded fractionally, or not
    """

    def __init__(self, ft_session: FTSession, symbol: str):
        """
        Initializes a new instance of the SymbolQuote class.

        Args:
            ft_session (FTSession):
                The session object used for making HTTP requests to Firstrade.
            symbol (str): The symbol for which the quote information is retrieved.
        """
        self.ft_session = ft_session
        self.symbol = symbol
        symbol_data = self.ft_session.get(
            url=urls.quote(self.symbol), headers=urls.session_headers()
        )
        soup = BeautifulSoup(symbol_data.text, "xml")
        quote = soup.find("quote")
        self.symbol = quote.find("symbol").text
        self.underlying_symbol = quote.find("underlying_symbol").text
        self.tick = quote.find("tick").text
        self.exchange = quote.find("exchange").text
        self.bid = float(quote.find("bid").text.replace(",", ""))
        self.ask = float(quote.find("ask").text.replace(",", ""))
        self.last = float(quote.find("last").text.replace(",", ""))
        temp_store = quote.find("bidsize").text.replace(",", "")
        self.bid_size = int(temp_store) if temp_store.isdigit() else 0
        temp_store = quote.find("asksize").text.replace(",", "")
        self.ask_size = int(temp_store) if temp_store.isdigit() else 0
        temp_store = quote.find("lastsize").text.replace(",", "")
        self.last_size = int(temp_store) if temp_store.isdigit() else 0
        self.bid_mmid = quote.find("bidmmid").text
        self.ask_mmid = quote.find("askmmid").text
        self.last_mmid = quote.find("lastmmid").text
        self.change = float(quote.find("change").text.replace(",", ""))
        if quote.find("high").text == "N/A":
            self.high = None
        else:
            self.high = float(quote.find("high").text.replace(",", ""))
        if quote.find("low").text == "N/A":
            self.low = "None"
        else:
            self.low = float(quote.find("low").text.replace(",", ""))
        self.change_color = quote.find("changecolor").text
        self.volume = quote.find("vol").text
        self.bidxask = quote.find("bidxask").text
        self.quote_time = quote.find("quotetime").text
        self.last_trade_time = quote.find("lasttradetime").text
        self.real_time = quote.find("realtime").text == "T"
        self.fractional = quote.find("fractional").text == "T"
        self.err_code = quote.find("errcode").text
        self.company_name = quote.find("companyname").text

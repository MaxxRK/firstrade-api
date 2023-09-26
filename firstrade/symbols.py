from bs4 import BeautifulSoup
from account import FTSession
from decimal import Decimal as D
import urls


class SymbolInfo:
    def __init__(self, ft_session: FTSession, symbol: str):
        self.ft_session = ft_session
        self.symbol = symbol
        self.exchange = ""
        self.bid = 0
        self.ask = 0
        self.last = 0
        self.change = 0
        self.high = 0
        self.low = 0
        self.volume = 0
        self.company_name = ""
        self.get_quote()

    def get_quote(self):
        url = urls.quote(self.symbol)
        headers = urls.quote_headers()
        symbol_data = self.ft_session.get(url=url, headers=headers)
        soup = BeautifulSoup(symbol_data.text, 'xml')
        quote = soup.find('quote')
        self.symbol = quote.find('symbol').text
        self.exchange = quote.find('exchange').text
        self.bid = D(quote.find('bid').text)
        self.ask = D(quote.find('ask').text)
        self.last = D(quote.find('last').text)
        self.change = D(quote.find('change').text)
        self.high = D(quote.find('high').text)
        self.low = D(quote.find('low').text)
        self.volume = quote.find('vol').text
        self.company_name = quote.find('companyname').text

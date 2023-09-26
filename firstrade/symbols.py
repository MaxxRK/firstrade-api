from bs4 import BeautifulSoup
from account import FTSession
from decimal import Decimal as D


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
        url = f'https://invest.firstrade.com/cgi-bin/getxml?page=quo&quoteSymbol={self.symbol}'

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Host': 'invest.firstrade.com',
            'Referer': 'https://invest.firstrade.com/cgi-bin/main',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.81',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Microsoft Edge";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
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


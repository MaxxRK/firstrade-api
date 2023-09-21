import requests
import pickle
import re
from bs4 import BeautifulSoup


class FTSession:
    def __init__(self, username, password, pin):
        self.username = username
        self.password = password
        self.pin = pin
        self.session = requests.Session()
        self.cookies = {}
        self.account_numbers = []
        self.login()

    def login(self):
        cookies = self.load_cookies()
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
        cookies = requests.utils.cookiejar_from_dict(cookies)
        self.session.cookies.update(cookies)
        url = 'https://invest.firstrade.com/cgi-bin/getxml?'
        if "/cgi-bin/sessionfailed?reason=6" in self.session.get(url=url, headers=headers, cookies=cookies).text:
            url = 'https://invest.firstrade.com/cgi-bin/login'
            headers = {
                'Host': 'invest.firstrade.com',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': '"Microsoft Edge";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.31',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            self.session.get(url=url, headers=headers)
            url = 'https://invest.firstrade.com/cgi-bin/login'
            headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Length': '109',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'invest.firstrade.com',
            'Origin': 'https://invest.firstrade.com',
            'Referer': 'https://invest.firstrade.com/cgi-bin/login',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.81',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Microsoft Edge";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

            data = {
            'redirect': '',
            'ft_locale': 'en-us',
            'login.x': 'Log In',
            'username': self.username,
            'password': self.password,
            'destination_page': 'home'
        }
                          
            self.session.post(url=url, headers=headers, cookies=self.session.cookies, data=data)

            url = 'https://invest.firstrade.com/cgi-bin/enter_pin?destination_page=home'

            headers ={
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Length': '60',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'invest.firstrade.com',
            'Origin': 'https://invest.firstrade.com',
            'Referer': 'https://invest.firstrade.com/cgi-bin/enter_pin?destination_page=home',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.81',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Microsoft Edge";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

            data = {
            'destination_page': 'home',
            'pin': self.pin,
            'pin.x': '++OK++',
            'sring': '0',
            'pin': self.pin
        }
        
            self.session.post(url=url, headers=headers, cookies=self.session.cookies, data=data)
            self.save_cookies()
        self.cookies = self.session.cookies

    def load_cookies(self):
        try:
            with open('cookies.pkl', 'rb') as f:
                cookies = pickle.load(f)
        except:
            cookies = {}
        return cookies

    def save_cookies(self):
        with open('cookies.pkl', 'wb') as f:
            pickle.dump(self.session.cookies.get_dict(), f)
    
    def __getattr__(self, name):
        # forward unknown attribute access to session object
        return getattr(self.session, name)
        

class FTAccountData:
     
    def accounts(self):
        url = '	https://invest.firstrade.com/cgi-bin/getaccountlist'
        headers = {
            'Host': 'invest.firstrade.com',
            'Connection': 'keep-alive',
            'Content-Length': '0',
            'sec-ch-ua': '"Microsoft Edge";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'Accept': 'text/html, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.31',
            'sec-ch-ua-platform': '"Windows"',
            'Origin': 'https://invest.firstrade.com',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://invest.firstrade.com/cgi-bin/main',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        html_string = self.session.get(url=url, headers=headers, cookies=self.cookies).text
        self.account_numbers = re.findall(r"accountChangeSubmit\('(\d+)',", html_string)
        return self.account_numbers
        

symbol = 'INTC'
url = f'https://invest.firstrade.com/cgi-bin/getxml?page=quo&quoteSymbol={symbol}'
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
symbol_data = firstrade_session.get(url=url, headers=headers)
soup = BeautifulSoup(symbol_data.text, 'xml')
quote = soup.find('quote')
symbol = quote.find('symbol').text
exchange = quote.find('exchange').text
bid = quote.find('bid').text
ask = quote.find('ask').text
last = quote.find('last').text
change = quote.find('change').text
high = quote.find('high').text
low = quote.find('low').text
volume = quote.find('vol').text
company_name = quote.find('companyname').text

print(f"Symbol: {symbol}")
print(f"Exchange: {exchange}")
print(f"Bid: {bid}")
print(f"Ask: {ask}")
print(f"Last: {last}")
print(f"Change: {change}")
print(f"High: {high}")
print(f"Low: {low}")
print(f"Volume: {volume}")
print(f"Company Name: {company_name}")
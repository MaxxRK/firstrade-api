import requests
import pickle
import re
from bs4 import BeautifulSoup
from firstrade import urls


class FTSession:
    """
    Class creating a session for Firstrade.
    """
    def __init__(self, username, password, pin, persistent_session=False):
        """
        Initializes a new instance of the FTSession class.

        Args:
            username (str): Firstrade login username.
            password (str): Firstrade login password.
            pin (str): Firstrade login pin.
            persistent_session (bool, optional): Whether the user wants to save the session cookies. Defaults to False.
        """
        self.username = username
        self.password = password
        self.pin = pin
        self.persistent_session = persistent_session
        self.session = requests.Session()
        self.cookies = {}
        self.login()

    def login(self):
        """
        Method to validate and login to the Firstrade platform.
        """
        headers = urls.session_headers()
        cookies = self.load_cookies()
        cookies = requests.utils.cookiejar_from_dict(cookies)
        self.session.cookies.update(cookies)
        if "/cgi-bin/sessionfailed?reason=6" in self.session.get(
            url=urls.get_xml(), headers=urls.session_headers(), cookies=cookies
        ).text:
            self.session.get(url=urls.login(), headers=headers)
            data = {
                'redirect': '',
                'ft_locale': 'en-us',
                'login.x': 'Log In',
                'username': self.username,
                'password': self.password,
                'destination_page': 'home'
            }

            self.session.post(
                url=urls.login(), headers=headers,
                cookies=self.session.cookies, data=data
            )
            data = {
                'destination_page': 'home',
                'pin': self.pin,
                'pin.x': '++OK++',
                'sring': '0',
                'pin': self.pin
            }

            self.session.post(
                url=urls.pin(), headers=headers,
                cookies=self.session.cookies, data=data
            )
            if self.persistent_session:
                self.save_cookies()
        self.cookies = self.session.cookies
        if "/cgi-bin/sessionfailed?reason=6" in self.session.get(
            url=urls.get_xml(), headers=urls.session_headers(), cookies=cookies
        ).text:
            raise Exception('Login failed. Check your credentials.')

    def load_cookies(self):
        """
        Checks if session cookies were saved.

        Returns:
            Dict: Dictionary of cookies. Nom Nom
        """
        try:
            with open('cookies.pkl', 'rb') as f:
                cookies = pickle.load(f)
        except FileNotFoundError:
            cookies = {}
        return cookies

    def save_cookies(self):
        """
        Saves session cookies to a file.
        """
        with open('cookies.pkl', 'wb') as f:
            pickle.dump(self.session.cookies.get_dict(), f)

    def __getattr__(self, name):
        """
        Forwards unknown attribute access to session object.

        Args:
            name (str): The name of the attribute to be accessed.

        Returns:
            The value of the requested attribute from the session object.
        """
        return getattr(self.session, name)


class FTAccountData:
    """
    Dataclass for storing account information.
    """
    def __init__(self, session):
        """
        Initializes a new instance of the FTAccountData class.

        Args:
            session (requests.Session): The session object used for making HTTP requests.
        """
        self.session = session
        self.cookies = self.session.cookies
        self.all_accounts = []
        self.account_numbers = []
        self.account_types = []
        self.account_owners = []
        self.account_balances = []
        self.securities_held = {}
        all_account_info = []
        html_string = self.session.get(
            url=urls.account_list(),
            headers=urls.session_headers(),
            cookies=self.cookies
        ).text
        regex_accounts = re.findall(
            r'<tr><th><a href=".*?">(.*?)</a></th><td>(.*?)</td></tr>', html_string
        )
        for match in regex_accounts:
            start = match[0].split('-')[1]
            type = start.split(' ')[0]
            owner = start.split(' ')[1] + start.split(' ')[2]
            account = match[0].split('-')[0]
            balance = float(match[1].replace(',', ''))
            self.account_types.append(type)
            self.account_owners.append(owner)
            self.account_numbers.append(account)
            self.account_balances.append(balance)
            all_account_info.append({account: {'Type': type, 'Owner': owner, 'Balance': balance}})
        self.all_accounts = all_account_info

    def get_positions(self, account):
        """Gets currently held positions for a given account.

        Args:
            account (str): Account number of the account you want to get positions for.

        Returns:
            self.securities_held {dict}: Dict of held positions with the pos. ticker as the key.
        """
        data = {
            'page': 'pos',
            'accountId': str(account),
        }
        position_soup = BeautifulSoup(self.session.post(
            url=urls.get_xml(),
            headers=urls.session_headers(),
            data=data,
            cookies=self.cookies
        ).text, 'xml')

        tickers = position_soup.find_all('symbol')
        quantity = position_soup.find_all('quantity')
        price = position_soup.find_all('price')
        change = position_soup.find_all('change')
        change_percent = position_soup.find_all('changepercent')
        vol = position_soup.find_all('vol')
        for i, ticker in enumerate(tickers):
            ticker = ticker.text
            self.securities_held[ticker] = {
                'quantity': quantity[i].text,
                'price': price[i].text, 'change': change[i].text,
                'change_percent': change_percent[i].text, 'vol': vol[i].text
            }
        return self.securities_held

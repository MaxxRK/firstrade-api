import requests
import pickle
import re
import urls


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
        headers = urls.init_headers()
        cookies = requests.utils.cookiejar_from_dict(cookies)
        self.session.cookies.update(cookies)
        url = urls.get_xml()
        if "/cgi-bin/sessionfailed?reason=6" in self.session.get(url=url, headers=headers, cookies=cookies).text:
            url = urls.login()
            headers = urls.init_headers_two()
            self.session.get(url=url, headers=headers)
            url = urls.login()
            headers = urls.login_headers()

            data = {
                'redirect': '',
                'ft_locale': 'en-us',
                'login.x': 'Log In',
                'username': self.username,
                'password': self.password,
                'destination_page': 'home'
            }

            self.session.post(url=url, headers=headers, cookies=self.session.cookies, data=data)
            url = urls.pin()
            headers = urls.pin_headers()
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
    def __init__(self, session):
        self.session = session
        self.cookies = self.session.cookies
        self.all_accounts = []
        self.account_numbers = []
        self.account_types = []
        self.account_owners = []
        self.account_balances = []
        self.get_accounts()

    def get_accounts(self):
        all_account_info = []
        url = urls.account_list()
        headers = urls.account_headers()
        html_string = self.session.get(url=url, headers=headers, cookies=self.cookies).text
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
            print(f"Type: {type}, Account#: {account} Owner: {owner}, Balance: {balance}")
        self.all_accounts = all_account_info

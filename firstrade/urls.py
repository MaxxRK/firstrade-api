def get_xml():
    return "https://invest.firstrade.com/cgi-bin/getxml"


def login():
    #return "https://invest.firstrade.com/cgi-bin/login"
    return "https://api3x.firstrade.com/sess/login"


def pin():
    return "https://api3x.firstrade.com/sess/verify_pin"


def request_code():
    return "https://api3x.firstrade.com/sess/request_code"


def verify_pin():
    return "https://api3x.firstrade.com/sess/verify_pin"


def user_info():
    return "https://api3x.firstrade.com/private/userinfo"


def account_list():
    return "https://api3x.firstrade.com/private/acct_list"


def account_balances(account):
    return f"https://api3x.firstrade.com/private/balances?account={account}"


def account_positions(account):
    return f"https://api3x.firstrade.com/private/positions?account={account}&per_page=200"


def quote(account, symbol):
    return f"https://api3x.firstrade.com/public/quote?account={account}&q={symbol}"


def orderbar():
    return "https://invest.firstrade.com/cgi-bin/orderbar"


def account_status():
    return "https://invest.firstrade.com/cgi-bin/account_status"

def order_list():
    return "https://invest.firstrade.com/cgi-bin/orderstatus"


def status():
    return "https://invest.firstrade.com/scripts/profile/margin_v2.php"


def session_headers():
    headers = {
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "Host": "api3x.firstrade.com",
        "User-Agent": "okhttp/4.9.2",   
    }
    return headers

def access_token():
    return "833w3XuIFycv18ybi"

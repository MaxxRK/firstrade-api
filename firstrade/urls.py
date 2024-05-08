def get_xml():
    return "https://invest.firstrade.com/cgi-bin/getxml"


def login():
    return "https://invest.firstrade.com/cgi-bin/login"


def pin():
    return "https://invest.firstrade.com/cgi-bin/enter_pin?destination_page=home"


def account_list():
    return "https://invest.firstrade.com/cgi-bin/getaccountlist"


def quote(symbol):
    return f"https://invest.firstrade.com/cgi-bin/getxml?page=quo&quoteSymbol={symbol}"


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
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Host": "invest.firstrade.com",
        "Referer": "https://invest.firstrade.com/cgi-bin/main",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.81",
    }
    return headers

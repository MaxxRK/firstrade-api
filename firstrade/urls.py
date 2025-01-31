def login():
    return "https://api3x.firstrade.com/sess/login"


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
    return (
        f"https://api3x.firstrade.com/private/positions?account={account}&per_page=200"
    )


def quote(account, symbol):
    return f"https://api3x.firstrade.com/public/quote?account={account}&q={symbol}"


def order():
    return "https://api3x.firstrade.com/private/stock_order"


def order_list(account):
    return f"https://api3x.firstrade.com/private/order_status?account={account}"


def account_history(account, date_range, custom_range):
    if custom_range is None:
        return f"https://api3x.firstrade.com/private/account_history?range={date_range}&page=1&account={account}&per_page=1000"
    return f"https://api3x.firstrade.com/private/account_history?range={date_range}&range_arr[]={custom_range[0]}&range_arr[]={custom_range[1]}&page=1&account={account}&per_page=1000"


def cancel_order():
    return "https://api3x.firstrade.com/private/cancel_order"


def option_dates(symbol):
    return f"https://api3x.firstrade.com/public/oc?m=get_exp_dates&root_symbol={symbol}"


def option_quotes(symbol, date):
    return f"https://api3x.firstrade.com/public/oc?m=get_oc&root_symbol={symbol}&exp_date={date}&chains_range=A"


def greek_options():
    return "https://api3x.firstrade.com/private/greekoptions/analytical"


def option_order():
    return "https://api3x.firstrade.com/private/option_order"


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

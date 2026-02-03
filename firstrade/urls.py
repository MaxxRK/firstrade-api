def login() -> str:
    """Login URL for FirstTrade API."""
    return "https://api3x.firstrade.com/sess/login"


def request_code() -> str:
    """Request PIN/MFA option for FirstTrade API."""
    return "https://api3x.firstrade.com/sess/request_code"


def verify_pin() -> str:
    """Request PIN/MFA verification for FirstTrade API."""
    return "https://api3x.firstrade.com/sess/verify_pin"


def user_info() -> str:
    """Retrieve user information URL for FirstTrade API."""
    return "https://api3x.firstrade.com/private/userinfo"


def account_list() -> str:
    """Retrieve account list URL for FirstTrade API."""
    return "https://api3x.firstrade.com/private/acct_list"


def account_balances(account: str) -> str:
    """Retrieve account balances URL for FirstTrade API."""
    return f"https://api3x.firstrade.com/private/balances?account={account}"


def account_positions(account: str) -> str:
    """Retrieve account positions URL for FirstTrade API."""
    return f"https://api3x.firstrade.com/private/positions?account={account}&per_page=200"


def quote(account: str, symbol: str) -> str:
    """Symbol quote URL for FirstTrade API."""
    return f"https://api3x.firstrade.com/public/quote?account={account}&q={symbol}"


def order() -> str:
    """Place equity order URL for FirstTrade API."""
    return "https://api3x.firstrade.com/private/stock_order"


def order_list(account: str) -> str:
    """Retrieve placed order list URL for FirstTrade API."""
    return f"https://api3x.firstrade.com/private/order_status?account={account}"


def account_history(account: str, date_range: str, custom_range: list[str] | None) -> str:
    """Retrieve account history URL for FirstTrade API."""
    if custom_range is None:
        return f"https://api3x.firstrade.com/private/account_history?range={date_range}&page=1&account={account}&per_page=1000"
    return f"https://api3x.firstrade.com/private/account_history?range={date_range}&range_arr[]={custom_range[0]}&range_arr[]={custom_range[1]}&page=1&account={account}&per_page=1000"


def cancel_order() -> str:
    """Cancel placed order URL for FirstTrade API."""
    return "https://api3x.firstrade.com/private/cancel_order"


def option_dates(symbol: str) -> str:
    """Option dates URL for FirstTrade API."""
    return f"https://api3x.firstrade.com/public/oc?m=get_exp_dates&root_symbol={symbol}"


def option_quotes(symbol: str, date: str) -> str:
    """Option quotes URL for FirstTrade API."""
    return f"https://api3x.firstrade.com/public/oc?m=get_oc&root_symbol={symbol}&exp_date={date}&chains_range=A"


def greek_options() -> str:
    """Greek options analytical data URL for FirstTrade API."""
    return "https://api3x.firstrade.com/private/greekoptions/analytical"


def option_order() -> str:
    """Place option order URL for FirstTrade API."""
    return "https://api3x.firstrade.com/private/option_order"


def session_headers() -> dict[str, str]:
    """Session headers for FirstTrade API."""
    headers: dict[str, str] = {
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "Host": "api3x.firstrade.com",
        "User-Agent": "okhttp/4.9.2",
    }
    return headers


def access_token() -> str:
    """Access token for FirstTrade API."""
    return "833w3XuIFycv18ybi"

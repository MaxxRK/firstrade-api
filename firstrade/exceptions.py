class QuoteError(Exception):
    """Base class for exceptions in the Quote module."""


class QuoteRequestError(QuoteError):
    """Exception raised for errors in the HTTP request during a Quote."""

    def __init__(self, status_code, message="Error in HTTP request"):
        self.status_code = status_code
        self.message = f"{message}. HTTP status code: {status_code}"
        super().__init__(self.message)


class QuoteResponseError(QuoteError):
    """Exception raised for errors in the API response."""

    def __init__(self, symbol, error_message):
        self.symbol = symbol
        self.message = f"Failed to get data for {symbol}. API returned the following error: {error_message}"
        super().__init__(self.message)


class LoginError(Exception):
    """Exception raised for errors in the login process."""


class LoginRequestError(LoginError):
    """Exception raised for errors in the HTTP request during login."""

    def __init__(self, status_code, message="Error in HTTP request during login"):
        self.status_code = status_code
        self.message = f"{message}. HTTP status code: {status_code}"
        super().__init__(self.message)


class LoginResponseError(LoginError):
    """Exception raised for errors in the API response during login."""

    def __init__(self, error_message):
        self.message = (
            f"Failed to login. API returned the following error: {error_message}"
        )
        super().__init__(self.message)


class AccountError(Exception):
    """Base class for exceptions in the Account module."""


class AccountResponseError(AccountError):
    """Exception raised for errors in the API response when getting account data."""

    def __init__(self, error_message):
        self.message = f"Failed to get account data. API returned the following error: {error_message}"
        super().__init__(self.message)

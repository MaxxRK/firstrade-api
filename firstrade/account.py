import json
from pathlib import Path

import pyotp
import requests

from firstrade import urls
from firstrade.exceptions import (
    AccountResponseError,
    LoginError,
    LoginRequestError,
    LoginResponseError,
)


class FTSession:
    """Class creating a session for Firstrade.

    This class handles the creation and management of a session for logging into the Firstrade platform.
    It supports multi-factor authentication (MFA) and can save session cookies for persistent logins.

    Attributes:
        username (str): Firstrade login username.
        password (str): Firstrade login password.
        pin (str): Firstrade login pin.
        email (str, optional): Firstrade MFA email.
        phone (str, optional): Firstrade MFA phone number.
        mfa_secret (str, optional): Secret key for generating MFA codes.
        profile_path (str, optional): The path where the user wants to save the cookie pkl file.
        t_token (str, optional): Token used for MFA.
        otp_options (dict, optional): Options for OTP (One-Time Password) if MFA is enabled.
        login_json (dict, optional): JSON response from the login request.
        session (requests.Session): The requests session object used for making HTTP requests.

    Methods:
        __init__(username, password, pin=None, email=None, phone=None, mfa_secret=None, profile_path=None):
            Initializes a new instance of the FTSession class.
        login():
            Validates and logs into the Firstrade platform.
        login_two(code):
            Finishes the login process to the Firstrade platform. When using email or phone mfa.
        delete_cookies():
            Deletes the session cookies.
        _load_cookies():
            Checks if session cookies were saved and loads them.
        _save_cookies():
            Saves session cookies to a file.
        _mask_email(email):
            Masks the email for use in the API.
        _handle_mfa():
            Handles multi-factor authentication.

    """

    def __init__(
        self,
        username: str,
        password: str,
        pin: str = "",
        email: str = "",
        phone: str = "",
        mfa_secret: str = "",
        profile_path: str | None = None,
    ) -> None:
        """Initialize a new instance of the FTSession class.

        Args:
            username (str): Firstrade login username.
            password (str): Firstrade login password.
            pin (str): Firstrade login pin.
            email (str, optional): Firstrade MFA email.
            phone (str, optional): Firstrade MFA phone number.
            profile_path (str, optional): The path where the user wants to save the cookie pkl file.

        """
        self.username: str = username
        self.password: str = password
        self.pin: str = pin
        self.email: str = FTSession._mask_email(email) if email else ""
        self.phone: str = phone
        self.mfa_secret: str = mfa_secret
        self.profile_path: str | None = profile_path
        self.t_token: str | None = None
        self.otp_options: list[dict[str, str]] | None = None
        self.login_json: dict[str, str] = {}
        self.session = requests.Session()

    def login(self) -> bool:
        """Validate and log into the Firstrade platform.

        This method sets up the session headers, loads cookies if available, and performs the login request.
        It handles multi-factor authentication (MFA) if required.

        Raises:
            LoginRequestError: If the login request fails with a non-200 status code.
            LoginResponseError: If the login response contains an error message.

        """
        self.session.headers.update(urls.session_headers())
        ftat: str = self._load_cookies()
        if not ftat:
            self.session.headers["ftat"] = ftat
        response: requests.Response = self.session.get(url="https://api3x.firstrade.com/", timeout=10)
        self.session.headers["access-token"] = urls.access_token()

        data: dict[str, str] = {
            "username": r"" + self.username,
            "password": r"" + self.password,
        }

        response: requests.Response = self.session.post(
            url=urls.login(),
            data=data,
        )
        try:
            self.login_json: dict[str, str] = response.json()
        except json.decoder.JSONDecodeError as exc:
            error_msg = "Invalid JSON is your account funded?"
            raise LoginResponseError(error_msg) from exc
        if "mfa" not in self.login_json and "ftat" in self.login_json and not self.login_json["error"]:
            self.session.headers["sid"] = self.login_json["sid"]
            return False
        self.t_token: str | None = self.login_json.get("t_token")
        if not self.mfa_secret:
            self.otp_options: str | None = self.login_json.get("otp")
        if response.status_code != 200:
            raise LoginRequestError(response.status_code)
        if self.login_json["error"]:
            raise LoginResponseError(self.login_json["error"])
        need_code: bool | None = self._handle_mfa()
        if self.login_json["error"]:
            raise LoginResponseError(self.login_json["error"])
        if need_code:
            return True
        self.session.headers["ftat"] = self.login_json["ftat"]
        self.session.headers["sid"] = self.login_json["sid"]
        self._save_cookies()
        return False

    def login_two(self, code: str) -> None:
        """Finish login to the Firstrade platform."""
        data: dict[str, str | None] = {
            "otpCode": code,
            "verificationSid": self.session.headers["sid"],
            "remember_for": "30",
            "t_token": self.t_token,
        }
        response: requests.Response = self.session.post(urls.verify_pin(), data=data)
        self.login_json: dict[str, str] = response.json()
        if not self.login_json["error"]:
            raise LoginResponseError(self.login_json["error"])
        self.session.headers["ftat"] = self.login_json["ftat"]
        self.session.headers["sid"] = self.login_json["sid"]
        self._save_cookies()

    def delete_cookies(self) -> None:
        """Delete the session cookies."""
        path: Path = Path(self.profile_path) / f"ft_cookies{self.username}.json" if self.profile_path is not None else Path(f"ft_cookies{self.username}.json")
        path.unlink()

    def _load_cookies(self) -> str:
        """Check if session cookies were saved.

        Returns:
            str: The saved session token.

        """
        ftat = ""
        directory: Path = Path(self.profile_path) if self.profile_path is not None else Path()
        if not directory.exists():
            directory.mkdir(parents=True)

        for filepath in directory.iterdir():
            if filepath.name.endswith(f"{self.username}.json"):
                with filepath.open(mode="r") as f:
                    ftat: str = json.load(fp=f)
        return ftat

    def _save_cookies(self) -> str | None:
        """Save session cookies to a file."""
        if self.profile_path is not None:
            directory = Path(self.profile_path)
            if not directory.exists():
                directory.mkdir(parents=True)
            path: Path = directory / f"ft_cookies{self.username}.json"
        else:
            path = Path(f"ft_cookies{self.username}.json")
        with path.open("w") as f:
            ftat: str | None = self.session.headers.get("ftat")
            json.dump(obj=ftat, fp=f)

    @staticmethod
    def _mask_email(email: str) -> str:
        """Mask the email for use in the API.

        Args:
            email (str): The email address to be masked.

        Returns:
            str: The masked email address.

        """
        local, domain = email.split(sep="@")
        masked_local: str = local[0] + "*" * 4
        domain_name, tld = domain.split(".")
        masked_domain: str = domain_name[0] + "*" * 4
        return f"{masked_local}@{masked_domain}.{tld}"

    def _handle_mfa(self) -> bool:
        """Handle multi-factor authentication.

        This method processes the MFA requirements based on the login response and user-provided details.

        """
        response: requests.Response | None = None
        data: dict[str, str | None] = {}

        if self.pin:
            response: requests.Response = self._handle_pin_mfa(data)
        elif (self.email or self.phone) and not self.mfa_secret:
            response: requests.Response = self._handle_otp_mfa(data)
        elif self.mfa_secret:
            response: requests.Response = self._handle_secret_mfa(data)
        else:
            error_msg = "MFA required but no valid MFA method was provided (pin, email/phone, or mfa_secret)."
            raise LoginError(error_msg)

        self.login_json = response.json()
        if self.login_json["error"]:
            raise LoginResponseError(self.login_json["error"])

        if self.pin or self.mfa_secret:
            self.session.headers["sid"] = self.login_json["sid"]
            return False
        self.session.headers["sid"] = self.login_json["verificationSid"]
        return True

    def _handle_pin_mfa(self, data: dict[str, str | None]) -> requests.Response:
        """Handle PIN-based MFA."""
        data.update({
            "pin": self.pin,
            "remember_for": "30",
            "t_token": self.t_token,
        })
        return self.session.post(urls.verify_pin(), data=data)

    def _handle_otp_mfa(self, data: dict[str, str | None]) -> requests.Response:
        """Handle email/phone OTP-based MFA."""
        if not self.otp_options:
            error_msg = "No OTP options available."
            raise LoginResponseError(error_msg)

        for item in self.otp_options:
            if (item["channel"] == "sms" and self.phone and self.phone in item["recipientMask"]) or (item["channel"] == "email" and self.email and self.email == item["recipientMask"]):
                data.update({
                    "recipientId": item["recipientId"],
                    "t_token": self.t_token,
                })
                break

        return self.session.post(urls.request_code(), data=data)

    def _handle_secret_mfa(self, data: dict[str, str | None]) -> requests.Response:
        """Handle MFA secret-based authentication."""
        mfa_otp = pyotp.TOTP(self.mfa_secret).now()
        data.update({
            "mfaCode": mfa_otp,
            "remember_for": "30",
            "t_token": self.t_token,
        })
        return self.session.post(urls.verify_pin(), data=data)

    def __getattr__(self, name: str) -> object:
        """Forward unknown attribute access to session object.

        Args:
            name (str): The name of the attribute to be accessed.

        Returns:
            The value of the requested attribute from the session object.

        """
        return getattr(self.session, name)


class FTAccountData:
    """Dataclass for storing account information."""

    def __init__(self, session: requests.Session) -> None:
        """Initialize a new instance of the FTAccountData class.

        Args:
            session (requests.Session): The session object used for making HTTP requests.

        """
        self.session: requests.Session = session
        self.all_accounts: list[dict[str, object]] = []
        self.account_numbers: list[str] = []
        self.account_balances: dict[str, object] = {}
        response: requests.Response = self.session.get(url=urls.user_info())
        self.user_info: dict[str, object] = response.json()
        response: requests.Response = self.session.get(urls.account_list())
        if response.status_code != 200 or response.json()["error"] != "":
            raise AccountResponseError(response.json()["error"])
        self.all_accounts = response.json()
        for item in self.all_accounts["items"]:
            self.account_numbers.append(item["account"])
            self.account_balances[item["account"]] = item["total_value"]

    def get_account_balances(self, account: str) -> dict[str, object]:
        """Get account balances for a given account.

        Args:
            account (str): Account number of the account you want to get balances for.

        Returns:
            dict: Dict of the response from the API.

        """
        response: requests.Response = self.session.get(urls.account_balances(account))
        return response.json()

    def get_positions(self, account: str) -> dict[str, object]:
        """Get currently held positions for a given account.

        Args:
            account (str): Account number of the account you want to get positions for.

        Returns:
            dict: Dict of the response from the API.

        """
        response = self.session.get(urls.account_positions(account))
        return response.json()

    def get_account_history(
        self,
        account: str,
        date_range: str = "ytd",
        custom_range: list[str] | None = None,
    ) -> dict[str, object]:
        """Get account history for a given account.

        Args:
            account (str): Account number of the account you want to get history for.
            date_range (str): The range of the history. Defaults to "ytd".
                         Available options are
                         ["today", "1w", "1m", "2m", "mtd", "ytd", "ly", "cust"].
            custom_range (list[str] | None): The custom range of the history.
                                Defaults to None. If range is "cust",
                                this parameter is required.
                                Format: ["YYYY-MM-DD", "YYYY-MM-DD"].

        Returns:
            dict: Dict of the response from the API.

        """
        if date_range == "cust" and custom_range is None:
            raise ValueError("Custom range required.")
        response: requests.Response = self.session.get(
            urls.account_history(account, date_range, custom_range),
        )
        return response.json()

    def get_orders(self, account: str) -> list[dict[str, object]]:
        """Retrieve existing order data for a given account.

        Args:
            account (str): Account number of the account to retrieve orders for.

        Returns:
            list: A list of dictionaries, each containing details about an order.

        """
        response = self.session.get(url=urls.order_list(account))
        return response.json()

    def cancel_order(self, order_id: str) -> dict[str, object]:
        """Cancel an existing order.

        Args:
            order_id (str): The order ID to cancel.

        Returns:
            dict: A dictionary containing the response data.

        """
        data = {
            "order_id": order_id,
        }

        response = self.session.post(url=urls.cancel_order(), data=data)
        return response.json()

    def get_balance_overview(self, account: str, keywords: list[str] | None = None) -> dict[str, object]:
        """Return a filtered, flattened view of useful balance fields.

        This is a convenience helper over `get_account_balances` to quickly
        surface likely relevant numbers such as cash, available cash, and
        buying power without needing to know the exact response structure.

        Args:
            account (str): Account number to query balances for.
            keywords (list[str], optional): Additional case-insensitive substrings
                to match in keys. Defaults to a sensible set for balances.

        Returns:
            dict: A dict mapping dot-notated keys to values from the balances
                  response where the key path contains any of the keywords.

        """
        if keywords is None:
            keywords = [
                "cash",
                "avail",
                "withdraw",
                "buying",
                "bp",
                "equity",
                "value",
                "margin",
            ]

        payload: dict[str, object] = self.get_account_balances(account)

        filtered: dict[str, object] = {}

        def _walk(node: object, path: list[str]) -> None:
            if isinstance(node, dict):
                for k, v in node.items():
                    _walk(node=v, path=[*path, str(object=k)])
            elif isinstance(node, list):
                for i, v in enumerate(iterable=node):
                    _walk(node=v, path=[*path, str(object=i)])
            else:
                key_path: str = ".".join(path)
                low: str = key_path.lower()
                if any(sub in low for sub in keywords):
                    filtered[key_path] = node

        _walk(node=payload, path=[])
        return filtered

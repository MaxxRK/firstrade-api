import json
import os
import pickle

import pyotp
import requests

from firstrade import urls
from firstrade.exceptions import (
    AccountResponseError,
    LoginRequestError,
    LoginResponseError,
)


class FTSession:
    """
    Class creating a session for Firstrade.

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
        username,
        password,
        pin=None,
        email=None,
        phone=None,
        mfa_secret=None,
        profile_path=None,
    ):
        """
        Initializes a new instance of the FTSession class.

        Args:
            username (str): Firstrade login username.
            password (str): Firstrade login password.
            pin (str): Firstrade login pin.
            email (str, optional): Firstrade MFA email.
            phone (str, optional): Firstrade MFA phone number.
            profile_path (str, optional): The path where the user wants to save the cookie pkl file.
        """
        self.username = username
        self.password = password
        self.pin = pin
        self.email = FTSession._mask_email(email) if email is not None else None
        self.phone = phone
        self.mfa_secret = mfa_secret
        self.profile_path = profile_path
        self.t_token = None
        self.otp_options = None
        self.login_json = None
        self.session = requests.Session()

    def login(self):
        """
        Validates and logs into the Firstrade platform.

        This method sets up the session headers, loads cookies if available, and performs the login request.
        It handles multi-factor authentication (MFA) if required.

        Raises:
            LoginRequestError: If the login request fails with a non-200 status code.
            LoginResponseError: If the login response contains an error message.
        """
        self.session.headers = urls.session_headers()
        ftat = self._load_cookies()
        if ftat != "":
            self.session.headers["ftat"] = ftat
        response = self.session.get(url="https://api3x.firstrade.com/", timeout=10)
        self.session.headers["access-token"] = urls.access_token()

        data = {
            "username": r"" + self.username,
            "password": r"" + self.password,
        }

        response = self.session.post(
            url=urls.login(),
            data=data,
        )
        try:
            self.login_json = response.json()
        except json.decoder.JSONDecodeError:
            raise LoginResponseError("Invalid JSON is your account funded?")
        if (
            "mfa" not in self.login_json
            and "ftat" in self.login_json
            and self.login_json["error"] == ""
        ):
            self.session.headers["sid"] = self.login_json["sid"]
            return False
        self.t_token = self.login_json.get("t_token")
        if self.mfa_secret is None:
            self.otp_options = self.login_json.get("otp")
        if response.status_code != 200:
            raise LoginRequestError(response.status_code)
        if self.login_json["error"] != "":
            raise LoginResponseError(self.login_json["error"])
        need_code = self._handle_mfa()
        if self.login_json["error"] != "":
            raise LoginResponseError(self.login_json["error"])
        if need_code:
            return True
        self.session.headers["ftat"] = self.login_json["ftat"]
        self.session.headers["sid"] = self.login_json["sid"]
        self._save_cookies()
        return False

    def login_two(self, code):
        """Method to finish login to the Firstrade platform."""
        data = {
            "otpCode": code,
            "verificationSid": self.session.headers["sid"],
            "remember_for": "30",
            "t_token": self.t_token,
        }
        response = self.session.post(urls.verify_pin(), data=data)
        self.login_json = response.json()
        if self.login_json["error"] != "":
            raise LoginResponseError(self.login_json["error"])
        self.session.headers["ftat"] = self.login_json["ftat"]
        self.session.headers["sid"] = self.login_json["sid"]
        self._save_cookies()

    def delete_cookies(self):
        """Deletes the session cookies."""
        if self.profile_path is not None:
            path = os.path.join(self.profile_path, f"ft_cookies{self.username}.pkl")
        else:
            path = f"ft_cookies{self.username}.pkl"
        os.remove(path)

    def _load_cookies(self):
        """
        Checks if session cookies were saved.

        Returns:
            str: The saved session token.
        """

        ftat = ""
        directory = (
            os.path.abspath(self.profile_path) if self.profile_path is not None else "."
        )
        if not os.path.exists(directory):
            os.makedirs(directory)

        for filename in os.listdir(directory):
            if filename.endswith(f"{self.username}.pkl"):
                filepath = os.path.join(directory, filename)
                with open(filepath, "rb") as f:
                    ftat = pickle.load(f)
        return ftat

    def _save_cookies(self):
        """Saves session cookies to a file."""
        if self.profile_path is not None:
            directory = os.path.abspath(self.profile_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
            path = os.path.join(self.profile_path, f"ft_cookies{self.username}.pkl")
        else:
            path = f"ft_cookies{self.username}.pkl"
        with open(path, "wb") as f:
            ftat = self.session.headers.get("ftat")
            pickle.dump(ftat, f)

    @staticmethod
    def _mask_email(email):
        """
        Masks the email for use in the API.

        Args:
            email (str): The email address to be masked.

        Returns:
            str: The masked email address.
        """
        local, domain = email.split("@")
        masked_local = local[0] + "*" * 4
        domain_name, tld = domain.split(".")
        masked_domain = domain_name[0] + "*" * 4
        return f"{masked_local}@{masked_domain}.{tld}"

    def _handle_mfa(self):
        """
        Handles multi-factor authentication.

        This method processes the MFA requirements based on the login response and user-provided details.

        Raises:
            LoginRequestError: If the MFA request fails with a non-200 status code.
            LoginResponseError: If the MFA response contains an error message.
        """
        if not self.login_json["mfa"] and self.pin is not None:
            data = {
                "pin": self.pin,
                "remember_for": "30",
                "t_token": self.t_token,
            }
            response = self.session.post(urls.verify_pin(), data=data)
            self.login_json = response.json()
        elif not self.login_json["mfa"] and (
            self.email is not None or self.phone is not None
        ):
            for item in self.otp_options:
                if item["channel"] == "sms" and self.phone is not None:
                    if self.phone in item["recipientMask"]:
                        data = {
                            "recipientId": item["recipientId"],
                            "t_token": self.t_token,
                        }
                        break
                elif item["channel"] == "email" and self.email is not None:
                    if self.email == item["recipientMask"]:
                        data = {
                            "recipientId": item["recipientId"],
                            "t_token": self.t_token,
                        }
                        break
            response = self.session.post(urls.request_code(), data=data)
        elif self.login_json["mfa"] and self.mfa_secret is not None:
            mfa_otp = pyotp.TOTP(self.mfa_secret).now()
            data = {
                "mfaCode": mfa_otp,
                "remember_for": "30",
                "t_token": self.t_token,
            }
            response = self.session.post(urls.verify_pin(), data=data)
        self.login_json = response.json()
        if self.login_json["error"] == "":
            if self.pin or self.mfa_secret is not None:
                self.session.headers["sid"] = self.login_json["sid"]
                return False
            self.session.headers["sid"] = self.login_json["verificationSid"]
            return True

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
    """Dataclass for storing account information."""

    def __init__(self, session):
        """
        Initializes a new instance of the FTAccountData class.

        Args:
            session (requests.Session):
            The session object used for making HTTP requests.
        """
        self.session = session
        self.all_accounts = []
        self.account_numbers = []
        self.account_balances = {}
        response = self.session.get(url=urls.user_info())
        self.user_info = response.json()
        response = self.session.get(urls.account_list())
        if response.status_code != 200 or response.json()["error"] != "":
            raise AccountResponseError(response.json()["error"])
        self.all_accounts = response.json()
        for item in self.all_accounts["items"]:
            self.account_numbers.append(item["account"])
            self.account_balances[item["account"]] = item["total_value"]

    def get_account_balances(self, account):
        """Gets account balances for a given account.

        Args:
            account (str): Account number of the account you want to get balances for.

        Returns:
            dict: Dict of the response from the API.
        """
        response = self.session.get(urls.account_balances(account))
        return response.json()

    def get_positions(self, account):
        """Gets currently held positions for a given account.

        Args:
            account (str): Account number of the account you want to get positions for.

        Returns:
            dict: Dict of the response from the API.
        """

        response = self.session.get(urls.account_positions(account))
        return response.json()

    def get_account_history(self, account, date_range="ytd", custom_range=None):
        """Gets account history for a given account.

        Args:
            account (str): Account number of the account you want to get history for.
            range (str): The range of the history. Defaults to "ytd".
                         Available options are
                         ["today", "1w", "1m", "2m", "mtd", "ytd", "ly", "cust"].
            custom_range (str): The custom range of the history.
                                Defaults to None. If range is "cust",
                                this parameter is required.
                                Format: ["YYYY-MM-DD", "YYYY-MM-DD"].

        Returns:
            dict: Dict of the response from the API.
        """
        if date_range == "cust" and custom_range is None:
            raise ValueError("Custom range is required when date_range is 'cust'.")
        response = self.session.get(
            urls.account_history(account, date_range, custom_range)
        )
        return response.json()

    def get_orders(self, account):
        """
        Retrieves existing order data for a given account.

        Args:
            ft_session (FTSession): The session object used for making HTTP requests to Firstrade.
            account (str): Account number of the account to retrieve orders for.

        Returns:
            list: A list of dictionaries, each containing details about an order.
        """

        response = self.session.get(url=urls.order_list(account))
        return response.json()

    def cancel_order(self, order_id):
        """
        Cancels an existing order.

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

    def get_balance_overview(self, account, keywords=None):
        """
        Returns a filtered, flattened view of useful balance fields.

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

        payload = self.get_account_balances(account)

        filtered = {}

        def _walk(node, path):
            if isinstance(node, dict):
                for k, v in node.items():
                    _walk(v, path + [str(k)])
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    _walk(v, path + [str(i)])
            else:
                key_path = ".".join(path)
                low = key_path.lower()
                if any(sub in low for sub in keywords):
                    filtered[key_path] = node

        _walk(payload, [])
        return filtered

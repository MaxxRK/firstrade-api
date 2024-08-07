import os
import pickle

import requests

from firstrade import urls


class FTSession:

    """Class creating a session for Firstrade."""
    def __init__(self, username, password, pin=None, email=None, phone=None, profile_path=None):
        """
        Initializes a new instance of the FTSession class.

        Args:
            username (str): Firstrade login username.
            password (str): Firstrade login password.
            pin (str): Firstrade login pin.
            persistent_session (bool, optional): Whether the user wants to save the session cookies.
            profile_path (str, optional): The path where the user wants to save the cookie pkl file.
        """
        self.username = username
        self.password = password
        self.pin = pin
        self.email = self._mask_email(email) if email is not None else None
        self.phone = phone
        self.profile_path = profile_path
        self.t_token = None
        self.otp_options = None
        self.login_json = None
        self.session = requests.Session()

    def login(self):
        """Method to validate and login to the Firstrade platform."""
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
        self.login_json = response.json()
        if "mfa" not in self.login_json and "ftat" in self.login_json and self.login_json["error"] == "":
            self.session.headers["sid"] = self.login_json["sid"]
            return False
        self.t_token = self.login_json.get("t_token")
        self.otp_options = self.login_json.get("otp")
        if self.login_json["error"] != "" or response.status_code != 200:
            raise Exception(f"Login failed api reports the following error(s). {self.login_json['error']}")
        
        need_code = self._handle_mfa()
        if self.login_json["error"]!= "":
                raise Exception(f"Login failed api reports the following error(s): {self.login_json['error']}.")
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
        if self.login_json["error"]!= "":
                raise Exception(f"Login failed api reports the following error(s): {self.login_json['error']}.")
        self.session.headers["ftat"] = self.login_json["ftat"]
        self.session.headers["sid"] = self.login_json["sid"]
        print(self.login_json)
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
            Dict: Dictionary of cookies. Nom Nom
        """

        ftat = ""
        directory = os.path.abspath(self.profile_path) if self.profile_path is not None else "."
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
        
    def _mask_email(self, email):
        """Masks the email for security purposes."""
        local, domain = email.split('@')
        masked_local = local[0] + '*' * 4
        domain_name, tld = domain.split('.')
        masked_domain = domain_name[0] + '*' * 4
        return f"{masked_local}@{masked_domain}.{tld}"
    
    def _handle_mfa(self):
        """Handles multi-factor authentication."""
        if "mfa" in self.login_json and self.pin is not None:
            data = {
                "pin": self.pin,
                "remember_for": "30",
                "t_token": self.t_token, 
            }
            response = self.session.post(urls.pin(), data=data)
            self.login_json = response.json()
        elif "mfa" in self.login_json and (self.email is not None or self.phone is not None):
            for item in self.otp_options:
                if item["channel"] == "sms" and self.phone is not None:
                    if self.phone in item["recipientMask"]:
                        data = {
                            "recipientId": item["recipientId"],
                            "t_token": self.t_token,
                        }
                elif item["channel"] == "email" and self.email is not None:
                    if self.email == item["recipientMask"]:
                        data = {
                            "recipientId": item["recipientId"],
                            "t_token": self.t_token, 
                        }
            response = self.session.post(urls.request_code(), data=data)
        print(response.json())
        self.login_json = response.json()
        if self.login_json["error"] == "":
            self.session.headers["sid"]= self.login_json["verificationSid"]
            return False if self.pin is not None else True


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
        self.account_statuses = []
        self.account_balances = []
        response = self.session.get(url=urls.user_info())
        if response.status_code != 200:
            raise Exception("Failed to get user info.")
        self.user_info = response.json()
        response = self.session.get(urls.account_list())
        if response.status_code != 200 or response.json()["error"] != "":
            raise Exception(f"Failed to get account list. API returned the following error: {response.json()['error']}")
        self.all_accounts = response.json()
        for item in self.all_accounts["items"]:
            self.account_numbers.append(item["account"])
            self.account_balances.append(float(item["total_value"]))

    def get_account_balances(self, account):
        """Gets account balances for a given account.

        Args:
            account (str): Account number of the account you want to get balances for.

        Returns:
            dict: Dict of the response from the API.
        """
        response = self.session.get(urls.account_balances(account))
        if response.status_code != 200 or response.json()["error"] != "":
            raise Exception(f"Failed to get account balances. API returned the following error: {response.json()['error']}")
        return response.json()

    def get_positions(self, account):
        """Gets currently held positions for a given account.

        Args:
            account (str): Account number of the account you want to get positions for.

        Returns:
            dict: Dict of the response from the API.
        """
        
        response = self.session.get(urls.account_positions(account))
        if response.status_code != 200 or response.json()["error"] != "":
            raise Exception(f"Failed to get account positions. API returned the following error: {response.json()['error']}")
        return response.json()

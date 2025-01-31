from enum import Enum

from firstrade import urls
from firstrade.account import FTSession


class PriceType(str, Enum):
    """
    Enum for valid price types in an order.

    Attributes:
        MARKET (str): Market order, executed at the current market price.
        LIMIT (str): Limit order, executed at a specified price or better.
        STOP (str): Stop order, becomes a market order once a specified price is reached.
        STOP_LIMIT (str): Stop-limit order, becomes a limit order once a specified price is reached.
        TRAILING_STOP_DOLLAR (str): Trailing stop order with a specified dollar amount.
        TRAILING_STOP_PERCENT (str): Trailing stop order with a specified percentage.
    """

    LIMIT = "2"
    MARKET = "1"
    STOP = "3"
    STOP_LIMIT = "4"
    TRAILING_STOP_DOLLAR = "5"
    TRAILING_STOP_PERCENT = "6"


class Duration(str, Enum):
    """
    Enum for valid order durations.

    Attributes:
        DAY (str): Day order.
        GT90 (str): Good till 90 days order.
        PRE_MARKET (str): Pre-market order.
        AFTER_MARKET (str): After-market order.
        DAY_EXT (str): Day extended order.
    """

    DAY = "0"
    GT90 = "1"
    PRE_MARKET = "A"
    AFTER_MARKET = "P"
    DAY_EXT = "D"


class OrderType(str, Enum):
    """
    Enum for valid order types.

    Attributes:
        BUY (str): Buy order.
        SELL (str): Sell order.
        SELL_SHORT (str): Sell short order.
        BUY_TO_COVER (str): Buy to cover order.
        BUY_OPTION (str): Buy option order.
        SELL_OPTION (str): Sell option order.
    """

    BUY = "B"
    SELL = "S"
    SELL_SHORT = "SS"
    BUY_TO_COVER = "BC"
    BUY_OPTION = "BO"
    SELL_OPTION = "SO"


class OrderInstructions(str, Enum):
    """
    Enum for valid order instructions.

    Attributes:
        AON (str): All or none.
        OPG (str): At the Open.
        CLO (str): At the Close.
    """

    AON = "1"
    OPG = "4"
    CLO = "5"


class OptionType(str, Enum):
    """
    Enum for valid option types.

    Attributes:
        CALL (str): Call option.
        PUT (str): Put option.
    """

    CALL = "C"
    PUT = "P"


class Order:
    """
    Represents an order with methods to place it.

    Attributes:
        ft_session (FTSession): The session object for placing orders.
    """

    def __init__(self, ft_session: FTSession):
        self.ft_session = ft_session

    def place_order(
        self,
        account: str,
        symbol: str,
        price_type: PriceType,
        order_type: OrderType,
        duration: Duration,
        quantity: int = 0,
        price: float = 0.00,
        stop_price: float = None,
        dry_run: bool = True,
        notional: bool = False,
        order_instruction: OrderInstructions = "0",
    ):
        """
        Builds and places an order.

        Args:
            account (str): The account number to place the order in.
            symbol (str): The ticker symbol for the order.
            price_type (PriceType): The price type for the order (e.g., LIMIT, MARKET, STOP).
            order_type (OrderType): The type of order (e.g., BUY, SELL).
            duration (Duration): The duration of the order (e.g., DAY, GT90).
            quantity (int, optional): The number of shares to buy or sell. Defaults to 0.
            price (float, optional): The price at which to buy or sell the shares. Defaults to 0.00.
            stop_price (float, optional): The stop price for stop orders. Defaults to None.
            dry_run (bool, optional): If True, the order will not be placed but will be built and validated. Defaults to True.
            notional (bool, optional): If True, the order will be placed based on a notional dollar amount rather than share quantity. Defaults to False.
            order_instruction (OrderInstructions, optional): Additional order instructions (e.g., AON, OPG). Defaults to "0".

        Raises:
            ValueError: If AON orders are not limit orders or if AON orders have a quantity of 100 shares or less.
            PreviewOrderError: If the order preview fails.
            PlaceOrderError: If the order placement fails.

        Returns:
            dict: A dictionary containing the order confirmation data.
        """

        if price_type == PriceType.MARKET and not notional:
            price = ""
        if order_instruction == OrderInstructions.AON and price_type != PriceType.LIMIT:
            raise ValueError("AON orders must be a limit order.")
        if order_instruction == OrderInstructions.AON and quantity <= 100:
            raise ValueError("AON orders must be greater than 100 shares.")

        data = {
            "symbol": symbol,
            "transaction": order_type,
            "shares": quantity,
            "duration": duration,
            "preview": "true",
            "instructions": order_instruction,
            "account": account,
            "price_type": price_type,
            "limit_price": "0",
        }
        if notional:
            data["dollar_amount"] = price
            del data["shares"]
        if price_type in [PriceType.LIMIT, PriceType.STOP_LIMIT]:
            data["limit_price"] = price
        if price_type in [PriceType.STOP, PriceType.STOP_LIMIT]:
            data["stop_price"] = stop_price
        response = self.ft_session.post(url=urls.order(), data=data)
        if response.status_code != 200 or response.json()["error"] != "":
            return response.json()
        preview_data = response.json()
        if dry_run:
            return preview_data
        data["preview"] = "false"
        data["stage"] = "P"
        response = self.ft_session.post(url=urls.order(), data=data)
        return response.json()

    def place_option_order(
        self,
        account: str,
        option_symbol: str,
        price_type: PriceType,
        order_type: OrderType,
        contracts: int,
        duration: Duration,
        stop_price: float = None,
        price: float = 0.00,
        dry_run: bool = True,
        order_instruction: OrderInstructions = "0",
    ):
        """
        Builds and places an option order.

        Args:
            account (str): The account number to place the order in.
            option_symbol (str): The option ticker symbol for the order.
            price_type (PriceType): The price type for the order (e.g., LIMIT, MARKET, STOP).
            order_type (OrderType): The type of order (e.g., BUY, SELL).
            contracts (int): The number of option contracts to buy or sell.
            duration (Duration): The duration of the order (e.g., DAY, GT90).
            stop_price (float, optional): The stop price for stop orders. Defaults to None.
            price (float, optional): The price at which to buy or sell the option contracts. Defaults to 0.00.
            dry_run (bool, optional): If True, the order will not be placed but will be built and validated. Defaults to True.
            order_instruction (OrderInstructions, optional): Additional order instructions (e.g., AON, OPG). Defaults to "0".

        Raises:
            ValueError: If AON orders are not limit orders or if AON orders have a quantity of 100 contracts or less.
            PreviewOrderError: If there is an error during the preview of the order.
            PlaceOrderError: If there is an error during the placement of the order.

        Returns:
            dict: A dictionary containing the order confirmation data.
        """

        if order_instruction == OrderInstructions.AON and price_type != PriceType.LIMIT:
            raise ValueError("AON orders must be a limit order.")
        if order_instruction == OrderInstructions.AON and contracts <= 100:
            raise ValueError("AON orders must be greater than 100 shares.")

        data = {
            "duration": duration,
            "instructions": order_instruction,
            "transaction": order_type,
            "contracts": contracts,
            "symbol": option_symbol,
            "preview": "true",
            "account": account,
            "price_type": price_type,
        }
        if price_type in [PriceType.LIMIT, PriceType.STOP_LIMIT]:
            data["limit_price"] = price
        if price_type in [PriceType.STOP, PriceType.STOP_LIMIT]:
            data["stop_price"] = stop_price

        response = self.ft_session.post(url=urls.option_order(), data=data)
        if response.status_code != 200 or response.json()["error"] != "":
            return response.json()
        if dry_run:
            return response.json()
        data["preview"] = "false"
        response = self.ft_session.post(url=urls.option_order(), data=data)
        return response.json()

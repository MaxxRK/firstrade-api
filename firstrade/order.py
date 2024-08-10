from enum import Enum

from firstrade import urls
from firstrade.account import FTSession


class PriceType(str, Enum):
    """
    This is an :class: 'enum.Enum'
    that contains the valid price types for an order.
    """

    LIMIT = "2"
    MARKET = "1"
    STOP = "3"
    STOP_LIMIT = "4"
    TRAILING_STOP_DOLLAR = "5"
    TRAILING_STOP_PERCENT = "6"


class Duration(str, Enum):
    """
    This is an :class:'~enum.Enum'
    that contains the valid durations for an order.
    """

    DAY = "0"
    GT90 = "1"
    PRE_MARKET = "A"
    AFTER_MARKET = "P"
    DAY_EXT = "D"


class OrderType(str, Enum):
    """
    This is an :class:'~enum.Enum'
    that contains the valid order types for an order.
    """

    BUY = "B"
    SELL = "S"
    SELL_SHORT = "SS"
    BUY_TO_COVER = "BC"
    BUY_OPTION = "BO"
    SELL_OPTION = "SO"


class OrderInstructions(str, Enum):
    """
    This is an :class:'~enum.Enum'
    that contains the valid instructions for an order.
    """

    AON = "1"
    OPG = "4"
    CLO = "5"


class OptionType(str, Enum):
    """
    This is an :class:'~enum.Enum'
    that contains the valid option types for an order.
    """

    CALL = "C"
    PUT = "P"


class Order:
    """
    This class contains information about an order.
    It also contains a method to place an order.
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
        :attr: 'order_confirmation`
        contains the order confirmation data after order placement.

        Args:
            account (str): Account number of the account to place the order in.
            symbol (str): Ticker to place the order for.
            order_type (PriceType): Price Type i.e. LIMIT, MARKET, STOP, etc.
            quantity (float): The number of shares to buy.
            duration (Duration): Duration of the order i.e. DAY, GT90, etc.
            price (float, optional): The price to buy the shares at. Defaults to 0.00.
            dry_run (bool, optional): Whether you want the order to be placed or not.
                                      Defaults to True.

        Returns:
            Order:order_confirmation: Dictionary containing the order confirmation data.
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
            raise Exception(
                f"Failed to preview order for {symbol}. " 
                f"API returned the following error: {response.json()['error']} "
                f"With the following message: {response.json()['message']} "
            )
        preview_data = response.json()
        if dry_run:
            return preview_data
        data["preview"] = "false"
        data["stage"] = "P"
        
        response = self.ft_session.post(url=urls.order(), data=data)
        if response.status_code != 200 or response.json()["error"] != "":
            raise Exception(
                f"Failed to preview order for {symbol}. " 
                f"API returned the following error: {response.json()['error']} "
                f"With the following message: {response.json()['message']} "
            )
        return response.json()

    def place_option_order(
            self,
            account: str,
            symbol: str,
            price_type: PriceType,
            order_type: OrderType,
            quantity: int,
            duration: Duration,
            stop_price: float = None,
            price: float = 0.00,
            dry_run: bool = True,
            order_instruction: OrderInstructions = "0",
    ):
        
        
        if order_instruction == OrderInstructions.AON and price_type != PriceType.LIMIT:
            raise ValueError("AON orders must be a limit order.")
        if order_instruction == OrderInstructions.AON and quantity <= 100:
                raise ValueError("AON orders must be greater than 100 shares.")
            
        
        data = {
            "duration": duration,
            "instructions": order_instruction,
            "transaction": order_type,
            "contracts": quantity,
            "symbol": symbol,
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
            raise Exception(
                f"Failed to preview order for {symbol}. " 
                f"API returned the following error: {response.json()['error']} "
                f"With the following message: {response.json()['message']} "
            )
        if dry_run:
            return response.json()
        data["preview"] = "false"
        response = self.ft_session.post(url=urls.option_order(), data=data)
        if response.status_code != 200 or response.json()["error"] != "":
            raise Exception(
                f"Failed to preview order for {symbol}. " 
                f"API returned the following error: {response.json()['error']} "
                f"With the following message: {response.json()['message']} "
            )
        return response.json()

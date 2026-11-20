import enum

from firstrade import urls
from firstrade.account import FTSession


class PriceType(enum.StrEnum):
    """Enum for valid price types in an order.

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


class Duration(enum.StrEnum):
    """Enum for valid order durations.

    Attributes:
        DAY (str): Day order (9:30 AM - 4 PM ET)
        DAY_EXT (str): Day extended order (8 AM - 8 PM ET).
        OVERNIGHT (str): Overnight order (8 PM - 4 AM ET).
        GT90 (str): Good till 90 days order (9:30 AM - 4 PM ET).

    """

    DAY = "0"
    DAY_EXT = "D"
    OVERNIGHT = "N"
    GT90 = "1"


class OrderType(enum.StrEnum):
    """Enum for valid order types.

    Attributes:
        BUY (str): Buy order.
        SELL (str): Sell order.
        SELL_SHORT (str): Sell short order.
        BUY_TO_COVER (str): Buy to cover order.
        BUY_OPTION (str): Buy option order (opens a long position).
        SELL_OPTION (str): Sell option order (opens a short position).
        BUY_TO_CLOSE_OPTION (str): Buy an option to close a short position.
        SELL_TO_CLOSE_OPTION (str): Sell an option to close a long position.

    """

    BUY = "B"
    SELL = "S"
    SELL_SHORT = "SS"
    BUY_TO_COVER = "BC"
    BUY_OPTION = "BO"
    SELL_OPTION = "SO"
    BUY_TO_CLOSE_OPTION = "BC"
    SELL_TO_CLOSE_OPTION = "SC"


class OrderInstructions(enum.StrEnum):
    """Enum for valid order instructions.

    Attributes:
        NONE (str): No special instruction.
        AON (str): All or none.
        OPG (str): At the Open.
        CLO (str): At the Close.

    """

    NONE = "0"
    AON = "1"
    OPG = "4"
    CLO = "5"


class OptionType(enum.StrEnum):
    """Enum for valid option types.

    Attributes:
        CALL (str): Call option.
        PUT (str): Put option.

    """

    CALL = "C"
    PUT = "P"


class SpreadLimitType(enum.StrEnum):
    """Enum for whether a spread order pays or receives its net price.

    Attributes:
        DEBIT (str): The order pays the net price.
        CREDIT (str): The order receives the net price.

    """

    DEBIT = "D"
    CREDIT = "C"


class Order:
    """Represents an order with methods to place it.

    Attributes:
        ft_session (FTSession): The session object for placing orders.

    """

    def __init__(self, ft_session: FTSession) -> None:
        """Initialize the Order with a FirstTrade session."""
        self.ft_session: FTSession = ft_session

    def place_order(
        self,
        account: str,
        symbol: str,
        price_type: PriceType,
        order_type: OrderType,
        duration: Duration,
        quantity: int = 0,
        price: float = 0.00,
        stop_price: float | None = None,
        *,
        dry_run: bool = True,
        notional: bool = False,
        order_instruction: OrderInstructions = OrderInstructions.NONE,
    ):
        """Build and place an order.

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
        if price_type in {PriceType.LIMIT, PriceType.STOP_LIMIT}:
            data["limit_price"] = price
        if price_type in {PriceType.STOP, PriceType.STOP_LIMIT}:
            data["stop_price"] = stop_price
        response: requests.Response = self.ft_session._request("post", url=urls.order(), data=data)
        if response.status_code != 200 or response.json()["error"] != "":
            return response.json()
        preview_data = response.json()
        if dry_run:
            return preview_data
        data["preview"] = "false"
        data["stage"] = "P"
        response = self.ft_session._request("post", url=urls.order(), data=data)
        return response.json()

    def place_option_order(
        self,
        account: str,
        option_symbol: str,
        price_type: PriceType,
        order_type: OrderType,
        contracts: int,
        duration: Duration,
        stop_price: float | None = None,
        price: float = 0.00,
        *,
        dry_run: bool = True,
        preview: bool = True,
        order_instruction: OrderInstructions = OrderInstructions.NONE,
    ):
        """Build and place an option order.

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
            preview (bool, optional): If True, a preview request is sent first and the order is only placed when the preview is clean. If False, the real order is sent directly, saving one round trip, and any problem the preview would have caught comes back from the order itself. Cannot be combined with dry_run, because a dry run is a preview. Defaults to True.

        Raises:
            ValueError: If AON orders are not limit orders or if AON orders have a quantity of 100 contracts or less.
                Also if preview is False while dry_run is True.

        Returns:
            dict: A dictionary containing the order confirmation data.

        """
        if order_instruction == OrderInstructions.AON and price_type != PriceType.LIMIT:
            raise ValueError("AON orders must be a limit order.")
        if order_instruction == OrderInstructions.AON and contracts <= 100:
            raise ValueError("AON orders must be greater than 100 shares.")
        if dry_run and not preview:
            raise ValueError("A dry run is a preview: preview=False cannot be combined with dry_run=True.")

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
        if price_type in {PriceType.LIMIT, PriceType.STOP_LIMIT}:
            data["limit_price"] = price
        if price_type in {PriceType.STOP, PriceType.STOP_LIMIT}:
            data["stop_price"] = stop_price

        if not preview:
            data["preview"] = "false"
            response = self.ft_session._request("post", url=urls.option_order(), data=data)
            return response.json()

        response = self.ft_session._request("post", url=urls.option_order(), data=data)
        if response.status_code != 200 or response.json()["error"] != "":
            return response.json()
        if dry_run:
            return response.json()
        data["preview"] = "false"
        response = self.ft_session._request("post", url=urls.option_order(), data=data)
        return response.json()

    def place_spread_order(
        self,
        account: str,
        leg1_symbol: str,
        leg1_transaction: OrderType,
        leg2_symbol: str,
        leg2_transaction: OrderType,
        limit_type: SpreadLimitType,
        net_price: float,
        contracts: int = 1,
        *,
        dry_run: bool = True,
        preview: bool = True,
    ) -> dict:
        """Build and place a two-leg option spread order.

        Spread orders are limit orders priced as one net amount. They are day orders:
        the endpoint rejects ``duration`` and ``limit_price``. Firstrade only accepts them
        during market hours and answers error code 1110 otherwise.

        Args:
            account (str): The account number to place the order in.
            leg1_symbol (str): The option ticker symbol for the first leg.
            leg1_transaction (OrderType): BUY_OPTION, SELL_OPTION, BUY_TO_CLOSE_OPTION or SELL_TO_CLOSE_OPTION.
            leg2_symbol (str): The option ticker symbol for the second leg.
            leg2_transaction (OrderType): The transaction for the second leg.
            limit_type (SpreadLimitType): DEBIT if the order pays the net price, CREDIT if it receives it.
            net_price (float): The net price of the whole spread, always positive.
            contracts (int, optional): The number of spreads. Both legs use it. Defaults to 1.
            dry_run (bool, optional): If True, the order is built and validated but not placed. Defaults to True.
            preview (bool, optional): If True, a preview request is sent first and the order is only placed when the preview is clean. If False, the real order is sent directly. Cannot be combined with dry_run. Skipping the preview was checked live for single-leg orders; for spreads it was only seen to be rejected the same way with and without a preview (insufficient equity), not accepted. Defaults to True.

        Returns:
            dict: A dictionary containing the order confirmation data, or the error.

        Raises:
            ValueError: If preview is False while dry_run is True.

        """
        if dry_run and not preview:
            raise ValueError("A dry run is a preview: preview=False cannot be combined with dry_run=True.")

        data = {
            "order_type": "spread",
            "transaction1": leg1_transaction,
            "symbol1": leg1_symbol,
            "contracts1": contracts,
            "transaction2": leg2_transaction,
            "symbol2": leg2_symbol,
            "contracts2": contracts,
            "limit_type": limit_type,
            "net_price": net_price,
            "instructions": OrderInstructions.NONE,
            "preview": "true",
            "account": account,
        }

        if not preview:
            data["preview"] = "false"
            response = self.ft_session._request("post", url=urls.complex_option_order(), data=data)
            return response.json()

        response = self.ft_session._request("post", url=urls.complex_option_order(), data=data)
        if response.status_code != 200 or response.json()["error"] != "":
            return response.json()
        if dry_run:
            return response.json()
        data["preview"] = "false"
        response = self.ft_session._request("post", url=urls.complex_option_order(), data=data)
        return response.json()

    def modify_spread_order(
        self,
        order_id: str,
        net_price: float,
        contracts: int,
        *,
        dry_run: bool = True,
        preview: bool = True,
        instructions: OrderInstructions = OrderInstructions.NONE,
    ) -> dict:
        """Change the net price or size of a working spread order.

        Firstrade replaces the order: the old one is cancelled and a new one with the new terms
        is entered in one request, so the new order has a new id and the old one is left as
        ``ORDER-UPDATED``. Look the new id up in the order list.

        Args:
            order_id (str): The id of a working spread order (either leg's id, from the order list).
            net_price (float): The new net price of the whole spread, positive.
            contracts (int): The new number of spreads.
            dry_run (bool, optional): If True, only the preview request is sent. Defaults to True.
            preview (bool, optional): If True, a preview request is sent first and the change is only
                made when the preview is clean. If False, the change is sent directly. Cannot be
                combined with dry_run. Defaults to True.
            instructions (OrderInstructions, optional): Order instructions. Defaults to NONE.

        Returns:
            dict: The preview (net price, both legs' quotes, estimated total) or, for a real change,
                ``{"result": {"state": "ORDER-PROCESSING"}}``.

        """
        return self._modify(urls.complex_option_order_edit(), order_id, net_price, contracts, dry_run, preview, instructions)

    def modify_option_order(
        self,
        order_id: str,
        price: float,
        contracts: int,
        price_type: PriceType = PriceType.LIMIT,
        duration: Duration = Duration.DAY,
        *,
        dry_run: bool = True,
        preview: bool = True,
        instructions: OrderInstructions = OrderInstructions.NONE,
    ) -> dict:
        """Change the price or size of a working single-leg option order.

        The request mirrors the one the Firstrade mobile app builds for a single-leg edit. Unlike
        ``modify_spread_order`` it has not been tried against a live order, so treat it as untested.

        Args:
            order_id (str): The id of a working option order, from the order list.
            price (float): The new limit price.
            contracts (int): The new number of contracts.
            price_type (PriceType, optional): The price type. Defaults to LIMIT.
            duration (Duration, optional): The duration. Defaults to DAY.
            dry_run (bool, optional): If True, only the preview request is sent. Defaults to True.
            preview (bool, optional): If True, a preview request is sent first. If False, the change
                is sent directly. Cannot be combined with dry_run. Defaults to True.
            instructions (OrderInstructions, optional): Order instructions. Defaults to NONE.

        Returns:
            dict: The preview or the result of the change.

        """
        return self._modify(
            urls.option_order_edit(), order_id, price, contracts, dry_run, preview, instructions,
            extra={"price_type": price_type, "duration": duration},
        )

    def _modify(
        self,
        url: str,
        order_id: str,
        price: float,
        contracts: int,
        dry_run: bool,
        preview: bool,
        instructions: OrderInstructions,
        extra: dict | None = None,
    ) -> dict:
        """Send a cancel/replace request, previewing first unless told not to.

        Args:
            url (str): The cancel/replace endpoint.
            order_id (str): The id of the working order.
            price (float): The new price.
            contracts (int): The new number of contracts.
            dry_run (bool): If True, only the preview request is sent.
            preview (bool): If True, a preview request is sent first.
            instructions (OrderInstructions): Order instructions.
            extra (dict | None): Further fields the endpoint takes.

        Returns:
            dict: The preview or the result of the change.

        Raises:
            ValueError: If preview is False while dry_run is True.

        """
        if dry_run and not preview:
            raise ValueError("A dry run is a preview: preview=False cannot be combined with dry_run=True.")
        data = {
            "order_id": order_id,
            "contracts": contracts,
            "limit_price": price,
            "instructions": instructions,
            **(extra or {}),
        }
        if preview:
            response = self.ft_session._request("post", url=url, data={**data, "preview": "true"})
            if response.status_code != 200 or response.json()["error"] != "":
                return response.json()
            if dry_run:
                return response.json()
        response = self.ft_session._request("post", url=url, data={**data, "preview": "false"})
        return response.json()

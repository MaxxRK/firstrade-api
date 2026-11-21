import dataclasses
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

    ``BUY_TO_CLOSE_OPTION`` and ``BUY_TO_COVER`` are both ``"BC"``: Firstrade uses one code for
    both and tells them apart by the security. So ``BUY_TO_CLOSE_OPTION`` is an alias of
    ``BUY_TO_COVER``: ``OrderType("BC")`` is ``BUY_TO_COVER`` and iterating ``OrderType`` shows
    only that name. The value sent is the same either way.

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


class MultiLegStrategy(enum.StrEnum):
    """The strategies the multi-leg order endpoint takes, by the value it expects.

    The values are the ones the server accepted when they were sent to it as previews; any other
    (``strangle``, ``vertical``, ``calendar``, the short codes ``SP``/``ST``/``BF``/``CD``/``ICD``/``IBF``)
    is answered with ``Invalid order type.``

    Attributes:
        SPREAD (str): Two legs, calls or puts.
        STRADDLE (str): A call and a put at one strike and one expiration, bought to open or sold to close.
        BUTTERFLY (str): Three legs at equal strike steps, the middle one twice the size of each wing.
        CONDOR (str): Four legs.
        IRON_CONDOR (str): Four legs: a put spread and a call spread.
        IRON_BUTTERFLY (str): Four legs sharing a middle strike.

    """

    SPREAD = "spread"
    STRADDLE = "straddle"
    BUTTERFLY = "butterfly"
    CONDOR = "condor"
    IRON_CONDOR = "ironcondor"
    IRON_BUTTERFLY = "ironbutterfly"


class CloseOutType(enum.StrEnum):
    """The strategy codes the close-pair lookup takes, as the server lists them.

    These are not the values of ``MultiLegStrategy``: the server answers anything else with
    ``"co_type" must be one of [SP, ST, BF, ICD, CD, IBF]``.

    Attributes:
        SPREAD (str): A spread.
        STRADDLE (str): A straddle.
        BUTTERFLY (str): A butterfly.
        CONDOR (str): A condor.
        IRON_CONDOR (str): An iron condor.
        IRON_BUTTERFLY (str): An iron butterfly.

    """

    SPREAD = "SP"
    STRADDLE = "ST"
    BUTTERFLY = "BF"
    CONDOR = "CD"
    IRON_CONDOR = "ICD"
    IRON_BUTTERFLY = "IBF"


@dataclasses.dataclass(frozen=True)
class Leg:
    """One leg of a multi-leg option order.

    Attributes:
        symbol (str): The option ticker symbol.
        transaction (OrderType): BUY_OPTION, SELL_OPTION, BUY_TO_CLOSE_OPTION or SELL_TO_CLOSE_OPTION.
        contracts (int): The number of contracts of this leg. Defaults to 1.

    """

    symbol: str
    transaction: OrderType
    contracts: int = 1


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
            preview (bool, optional): If True, a preview request is sent first and the order is only
                placed when the preview is clean. If False, the real order is sent directly, saving one
                round trip, and any problem the preview would have caught comes back from the order
                itself. Cannot be combined with dry_run, because a dry run is a preview. Defaults to True.

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
            preview (bool, optional): If True, a preview request is sent first and the order is only
                placed when the preview is clean. If False, the real order is sent directly. Cannot be
                combined with dry_run. A spread sent this way, without a preview, was accepted and filled
                on a live account. Defaults to True.

        Returns:
            dict: A dictionary containing the order confirmation data, or the error.

        """
        return self.place_complex_order(
            account,
            MultiLegStrategy.SPREAD,
            [Leg(leg1_symbol, leg1_transaction, contracts), Leg(leg2_symbol, leg2_transaction, contracts)],
            limit_type,
            net_price,
            dry_run=dry_run,
            preview=preview,
        )

    def place_complex_order(
        self,
        account: str,
        strategy: MultiLegStrategy,
        legs: list[Leg],
        limit_type: SpreadLimitType,
        net_price: float,
        *,
        dry_run: bool = True,
        preview: bool = True,
    ) -> dict:
        """Build and place a multi-leg option order: a spread, straddle, butterfly, condor or iron one.

        The order is one limit order priced as a single net amount, a day order. The library checks
        only what it needs to build the request (two to four legs). Everything about the strategy
        itself is the server's to judge, and its answer comes back untouched, with its reference code:
        that a straddle takes one call and one put at one strike, bought to open or sold to close;
        that a butterfly has three legs at equal strike steps with the middle one twice the size of
        a wing; that the legs of a condor or iron strategy have to fit together.

        Args:
            account (str): The account number to place the order in.
            strategy (MultiLegStrategy): The strategy, by the value the server expects.
            legs (list[Leg]): Two to four legs, in the order the strategy is described.
            limit_type (SpreadLimitType): DEBIT if the order pays the net price, CREDIT if it receives it.
            net_price (float): The net price of the whole order, always positive.
            dry_run (bool, optional): If True, the order is built and validated but not placed. Defaults to True.
            preview (bool, optional): If True, a preview request is sent first and the order is only
                placed when the preview is clean. If False, the real order is sent directly. Cannot be
                combined with dry_run. Defaults to True.

        Returns:
            dict: A dictionary containing the order confirmation data, or the error.

        Raises:
            ValueError: If preview is False while dry_run is True, or there are not two to four legs.

        """
        if dry_run and not preview:
            raise ValueError("A dry run is a preview: preview=False cannot be combined with dry_run=True.")
        if not 2 <= len(legs) <= 4:
            raise ValueError("A multi-leg order has two to four legs.")

        data: dict[str, object] = {"order_type": strategy}
        for index, leg in enumerate(legs, start=1):
            data[f"transaction{index}"] = leg.transaction
            data[f"symbol{index}"] = leg.symbol
            data[f"contracts{index}"] = leg.contracts
        data.update(
            {
                "limit_type": limit_type,
                "net_price": net_price,
                "instructions": OrderInstructions.NONE,
                "preview": "true",
                "account": account,
            }
        )

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

    def get_option_order_analysis(
        self,
        option_symbol: str,
        order_type: OrderType,
        contracts: int,
        price: float,
        price_type: PriceType = PriceType.LIMIT,
    ) -> dict:
        """Ask what a single-leg option order would be: its strategy, cost, break-even and worst case.

        This is the overview the mobile app shows before an order is placed. It places nothing and
        takes none of the order's own bookkeeping fields: no account, preview, duration or instructions
        (the server refuses all four).

        Args:
            option_symbol (str): The option ticker symbol.
            order_type (OrderType): BUY_OPTION, SELL_OPTION, BUY_TO_CLOSE_OPTION or SELL_TO_CLOSE_OPTION.
            contracts (int): The number of contracts.
            price (float): The limit price.
            price_type (PriceType, optional): The price type. Defaults to LIMIT.

        Returns:
            dict: ``strategy`` (e.g. "Long Call (Bullish)"), ``estimatedTotal``, ``breakevenPrice``,
                ``maxProfit``, ``maxLoss`` and a ``summary`` in words, or the server's error.

        """
        data = {
            "transaction": order_type,
            "symbol": option_symbol,
            "contracts": contracts,
            "price_type": price_type,
            "limit_price": price,
        }
        response = self.ft_session._request("post", url=urls.option_order_analysis(), data=data)
        return response.json()

    def get_complex_option_order_analysis(
        self,
        strategy: MultiLegStrategy,
        legs: list[Leg],
        limit_type: SpreadLimitType,
        net_price: float,
    ) -> dict:
        """Ask what a multi-leg order would be: its strategy, cost, break-even and worst case.

        The multi-leg counterpart of ``get_option_order_analysis``, with the legs of
        ``place_complex_order``. It places nothing, and takes no account, preview or instructions.

        Args:
            strategy (MultiLegStrategy): The strategy, by the value the server expects.
            legs (list[Leg]): Two to four legs.
            limit_type (SpreadLimitType): DEBIT if the order pays the net price, CREDIT if it receives it.
            net_price (float): The net price of the whole order, always positive.

        Returns:
            dict: ``strategy`` (e.g. "Long Call Vertical Spread (Bullish)"), ``estimatedTotal``,
                ``breakevenPrice``, ``maxProfit``, ``maxLoss`` and a ``summary`` in words, or the
                server's error.

        Raises:
            ValueError: If there are not two to four legs.

        """
        if not 2 <= len(legs) <= 4:
            raise ValueError("A multi-leg order has two to four legs.")
        data: dict[str, object] = {"order_type": strategy}
        for index, leg in enumerate(legs, start=1):
            data[f"transaction{index}"] = leg.transaction
            data[f"symbol{index}"] = leg.symbol
            data[f"contracts{index}"] = leg.contracts
        data.update({"limit_type": limit_type, "net_price": net_price})
        response = self.ft_session._request("post", url=urls.complex_option_order_analysis(), data=data)
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
        return self._modify(
            urls.complex_option_order_edit(),
            {
                "order_id": order_id,
                "contracts": contracts,
                "limit_price": net_price,
                "instructions": instructions,
            },
            dry_run=dry_run,
            preview=preview,
        )

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

        The request mirrors the one the Firstrade mobile app builds for a single-leg edit, and was
        checked against a live account: the preview and the change were both accepted, and the order
        list showed the old order as ``ORDER-UPDATED`` and a new one at the new price.

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
            urls.option_order_edit(),
            {
                "order_id": order_id,
                "contracts": contracts,
                "price_type": price_type,
                "limit_price": price,
                "duration": duration,
                "instructions": instructions,
            },
            dry_run=dry_run,
            preview=preview,
        )

    def modify_stock_order(
        self,
        order_id: str,
        shares: int,
        price_type: PriceType = PriceType.LIMIT,
        price: float | None = None,
        duration: Duration = Duration.DAY,
        *,
        dry_run: bool = True,
        preview: bool = True,
        instructions: OrderInstructions = OrderInstructions.NONE,
    ) -> dict:
        """Change the price or size of a working equity order.

        The request is the one the Firstrade mobile app sends for an equity edit: the order form
        without ``symbol`` and ``transaction``, which an edit cannot change (the server refuses
        both). Market and limit orders are supported. A stop or trailing-stop edit needs fields
        that were not checked, so those price types raise ``ValueError``.

        Firstrade replaces the order as it does for options: the old one is cancelled and a new one
        entered, so the new order has a new id.

        Args:
            order_id (str): The id of a working equity order, from the order list.
            shares (int): The new number of shares.
            price_type (PriceType, optional): MARKET or LIMIT. Defaults to LIMIT.
            price (float, optional): The new limit price. Required for a limit order.
            duration (Duration, optional): The duration. Defaults to DAY.
            dry_run (bool, optional): If True, only the preview request is sent. Defaults to True.
            preview (bool, optional): If True, a preview request is sent first. If False, the change
                is sent directly. Cannot be combined with dry_run. Defaults to True.
            instructions (OrderInstructions, optional): Order instructions. Defaults to NONE.

        Returns:
            dict: The preview or the result of the change.

        Raises:
            ValueError: If price_type is not MARKET or LIMIT, or a limit order has no price.

        """
        if price_type not in {PriceType.MARKET, PriceType.LIMIT}:
            raise ValueError("Only market and limit equity orders can be edited here.")
        if price_type == PriceType.LIMIT and price is None:
            raise ValueError("A limit order needs a price.")
        data: dict[str, object] = {
            "order_id": order_id,
            "shares": shares,
            "price_type": price_type,
            "duration": duration,
            "instructions": instructions,
        }
        if price_type == PriceType.LIMIT:
            data["limit_price"] = price
        return self._modify(urls.order_edit(), data, dry_run=dry_run, preview=preview)

    def _modify(self, url: str, data: dict[str, object], *, dry_run: bool, preview: bool) -> dict:
        """Send a cancel/replace request, previewing first unless told not to.

        Args:
            url (str): The cancel/replace endpoint.
            data (dict): The request body without the ``preview`` flag.
            dry_run (bool): If True, only the preview request is sent.
            preview (bool): If True, a preview request is sent first.

        Returns:
            dict: The preview or the result of the change.

        Raises:
            ValueError: If preview is False while dry_run is True.

        """
        if dry_run and not preview:
            raise ValueError("A dry run is a preview: preview=False cannot be combined with dry_run=True.")
        if preview:
            response = self.ft_session._request("post", url=url, data={**data, "preview": "true"})
            if response.status_code != 200 or response.json()["error"] != "":
                return response.json()
            if dry_run:
                return response.json()
        response = self.ft_session._request("post", url=url, data={**data, "preview": "false"})
        return response.json()

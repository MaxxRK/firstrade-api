from enum import Enum

from firstrade.account import FTSession
from firstrade import urls

from bs4 import BeautifulSoup


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


class Order:

    """
    This class contains information about an order.
    It also contains a method to place an order.
    """
    def __init__(self, ft_session: FTSession):
        self.ft_session = ft_session
        self.order_confirmation = {}

    def place_order(
        self,
        account,
        symbol,
        price_type: PriceType,
        order_type: OrderType,
        quantity,
        duration: Duration,
        price=0.00,
        dry_run=True,
        notional=False,
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

        if dry_run:
            previewOrders = "1"
        else:
            previewOrders = ""

        if price_type == PriceType.MARKET:
            price = ""

        data = {
            "submiturl": "/cgi-bin/orderbar",
            "orderbar_clordid": "",
            "orderbar_accountid": "",
            "notional": "yes" if notional else "",
            "stockorderpage": "yes",
            "submitOrders": "1",
            "previewOrders": previewOrders,
            "lotMethod": "1",
            "accountType": "1",
            "quoteprice": "",
            "viewederror": "",
            "stocksubmittedcompanyname1": "",
            "accountId": account,
            "transactionType": order_type,
            "quantity": quantity,
            "symbol": symbol,
            "priceType": price_type,
            "limitPrice": price,
            "duration": duration,
            "qualifier": "0",
            "cond_symbol0_0": "",
            "cond_type0_0": "2",
            "cond_compare_type0_0": "2",
            "cond_compare_value0_0": "",
            "cond_and_or0": "1",
            "cond_symbol0_1": "",
            "cond_type0_1": "2",
            "cond_compare_type0_1": "2",
            "cond_compare_value0_1": "",
        }

        order_data = BeautifulSoup(
            self.ft_session.post(
                url=urls.orderbar(), headers=urls.session_headers(), data=data
            ).text,
            "xml",
        )
        order_confirmation = {}
        order_success = order_data.find("success").text.strip()
        order_confirmation["success"] = order_success
        action_data = order_data.find("actiondata").text.strip()
        if order_success != "No":
            # Extract the table data
            table_start = action_data.find("<table")
            table_end = action_data.find("</table>") + len("</table>")
            table_data = action_data[table_start:table_end]
            table_data = BeautifulSoup(table_data, "xml")
            titles = table_data.find_all("th")
            data = table_data.find_all("td")
            for i, title in enumerate(titles):
                order_confirmation[f"{title.get_text()}"] = data[i].get_text()
            if not dry_run:
                start_index = action_data.find(
                    "Your order reference number is: "
                ) + len("Your order reference number is: ")
                end_index = action_data.find("</div>", start_index)
                order_number = action_data[start_index:end_index]
            else:
                start_index = action_data.find('id="') + len('id="')
                end_index = action_data.find('" style=', start_index)
                order_number = action_data[start_index:end_index]
            order_confirmation["orderid"] = order_number
        else:
            order_confirmation["actiondata"] = action_data
        order_confirmation["errcode"] = order_data.find("errcode").text.strip()
        self.order_confirmation = order_confirmation

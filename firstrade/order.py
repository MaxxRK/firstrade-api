from account import FTSession
import urls
import re
from bs4 import BeautifulSoup


class Order:
    def __init__(self, ft_session: FTSession):
        self.ft_session = ft_session,
        self.symbol = '',
        self.order_type = '',
        self.quantity = '',
        self.price = 0.0,
        self.duration = '',
        self.order_confirmation = {}

    def place_order(self, account, symbol, order_type, quantity, price, duration, dry_run=True):
        if dry_run:
            previewOrders = '1'
        else:
            previewOrders = ''

        data = {
            'submiturl': '/cgi-bin/orderbar',
            'orderbar_clordid': '',
            'orderbar_accountid': '',
            'stockorderpage': 'yes',
            'submitOrders': '1',
            'previewOrders': previewOrders,
            'lotMethod': '1',
            'accountType': '1',
            'quoteprice': '',
            'viewederror': '',
            'stocksubmittedcompanyname1': '',
            'accountId': account,
            'transactionType': 'S',
            'quantity': quantity,
            'symbol': symbol,
            'priceType': order_type,
            'limitPrice': price,
            'duration': duration,
            'qualifier': '0',
            'cond_symbol0_0': '',
            'cond_type0_0': '2',
            'cond_compare_type0_0': '2',
            'cond_compare_value0_0': '',
            'cond_and_or0': '1',
            'cond_symbol0_1': '',
            'cond_type0_1': '2',
            'cond_compare_type0_1': '2',
            'cond_compare_value0_1': ''
        }

        order_data = BeautifulSoup(self.ft_session.post(
            url=urls.orderbar(),
            headers=urls.session_headers(),
            data=data
        ).text, 'xml')
        order_success = order_data.find('success').text.strip()
        self.order_confirmation['success'] = order_success
        action_data = order_data.find('actiondata').text.strip()
        # Extract the table data
        table_start = action_data.find('<table')
        table_end = action_data.find('</table>') + len('</table>')
        table_data = action_data[table_start:table_end]
        table_data = BeautifulSoup(table_data, 'xml')
        titles = table_data.find('th')
        data = table_data.find('td')
        for i, title in enumerate(titles):
            self.order_confirmation[title] = data[i]
        
        print(self.order_confirmation)
        
        start_index = action_data.find('Your order reference number is: ') + len('Your order reference number is: ')
        end_index = action_data.find('</div>', start_index)
        order_number = action_data[start_index:end_index]
        self.order_confirmation['orderid'] = order_number
        return self.order_confirmation
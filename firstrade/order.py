from account import FTSession
import urls
import re
from bs4 import BeautifulSoup


class Order:
    def __init__(self, ft_session: FTSession):
        self.ft_session = ft_session
        self.symbol = ''
        self.order_type = ''
        self.quantity = ''
        self.price = 0.0
        self.duration = ''
        self.order_confirmation = {}

    def place_order(self, account, symbol, order_type, quantity, price, duration, dry_run=True):
        if dry_run:
            previewOrders = '1'
        else:
            previewOrders = ''

        if price == '0.00' and order_type == '1':
            price = ''

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
            'transactionType': 'B',
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
        if order_success != "No":
            # Extract the table data
            table_start = action_data.find('<table')
            table_end = action_data.find('</table>') + len('</table>')
            table_data = action_data[table_start:table_end]
            table_data = BeautifulSoup(table_data, 'xml')
            titles = table_data.find_all('th')
            data = table_data.find_all('td')
            for i, title in enumerate(titles):
                self.order_confirmation[f'{title.get_text()}'] = data[i].get_text()
            if not dry_run:
                start_index = action_data.find('Your order reference number is: ') + len('Your order reference number is: ')
                end_index = action_data.find('</div>', start_index)
                order_number = action_data[start_index:end_index]
            else:
                start_index = action_data.find('id="') + len('id="')
                end_index = action_data.find('" style=', start_index)
                order_number = action_data[start_index:end_index]
            self.order_confirmation['orderid'] = order_number
        else:
            self.order_confirmation['actiondata'] = action_data
        self.order_confirmation['errcode'] = order_data.find('errcode').text.strip()
        return self.order_confirmation
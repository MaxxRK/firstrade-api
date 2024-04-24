import random
import time
from tqdm import tqdm
from scalp_reverse_splits import TheMarket
import scalp_reverse_splits
from datetime import datetime
import json
import os
import alpaca_reverse as ar
from firstrade import account, order, symbols


def execute_fractional_sell_order(ft_ss, ticker, quantity, account_number):
    ft_order = order.Order(ft_ss)
    ft_order.place_order(account_number,
                         symbol=ticker,
                         price_type=order.PriceType.MARKET,
                         order_type=order.OrderType.SELL,
                         quantity=quantity,
                         duration=order.Duration.DAY,
                         dry_run=False,
                         notional=False)
    return ft_order.order_confirmation


def sell_fractional_split_stocks(ft_ss, open_positions, known_bads, market, account_number, buy_price=1.44, sell_price=1.60):
    owned_stocks = []
    sold_list = []
    sold_cash = 0.0
    for key in tqdm(open_positions, desc="Selling positions"):
        try:
            quote = symbols.SymbolQuote(ft_ss, key)
            ticker = quote.symbol
            quantity = quote.quantity

            owned_stocks.append(ticker)

            if ticker in known_bads:
                print(f"{ticker} is a known bad")
                continue

            if quantity == 0:
                # print(f"{ticker} has 0 quantity; not selling.")
                continue

            if float(position['intraday_quantity']) != 0:
                # print(f"{ticker} has intraday quantity; not selling.")
                continue
            if float(position['shares_available_for_exercise']) <= 0:
                # print(f"{ticker} has no shares available for exercise; not selling.")
                continue

            stock = market.get_stock(ticker)
            if not stock:
                print(f"{ticker} not found in market, checking in Robinhood and adding to market")
                time.sleep(0.5 + random.randint(0, 500) / 100)
                current_bid_price = r.stocks.get_latest_price(ticker, priceType='bid_price')[0]
                print(f"Current bid price: {current_bid_price}")
                market.add_stock(ticker=ticker, price=current_bid_price)
                stock = market.get_stock(ticker)

            if stock.fractional_tradability is None:
                print("Updating fractional tradability for", ticker)
                time.sleep(0.5 + random.randint(0, 500) / 100)
                stock_info = r.stocks.get_instruments_by_symbols(ticker)
                if len(stock_info) == 0:
                    print(f"{ticker} not found in Robinhood.")
                    scalp_reverse_splits.add_bad_to_list(ticker)
                    continue
                stock_info = stock_info[0]
                tradable = stock_info['fractional_tradability'] == 'tradable'
                market.modify_stock(ticker, 'fractional_tradability', tradable)
                if not tradable:
                    # print(f"{ticker} is not tradable fractionally.")
                    continue

            if stock.fractional_tradability:
                print(f"Attempting to sell {ticker} for {stock.price}")
                time.sleep(0.5 + random.randint(0, 500) / 100)
                sale = execute_fractional_sell_order(ft_ss=ft_ss,
                                                     ticker=ticker,
                                                     quantity=quantity,
                                                     account_number=account_number)
                print(f"Sale: {sale}")
                if 'error' not in sale:
                    sold_cash += float(stock.price) * quantity
                    sold_list.append(scalp_reverse_splits.FinVizStock(ticker, stock.price * (quantity)))
                continue

            if quantity == 1.0 and float(position['shares_available_for_exercise']) == 1.0:
                if stock.price < buy_price:
                    # print(f"{ticker} has 1 share and is in target buy range; not selling.")
                    continue
                elif stock.price > sell_price:
                    print("Price has risen above sell price, selling.")
                    sale = execute_fractional_sell_order(ft_ss=ft_ss,
                                                         ticker=ticker,
                                                         quantity=quantity,
                                                         account_number=account_number)
                    print(f"Sale: {sale}")
                    if 'error' not in sale:
                        sold_cash += float(stock.price) * quantity
                        sold_list.append(scalp_reverse_splits.FinVizStock(ticker, stock.price * (quantity)))

            elif quantity >= 100:
                print(f"{ticker} is presumably being used for wheel strategy; not selling.")
                continue

            elif (1.0 < float(position['shares_available_for_exercise']) < 5) and (
                    float(position['average_buy_price']) < buy_price):
                print(f"Conditions met for selling all but one of {ticker}")
                time.sleep(0.5 + random.randint(0, 500) / 100)
                sale = execute_fractional_sell_order(ft_ss=ft_ss,
                                                     ticker=ticker,
                                                     quantity=quantity,
                                                     account_number=account_number)
                print(f"Sale: {sale}")
                if 'error' not in sale:
                    sold_cash += float(stock.price) * (quantity - 1)
                    sold_list.append(scalp_reverse_splits.FinVizStock(ticker, stock.price * (quantity - 1)))

            else:
                print(f"Uncategorized position: {position}")
                time.sleep(0.5 + random.randint(0, 500) / 100)
                stock_info = r.stocks.get_instruments_by_symbols(ticker)
                if len(stock_info) == 0:
                    print(f"{ticker} not found in Robinhood.")
                    scalp_reverse_splits.add_bad_to_list(ticker)
                    continue
                stock_info = stock_info[0]
                print(stock_info)
        except Exception as e:
            print(e)
            continue
    print("-" * 50)
    return owned_stocks, sold_list, sold_cash, market


def execute_buy_order(ft_ss, ticker, price, account_number):
    ft_order = order.Order(ft_ss)
    ft_order.place_order(account_number,
                         symbol=ticker,
                         price_type=order.PriceType.LIMIT,
                         order_type=order.OrderType.BUY,
                         quantity=1,
                         duration=order.Duration.DAY,
                         price=price,
                         dry_run=False,
                         notional=False)
    return ft_order.order_confirmation


def buy_stock_to_split(ft_ss, market, owned_stocks, account, buying_power, buy_price=1.44):
    print(f"Owned stocks: {owned_stocks}")
    buy_list = []
    spent_cash = 0.0

    for stock in tqdm(market.stocks, desc="Checking stonks prices"):
        if stock.price is None:
            print(f"No price in market for {stock.ticker}, getting from Robinhood")
            current_bid_price = r.stocks.get_latest_price(stock.ticker, priceType='bid_price')[0]
            if current_bid_price is not None:
                print(f"Current bid price: {current_bid_price}")
                market.modify_stock(stock.ticker, 'price', current_bid_price)
            else:
                market.remove_stock(stock.ticker)

    # order market by price and buy the cheapest first
    market.stocks = sorted(market.stocks, key=lambda x: x.price)

    for stock in tqdm(market.stocks, desc="Buying stonks"):
        try:
            if spent_cash >= buying_power * 0.90:
                break

            if stock.fractional_tradability:
                continue

            elif stock.fractional_tradability is None:
                print(f"Checking fractional tradability for {stock.ticker}")
                time.sleep(0.5 + random.randint(0, 500) / 100)
                stock_info = r.stocks.get_instruments_by_symbols(stock.ticker)
                stock_info = stock_info[0]
                if stock_info['fractional_tradability'] != 'tradable':
                    market.set_fractional_tradability(stock.ticker, False)
                else:
                    market.set_fractional_tradability(stock.ticker, True)
                    continue

            if stock.price < buy_price and stock.ticker not in owned_stocks:
                buy_list.append(stock)
                print(f"Current spent amount: ${round(spent_cash, 2)}")
                print(f"Remaining buying power (est): ${round(buying_power * .95 - spent_cash, 2)}")
                time.sleep(0.5 + random.randint(0, 500) / 100)
                print(f"Buying 1 share of {stock.ticker} for ${stock.price}")
                purchase = r.orders.order(symbol=stock.ticker,
                                          quantity=1,
                                          side="buy",
                                          account_number=account,
                                          limitPrice=stock.price,
                                          timeInForce='gfd',
                                          extendedHours=False,
                                          jsonify=True)
                if 'error' not in purchase:
                    spent_cash += stock.price
                if 'detail' in purchase:
                    if "Not enough buying power" in purchase['detail']:
                        print("Not enough buying power")
                        break
                print("Purchase: " + str(purchase))
            elif stock.price > buy_price:
                print(f"{stock.ticker} is above buy price; not buying.")
            elif stock.ticker in owned_stocks:
                print(f"Already own {stock.ticker}; not buying.")
            else:
                print(f"Uncategorized position: {stock.ticker}")
        except Exception as e:
            print(e)
            if "is not a valid stock ticker. It is being ignored" in str(e):
                add_bad_to_list(stock.ticker)
            if "list index out of range" in str(e):
                add_bad_to_list(stock.ticker)
    for i in range(2):
        print("*" * 50)
    return buy_list, spent_cash, market


def process_first_trade_buy_sell(username, password, pin, pickle_name, account_number, market, buy_price=1.44, sell_price=1.60):
    ft_ss = account.FTSession(username=username, password=password, pin=pin, persist_session=True, profile_path=pickle_name)
    ft_accounts = account.FTAccountData(ft_ss)
    if len(ft_accounts.account_numbers) < 1:
        raise Exception("No accounts found or an error occured exiting...")
    known_bads = ar.get_known_bads()
    ft_accounts.get_positions(account=account_number)
    open_positions = ft_accounts.securities_held
    owned_stocks, sold_list, sold_cash, market = sell_fractional_split_stocks(ft_ss=ft_ss,
                                                                              open_positions=open_positions,
                                                                              known_bads=known_bads,
                                                                              market=market,
                                                                              account_number=account_number,
                                                                              buy_price=buy_price,
                                                                              sell_price=sell_price)
    print("SELLING COMPLETE")
    print("-" * 50)
    if len(sold_list) != 0:
        print("Sold list:")
        for stock in sold_list:
            print(stock.ticker + " | " + str(round(float(stock.price), 3)))
        print("-" * 50)
    print(f"Sold cash: ${round(sold_cash, 2)}")
    buying_power = ft_accounts.account_balances[account_number]['buying_power']
    print(f"Buying power: ${round(buying_power, 2)}")
    print("-" * 50)
    buy_list, buy_cash, market = buy_stock_to_split(ftss=ftss,
                                                    owned_stocks=owned_stocks,
                                                    market=market,
                                                    account=account,
                                                    buying_power=buying_power,
                                                    buy_price=buy_price)




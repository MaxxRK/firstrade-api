#!/usr/bin/python3

import json

from firstrade import account, order, symbols

# Create a session
# mfa_secret is the secret key to generate TOTP (not the backup code), see:
# https://help.firstrade.info/en/articles/9260184-two-factor-authentication-2fa
# save session flag now required to save cookies json file
ft_ss = account.FTSession(username="", password="", mfa_secret="", save_session=True)
# ft_ss = account.FTSession(username="", password="", email="", profile_path="")
need_code = ft_ss.login()
if need_code:
    code = input("Please enter the pin sent to your email/phone: ")
    ft_ss.login_two(code)

# Get account data
ft_accounts = account.FTAccountData(ft_ss)
if len(ft_accounts.account_numbers) < 1:
    raise Exception("No accounts found or an error occured exiting...")

# Print ALL account data
print(f"Account data: {json.dumps(ft_accounts.all_accounts, indent=2)}")

# Print 1st account number.
print(f"1st account number: {ft_accounts.account_numbers[0]}")

# Print ALL accounts market values.
print(f"Account(s) current balance(s): {ft_accounts.account_balances}")

# Get quote for INTC
quote = symbols.SymbolQuote(ft_ss, ft_accounts.account_numbers[0], "INTC")
print("Quote for INTC:")
print(f"\tSymbol: {quote.symbol}")
print(f"\tTick: {quote.tick}")
print(f"\tExchange: {quote.exchange}")
print(f"\tBid: {quote.bid}")
print(f"\tAsk: {quote.ask}")
print(f"\tLast: {quote.last}")
print(f"\tBid Size: {quote.bid_size}")
print(f"\tAsk Size: {quote.ask_size}")
print(f"\tLast Size: {quote.last_size}")
print(f"\tBid MMID: {quote.bid_mmid}")
print(f"\tAsk MMID: {quote.ask_mmid}")
print(f"\tLast MMID: {quote.last_mmid}")
print(f"\tChange: {quote.change}")
print(f"\tHigh: {quote.high}")
print(f"\tLow: {quote.low}")
print(f"\tChange Color: {quote.change_color}")
print(f"\tVolume: {quote.volume}")
print(f"\tQuote Time: {quote.quote_time}")
print(f"\tLast Trade Time: {quote.last_trade_time}")
print(f"\tReal Time: {quote.realtime}")
print(f"\tFractional: {quote.is_fractional}")
print(f"\tCompany Name: {quote.company_name}")

# Get positions and print them out for an account.
positions = ft_accounts.get_positions(account=ft_accounts.account_numbers[0])
print(f"Current positions held in account {ft_accounts.account_numbers[0]}: {json.dumps(positions, indent=2)}")
print(f"Current positions (summed up) held in account {ft_accounts.account_numbers[0]}:")
for item in positions["items"]:
    print(f"\t{item['quantity']}\tof security {item['symbol']}.")

# Get account history for a custom date range
history = ft_accounts.get_account_history(
    account=ft_accounts.account_numbers[0],
    date_range="cust",
    custom_range=["2025-12-01", "2025-12-31"],
)

print(f"Transaction history (December 2025) for account #{ft_accounts.account_numbers[0]}: {json.dumps(history, indent=2)}")
if len(history["items"]) > 0:
    print("Transaction history (summed up) for December 2025:")
    for item in history["items"]:
        print(f"\t{item['report_date']}: {item['amount']}$\tof {item['symbol']}")

# Create an order object.
ft_order = order.Order(ft_ss)

# Place a dry run order and print out order confirmation data.
order_conf = ft_order.place_order(
    ft_accounts.account_numbers[0],
    symbol="INTC",
    price_type=order.PriceType.LIMIT,
    order_type=order.OrderType.BUY,
    duration=order.Duration.DAY,
    quantity=1,
    price=3.37,
    dry_run=True,
)
print(f"Preview of an order to buy 1 share of INTC: {json.dumps(order_conf, indent=2)}")

if order_conf.get("error"):
    print(f"Error placing order: {order_conf['error']} : {order_conf['message']}")
elif "order_id" not in order_conf["result"]:
    print("Dry run complete!")
else:
    print("Order placed successfully!")
    print(f"\tOrder ID: {order_conf['result']['order_id']}.")
    print(f"\tOrder State: {order_conf['result']['state']}.")

# Cancel placed order (on success and if it was not a dry_run)
if not order_conf.get("error") and "order_id" in order_conf["result"]:
    cancel = ft_accounts.cancel_order(order_conf["result"]["order_id"])
    if cancel["result"]["result"] == "success":
        print(f"Order cancelled successfully: {cancel}.")
    else:
        print(f"Cannot cancel order: {cancel}.")


# Retrieve OHLC data
ohlc = symbols.SymbolOHLC(ft_ss, "INTC", range_="1y")
print(f"Open-high-low-close chart data for INTC (first two values, format: <timestamp, open, high, low, close, volume>): {ohlc.candles[:2]}")

# Check orders
recent_orders = ft_accounts.get_orders(ft_accounts.account_numbers[0])
print(f"Recent orders: {json.dumps(recent_orders, indent=2)}")

# Get option dates for a symbol
option_first = symbols.OptionQuote(ft_ss, "INTC")
print("Option expiration dates for INTC:")
for item in option_first.option_dates["items"]:
    print(
        f"\tExpiration Date: {item['exp_date']} Days Left: {item['day_left']} Expiration Type: {item['exp_type']}",
    )

# Get option quote
option_quote = option_first.get_option_quote(
    "INTC",
    option_first.option_dates["items"][0]["exp_date"],
)
limited_option_quote = {
    **option_quote,
    "items": option_quote["items"][:2],
}
print(f"Option quote for INTC (limited to the first two items): {json.dumps(limited_option_quote, indent=2)}")

# Get option greeks
option_greeks = option_first.get_greek_options(
    "INTC",
    option_first.option_dates["items"][0]["exp_date"],
)
limited_option_greeks = {
    **option_greeks,
    "chains": option_greeks["chains"][:2],
}
print(f"Option greeks at {option_first.option_dates['items'][0]['exp_date']} for INTC (limited to the first two chains): {json.dumps(limited_option_greeks, indent=2)}")

# Place dry option order
option_order = ft_order.place_option_order(
    account=ft_accounts.account_numbers[0],
    option_symbol=option_quote["items"][0]["opt_symbol"],
    order_type=order.OrderType.BUY_OPTION,
    price_type=order.PriceType.LIMIT,
    duration=order.Duration.DAY,
    price=0.01,
    contracts=1,
    dry_run=True,
)
print(f"Preview of an option order for {option_quote['items'][0]['opt_symbol']}: {json.dumps(option_order, indent=2)}")

# Delete the session cookie
# ft_ss.delete_cookies()

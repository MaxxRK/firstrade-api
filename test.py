from firstrade import account, order, symbols

# Create a session
ft_ss = account.FTSession(username="", password="", email = "", profile_path="")
need_code = ft_ss.login()
if need_code:
    code = input("Please enter the pin sent to your email/phone: ")
    ft_ss.login_two(code)

# Get account data
ft_accounts = account.FTAccountData(ft_ss)
if len(ft_accounts.account_numbers) < 1:
    raise Exception("No accounts found or an error occured exiting...")

# Print ALL account data
print(ft_accounts.all_accounts)

# Print 1st account number.
print(ft_accounts.account_numbers[0])

# Print ALL accounts market values.
print(ft_accounts.account_balances)

# Get quote for INTC
quote = symbols.SymbolQuote(ft_ss, ft_accounts.account_numbers[0], "INTC")
print(f"Symbol: {quote.symbol}")
print(f"Tick: {quote.tick}")
print(f"Exchange: {quote.exchange}")
print(f"Bid: {quote.bid}")
print(f"Ask: {quote.ask}")
print(f"Last: {quote.last}")
print(f"Bid Size: {quote.bid_size}")
print(f"Ask Size: {quote.ask_size}")
print(f"Last Size: {quote.last_size}")
print(f"Bid MMID: {quote.bid_mmid}")
print(f"Ask MMID: {quote.ask_mmid}")
print(f"Last MMID: {quote.last_mmid}")
print(f"Change: {quote.change}")
print(f"High: {quote.high}")
print(f"Low: {quote.low}")
print(f"Change Color: {quote.change_color}")
print(f"Volume: {quote.volume}")
print(f"Quote Time: {quote.quote_time}")
print(f"Last Trade Time: {quote.last_trade_time}")
print(f"Real Time: {quote.realtime}")
print(f"Fractional: {quote.is_fractional}")
print(f"Company Name: {quote.company_name}")

# Get positions and print them out for an account.
positions = ft_accounts.get_positions(account=ft_accounts.account_numbers[1])
print(positions)
for item in positions["items"]:
    print(
        f"Quantity {item['quantity']} of security {item['symbol']} held in account {ft_accounts.account_numbers[1]}"
    )

# Get account history (past 200)
history = ft_accounts.get_account_history(
    account=ft_accounts.account_numbers[0],
    date_range="cust",
    custom_range=["2024-01-01", "2024-06-30"]
)

for item in history["items"]:
    print(f"Transaction: {item['symbol']} on {item['report_date']} for {item['amount']}.")


# Create an order object.
ft_order = order.Order(ft_ss)

# Place dry run order and print out order confirmation data.
order_conf = ft_order.place_order(
    ft_accounts.account_numbers[0],
    symbol="INTC",
    price_type=order.PriceType.LIMIT,
    order_type=order.OrderType.BUY,
    duration=order.Duration.DAY,
    quantity=1,
    dry_run=True,
)

print(order_conf)

if "order_id" not in order_conf["result"]:
    print("Dry run complete.")
    print(order_conf["result"])
else:
    print("Order placed successfully.")
    print(f"Order ID: {order_conf['result']['order_id']}.")
    print(f"Order State: {order_conf['result']['state']}.")

# Cancel placed order
# cancel = ft_accounts.cancel_order(order_conf['result']["order_id"])
# if cancel["result"]["result"] == "success":
    # print("Order cancelled successfully.")
# print(cancel)

# Check orders
recent_orders = ft_accounts.get_orders(ft_accounts.account_numbers[0])
print(recent_orders)

#Get option dates
option_first = symbols.OptionQuote(ft_ss, "INTC")
for item in option_first.option_dates["items"]:
    print(f"Expiration Date: {item['exp_date']} Days Left: {item['day_left']} Expiration Type: {item['exp_type']}")

# Get option quote
option_quote = option_first.get_option_quote("INTC", option_first.option_dates["items"][0]["exp_date"])
print(option_quote)

# Get option greeks
option_greeks = option_first.get_greek_options("INTC", option_first.option_dates["items"][0]["exp_date"])
print(option_greeks)

print(f"Placing dry option order for {option_quote['items'][0]['opt_symbol']} with a price of {option_quote['items'][0]['ask']}.")
print("Symbol readable ticker 'INTC'")

# Place dry option order
option_order = ft_order.place_option_order(
    account=ft_accounts.account_numbers[0],
    option_symbol=option_quote["items"][0]["opt_symbol"],
    order_type=order.OrderType.BUY_OPTION,
    price_type=order.PriceType.MARKET,
    duration=order.Duration.DAY,
    contracts=1,
    dry_run=True,
)

print(option_order)

# Delete cookies
ft_ss.delete_cookies()

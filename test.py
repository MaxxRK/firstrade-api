from firstrade import account, order, symbols
from firstrade.order import get_orders

# Create a session
ft_ss = account.FTSession(username="", password="", pin="")

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
quote = symbols.SymbolQuote(ft_ss, "INTC")
print(f"Symbol: {quote.symbol}")
print(f"Underlying Symbol: {quote.underlying_symbol}")
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
print(f"Bid x Ask: {quote.bidxask}")
print(f"Quote Time: {quote.quote_time}")
print(f"Last Trade Time: {quote.last_trade_time}")
print(f"Real Time: {quote.real_time}")
print(f"Fractional: {quote.fractional}")
print(f"Error Code: {quote.err_code}")
print(f"Company Name: {quote.company_name}")

# Get positions and print them out for an account.
positions = ft_accounts.get_positions(account=ft_accounts.account_numbers[1])
for key in ft_accounts.securities_held:
    print(
        f"Quantity {ft_accounts.securities_held[key]['quantity']} of security {key} held in account {ft_accounts.account_numbers[1]}"
    )

# Create an order object.
ft_order = order.Order(ft_ss)

# Place order and print out order confirmation data.
ft_order.place_order(
    ft_accounts.account_numbers[0],
    symbol="INTC",
    price_type=order.PriceType.MARKET,
    order_type=order.OrderType.BUY,
    quantity=1,
    duration=order.Duration.DAY,
    dry_run=True,
)

# Print Order data Dict
print(ft_order.order_confirmation)

# Check if order was successful
if ft_order.order_confirmation["success"] == "Yes":
    print("Order placed successfully.")
    # Print Order ID
    print(f"Order ID: {ft_order.order_confirmation['orderid']}.")
else:
    print("Failed to place order.")
    # Print errormessage
    print(ft_order.order_confirmation["actiondata"])

# Check orders
current_orders = get_orders(ft_ss, ft_accounts.account_numbers[0])
print(current_orders)

# Delete cookies
ft_ss.delete_cookies()

import account
import symbols
import order

# Create a session
ft_ss = account.FTSession(username='', password='', pin='')

# Get account data
ft_accounts = account.FTAccountData(ft_ss)

# Print ALL account data
print(ft_accounts.all_accounts)

# Print 1st account number.
print(ft_accounts.account_numbers[0])

# Print ALL accounts market values.
print(ft_accounts.account_balances)

# Get quote for INTC
quote = symbols.SymbolQuote(ft_ss, 'INTC')
print(f"Symbol: {quote.symbol}")
print(f"Exchange: {quote.exchange}")
print(f"Bid: {quote.bid}")
print(f"Ask: {quote.ask}")
print(f"Last: {quote.last}")
print(f"Change: {quote.change}")
print(f"High: {quote.high}")
print(f"Low: {quote.low}")
print(f"Volume: {quote.volume}")
print(f"Company Name: {quote.company_name}")

ft_order = order.Order(ft_ss)
# Place order and print out order confirmation data.
ft_order.place_order(
    ft_accounts.account_numbers[0],
    symbol='INTC',
    order_type=order.PriceType.MARKET,
    quantity=1,
    duration=order.Duration.DAY,
    dry_run=False
)

# Print Order data Dict
print(ft_order.order_confirmation)

# Check if order was successful
if ft_order.order_confirmation['success'] == 'Yes':
    print('Order placed successfully.')
    # Print Order ID
    print(ft_order.order_confirmation['orderid'])
else:
    print('Failed to place order.')
    # Print errormessage
    print(ft_order.order_confirmation['actiondata'])

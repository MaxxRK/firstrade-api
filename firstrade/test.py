import account
import symbols
import order

ft_ss = account.FTSession(username='', password='', pin='')
ft_accounts = account.FTAccountData(ft_ss)

print(ft_accounts.all_accounts)

print(ft_accounts.account_numbers[0])
print(ft_accounts.account_balances)

quote = symbols.SymbolInfo(ft_ss, 'INTC')


order_data = order.Order(ft_ss).place_order(
    ft_accounts.account_numbers[0],
    symbol='INTC',
    order_type='1',
    quantity='1',
    price='0.00',
    duration='0',
    dry_run=False
)
print(order_data)
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
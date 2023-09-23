import account
import symbols


ft_ss = account.FTSession(username='', password='', pin='')
ft_accounts = account.FTAccountData(ft_ss)
print(ft_accounts.all_accounts)

accounts = ft_accounts.all_accounts
print(ft_accounts.account_balances)

quote = symbols.SymbolInfo(ft_ss, 'AAPL')

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
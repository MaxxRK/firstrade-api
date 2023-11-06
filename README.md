# firstrade-api
 A reverse-engineered python API to interact with the Firstrade Trading platform.

 This is not an official api! This api's functionality may change at any time.

 This api provides a means of buying and selling stocks through Firstrade. It uses the Session class from requests to get authorization cookies. The rest is done with reverse engineered requests to Firstrade's API. 

 ---

## Contribution
I am new to coding and new to open-source. I would love any help and suggestions!

## Setup
Install using pypi:
```
pip install firstrade
```

## Quikstart
The code below will: 
- Login and print account info. 
- Get a quote for 'INTC' and print out the information
- Place a market order for 'INTC' on the first account in the `account_numbers` list
- Print out the order confirmation

```
from firstrade import account
from firstrade import symbols
from firstrade import order

# Create a session
ft_ss = account.FTSession(username='', password='', pin='')

# Get account data
ft_accounts = account.FTAccountData(ft_ss)
if len(ft_accounts.account_numbers) < 1:
    raise Exception('No accounts found or an error occured exiting...')

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

# Get positions and print them out for an account.
positions = ft_accounts.get_positions(account=ft_accounts.account_numbers[1])
for key in ft_accounts.securities_held:
    print(f"Quantity {ft_accounts.securities_held[key]['quantity']} of security {key} held in account {ft_accounts.account_numbers[1]}")

# Create an order object.   
ft_order = order.Order(ft_ss)

# Place order and print out order confirmation data.
ft_order.place_order(
    ft_accounts.account_numbers[0],
    symbol='INTC',
    price_type=order.PriceType.MARKET,
    order_type=order.OrderType.BUY,
    quantity=1,
    duration=order.Duration.DAY,
    dry_run=True
)

# Print Order data Dict
print(ft_order.order_confirmation)

# Check if order was successful
if ft_order.order_confirmation['success'] == 'Yes':
    print('Order placed successfully.')
    # Print Order ID
    print(f"Order ID: {ft_order.order_confirmation['orderid']}.")
else:
    print('Failed to place order.')
    # Print errormessage
    print(ft_order.order_confirmation['actiondata'])
```
This code is also in test.py

---

 ## Implemented Features
 - [x] Login
 - [x] Get Quotes
 - [x] Get Account Data
 - [x] Place Orders and Receive order confirmation
 - [x] Get Currently Held Positions

## TO DO
- [ ] Check on placed order status.
- [ ] Cancel placed orders
- [ ] Options
- [ ] Give me some Ideas!

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/O5O6PTOYG)  

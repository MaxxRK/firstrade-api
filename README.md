# firstrade-api

A reverse-engineered python API to interact with the Firstrade Trading platform.

This is not an official api! This api's functionality may change at any time.

This api provides a means of buying and selling stocks through Firstrade. It uses the Session class from requests to get authorization cookies. The rest is done with reverse engineered requests to Firstrade's API.

In order to use Fractional shares you must accept the agreement on the website before using it in this API.

---

## Contribution

Please feel free to contribute to this project. If you find any bugs, please open an issue.

## Disclaimer
I am not a financial advisor and not affiliated with Firstrade in any way. Use this tool at your own risk. I am not responsible for any losses or damages you may incur by using this project. This tool is provided as-is with no warranty.

## Setup

Install using pypi:

```
pip install firstrade
```

## Quickstart

The code in `test.py` will:
- Login and print account info.
- Get a quote for 'INTC' and print out the information
- Place a dry run market order for 'INTC' on the first account in the `account_numbers` list
- Print out the order confirmation
- Contains a cancel order example
- Get OHLC data
- Get an option Dates, Quotes, and Greeks
- Place a dry run option order
- Place a dry run two-leg option spread order
- List watchlists, create one, add a symbol to it then delete it
---

## Implemented Features

- [x] Login (With all 2FA methods now supported!) 
- [x] Get Quotes
- [x] Get OHLC (timestamp, open, high, low, close, volume)
- [x] Get Account Data
- [x] Place Orders and Receive order confirmation
- [x] Get Currently Held Positions
- [x] Fractional Trading support (thanks to @jiak94)
- [x] Check on placed order status. (thanks to @Cfomodz)
- [x] Cancel placed orders
- [x] Options (Orders, Quotes, Greeks)
- [x] Multi-leg option orders: spread, straddle, butterfly, condor, iron condor, iron butterfly (`Order.place_complex_order`, and `Order.place_spread_order` for two legs; limit only, see [Options](#options) for what has and has not been verified)
- [x] Change the price or size of a working order (`Order.modify_stock_order`, `Order.modify_option_order`, `Order.modify_spread_order`)
- [x] Order History
- [x] Manage watchlists

## TO DO

- [ ] Test options fully
- [ ] Give me some Ideas!

## Options

### I am very new to options trading and have not fully tested this feature.

#### Spread orders

`place_spread_order` posts to `private/complex_option_order`.

- Each leg takes a transaction code: `BO`/`SO` to open, `BC`/`SC` to close.
  `OrderType.BUY_TO_CLOSE_OPTION` and `SELL_TO_CLOSE_OPTION` are the close codes.
- `limit_type` is `SpreadLimitType.DEBIT` when the order pays the net price and `CREDIT` when it receives it.
  `net_price` is always positive and is required.
- **Spreads are limit orders only.** The endpoint has no market order: leaving `net_price` out, sending `0`,
  or adding a `price_type` is rejected, and `limit_type` only accepts `D` and `C`.
- They are day orders. The endpoint rejects `duration` and `limit_price`, and answers error 1110 outside
  market hours.
- Firstrade may refuse a spread for an account with too little equity (error 1101). A contract that is not
  on the option chain is refused with error 2044.

#### Other multi-leg strategies

`place_complex_order(account, strategy, legs, limit_type, net_price)` sends the same endpoint up to four legs. The
strategy is a `MultiLegStrategy` whose values are the ones the server accepts (`spread`, `straddle`, `butterfly`,
`condor`, `ironcondor`, `ironbutterfly`; anything else, such as `strangle` or the short codes, is answered with
`Invalid order type.`). Legs are `Leg(symbol, transaction, contracts)`, two to four of them.

The library checks only the number of legs. What a strategy has to look like is the server's to judge, and its
answer comes back untouched with its reference code. What the server said when previews were sent to it:

| Strategy | Legs | Rules the server stated |
| --- | --- | --- |
| spread | 2 | calls or puts |
| straddle | 2 | one call and one put at the same strike and expiration; buy to open or sell to close only |
| butterfly | **3**, not 4 | equal strike steps between the legs; the middle leg twice the size of a wing (1:2:1, 2:4:2); bought or sold |
| condor | 4 | |
| ironcondor | 4 | a put spread and a call spread |
| ironbutterfly | 4 | the two middle legs share a strike |

These were checked as previews only. No multi-leg order other than a spread has been submitted, and no
strategy has been closed, so treat the placing of a straddle, butterfly, condor or iron order as unverified.

#### Skipping the preview

`place_option_order` and `place_spread_order` take `preview` (default `True`). With `preview=False` the real
order is sent directly, without the `preview=true` request in front of it, which saves one round trip. Any
problem the preview would have caught then comes back from the order itself. It cannot be combined with
`dry_run=True`, because a dry run is a preview.

#### Changing a working order

`modify_spread_order(order_id, net_price, contracts)`, `modify_option_order(order_id, price, contracts)` and
`modify_stock_order(order_id, shares, price_type, price)` post to `private/cxlrpl_complexoption_order`,
`private/cxlrpl_option_order` and `private/cxlrpl_stock_order`, the endpoints the Firstrade mobile app calls for an
edit. Firstrade replaces the order: the old one is cancelled and a new one entered in a single request, so the new
order has a new id and the old one is listed as `ORDER-UPDATED`. Take the new id from the order list. `order_id` is
the id shown in the order list (either leg's, for a spread), not the internal `clordid` the website uses. The account
is not sent, and neither are the symbol and the transaction of a stock edit (the server refuses both). `preview` and
`dry_run` work as for placing an order.

`modify_stock_order` supports market and limit orders. A stop or trailing-stop edit needs fields that were not
checked, so it raises `ValueError`. The field names come from the app's code and from the server's own validation
messages (it names the field it wants: `shares`, not `quantity`, then `price_type`, then `duration`).

#### Tests

`tests/test_order.py` runs offline: the session is a stand-in that records each request, and the tests pin the
body each order and edit method sends and the order of the preview and the real request.

```
python -m unittest discover -s tests
```

#### What has been checked against a live account

| | Verified | Not verified |
| --- | --- | --- |
| Single-leg order, `preview=False` | Accepted, listed, and cancelled | |
| Spread request format | Accepted by the validator, which then checked equity (1101) and open positions (1100) | |
| Spread, `preview=False` | Rejected with the same 1101 as with a preview in front of it | That a spread is accepted and placed |
| Spread fills, order-list shape, positions | | Everything: the account used could not afford a spread |
| Spread `BC`/`SC` close codes | Recognised by the validator | Closing an actual position |
| `place_complex_order` | Previews accepted for a straddle, a butterfly (calls and puts, 1:2:1 and 2:4:2, bought and sold), a condor, an iron condor and an iron butterfly | Submitting any of them, closing any of them, and the rules of the condor and the iron strategies |
| `modify_spread_order` | Previewed and submitted on a working spread: price changed, old order `ORDER-UPDATED`, new order working | Partial fills; what happens to a spread already partly filled |
| `modify_option_order` | Previewed and submitted on a working one-contract limit order: price changed, old order `ORDER-UPDATED`, new order working | Partial fills, stop orders |
| `modify_stock_order` | Previewed and submitted on a working one-share limit order: price changed, old order `ORDER-UPDATED`, new order working | Market orders, partial fills, stop orders |

The spread details come from the endpoint's own validator messages and from the write-up in
[PatrickSUDO/firstrade-mcp-server](https://github.com/PatrickSUDO/firstrade-mcp-server)
(`docs/option-order-api.md`), not from Firstrade. If you place a spread that is accepted, an issue with what
the order list and positions look like afterwards would help.

Please:
- USE THIS FEATURE LIKE IT IS A ALPHA/BETA
- PUT IN A GITHUB ISSUE IF YOU FIND ANY PROBLEMS
  
## If you would like to support me, you can do so here:
[![GitHub Sponsors](https://img.shields.io/github/sponsors/maxxrk?style=social)](https://github.com/sponsors/maxxrk)
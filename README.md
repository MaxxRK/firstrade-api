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
- [x] Multi-leg option orders (`Order.place_complex_order`, and `Order.place_spread_order` for two legs): the six strategies the server accepts, which are spread, straddle, butterfly, condor, iron condor and iron butterfly. Limit orders only. Only the spread has been placed and filled on a live account; the other five were checked as previews. Other strategies (calendar and diagonal spreads, ratio spreads, strangles, a roll) are not supported, or not tried: see [Options](#options)
- [x] How many shares of a symbol an account holds (`FTAccountData.get_share`), and end a session (`FTSession.logout`)
- [x] Read one order, find the positions that close together as a strategy, and ask what an order would be before placing it (`FTAccountData.get_order_detail`, `get_close_pairs`, `get_match_close_pairs`, `Order.get_option_order_analysis`, `Order.get_complex_option_order_analysis`)
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

**Strategies this does not cover.** The endpoint takes only the six values above, so a strangle, a calendar
spread and the other combinations that are not one of them cannot be placed through it. The website's order form
also offers a roll (`RF`); no value of `order_type` was found for it, and it has not been tried through this
library. Do not assume that a combination you can build in the Firstrade app or on the website is available here.

#### What an order would be

`get_option_order_analysis(option_symbol, order_type, contracts, price)` and
`get_complex_option_order_analysis(strategy, legs, limit_type, net_price)` ask the server what an order would be
before it is placed, as the mobile app's overview page does. They return the strategy's name (`Long Call
Vertical Spread (Bullish)`, `Long Call Butterfly`), `estimatedTotal`, `breakevenPrice`, `maxProfit`, `maxLoss` and a
`summary` in words. They place nothing, and the server refuses `account`, `preview` and `instructions` on them (and
`duration` on the single-leg one), so none is sent. Mind the types: the numbers are floats (a 29 dollar spread
comes back as `28.999999999999996`), `maxProfit` is the string `"Infinite"` for a long call, and `breakevenPrice` is
`"-"` for a butterfly.

`FTAccountData.get_share(account, symbol)` returns the number of shares of a symbol an account holds, under
`result.shares`. The server answers for any symbol, an option symbol or one that does not exist included, with 0 when
nothing is held.

`FTSession.logout()` ends the session on Firstrade's side with a POST that has no body. Afterwards the session's
`ftat` and `sid` are refused (401). The saved cookie file is left alone, and a new login that uses it still works
without a second factor.

`FTAccountData.get_order_detail(order_id)` returns one order in the shape the order list uses, so a spread is still
one leg per answer. `get_close_pairs` and `get_match_close_pairs` find the positions that can be closed together as
one strategy. They were only asked of an account with no positions, so the shape of a match is not known.
The strategy is a `CloseOutType` (`SP`, `ST`, `BF`, `CD`, `ICD`, `IBF`): the server lists exactly these and refuses
the `MultiLegStrategy` values.

#### Skipping the preview

Every method that places or changes an order takes `preview` and `dry_run`: `place_option_order`,
`place_spread_order`, `place_complex_order`, `modify_option_order`, `modify_spread_order` and
`modify_stock_order`. The defaults are `preview=True` and `dry_run=True`, so a call that changes nothing else
sends one preview request and places or changes nothing.

- `dry_run=False` with the default `preview=True` sends the preview first and then, if it came back clean, the
  real request.
- `dry_run=False` with `preview=False` sends the real request directly, without the `preview=true` request in
  front of it, which saves one round trip. Any problem the preview would have caught then comes back from the
  order itself.
- `preview=False` cannot be combined with `dry_run=True`, because a dry run is a preview: the call raises
  `ValueError` and sends nothing.

Skipping the preview was tried on a live account for single-leg orders, for spreads and for editing a spread. It
was not tried for the other multi-leg strategies, for editing a single-leg or a stock order, or after a
rejected preview (a rejected preview stops the real request when `preview=True`, as the tests check).

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
| Spread, `preview=False` | The same request body, sent without a preview, was accepted and filled on a live account: a call debit spread bought and sold back, a put credit spread sold and bought back (TLT, one-dollar wide). It was sent by a client that built the body itself, before this method existed in the installed version, so the method as such was not the one sending | Partial fills |
| Spread order list and positions | A spread is listed as two rows, one per leg, linked by `other_leg_order_id` and `all_other_leg_ids`, with `mleg` set to `CO`; each row carries its own leg's `avg_exe_price`, so the net fill price is the near leg's less the far leg's. The positions are listed per leg | |
| Spread `BC`/`SC` close codes | Used to close both spreads above: they filled | |
| `place_complex_order` | Previews accepted for a straddle, a butterfly (calls and puts, 1:2:1 and 2:4:2, bought and sold), a condor, an iron condor and an iron butterfly | Submitting any of them (with or without a preview), closing any of them, and the rules of the condor and the iron strategies |
| `get_option_order_analysis`, `get_complex_option_order_analysis` | Answered for a spread, a butterfly and a single call, and the numbers read back | A condor and the iron strategies; the shape of `breakevenPrice` where a strategy has two |
| `get_share` | Answered with 0 for a symbol, an option symbol and one that does not exist | A symbol that is held: no shares were held |
| `logout` | On a session of its own: answered `success`, then the same session's `ftat` and `sid` got 401; the saved cookie file did not change, and a new login worked without a second factor | |
| `get_order_detail` | Answered for a filled order | An order that is still working, a partly filled one |
| `get_close_pairs`, `get_match_close_pairs` | Accepted by the server, with the fields it asked for | Anything but an empty answer: no account position was held |
| `modify_spread_order` | Previewed and submitted on a working spread, and submitted with `preview=False`: price changed, old order `ORDER-UPDATED`, new order working | Partial fills; what happens to a spread already partly filled |
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
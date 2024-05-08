# firstrade-api

A reverse-engineered python API to interact with the Firstrade Trading platform.

This is not an official api! This api's functionality may change at any time.

This api provides a means of buying and selling stocks through Firstrade. It uses the Session class from requests to get authorization cookies. The rest is done with reverse engineered requests to Firstrade's API.

In order to use Fractional shares you must accept the agreement on the website before using it in this API.

---

## Contribution

I am new to coding and new to open-source. I would love any help and suggestions!

## Setup

Install using pypi:

```
pip install firstrade
```

## Quikstart

`Checkout test.py for sample code.`

This code will:
- Login and print account info.
- Get a quote for 'INTC' and print out the information
- Place a market order for 'INTC' on the first account in the `account_numbers` list
- Print out the order confirmation

`Checkout test.py for sample code.`

---

## Implemented Features

- [x] Login
- [x] Get Quotes
- [x] Get Account Data
- [x] Place Orders and Receive order confirmation
- [x] Get Currently Held Positions
- [x] Fractional Trading support (thanks to @jiak94)
- [x] Check on placed order status. (thanks to @Cfomodz)

## TO DO

- [ ] Cancel placed orders
- [ ] Options
- [ ] Give me some Ideas!

## If you would like to support me, you can do so here:
[![GitHub Sponsors](https://img.shields.io/github/sponsors/maxxrk?style=social)](https://github.com/sponsors/maxxrk) 
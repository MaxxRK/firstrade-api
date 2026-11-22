"""What the order methods send.

The session is a stand-in that records each request, so these run offline.  The bodies are the
ones the Firstrade mobile app builds and the server accepted when they were tried against a live
account (see the README); a test here pins one so that a refactor cannot change it unseen.

    python -m unittest discover -s tests
"""

from __future__ import annotations

import unittest

from firstrade import account, order, urls


class _Response:
    status_code = 200

    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class _Session:
    """Records every request and answers each with a clean reply."""

    def __init__(self, reply: dict | None = None) -> None:
        self.requests: list[tuple[str, str, dict]] = []
        self.reply = reply if reply is not None else {"error": "", "result": {}}

    def _request(self, method: str, url: str, **kwargs: object) -> _Response:
        self.requests.append((method, url, dict(kwargs.get("data") or {})))  # type: ignore[call-overload]
        return _Response(self.reply)

    def sent(self) -> list[tuple[str, str]]:
        """(endpoint name, preview flag) of every request, in order."""
        return [(url.rsplit("/", 1)[-1], str(data.get("preview"))) for _, url, data in self.requests]


def _client(reply: dict | None = None) -> tuple[order.Order, _Session]:
    session = _Session(reply)
    return order.Order(session), session  # type: ignore[arg-type]


def _accounts(reply: dict | None = None) -> tuple[account.FTAccountData, _Session]:
    """FTAccountData without logging in: only its session is used by the methods under test."""
    session = _Session(reply)
    data = account.FTAccountData.__new__(account.FTAccountData)
    data.session = session  # type: ignore[assignment]
    return data, session


class SpreadOrderTests(unittest.TestCase):
    def _place(self, **kwargs: object) -> _Session:
        client, session = _client()
        client.place_spread_order(
            account="81234567",
            leg1_symbol="TLT261127C00081000",
            leg1_transaction=order.OrderType.BUY_OPTION,
            leg2_symbol="TLT261127C00082000",
            leg2_transaction=order.OrderType.SELL_OPTION,
            limit_type=order.SpreadLimitType.DEBIT,
            net_price=0.29,
            contracts=1,
            **kwargs,  # type: ignore[arg-type]
        )
        return session

    def test_body_is_the_one_the_server_accepted(self) -> None:
        session = self._place(dry_run=False, preview=False)
        [(method, url, body)] = session.requests
        self.assertEqual((method, url), ("post", urls.complex_option_order()))
        self.assertEqual(
            body,
            {
                "order_type": "spread",
                "transaction1": "BO",
                "symbol1": "TLT261127C00081000",
                "contracts1": 1,
                "transaction2": "SO",
                "symbol2": "TLT261127C00082000",
                "contracts2": 1,
                "limit_type": "D",
                "net_price": 0.29,
                "instructions": "0",
                "preview": "false",
                "account": "81234567",
            },
        )

    def test_a_credit_spread_says_so(self) -> None:
        client, session = _client()
        client.place_spread_order(
            "81234567",
            "TLT261127P00080000",
            order.OrderType.SELL_OPTION,
            "TLT261127P00079000",
            order.OrderType.BUY_OPTION,
            order.SpreadLimitType.CREDIT,
            0.12,
            dry_run=False,
            preview=False,
        )
        self.assertEqual(session.requests[0][2]["limit_type"], "C")

    def test_closing_uses_the_close_codes(self) -> None:
        self.assertEqual(order.OrderType.BUY_TO_CLOSE_OPTION.value, "BC")
        self.assertEqual(order.OrderType.SELL_TO_CLOSE_OPTION.value, "SC")

    def test_default_is_a_preview_only(self) -> None:
        self.assertEqual(self._place().sent(), [("complex_option_order", "true")])

    def test_a_clean_preview_is_followed_by_the_order(self) -> None:
        session = self._place(dry_run=False)
        self.assertEqual(
            session.sent(), [("complex_option_order", "true"), ("complex_option_order", "false")]
        )

    def test_a_rejected_preview_stops_there(self) -> None:
        client, session = _client({"error": "Bad Request", "message": "no"})
        client.place_spread_order(
            "81234567",
            "A",
            order.OrderType.BUY_OPTION,
            "B",
            order.OrderType.SELL_OPTION,
            order.SpreadLimitType.DEBIT,
            0.1,
            dry_run=False,
        )
        self.assertEqual(session.sent(), [("complex_option_order", "true")])

    def test_a_dry_run_cannot_skip_its_preview(self) -> None:
        with self.assertRaises(ValueError):
            self._place(dry_run=True, preview=False)


class MultiLegOrderTests(unittest.TestCase):
    """place_complex_order: up to four legs, and the strategy as the server spells it."""

    def _legs(self, *specs: tuple) -> list[order.Leg]:
        return [order.Leg(f"TLT261127{right}{int(strike * 1000):08d}", tx, *rest) for tx, right, strike, *rest in specs]

    def _place(self, strategy: order.MultiLegStrategy, legs: list[order.Leg], **kwargs: object) -> _Session:
        client, session = _client()
        client.place_complex_order(
            "81234567",
            strategy,
            legs,
            order.SpreadLimitType.DEBIT,
            0.50,
            dry_run=False,
            preview=False,
            **kwargs,  # type: ignore[arg-type]
        )
        return session

    def test_the_strategy_values_are_the_ones_the_server_accepted(self) -> None:
        self.assertEqual(
            [member.value for member in order.MultiLegStrategy],
            ["spread", "straddle", "butterfly", "condor", "ironcondor", "ironbutterfly"],
        )

    def test_a_butterfly_is_three_legs_with_the_middle_one_doubled(self) -> None:
        legs = self._legs(("BO", "C", 81), ("SO", "C", 82, 2), ("BO", "C", 83))
        [(_, url, body)] = self._place(order.MultiLegStrategy.BUTTERFLY, legs).requests
        self.assertEqual(url, urls.complex_option_order())
        self.assertEqual(body["order_type"], "butterfly")
        self.assertEqual(
            [(body[f"transaction{i}"], body[f"contracts{i}"]) for i in (1, 2, 3)],
            [("BO", 1), ("SO", 2), ("BO", 1)],
        )
        self.assertNotIn("symbol4", body)
        self.assertNotIn("transaction4", body)

    def test_a_four_leg_strategy_sends_all_four(self) -> None:
        legs = self._legs(("BO", "P", 79), ("SO", "P", 80), ("SO", "C", 83), ("BO", "C", 84))
        [(_, _, body)] = self._place(order.MultiLegStrategy.IRON_CONDOR, legs).requests
        self.assertEqual(body["order_type"], "ironcondor")
        for index in (1, 2, 3, 4):
            self.assertIn(f"symbol{index}", body)
            self.assertIn(f"contracts{index}", body)
        self.assertEqual(body["limit_type"], "D")
        self.assertEqual(body["net_price"], 0.5)

    def test_a_straddle_is_a_call_and_a_put(self) -> None:
        legs = self._legs(("BO", "C", 82), ("BO", "P", 82))
        [(_, _, body)] = self._place(order.MultiLegStrategy.STRADDLE, legs).requests
        self.assertEqual(body["order_type"], "straddle")
        self.assertTrue(body["symbol1"].endswith("C00082000"))
        self.assertTrue(body["symbol2"].endswith("P00082000"))

    def test_the_server_judges_the_strategy_and_its_answer_comes_back_untouched(self) -> None:
        reply = {"error": "Bad Request", "message": "Invalid number of contracts. Reference code: 2163"}
        client, session = _client(reply)
        legs = self._legs(("BO", "C", 81), ("SO", "C", 82), ("BO", "C", 83))
        result = client.place_complex_order(
            "81234567", order.MultiLegStrategy.BUTTERFLY, legs, order.SpreadLimitType.DEBIT, 0.5, dry_run=False
        )
        self.assertEqual(result, reply)
        self.assertEqual(session.sent(), [("complex_option_order", "true")])  # stopped at the preview

    def test_legs_outside_two_to_four_are_refused_before_anything_is_sent(self) -> None:
        client, session = _client()
        one = self._legs(("BO", "C", 81))
        five = self._legs(*[("BO", "C", 80 + i) for i in range(5)])
        for legs in (one, five, []):
            with self.assertRaises(ValueError):
                client.place_complex_order(
                    "81234567", order.MultiLegStrategy.SPREAD, legs, order.SpreadLimitType.DEBIT, 0.5
                )
        self.assertEqual(session.requests, [])

    def test_a_spread_is_the_two_leg_case_and_sends_what_it_always_did(self) -> None:
        client, via_spread = _client()
        client.place_spread_order(
            "81234567", "A", order.OrderType.BUY_OPTION, "B", order.OrderType.SELL_OPTION,
            order.SpreadLimitType.DEBIT, 0.29, 3, dry_run=False, preview=False,
        )
        client2, via_complex = _client()
        client2.place_complex_order(
            "81234567", order.MultiLegStrategy.SPREAD,
            [order.Leg("A", order.OrderType.BUY_OPTION, 3), order.Leg("B", order.OrderType.SELL_OPTION, 3)],
            order.SpreadLimitType.DEBIT, 0.29, dry_run=False, preview=False,
        )
        self.assertEqual(via_spread.requests, via_complex.requests)

    def test_a_dry_run_cannot_skip_its_preview(self) -> None:
        client, _ = _client()
        legs = self._legs(("BO", "C", 82), ("BO", "P", 82))
        with self.assertRaises(ValueError):
            client.place_complex_order(
                "81234567", order.MultiLegStrategy.STRADDLE, legs, order.SpreadLimitType.DEBIT, 0.5, preview=False
            )


class AnalysisTests(unittest.TestCase):
    """What an order would be before it is placed.  The server refuses account, preview, duration and
    instructions on these two endpoints, so none of them is sent."""

    def test_a_spread_analysis_sends_the_legs_and_no_bookkeeping(self) -> None:
        client, session = _client()
        legs = [
            order.Leg("TLT261127C00081000", order.OrderType.BUY_OPTION),
            order.Leg("TLT261127C00082000", order.OrderType.SELL_OPTION),
        ]
        client.get_complex_option_order_analysis(
            order.MultiLegStrategy.SPREAD, legs, order.SpreadLimitType.DEBIT, 0.29
        )
        [(method, url, body)] = session.requests
        self.assertEqual((method, url), ("post", urls.complex_option_order_analysis()))
        self.assertEqual(
            body,
            {
                "order_type": "spread",
                "transaction1": "BO",
                "symbol1": "TLT261127C00081000",
                "contracts1": 1,
                "transaction2": "SO",
                "symbol2": "TLT261127C00082000",
                "contracts2": 1,
                "limit_type": "D",
                "net_price": 0.29,
            },
        )
        for refused in ("account", "preview", "instructions"):
            self.assertNotIn(refused, body)

    def test_a_butterfly_analysis_carries_its_doubled_middle(self) -> None:
        client, session = _client()
        legs = [
            order.Leg("TLT261127C00081000", order.OrderType.BUY_OPTION),
            order.Leg("TLT261127C00082000", order.OrderType.SELL_OPTION, 2),
            order.Leg("TLT261127C00083000", order.OrderType.BUY_OPTION),
        ]
        client.get_complex_option_order_analysis(
            order.MultiLegStrategy.BUTTERFLY, legs, order.SpreadLimitType.DEBIT, 0.05
        )
        body = session.requests[0][2]
        self.assertEqual((body["order_type"], body["contracts2"]), ("butterfly", 2))

    def test_the_analysis_refuses_a_bad_number_of_legs_before_sending(self) -> None:
        client, session = _client()
        with self.assertRaises(ValueError):
            client.get_complex_option_order_analysis(
                order.MultiLegStrategy.SPREAD,
                [order.Leg("A", order.OrderType.BUY_OPTION)],
                order.SpreadLimitType.DEBIT,
                0.1,
            )
        self.assertEqual(session.requests, [])

    def test_a_single_leg_analysis_sends_no_account_or_duration(self) -> None:
        client, session = _client()
        client.get_option_order_analysis("TLT261127C00081000", order.OrderType.BUY_OPTION, 1, 0.41)
        [(method, url, body)] = session.requests
        self.assertEqual((method, url), ("post", urls.option_order_analysis()))
        self.assertEqual(
            body,
            {
                "transaction": "BO",
                "symbol": "TLT261127C00081000",
                "contracts": 1,
                "price_type": "2",
                "limit_price": 0.41,
            },
        )
        for refused in ("account", "preview", "duration", "instructions"):
            self.assertNotIn(refused, body)

    def test_the_answer_is_returned_as_it_came(self) -> None:
        reply = {"error": "", "strategy": "Long Call (Bullish)", "maxProfit": "Infinite", "maxLoss": 41}
        client, _ = _client(reply)
        self.assertEqual(client.get_option_order_analysis("A", order.OrderType.BUY_OPTION, 1, 1.0), reply)


class OrderReadTests(unittest.TestCase):
    """Reading one order, and the positions that close together."""

    def test_order_detail_is_a_get_with_only_the_order_id(self) -> None:
        data, session = _accounts()
        data.get_order_detail("Y1-1")
        [(method, url, body)] = session.requests
        self.assertEqual((method, url), ("get", urls.order_detail("Y1-1")))
        self.assertTrue(url.endswith("/private/order_detail?order_id=Y1-1"))
        self.assertNotIn("account", url)  # the server refuses it
        self.assertEqual(body, {})

    def test_close_pairs_needs_a_strategy_and_a_symbol(self) -> None:
        data, session = _accounts()
        data.get_close_pairs("81234567", order.CloseOutType.SPREAD, option_symbol="TLT261127C00081000")
        [(method, url, body)] = session.requests
        self.assertEqual((method, url), ("post", urls.close_pairs()))
        self.assertEqual(
            body, {"account": "81234567", "co_type": "SP", "option_symbol": "TLT261127C00081000"}
        )

    def test_close_pairs_can_look_by_underlying(self) -> None:
        data, session = _accounts()
        data.get_close_pairs("81234567", order.CloseOutType.STRADDLE, underlying_symbol="TLT")
        body = session.requests[0][2]
        self.assertEqual(body, {"account": "81234567", "co_type": "ST", "underlying_symbol": "TLT"})

    def test_close_pairs_without_any_symbol_is_refused_before_sending(self) -> None:
        data, session = _accounts()
        with self.assertRaises(ValueError):
            data.get_close_pairs("81234567", order.CloseOutType.SPREAD)
        self.assertEqual(session.requests, [])

    def test_the_close_out_codes_are_the_ones_the_server_lists(self) -> None:
        # '"co_type" must be one of [SP, ST, BF, ICD, CD, IBF]', and not the multi-leg values
        self.assertEqual(
            sorted(member.value for member in order.CloseOutType),
            sorted(["SP", "ST", "BF", "ICD", "CD", "IBF"]),
        )
        self.assertFalse({m.value for m in order.CloseOutType} & {m.value for m in order.MultiLegStrategy})

    def test_buy_to_close_and_buy_to_cover_send_the_same_code(self) -> None:
        self.assertEqual(order.OrderType.BUY_TO_CLOSE_OPTION.value, "BC")
        self.assertIs(order.OrderType.BUY_TO_CLOSE_OPTION, order.OrderType.BUY_TO_COVER)

    def test_share_is_a_get_with_the_symbol_and_the_account(self) -> None:
        data, session = _accounts()
        data.get_share("81234567", "TLT")
        [(method, url, body)] = session.requests
        self.assertEqual(method, "get")
        self.assertEqual(url, urls.share("81234567", "TLT"))
        self.assertTrue(url.endswith("/private/get_share?symbol=TLT&account=81234567"))
        self.assertEqual(body, {})

    def test_logout_is_a_post_with_no_body(self) -> None:
        session = _Session({"error": "", "result": "success"})
        ft = account.FTSession.__new__(account.FTSession)
        ft._request = session._request  # type: ignore[method-assign]
        self.assertEqual(ft.logout(), {"error": "", "result": "success"})
        self.assertEqual(session.requests, [("post", urls.logout(), {})])
        self.assertTrue(urls.logout().endswith("/sess/logout"))

    def test_match_close_pairs_sends_only_the_account(self) -> None:
        data, session = _accounts()
        data.get_match_close_pairs("81234567")
        [(method, url, body)] = session.requests
        self.assertEqual((method, url), ("post", urls.match_close_pairs()))
        self.assertEqual(body, {"account": "81234567"})


class SingleLegOrderTests(unittest.TestCase):
    def _place(self, **kwargs: object) -> _Session:
        client, session = _client()
        client.place_option_order(
            account="81234567",
            option_symbol="TLT261127C00083000",
            price_type=order.PriceType.LIMIT,
            order_type=order.OrderType.BUY_OPTION,
            contracts=1,
            duration=order.Duration.DAY,
            price=0.01,
            **kwargs,  # type: ignore[arg-type]
        )
        return session

    def test_without_a_preview_only_the_order_is_sent(self) -> None:
        session = self._place(dry_run=False, preview=False)
        self.assertEqual(session.sent(), [("option_order", "false")])

    def test_default_still_previews_first(self) -> None:
        self.assertEqual(
            self._place(dry_run=False).sent(), [("option_order", "true"), ("option_order", "false")]
        )

    def test_a_dry_run_cannot_skip_its_preview(self) -> None:
        with self.assertRaises(ValueError):
            self._place(dry_run=True, preview=False)


class EditTests(unittest.TestCase):
    """The three cancel/replace endpoints of the mobile app: stock, single-leg option, spread."""

    def test_the_endpoints(self) -> None:
        self.assertTrue(urls.order_edit().endswith("/private/cxlrpl_stock_order"))
        self.assertTrue(urls.option_order_edit().endswith("/private/cxlrpl_option_order"))
        self.assertTrue(urls.complex_option_order_edit().endswith("/private/cxlrpl_complexoption_order"))

    def test_spread_edit_body(self) -> None:
        client, session = _client()
        client.modify_spread_order("Y1-1", 0.02, 1, dry_run=False, preview=False)
        [(_, url, body)] = session.requests
        self.assertEqual(url, urls.complex_option_order_edit())
        # no account, symbol or transaction; no price_type or duration for a spread
        self.assertEqual(
            body,
            {
                "order_id": "Y1-1",
                "contracts": 1,
                "limit_price": 0.02,
                "instructions": "0",
                "preview": "false",
            },
        )

    def test_option_edit_body(self) -> None:
        client, session = _client()
        client.modify_option_order("Y1-1", 0.02, 1, dry_run=False, preview=False)
        [(_, url, body)] = session.requests
        self.assertEqual(url, urls.option_order_edit())
        self.assertEqual(
            body,
            {
                "order_id": "Y1-1",
                "contracts": 1,
                "price_type": "2",
                "limit_price": 0.02,
                "duration": "0",
                "instructions": "0",
                "preview": "false",
            },
        )

    def test_stock_edit_body_is_in_shares_and_has_no_symbol_or_transaction(self) -> None:
        client, session = _client()
        client.modify_stock_order("Y1-1", 3, price=9.5, dry_run=False, preview=False)
        [(_, url, body)] = session.requests
        self.assertEqual(url, urls.order_edit())
        self.assertEqual(
            body,
            {
                "order_id": "Y1-1",
                "shares": 3,
                "price_type": "2",
                "limit_price": 9.5,
                "duration": "0",
                "instructions": "0",
                "preview": "false",
            },
        )
        self.assertNotIn("symbol", body)
        self.assertNotIn("transaction", body)
        self.assertNotIn("contracts", body)  # the server wants shares

    def test_a_market_edit_has_no_price(self) -> None:
        client, session = _client()
        client.modify_stock_order(
            "Y1-1", 3, order.PriceType.MARKET, dry_run=False, preview=False
        )
        body = session.requests[0][2]
        self.assertEqual(body["price_type"], "1")
        self.assertNotIn("limit_price", body)

    def test_stock_edit_refuses_what_it_has_not_checked(self) -> None:
        client, session = _client()
        for price_type in (
            order.PriceType.STOP,
            order.PriceType.STOP_LIMIT,
            order.PriceType.TRAILING_STOP_DOLLAR,
            order.PriceType.TRAILING_STOP_PERCENT,
        ):
            with self.assertRaises(ValueError):
                client.modify_stock_order("Y1-1", 3, price_type, price=1.0)
        with self.assertRaises(ValueError):
            client.modify_stock_order("Y1-1", 3)  # a limit order needs a price
        self.assertEqual(session.requests, [])  # nothing was sent for any of them

    def test_edits_preview_first_by_default_and_only_previewing_is_the_default(self) -> None:
        for call in (
            lambda c: c.modify_spread_order("Y1-1", 0.02, 1),
            lambda c: c.modify_option_order("Y1-1", 0.02, 1),
            lambda c: c.modify_stock_order("Y1-1", 3, price=9.5),
        ):
            client, session = _client()
            call(client)
            self.assertEqual([flag for _, flag in session.sent()], ["true"])

    def test_a_confirmed_edit_previews_then_changes(self) -> None:
        client, session = _client()
        client.modify_stock_order("Y1-1", 3, price=9.5, dry_run=False)
        self.assertEqual([flag for _, flag in session.sent()], ["true", "false"])

    def test_a_rejected_preview_stops_before_the_change(self) -> None:
        client, session = _client({"error": "Bad Request", "message": "no"})
        client.modify_spread_order("Y1-1", 0.02, 1, dry_run=False)
        self.assertEqual([flag for _, flag in session.sent()], ["true"])

    def test_a_dry_run_cannot_skip_its_preview(self) -> None:
        client, _ = _client()
        for call in (
            lambda: client.modify_spread_order("Y1-1", 0.02, 1, preview=False),
            lambda: client.modify_option_order("Y1-1", 0.02, 1, preview=False),
            lambda: client.modify_stock_order("Y1-1", 3, price=9.5, preview=False),
        ):
            with self.assertRaises(ValueError):
                call()


if __name__ == "__main__":
    unittest.main()

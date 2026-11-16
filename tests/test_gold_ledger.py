import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from datetime import date

from server.commerce import (
    DuplicateProviderTransaction,
    GOLD_PACKAGES,
    GoldLedger,
    InvalidPayment,
    PaymentsNotConfigured,
)
import game


class GoldLedgerTests(unittest.TestCase):
    def test_legacy_client_form_cannot_grant_premium_currency(self):
        game_obj = game.Game.__new__(game.Game)
        game_obj._pf_fields = {'Nombre': 'test'}
        game_obj._pf_active = 'Nombre'
        game_obj._pf_pending_cost = 5
        game_obj.caught_count = 10
        game_obj.state = game.GameState.PURCHASE_FORM
        game_obj._add_message = lambda message: None

        game_obj._pf_submit()

        self.assertEqual(game_obj.caught_count, 10)
        self.assertFalse(hasattr(game_obj, 'gems'))
        self.assertEqual(game_obj.state, game.GameState.ITEM_STORE)

    def test_gold_catalog_uses_requested_prices_and_christmas_discount(self):
        with TemporaryDirectory() as temp_dir:
            ledger = GoldLedger(Path(temp_dir) / 'commerce.sqlite3')

            regular = {item['sku']: item for item in ledger.catalog(date(2026, 11, 13))}
            christmas = {item['sku']: item for item in ledger.catalog(date(2026, 12, 25))}
            self.assertEqual(regular['gold_starter']['gold'], 100)
            self.assertEqual(regular['gold_starter']['price_minor'], 200)
            self.assertEqual(regular['gold_value']['gold'], 1_000_000)
            self.assertEqual(regular['gold_value']['price_minor'], 1000)
            self.assertEqual(regular['gold_mega']['gold'], 10_000_000)
            self.assertEqual(regular['gold_mega']['price_minor'], 1500)
            self.assertEqual(christmas['gold_starter']['price_minor'], 100)
            self.assertEqual(christmas['gold_value']['price_minor'], 500)
            self.assertEqual(christmas['gold_mega']['price_minor'], 750)
            self.assertTrue(christmas['gold_mega']['discount_active'])
            self.assertEqual(regular['gold_mega']['currency'], 'USD')
            for day in (24, 25, 26):
                promo = {item['sku']: item for item in ledger.catalog(date(2026, 12, day))}
                self.assertEqual(promo['gold_mega']['price_minor'], 750)
            for day in (23, 27):
                outside = {item['sku']: item for item in ledger.catalog(date(2026, 12, day))}
                self.assertEqual(outside['gold_mega']['price_minor'], 1500)

    def test_checkout_is_disabled_by_default(self):
        with TemporaryDirectory() as temp_dir:
            ledger = GoldLedger(Path(temp_dir) / 'commerce.sqlite3')

            with self.assertRaises(PaymentsNotConfigured):
                ledger.create_order('account-1', 'gold_starter', date(2026, 11, 13))

    def test_verified_payment_credits_gold_once(self):
        with TemporaryDirectory() as temp_dir:
            ledger = GoldLedger(
                Path(temp_dir) / 'commerce.sqlite3',
                checkout_enabled=True,
            )
            order_id = ledger.create_order('account-1', 'gold_starter', date(2026, 11, 13))

            balance = ledger.fulfill_verified_payment(
                order_id, 'provider-tx-1', 200, 'usd')
            replayed_balance = ledger.fulfill_verified_payment(
                order_id, 'provider-tx-1', 200, 'USD')

            self.assertEqual(balance, GOLD_PACKAGES['gold_starter'])
            self.assertEqual(replayed_balance, balance)
            self.assertEqual(ledger.get_balance('account-1'), balance)
            reopened = GoldLedger(Path(temp_dir) / 'commerce.sqlite3')
            self.assertEqual(reopened.get_balance('account-1'), balance)

    def test_mismatched_amount_does_not_credit_gold(self):
        with TemporaryDirectory() as temp_dir:
            ledger = GoldLedger(
                Path(temp_dir) / 'commerce.sqlite3',
                checkout_enabled=True,
            )
            order_id = ledger.create_order('account-1', 'gold_starter', date(2026, 11, 13))

            with self.assertRaises(InvalidPayment):
                ledger.fulfill_verified_payment(
                    order_id, 'provider-tx-2', 1, 'USD')

            self.assertEqual(ledger.get_balance('account-1'), 0)

    def test_christmas_order_requires_the_discounted_server_amount(self):
        with TemporaryDirectory() as temp_dir:
            ledger = GoldLedger(
                Path(temp_dir) / 'commerce.sqlite3',
                checkout_enabled=True,
            )
            order_id = ledger.create_order(
                'account-1', 'gold_mega', date(2026, 12, 25))

            with self.assertRaises(InvalidPayment):
                ledger.fulfill_verified_payment(order_id, 'tx-full-price', 1500, 'USD')
            balance = ledger.fulfill_verified_payment(
                order_id, 'tx-holiday-price', 750, 'USD')

            self.assertEqual(balance, GOLD_PACKAGES['gold_mega'])

    def test_provider_transaction_cannot_fund_two_orders(self):
        with TemporaryDirectory() as temp_dir:
            ledger = GoldLedger(
                Path(temp_dir) / 'commerce.sqlite3',
                checkout_enabled=True,
            )
            first_order = ledger.create_order('account-1', 'gold_starter', date(2026, 11, 13))
            second_order = ledger.create_order('account-2', 'gold_starter', date(2026, 11, 13))
            ledger.fulfill_verified_payment(first_order, 'provider-tx-3', 200, 'USD')

            with self.assertRaises(DuplicateProviderTransaction):
                ledger.fulfill_verified_payment(second_order, 'provider-tx-3', 200, 'USD')

            self.assertEqual(ledger.get_balance('account-1'), GOLD_PACKAGES['gold_starter'])
            self.assertEqual(ledger.get_balance('account-2'), 0)


if __name__ == '__main__':
    unittest.main()
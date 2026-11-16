"""Provider-neutral server-side gold wallet and purchase ledger.

Payment adapters must verify provider signatures and paid status before calling
``fulfill_verified_payment``. Never expose that method directly to the game client.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Mapping
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4


GOLD_PACKAGES = {
    'gold_starter': 100,
    'gold_value': 1_000_000,
    'gold_mega': 10_000_000,
}
GOLD_PACKAGE_PRICES_MINOR = {
    'gold_starter': 200,
    'gold_value': 1000,
    'gold_mega': 1500,
}
GOLD_CURRENCY = 'USD'
CHRISTMAS_DISCOUNT_DAYS = range(24, 27)


class CommerceError(Exception):
    """Base class for invalid commerce operations."""


class PaymentsNotConfigured(CommerceError):
    """Raised until trusted server-side prices have been configured."""


class InvalidPayment(CommerceError):
    """Raised when a verified provider payment does not match its order."""


class DuplicateProviderTransaction(CommerceError):
    """Raised when one provider transaction is presented for different orders."""


class GoldLedger:
    """SQLite ledger; only verified server payment events may grant gold."""

    def __init__(
        self,
        database_path: str | os.PathLike[str],
        *,
        checkout_enabled: bool = False,
    ) -> None:
        self.database_path = Path(database_path)
        self.checkout_enabled = checkout_enabled
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @staticmethod
    def _discount_active(on_date: date) -> bool:
        return on_date.month == 12 and on_date.day in CHRISTMAS_DISCOUNT_DAYS

    def catalog(self, on_date: date | None = None) -> list[dict[str, int | str | bool]]:
        if on_date is None:
            on_date = datetime.now(timezone.utc).date()
        discount_active = self._discount_active(on_date)
        return [
            {
                'sku': sku,
                'gold': amount,
                'regular_price_minor': GOLD_PACKAGE_PRICES_MINOR[sku],
                'price_minor': (GOLD_PACKAGE_PRICES_MINOR[sku] // 2
                                if discount_active else GOLD_PACKAGE_PRICES_MINOR[sku]),
                'currency': GOLD_CURRENCY,
                'discount_active': discount_active,
                'purchase_enabled': self.checkout_enabled,
            }
            for sku, amount in GOLD_PACKAGES.items()
        ]

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database_path, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys = ON')
        try:
            yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                '''
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id TEXT PRIMARY KEY,
                    gold_balance INTEGER NOT NULL DEFAULT 0 CHECK (gold_balance >= 0)
                );
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    order_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL REFERENCES accounts(account_id),
                    package_sku TEXT NOT NULL,
                    gold_amount INTEGER NOT NULL CHECK (gold_amount > 0),
                    expected_amount_minor INTEGER NOT NULL CHECK (expected_amount_minor > 0),
                    currency TEXT NOT NULL CHECK (length(currency) = 3),
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'paid')),
                    provider_transaction_id TEXT UNIQUE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS gold_ledger (
                    entry_id INTEGER PRIMARY KEY,
                    account_id TEXT NOT NULL REFERENCES accounts(account_id),
                    order_id TEXT NOT NULL UNIQUE REFERENCES purchase_orders(order_id),
                    provider_transaction_id TEXT NOT NULL UNIQUE,
                    gold_delta INTEGER NOT NULL CHECK (gold_delta > 0),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                '''
            )

    def create_order(self, account_id: str, package_sku: str,
                     on_date: date | None = None) -> str:
        """Create a pending order using the server catalog, never a client price."""
        if not account_id or len(account_id) > 160:
            raise ValueError('A valid authenticated account ID is required.')
        if package_sku not in GOLD_PACKAGES:
            raise ValueError('Unknown gold package.')
        if not self.checkout_enabled:
            raise PaymentsNotConfigured('Checkout is disabled until a payment provider is integrated.')

        if on_date is None:
            on_date = datetime.now(timezone.utc).date()
        price_minor = GOLD_PACKAGE_PRICES_MINOR[package_sku]
        if self._discount_active(on_date):
            price_minor //= 2
        currency = GOLD_CURRENCY

        order_id = uuid4().hex
        with self._connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            connection.execute(
                'INSERT OR IGNORE INTO accounts (account_id) VALUES (?)', (account_id,))
            connection.execute(
                '''INSERT INTO purchase_orders
                   (order_id, account_id, package_sku, gold_amount,
                    expected_amount_minor, currency)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (order_id, account_id, package_sku, GOLD_PACKAGES[package_sku],
                 price_minor, currency),
            )
            connection.commit()
        return order_id

    def fulfill_verified_payment(
        self,
        order_id: str,
        provider_transaction_id: str,
        paid_amount_minor: int,
        currency: str,
    ) -> int:
        """Credit an order after a trusted adapter verifies the provider event.

        Returns the resulting balance. Replaying the same transaction for the
        same order is idempotent; reusing it for another order is rejected.
        """
        if not provider_transaction_id:
            raise InvalidPayment('A provider transaction ID is required.')

        with self._connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            existing = connection.execute(
                '''SELECT order_id, account_id FROM gold_ledger
                   WHERE provider_transaction_id = ?''',
                (provider_transaction_id,),
            ).fetchone()
            if existing is not None:
                if existing['order_id'] != order_id:
                    connection.rollback()
                    raise DuplicateProviderTransaction(
                        'Provider transaction was already applied to another order.')
                balance = connection.execute(
                    'SELECT gold_balance FROM accounts WHERE account_id = ?',
                    (existing['account_id'],),
                ).fetchone()['gold_balance']
                connection.commit()
                return balance

            order = connection.execute(
                'SELECT * FROM purchase_orders WHERE order_id = ?', (order_id,)
            ).fetchone()
            if order is None:
                connection.rollback()
                raise InvalidPayment('Unknown purchase order.')
            if order['status'] != 'pending':
                connection.rollback()
                raise InvalidPayment('Purchase order is not pending.')
            if (paid_amount_minor != order['expected_amount_minor'] or
                    currency.upper() != order['currency']):
                connection.rollback()
                raise InvalidPayment('Paid amount or currency does not match the order.')

            connection.execute(
                '''INSERT INTO gold_ledger
                   (account_id, order_id, provider_transaction_id, gold_delta)
                   VALUES (?, ?, ?, ?)''',
                (order['account_id'], order_id, provider_transaction_id,
                 order['gold_amount']),
            )
            connection.execute(
                'UPDATE accounts SET gold_balance = gold_balance + ? WHERE account_id = ?',
                (order['gold_amount'], order['account_id']),
            )
            connection.execute(
                '''UPDATE purchase_orders
                   SET status = 'paid', provider_transaction_id = ? WHERE order_id = ?''',
                (provider_transaction_id, order_id),
            )
            balance = connection.execute(
                'SELECT gold_balance FROM accounts WHERE account_id = ?',
                (order['account_id'],),
            ).fetchone()['gold_balance']
            connection.commit()
            return balance

    def get_balance(self, account_id: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                'SELECT gold_balance FROM accounts WHERE account_id = ?', (account_id,)
            ).fetchone()
        return 0 if row is None else int(row['gold_balance'])
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import shutil
import tempfile
import unittest

from payment_verifier import PaymentVerifier
from storage import StorageManager


class TestPaymentVerifier(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.receipts_file = os.path.join(self.test_dir, "receipts.json")
        self.db_path = os.path.join(self.test_dir, "test.db")
        self.state_json = os.path.join(self.test_dir, "state.json")
        self.storage = StorageManager(db_path=self.db_path, state_json_path=self.state_json)
        self.verifier = PaymentVerifier(receipts_file=self.receipts_file, binance_uid="254779310")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_status_reporting(self):
        status = self.verifier.get_verification_status()
        self.assertIn("binance_pay_uid", status)
        self.assertEqual(status["binance_pay_uid"]["target_uid"], "254779310")
        self.assertIn("receipts_registry", status)

    def test_register_valid_receipt(self):
        receipt = {
            "tx_hash": "BINANCE-PAY-TX-998877",
            "amount": 12.0,
            "currency": "USDT",
            "deliverable_id": 1
        }
        res = self.verifier.register_receipt(receipt)
        self.assertTrue(res)

        # Check payment detection
        check = self.verifier.check_for_payments()
        self.assertIsNotNone(check)
        self.assertTrue(check["confirmed"])
        self.assertEqual(check["amount"], 12.0)
        self.assertEqual(check["currency"], "USDT")
        self.assertEqual(check["tx_reference"], "BINANCE-PAY-TX-998877")

    def test_reject_zero_or_simulated_receipt(self):
        # Zero amount rejected
        res_zero = self.verifier.register_receipt({"tx_hash": "TX1", "amount": 0.0})
        self.assertFalse(res_zero)

        # Simulated rejected
        res_sim = self.verifier.register_receipt({"tx_hash": "TX2", "amount": 5.0, "is_simulated": True})
        self.assertFalse(res_sim)

    def test_storage_integration_with_revenue(self):
        self.assertFalse(self.storage.is_first_revenue_confirmed())
        payment_data = {
            "source": "binance_pay",
            "amount": 0.50,  # Below 1 USD is fully valid
            "currency": "USDT",
            "tx_reference": "TX-P2P-50CENTS"
        }
        rev_id = self.storage.record_confirmed_revenue(payment_data)
        self.assertGreater(rev_id, 0)
        self.assertTrue(self.storage.is_first_revenue_confirmed())

        stats = self.storage.get_summary_stats()
        self.assertEqual(stats["total_confirmed_revenue_usd"], 0.50)


if __name__ == "__main__":
    unittest.main()

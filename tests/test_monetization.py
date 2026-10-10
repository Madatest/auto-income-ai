#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest

from monetization import MonetizationAdvisor


class TestMonetizationAdvisor(unittest.TestCase):
    def test_evaluate_opportunity_monetization(self):
        info = MonetizationAdvisor.evaluate_opportunity_monetization("digital_product", custom_price=20.0)
        self.assertEqual(info["price_usd"], 20.0)
        self.assertGreater(info["net_revenue_usd"], 0)
        self.assertIn("Madagascar", info["local_cashout"])
        self.assertGreater(info["madagascar_readiness_score"], 10.0)

    def test_channel_coverage_and_fees(self):
        for ch_key, channel in MonetizationAdvisor.CHANNELS.items():
            self.assertTrue(channel["supports_madagascar"])
            self.assertGreaterEqual(channel["fee_percent"], 0.0)
            self.assertGreater(len(channel["local_cashout"]), 5)

    def test_checklist_generation(self):
        dummy_deliverable = {
            "title": "Produit Démo",
            "price_usd": 15.0,
            "monetization_channel": "crypto_usdt"
        }
        steps = MonetizationAdvisor.generate_monetization_checklist(dummy_deliverable)
        self.assertTrue(len(steps) >= 3)
        self.assertTrue(any("Madagascar" in s for s in steps))


if __name__ == "__main__":
    unittest.main()

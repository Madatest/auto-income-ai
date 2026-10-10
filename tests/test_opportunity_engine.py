#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shutil
import tempfile
import unittest

from storage import StorageManager
from opportunity_engine import OpportunityEngine


class TestOpportunityEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test.db")
        self.json_path = os.path.join(self.test_dir, "test.json")
        self.storage = StorageManager(self.db_path, self.json_path)
        self.config = {
            "scoring": {
                "weights": {
                    "observable_demand": 25,
                    "zero_start_cost": 20,
                    "speed_to_first_sale": 20,
                    "technical_feasibility": 15,
                    "madagascar_payment_readiness": 20
                }
            },
            "sources": [],
            "execution": {"allow_offline_fallback": True}
        }
        self.engine = OpportunityEngine(self.config, self.storage)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_scoring_logic(self):
        sample_opp = {
            "title": "Modèle Excel Gestion Budget Vendeurs",
            "category": "digital_product",
            "source_id": "test_src"
        }
        scored = self.engine.score_opportunity(sample_opp)
        self.assertIn("score", scored)
        self.assertGreaterEqual(scored["score"], 50.0)
        self.assertLessEqual(scored["score"], 100.0)

        breakdown = scored["score_breakdown"]
        self.assertEqual(breakdown["zero_start_cost"], 20.0)
        self.assertGreater(breakdown["madagascar_payment_readiness"], 10.0)

    def test_demo_dataset_collection_and_fallback(self):
        results = self.engine.collect_and_evaluate(force_simulation=True)
        self.assertGreaterEqual(len(results), 3)
        self.assertTrue(results[0]["score"] >= results[-1]["score"])

    def test_selection_of_best_opportunity(self):
        best = self.engine.select_best_opportunity()
        self.assertIsNotNone(best)
        self.assertTrue(len(best["title"]) > 0)


if __name__ == "__main__":
    unittest.main()

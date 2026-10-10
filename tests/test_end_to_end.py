#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shutil
import tempfile
import unittest

from main import AutoIncomeAgent


class TestEndToEndCycle(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "test_config.json")
        self.db_path = os.path.join(self.test_dir, "income.db")
        self.json_path = os.path.join(self.test_dir, "state.json")
        self.site_dir = os.path.join(self.test_dir, "site")
        self.deliverables_dir = os.path.join(self.site_dir, "deliverables")

        test_config = {
            "agent": {
                "name": "AUTO-INCOME AI TEST",
                "default_currency": "USD"
            },
            "scoring": {
                "weights": {
                    "observable_demand": 25,
                    "zero_start_cost": 20,
                    "speed_to_first_sale": 20,
                    "technical_feasibility": 15,
                    "madagascar_payment_readiness": 20
                }
            },
            "storage": {
                "sqlite_db": self.db_path,
                "state_json": self.json_path,
                "site_dir": self.site_dir,
                "deliverables_dir": self.deliverables_dir
            },
            "sources": [],
            "execution": {
                "simulation_mode": True,
                "allow_offline_fallback": True
            }
        }
        import json
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(test_config, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_autonomous_cycle(self):
        agent = AutoIncomeAgent(config_path=self.config_path, simulation_mode=True)
        summary = agent.run_cycle()

        self.assertEqual(summary["status"], "SUCCESS")
        self.assertGreater(summary["opportunities_scanned"], 0)
        self.assertIsNotNone(summary["deliverable"])
        self.assertTrue(os.path.exists(summary["deliverable"]["file_path"]))

        # Verify state persistence
        stats = agent.storage.get_summary_stats()
        self.assertEqual(stats["total_executions"], 1)
        self.assertEqual(stats["total_deliverables"], 1)
        self.assertEqual(stats["total_costs_usd"], 0.0)

        # Verify HTML site generated
        index_html = os.path.join(self.site_dir, "index.html")
        self.assertTrue(os.path.exists(index_html))


if __name__ == "__main__":
    unittest.main()

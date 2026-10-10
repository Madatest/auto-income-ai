#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shutil
import tempfile
import unittest

from storage import StorageManager


class TestStorageManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_income.db")
        self.json_path = os.path.join(self.test_dir, "test_state.json")
        self.storage = StorageManager(self.db_path, self.json_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_deduplication_via_hash(self):
        opp1 = {
            "title": "Produit Test 1",
            "category": "digital_product",
            "source_id": "test_src",
            "score": 85.0
        }
        # First save should succeed
        res1 = self.storage.save_opportunity(opp1)
        self.assertTrue(res1)

        # Second save with exact same title & source must be detected as duplicate
        res2 = self.storage.save_opportunity(opp1)
        self.assertFalse(res2)

    def test_deliverable_lifecycle(self):
        deliverable = {
            "opportunity_hash": "testhash123",
            "category": "microservice_gig",
            "title": "Service de test",
            "file_path": "/tmp/test.md",
            "relative_path": "deliverables/test.md",
            "monetization_channel": "comeup",
            "price_usd": 25.0,
            "quality_score": 95.0,
            "metadata": {"test_key": "test_val"}
        }
        d_id = self.storage.save_deliverable(deliverable)
        self.assertGreater(d_id, 0)

        deliverables = self.storage.get_all_deliverables()
        self.assertEqual(len(deliverables), 1)
        self.assertEqual(deliverables[0]["title"], "Service de test")
        self.assertEqual(deliverables[0]["metadata"]["test_key"], "test_val")

    def test_execution_logging_and_json_export(self):
        exec_id = self.storage.record_execution(
            status="SUCCESS",
            opps_found=5,
            deliverables_created=1,
            duration_sec=1.23,
            notes="Cycle de test unitaire"
        )
        self.assertGreater(exec_id, 0)
        self.assertTrue(os.path.exists(self.json_path))

        stats = self.storage.get_summary_stats()
        self.assertEqual(stats["total_executions"], 1)
        self.assertEqual(stats["total_costs_usd"], 0.0)


if __name__ == "__main__":
    unittest.main()

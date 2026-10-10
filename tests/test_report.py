#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shutil
import tempfile
import unittest

from storage import StorageManager
from report import ReportGenerator


class TestReportGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test.db")
        self.json_path = os.path.join(self.test_dir, "test.json")
        self.site_dir = os.path.join(self.test_dir, "site")
        self.storage = StorageManager(self.db_path, self.json_path)
        self.reporter = ReportGenerator(self.storage, self.site_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_console_summary_generation(self):
        summary = self.reporter.generate_console_summary(exec_id=1, duration_sec=2.5, opps_count=4)
        self.assertIn("AUTO-INCOME AI", summary)
        self.assertIn("0,00 $", summary)

    def test_html_dashboard_generation(self):
        # Insert a sample deliverable
        self.storage.save_deliverable({
            "opportunity_hash": "test123",
            "category": "digital_product",
            "title": "Mon Guide Test",
            "file_path": "/tmp/guide.md",
            "relative_path": "deliverables/guide.md",
            "monetization_channel": "gumroad",
            "price_usd": 12.0,
            "quality_score": 100.0,
            "metadata": {}
        })

        index_file = self.reporter.build_html_dashboard()
        self.assertTrue(os.path.exists(index_file))
        with open(index_file, "r", encoding="utf-8") as f:
            html = f.read()
            self.assertIn("AUTO-INCOME AI", html)
            self.assertIn("Mon Guide Test", html)
            self.assertIn("0,00 $", html)


if __name__ == "__main__":
    unittest.main()

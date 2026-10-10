#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shutil
import tempfile
import unittest

from wolf_supervisor import WolfSupervisor


class TestWolfSupervisor(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test.db")
        self.dir_file = os.path.join(self.test_dir, "directives.json")
        self.supervisor = WolfSupervisor(
            db_path=self.db_path,
            directives_file=self.dir_file
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_interrogation_protocol(self):
        sample_report = {
            "cycle_id": 1,
            "deliverable": {
                "title": "[Bounty] Solve issue #100",
                "category": "microservice_gig",
                "price_usd": 20.0
            },
            "first_real_revenue": False
        }
        res = self.supervisor.interrogate(sample_report)
        self.assertEqual(len(res), 10)
        self.assertIn("1_actual_production", res)
        self.assertIn("9_fastest_path_to_cash", res)
        self.assertIn("10_lesson_learned", res)

    def test_decision_quality_score_bounty_vs_digital_product(self):
        bounty_report = {
            "deliverable": {
                "title": "[Bounty] Active Python Gig",
                "category": "microservice_gig",
                "source_id": "github_bounties"
            }
        }
        bounty_score, _ = self.supervisor.score_decision_quality(bounty_report)

        digital_report = {
            "deliverable": {
                "title": "Slow Theoretical E-book",
                "category": "digital_product",
                "source_id": "slow_feed"
            }
        }
        digital_score, _ = self.supervisor.score_decision_quality(digital_report)

        # Bounty must score significantly higher than theoretical slow digital product
        self.assertGreater(bounty_score, 80.0)
        self.assertLess(digital_score, 60.0)
        self.assertGreater(bounty_score, digital_score)

    def test_review_cycle_and_persistence(self):
        sample_report = {
            "cycle_id": 42,
            "total_confirmed_revenue_usd": 0.0,
            "costs_incurred_usd": 0.0,
            "first_real_revenue": False,
            "deliverable": {
                "title": "[radar] Open Bounty Task",
                "category": "microservice_gig",
                "price_usd": 25.0
            }
        }
        directive = self.supervisor.review_cycle(sample_report)
        self.assertIsNotNone(directive)
        self.assertEqual(directive["cycle_id"], 42)
        self.assertIn("decision_score", directive)
        self.assertIn("weaknesses", directive)
        self.assertIn("assigned_task", directive)
        self.assertIn("acceptance_criteria", directive)

        # Verify persisted file
        self.assertTrue(os.path.exists(self.dir_file))

        # Verify get_active_directive
        loaded = self.supervisor.get_active_directive()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["cycle_id"], 42)

    def test_format_console_verdict(self):
        sample_report = {
            "cycle_id": 5,
            "first_real_revenue": False,
            "deliverable": {
                "title": "Test Gig",
                "category": "microservice_gig"
            }
        }
        review = self.supervisor.review_cycle(sample_report)
        console_txt = self.supervisor.format_console_verdict(review)
        self.assertIn("WOLF", console_txt)
        self.assertIn(WolfSupervisor.MOTTO, console_txt)
        self.assertIn("AUDIT SANS CONCESSION", console_txt)


if __name__ == "__main__":
    unittest.main()

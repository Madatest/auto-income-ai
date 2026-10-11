#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shutil
import tempfile
import unittest

from content_factory import ContentFactory


class TestContentFactory(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.factory = ContentFactory(output_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_build_all_5_models(self):
        categories = ["digital_product", "microservice_gig", "seo_content", "b2b_prospects", "micro_tool"]
        for cat in categories:
            opp = {
                "title": f"Titre Test pour {cat}",
                "category": cat,
                "description": f"Description de test pour {cat}",
                "hash": f"hash_{cat}"
            }
            deliverable = self.factory.build_deliverable(opp)
            self.assertEqual(deliverable["category"], cat)
            self.assertTrue(os.path.exists(deliverable["file_path"]))
            self.assertGreater(deliverable["quality_score"], 70.0)

            # Check that file content is non-empty
            with open(deliverable["file_path"], "r", encoding="utf-8") as f:
                content = f.read()
                self.assertGreater(len(content), 200)

    def test_qa_audit_flags_short_content(self):
        score, notes = self.factory._audit_quality("Court", "digital_product")
        self.assertLess(score, 60.0)
        self.assertIn("Longueur insuffisante", notes)

    def test_bounty_solution_generation(self):
        bounty_opp = {
            "title": "[Bounty $50] Fix authentication bug on Telegram bot",
            "category": "microservice_gig",
            "description": "The bot fails to validate auth tokens from user message payload. Needs immediate fix and unit tests.",
            "source_id": "github_bounties",
            "source_url": "https://github.com/example/bot/issues/42",
            "hash": "test_bounty_hash_1"
        }
        deliverable = self.factory.build_deliverable(bounty_opp)
        self.assertEqual(deliverable["category"], "bounty_solution")
        self.assertTrue(deliverable["metadata"]["is_bounty"])
        self.assertTrue(os.path.exists(deliverable["file_path"]))
        self.assertIn("proposal_snippet", deliverable["metadata"])
        self.assertGreater(len(deliverable["metadata"]["proposal_snippet"]), 50)
        self.assertGreaterEqual(deliverable["quality_score"], 80.0)

        with open(deliverable["file_path"], "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue("Proposed Solution" in content or "Pull Request" in content or "Modèle" in content or "Bounty" in content)
        self.assertIn("254779310", content)

    def test_qa_flags_pass_placeholder_in_bounty(self):
        fake_content = "# 🎯 GITHUB BOUNTY RESOLUTION DOSSIER : Test\n\ndef execute_resolution_fix():\n    pass\n\n## 5. Modèle\n254779310"
        score, notes = self.factory._audit_quality(fake_content, "bounty_solution")
        self.assertIn("Pénalité QA", notes)


if __name__ == "__main__":
    unittest.main()

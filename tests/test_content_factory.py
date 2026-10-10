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


if __name__ == "__main__":
    unittest.main()

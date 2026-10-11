#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import unittest
from outbound_agent import OutboundSubmitter


class TestOutboundSubmitter(unittest.TestCase):
    def test_extract_github_issue_info(self):
        url = "https://github.com/chatmcp/mcpso/issues/5032"
        info = OutboundSubmitter.extract_github_issue_info(url)
        self.assertIsNotNone(info)
        self.assertEqual(info["owner"], "chatmcp")
        self.assertEqual(info["repo"], "mcpso")
        self.assertEqual(info["issue_number"], 5032)

    def test_extract_invalid_url(self):
        self.assertIsNone(OutboundSubmitter.extract_github_issue_info("https://example.com/not_an_issue"))

    def test_submit_without_token_returns_awaiting_token(self):
        # Save token if present
        saved = os.environ.pop("GH_TOKEN", None)
        saved_gh = os.environ.pop("GITHUB_TOKEN", None)
        try:
            res = OutboundSubmitter.submit_issue_comment(
                "https://github.com/example/repo/issues/12",
                "Hello @maintainers"
            )
            self.assertFalse(res["success"])
            self.assertEqual(res["status"], "awaiting_token")
        finally:
            if saved:
                os.environ["GH_TOKEN"] = saved
            if saved_gh:
                os.environ["GITHUB_TOKEN"] = saved_gh


if __name__ == "__main__":
    unittest.main()

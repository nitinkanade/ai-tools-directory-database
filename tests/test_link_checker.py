"""
Unit tests for the dead-link checker script (scripts/check_links.py).
Tests mock network responses to ensure determinism and zero external dependencies.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(DB_DIR, "scripts"))

from check_links import (
    check_single_url,
    check_all_tools,
    generate_markdown_report,
    collect_tools_from_dir,
)

class TestLinkChecker(unittest.TestCase):
    def test_invalid_url_scheme_detected(self):
        res = check_single_url("ftp://invalid.com/file")
        self.assertEqual(res["category"], "INVALID_URL")
        self.assertEqual(res["status_code"], 0)

        empty_res = check_single_url("")
        self.assertEqual(empty_res["category"], "INVALID_URL")

    @patch("urllib.request.build_opener")
    def test_live_url_200_head_success(self, mock_build_opener):
        # Mock opener context manager
        mock_opener = MagicMock()
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.geturl.return_value = "https://example.com"
        mock_opener.open.return_value.__enter__.return_value = mock_response
        mock_build_opener.return_value = mock_opener

        res = check_single_url("https://example.com")
        self.assertEqual(res["category"], "LIVE")
        self.assertEqual(res["status_code"], 200)
        self.assertEqual(res["final_url"], "https://example.com")
        self.assertIsNone(res["error"])

    @patch("urllib.request.build_opener")
    def test_dead_url_404_handled(self, mock_build_opener):
        mock_opener = MagicMock()
        mock_opener.open.side_effect = urllib.error.HTTPError(
            url="https://example.com/not-found",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )
        mock_build_opener.return_value = mock_opener

        res = check_single_url("https://example.com/not-found")
        self.assertEqual(res["category"], "DEAD")
        self.assertEqual(res["status_code"], 404)
        self.assertIn("404", res["error"])

    @patch("urllib.request.build_opener")
    def test_head_405_falls_back_to_get_success(self, mock_build_opener):
        mock_opener = MagicMock()

        # First call (HEAD) raises 405 Method Not Allowed
        # Second call (GET) returns 200
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.geturl.return_value = "https://example.com/api"

        mock_enter = MagicMock()
        mock_enter.getcode.return_value = 200
        mock_enter.geturl.return_value = "https://example.com/api"

        def side_effect(req, timeout=None):
            if req.get_method() == "HEAD":
                raise urllib.error.HTTPError(
                    url=req.full_url,
                    code=405,
                    msg="Method Not Allowed",
                    hdrs={},
                    fp=None,
                )
            context = MagicMock()
            context.__enter__.return_value = mock_enter
            return context

        mock_opener.open.side_effect = side_effect
        mock_build_opener.return_value = mock_opener

        res = check_single_url("https://example.com/api")
        self.assertEqual(res["category"], "LIVE")
        self.assertEqual(res["status_code"], 200)

    @patch("urllib.request.build_opener")
    def test_bot_challenge_403_detected(self, mock_build_opener):
        mock_opener = MagicMock()
        # Both HEAD and GET raise 403
        mock_opener.open.side_effect = urllib.error.HTTPError(
            url="https://protected.ai",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=None,
        )
        mock_build_opener.return_value = mock_opener

        res = check_single_url("https://protected.ai")
        self.assertEqual(res["category"], "BOT_CHALLENGE")
        self.assertEqual(res["status_code"], 403)

    def test_generate_markdown_report(self):
        sample_results = [
            {
                "tool_id": "tool-1",
                "tool_name": "Tool One",
                "type": "website",
                "url": "https://tool-one.com",
                "status_code": 200,
                "category": "LIVE",
                "final_url": "https://tool-one.com",
                "error": None,
                "elapsed_ms": 120,
            },
            {
                "tool_id": "tool-2",
                "tool_name": "Tool Two",
                "type": "website",
                "url": "https://tool-two.com/broken",
                "status_code": 404,
                "category": "DEAD",
                "final_url": "https://tool-two.com/broken",
                "error": "HTTP 404: Not Found",
                "elapsed_ms": 95,
            },
        ]

        report = generate_markdown_report(sample_results, generated_at="2026-10-15 22:00:00 UTC")
        self.assertIn("# AI Tools Directory — URL Health & Dead-Link Report", report)
        self.assertIn("Total URLs Checked**: `2`", report)
        self.assertIn("Live & Accessible**: `1`", report)
        self.assertIn("Dead / Broken Links**: `1`", report)
        self.assertIn("Broken Links Requiring Immediate Attention", report)
        self.assertIn("Tool Two", report)

    def test_collect_tools_from_dir(self):
        tools_dir = os.path.join(DB_DIR, "data", "tools")
        tools = collect_tools_from_dir(tools_dir)
        self.assertGreaterEqual(len(tools), 40)
        self.assertTrue(any(t["id"] == "cursor" for t in tools))

if __name__ == "__main__":
    unittest.main()

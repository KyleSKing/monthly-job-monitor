import os
import sys
import unittest
from unittest import mock

API_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

import rescrape  # noqa: E402


class RescrapeTests(unittest.TestCase):
    def test_missing_token_returns_501(self):
        status, payload = rescrape.trigger_workflow("", "owner/repo")
        self.assertEqual(status, 501)
        self.assertIn("error", payload)

    def test_missing_repo_returns_501(self):
        status, payload = rescrape.trigger_workflow("tok", "")
        self.assertEqual(status, 501)

    def test_success_returns_202_with_correct_request(self):
        fake_resp = mock.MagicMock()
        fake_resp.status = 204
        fake_resp.__enter__ = lambda s: fake_resp
        fake_resp.__exit__ = lambda s, *a: False

        with mock.patch.object(
            rescrape.urllib.request, "urlopen", return_value=fake_resp
        ) as m:
            status, payload = rescrape.trigger_workflow("tok", "owner/repo", "main")

        self.assertEqual(status, 202)
        self.assertEqual(payload["status"], "triggered")

        # Assert the request targeted the right workflow with correct auth + body
        req = m.call_args.args[0]
        self.assertIn(
            "/repos/owner/repo/actions/workflows/monthly-scrape.yml/dispatches",
            req.full_url,
        )
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.headers["Authorization"], "Bearer tok")
        self.assertEqual(req.data, b'{"ref": "main"}')

    def test_github_http_error_propagates_code(self):
        err = rescrape.urllib.error.HTTPError(
            "url", 403, "Forbidden", hdrs=None, fp=None
        )
        with mock.patch.object(rescrape.urllib.request, "urlopen", side_effect=err):
            status, payload = rescrape.trigger_workflow("tok", "owner/repo")
        self.assertEqual(status, 403)
        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()

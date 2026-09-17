import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock
import asyncio

from scripts.run_round1e_c2_validation import aggregate_viewports, build_summary, capture_paths
from lp_engine.browser_qa import FAVICON_ROUTE_GLOB, _fulfill_favicon, classify_resource_error


class Round1EC2HarnessTest(unittest.IsolatedAsyncioTestCase):
    def test_favicon_only_is_benign_but_required_resources_are_critical(self):
        self.assertEqual(classify_resource_error("http://localhost/favicon.ico", 404), "BENIGN_NON_CRITICAL_RESOURCE")
        self.assertEqual(classify_resource_error("http://localhost/assets/hero.png", 404), "CRITICAL_RESOURCE_ERROR")
        self.assertEqual(classify_resource_error("http://localhost/style.css", 404), "CRITICAL_RESOURCE_ERROR")
        self.assertEqual(classify_resource_error("http://localhost/app.js", 404), "CRITICAL_RESOURCE_ERROR")

    async def test_favicon_route_returns_204(self):
        route = AsyncMock()
        await _fulfill_favicon(route)
        route.fulfill.assert_awaited_once_with(status=204, body=b"", headers={"Content-Type": "image/x-icon"})
        self.assertEqual(FAVICON_ROUTE_GLOB, "**/favicon.ico")

    def test_viewport_aggregation_is_per_result(self):
        total, passed, failed = aggregate_viewports([{"status": "PASS"}] * 26 + [{"status": "FAIL"}])
        self.assertEqual((total, passed, failed), (27, 26, 1))
        self.assertEqual(aggregate_viewports([{"status": "PASS"}] * 27), (27, 27, 0))

    def test_capture_count_uses_real_files(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            with patch("scripts.run_round1e_c2_validation.OUT", base):
                company = "maylynn_paint"
                target = base / "human_review" / company
                target.mkdir(parents=True)
                (target / "desktop_1440.png").write_bytes(b"x")
                self.assertEqual(len(capture_paths(company)), 1)
                (target / "mobile_390.png").write_bytes(b"x")
                self.assertEqual(len(capture_paths(company)), 2)

    def test_human_review_ready_requires_all_gates(self):
        reports = [{"company": str(i), "widths": 9, "pass_count": 9, "fail_count": 0, "photo_roles": ["a", "b", "c", "d"], "results": []} for i in range(3)]
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            with patch("scripts.run_round1e_c2_validation.OUT", base):
                for company in ("maylynn_paint", "nagi_no_mirai", "watashi_no_daidokoro"):
                    path = base / "human_review" / company
                    path.mkdir(parents=True)
                    (path / "desktop_1440.png").write_bytes(b"x")
                    (path / "mobile_390.png").write_bytes(b"x")
                self.assertTrue(build_summary(reports, {}, "sha")["human_review_ready"])
                reports[0]["fail_count"] = 1
                reports[0]["pass_count"] = 8
                self.assertFalse(build_summary(reports, {}, "sha")["human_review_ready"])


if __name__ == "__main__":
    unittest.main()

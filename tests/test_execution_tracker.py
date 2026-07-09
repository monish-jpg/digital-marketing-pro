"""execution-tracker.py — audit integrity (H3), resume-launch, exit codes."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _helpers import run_json, run_script  # type: ignore[import-not-found]


class ExecTrackerBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name)
        (self.home / "brands" / "acme").mkdir(parents=True)

    def et(self, *args):
        return run_json("execution-tracker.py", *args, marketing_home=self.home)

    def _log(self, content_id, result="success", platform="wordpress", action="publish-blog"):
        data, rc = self.et("--brand", "acme", "--action", "log-execution", "--data",
                           json.dumps({"platform": platform, "action_type": action,
                                       "content_id": content_id, "result": result}))
        self.assertEqual(rc, 0, data)


class TestLogAndHistory(ExecTrackerBase):
    def test_log_then_history(self):
        self._log("post-1")
        data, rc = self.et("--brand", "acme", "--action", "get-history")
        self.assertEqual(rc, 0)
        self.assertEqual(data["total"], 1)

    def test_missing_brand_exits_nonzero(self):
        proc = run_script("execution-tracker.py", "--brand", "ghost", "--action", "get-history",
                          marketing_home=self.home)
        self.assertNotEqual(proc.returncode, 0)


class TestAuditIntegrityH3(ExecTrackerBase):
    def test_corrupt_index_rebuilt_from_files(self):
        self._log("post-1")
        self._log("post-2", result="failure", platform="meta", action="launch-ads")
        # Corrupt the summary index — stats must rebuild from the exec-*.json files.
        idx = self.home / "brands" / "acme" / "executions" / "_index.json"
        idx.write_text("{ this is not json", encoding="utf-8")
        data, rc = self.et("--brand", "acme", "--action", "get-stats")
        self.assertEqual(rc, 0)
        self.assertEqual(data["total_executed"], 2)

    def test_index_written_atomically_no_tmp(self):
        self._log("post-1")
        tmp = self.home / "brands" / "acme" / "executions" / "_index.json.tmp"
        self.assertFalse(tmp.exists())


class TestResumeLaunch(ExecTrackerBase):
    def test_resume_launch_reports_prior_executions(self):
        self._log("camp-42 step-1", result="success")
        self._log("camp-42 step-2", result="failure", platform="meta", action="launch-ads")
        data, rc = self.et("--brand", "acme", "--action", "resume-launch",
                           "--data", json.dumps({"campaign_id": "camp-42", "from_step": 2}))
        self.assertEqual(rc, 0)
        self.assertEqual(data["status"], "resume-ready")
        self.assertEqual(data["from_step"], 2)
        self.assertEqual(len(data["prior_executions"]), 2)
        self.assertEqual(data["already_succeeded"], 1)

    def test_resume_launch_requires_data(self):
        proc = run_script("execution-tracker.py", "--brand", "acme", "--action", "resume-launch",
                          marketing_home=self.home)
        self.assertNotEqual(proc.returncode, 0)

    def test_resume_launch_bad_from_step(self):
        data, rc = self.et("--brand", "acme", "--action", "resume-launch",
                           "--data", json.dumps({"campaign_id": "c", "from_step": "abc"}))
        self.assertEqual(rc, 1)
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()

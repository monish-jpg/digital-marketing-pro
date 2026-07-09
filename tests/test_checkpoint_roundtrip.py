"""checkpoint-manager.py — resume roundtrip, env-aware brands/ layout, slug."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _helpers import run_json, run_script  # type: ignore[import-not-found]


class CheckpointBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name)

    def cp(self, *args):
        return run_json("checkpoint-manager.py", *args, marketing_home=self.home)


class TestCheckpointRoundtrip(CheckpointBase):
    def _init(self, brand="acme", workflow="engagement", topic="q2"):
        data, rc = self.cp("init", "--brand", brand, "--workflow", workflow, "--topic", topic)
        self.assertEqual(rc, 0, data)
        return data["run_id"]

    def test_init_uses_brands_layout(self):
        run_id = self._init()
        # env-aware, canonical brands/{slug}/runs layout
        run_dir = self.home / "brands" / "acme" / "runs" / run_id
        self.assertTrue(run_dir.exists(), f"missing {run_dir}")

    def test_save_then_status_reports_progress(self):
        run_id = self._init()
        self.cp("save", "--brand", "acme", "--run-id", run_id, "--step", "1", "--content", "part 1 body")
        data, rc = self.cp("status", "--brand", "acme", "--run-id", run_id)
        self.assertEqual(rc, 0)
        self.assertIn("1", data["completed_steps"])
        self.assertEqual(data["next_step"], "2")

    def test_load_returns_saved_content(self):
        run_id = self._init()
        self.cp("save", "--brand", "acme", "--run-id", run_id, "--step", "1", "--content", "hello body")
        data, rc = self.cp("load", "--brand", "acme", "--run-id", run_id, "--step", "1")
        self.assertEqual(rc, 0)
        self.assertEqual(data["content"], "hello body")

    def test_resume_picks_in_progress_run(self):
        run_id = self._init()
        self.cp("save", "--brand", "acme", "--run-id", run_id, "--step", "1", "--content", "x")
        data, rc = self.cp("resume", "--brand", "acme", "--workflow", "engagement")
        self.assertEqual(rc, 0)
        self.assertEqual(data["resume_run"]["run_id"], run_id)

    def test_finalize_marks_completed(self):
        run_id = self._init()
        data, rc = self.cp("finalize", "--brand", "acme", "--run-id", run_id, "--status", "completed")
        self.assertEqual(rc, 0)
        self.assertEqual(data["status"], "completed")

    def test_slug_boundary_raw_brand_name(self):
        # "Acme Co" must resolve to the same brands/acme-co run tree.
        data, rc = self.cp("init", "--brand", "Acme Co", "--workflow", "engagement", "--topic", "t")
        self.assertEqual(rc, 0)
        run_dir = self.home / "brands" / "acme-co" / "runs" / data["run_id"]
        self.assertTrue(run_dir.exists())

    def test_unknown_run_exits_nonzero(self):
        proc = run_script("checkpoint-manager.py", "status", "--brand", "acme", "--run-id", "nope",
                          marketing_home=self.home)
        self.assertNotEqual(proc.returncode, 0)


class TestNoPersonalName(unittest.TestCase):
    def test_source_has_no_personal_name(self):
        src = (Path(__file__).resolve().parent.parent / "scripts" / "checkpoint-manager.py").read_text(encoding="utf-8")
        self.assertNotIn("Shreea", src)

    def test_part11_label_not_hardcoded_model_names(self):
        src = (Path(__file__).resolve().parent.parent / "scripts" / "checkpoint-manager.py").read_text(encoding="utf-8")
        self.assertNotIn("Nano Banana Pro", src)
        self.assertNotIn("Veo 3.1", src)


if __name__ == "__main__":
    unittest.main()

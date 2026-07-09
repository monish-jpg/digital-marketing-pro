"""engagement-state.py — state machine, slug roundtrip (H2), decision matrix,
validate-part, set-checkpoint-run, init --repair, lif-log-change LIF rewrite."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _helpers import run_json, run_script  # type: ignore[import-not-found]


class EngagementBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name)

    def es(self, *args):
        return run_json("engagement-state.py", *args, marketing_home=self.home)

    def es_raw(self, *args):
        return run_script("engagement-state.py", *args, marketing_home=self.home)


class TestInitAndStatus(EngagementBase):
    def test_init_creates_tree(self):
        data, rc = self.es("init", "--brand", "Acme Co", "--id", "2026-Q2")
        self.assertEqual(rc, 0)
        self.assertEqual(data["action"], "initialised")
        self.assertEqual(data["brand"], "acme-co")
        self.assertEqual(data["engagement_id"], "2026-q2")

    def test_h2_status_resolves_raw_brand_name(self):
        # H2: init slugifies, status must resolve the SAME dir from the raw name.
        self.es("init", "--brand", "Acme Co", "--id", "2026-Q2")
        data, rc = self.es("status", "--brand", "Acme Co", "--id", "2026-Q2")
        self.assertEqual(rc, 0)
        self.assertEqual(data["current_part"], "1")
        self.assertEqual(len(data["parts"]), 12)

    def test_slug_roundtrip_via_mark_part(self):
        self.es("init", "--brand", "Acme Co", "--id", "2026-Q2")
        data, rc = self.es("mark-part-started", "--brand", "Acme Co", "--id", "2026-Q2", "--part", "2")
        self.assertEqual(rc, 0)
        self.assertEqual(data["part"], "2")


class TestPartTransitions(EngagementBase):
    def setUp(self):
        super().setUp()
        self.es("init", "--brand", "acme", "--id", "e1")

    def test_complete_advances_current_part(self):
        data, rc = self.es("mark-part-completed", "--brand", "acme", "--id", "e1", "--part", "1")
        self.assertEqual(rc, 0)
        self.assertEqual(data["next_part"], "2")

    def test_reopen_completed_requires_force(self):
        self.es("mark-part-completed", "--brand", "acme", "--id", "e1", "--part", "1")
        proc = self.es_raw("mark-part-started", "--brand", "acme", "--id", "e1", "--part", "1")
        self.assertNotEqual(proc.returncode, 0)  # exit 2 without --force

    def test_force_reopens_completed_part(self):
        self.es("mark-part-completed", "--brand", "acme", "--id", "e1", "--part", "1")
        data, rc = self.es("mark-part-started", "--brand", "acme", "--id", "e1", "--part", "1", "--force")
        self.assertEqual(rc, 0)


class TestDecisionMatrix(EngagementBase):
    def setUp(self):
        super().setUp()
        self.es("init", "--brand", "acme", "--id", "e1")

    def test_valid_trigger_records_reruns(self):
        data, rc = self.es("decision-matrix", "--brand", "acme", "--id", "e1",
                           "--triggers", "competitors_changed")
        self.assertEqual(rc, 0)
        self.assertIn("3.1", data["triggered_reruns"])

    def test_unknown_trigger_exits_nonzero(self):
        data, rc = self.es("decision-matrix", "--brand", "acme", "--id", "e1",
                           "--triggers", "bogus_trigger")
        self.assertEqual(rc, 1)
        self.assertIn("bogus_trigger", data["unknown_triggers"])
        self.assertIn("valid_triggers", data)

    def test_minor_corrections_only_no_reruns(self):
        data, rc = self.es("decision-matrix", "--brand", "acme", "--id", "e1",
                           "--triggers", "minor_corrections_only")
        self.assertEqual(rc, 0)
        self.assertEqual(data["triggered_reruns"], [])


class TestValidatePart(EngagementBase):
    def setUp(self):
        super().setUp()
        self.es("init", "--brand", "acme", "--id", "e1")

    def test_validate_existing_part(self):
        data, rc = self.es("validate-part", "--brand", "acme", "--id", "e1", "--part", "5")
        self.assertEqual(rc, 0)
        self.assertIn(data["status"], ("ok", "incomplete"))
        self.assertEqual(data["part"], "5")

    def test_validate_unknown_part_errors(self):
        proc = self.es_raw("validate-part", "--brand", "acme", "--id", "e1", "--part", "99")
        self.assertNotEqual(proc.returncode, 0)


class TestCheckpointRunLinkage(EngagementBase):
    def test_set_checkpoint_run(self):
        self.es("init", "--brand", "acme", "--id", "e1")
        data, rc = self.es("set-checkpoint-run", "--brand", "acme", "--id", "e1", "--run-id", "run-xyz")
        self.assertEqual(rc, 0)
        self.assertEqual(data["checkpoint_run_id"], "run-xyz")
        # Persisted in state
        state = self.home / "brands" / "acme" / "engagements" / "e1" / "_engagement.json"
        self.assertEqual(json.loads(state.read_text(encoding="utf-8"))["checkpoint_run_id"], "run-xyz")


class TestInitRepair(EngagementBase):
    def test_repair_preserves_existing_state(self):
        self.es("init", "--brand", "acme", "--id", "e1")
        # Mutate then repair — state must be preserved, no crash.
        self.es("mark-part-completed", "--brand", "acme", "--id", "e1", "--part", "1")
        data, rc = self.es("init", "--brand", "acme", "--id", "e1", "--repair")
        self.assertEqual(rc, 0)
        self.assertEqual(data["action"], "repaired")
        self.assertIn("_engagement.json", data["preserved_existing"])

    def test_init_without_repair_on_nonempty_fails(self):
        self.es("init", "--brand", "acme", "--id", "e1")
        proc = self.es_raw("init", "--brand", "acme", "--id", "e1")
        self.assertNotEqual(proc.returncode, 0)


class TestLifLogChange(EngagementBase):
    def test_lif_log_change_rewrites_lif_file(self):
        self.es("init", "--brand", "acme", "--id", "e1")
        lif = self.home / "brands" / "acme" / "engagements" / "e1" / "living-instruction-file.md"
        before = lif.read_text(encoding="utf-8")
        data, rc = self.es("lif-log-change", "--brand", "acme", "--id", "e1",
                           "--section", "Corrections", "--summary", "Fixed CAC figure")
        self.assertEqual(rc, 0)
        self.assertTrue(data["lif_file_rewritten"])
        after = lif.read_text(encoding="utf-8")
        self.assertIn("LIF Change Log", after)
        self.assertIn("Fixed CAC figure", after)
        self.assertNotEqual(before, after)


class TestNoPersonalDataOrPhantoms(EngagementBase):
    def test_schema_url_removed(self):
        self.es("init", "--brand", "acme", "--id", "e1")
        state = self.home / "brands" / "acme" / "engagements" / "e1" / "_engagement.json"
        payload = json.loads(state.read_text(encoding="utf-8"))
        self.assertNotIn("schema_url", payload)


if __name__ == "__main__":
    unittest.main()

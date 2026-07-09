"""test_skill_script_contracts.py — exercises scripts/check_skill_contracts.py.

This validates the CONTRACT LINTER itself (extraction + validation logic) and
that it runs cleanly over the whole repo. The repo-wide *zero-mismatch* gate is
run as a separate standalone step (`python scripts/check_skill_contracts.py`,
per the verification protocol) because doc-side mismatches are cleared by the
skill/agent packages; this suite must stay green independent of that timing.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import check_skill_contracts as csc  # noqa: E402


class TestSpecExtraction(unittest.TestCase):
    def test_extract_subcommand_script(self):
        spec = csc.extract_script_spec(SCRIPTS_DIR / "engagement-state.py")
        self.assertIsNotNone(spec)
        self.assertIn("init", spec["subcommands"])
        self.assertIn("validate-part", spec["subcommands"])
        self.assertIn("set-checkpoint-run", spec["subcommands"])
        self.assertIn("--brand", spec["flags"])

    def test_extract_action_script(self):
        spec = csc.extract_script_spec(SCRIPTS_DIR / "execution-tracker.py")
        self.assertIsNotNone(spec)
        self.assertIn("log-execution", spec["actions"])
        self.assertIn("resume-launch", spec["actions"])
        self.assertIn("--action", spec["flags"])

    def test_common_module_skipped(self):
        # Underscore-prefixed helpers are not linted as invocable scripts.
        specs = csc.load_all_specs()
        self.assertNotIn("_common.py", specs)


class TestParseInvocation(unittest.TestCase):
    def test_flags_and_action(self):
        inv = csc.parse_invocation(" --brand acme --action get-history --limit 10")
        self.assertIn("--brand", inv["flags"])
        self.assertIn("--action", inv["flags"])
        self.assertEqual(inv["action"], "get-history")

    def test_subcommand_leading(self):
        inv = csc.parse_invocation(" init --brand acme --id e1")
        self.assertEqual(inv["subcommand"], "init")

    def test_stops_at_shell_separator(self):
        inv = csc.parse_invocation(" --brand acme | python other.py --bogus")
        self.assertNotIn("--bogus", inv["flags"])


class TestValidateInvocation(unittest.TestCase):
    def setUp(self):
        self.spec = {
            "flags": {"--brand", "--action", "--help"},
            "subcommands": set(),
            "actions": {"get-history", "log-execution"},
            "uses_argparse": True,
        }

    def test_good_invocation_no_problems(self):
        inv = {"flags": ["--brand", "--action"], "subcommand": None, "action": "get-history"}
        self.assertEqual(csc.validate_invocation(self.spec, inv, "x.py"), [])

    def test_unknown_flag_flagged(self):
        inv = {"flags": ["--bogus"], "subcommand": None, "action": None}
        probs = csc.validate_invocation(self.spec, inv, "x.py")
        self.assertEqual(probs[0]["kind"], "unknown-flag")

    def test_unknown_action_flagged(self):
        inv = {"flags": [], "subcommand": None, "action": "nope"}
        probs = csc.validate_invocation(self.spec, inv, "x.py")
        self.assertEqual(probs[0]["kind"], "unknown-action")

    def test_placeholder_action_ignored(self):
        inv = {"flags": [], "subcommand": None, "action": "<action>"}
        self.assertEqual(csc.validate_invocation(self.spec, inv, "x.py"), [])

    def test_placeholder_flag_ignored(self):
        inv = {"flags": ["--<flag>"], "subcommand": None, "action": None}
        self.assertEqual(csc.validate_invocation(self.spec, inv, "x.py"), [])


class TestLintRunsOverRepo(unittest.TestCase):
    def test_lint_returns_structured_list(self):
        specs = csc.load_all_specs()
        self.assertGreater(len(specs), 50)
        mismatches = csc.lint(specs)
        self.assertIsInstance(mismatches, list)
        for mm in mismatches:
            self.assertIn(mm["kind"], ("unknown-flag", "unknown-action", "unknown-subcommand"))
            self.assertIn("file", mm)
            self.assertIn("script", mm)


if __name__ == "__main__":
    unittest.main()

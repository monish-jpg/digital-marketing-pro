"""connector_resolver.py — ACTION_SPECS + resolve_action probe.

Action resolution should never crash regardless of MCP configuration."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import connector_resolver  # noqa: E402  # pyright: ignore[reportMissingImports]  # type: ignore[import-not-found]


class TestActionSpecs(unittest.TestCase):
    def test_action_specs_present(self):
        self.assertGreater(len(connector_resolver.ACTION_SPECS), 10,
                           "expect at least 10 actions in the catalog")

    def test_each_spec_has_required_fields(self):
        for action_id, spec in connector_resolver.ACTION_SPECS.items():
            self.assertIn("operation", spec, f"missing operation in {action_id}")
            self.assertIn("purpose", spec, f"missing purpose in {action_id}")
            self.assertIn("script", spec, f"missing script in {action_id}")
            self.assertIn(spec["operation"], ("read", "write", "local"),
                          f"{action_id} has invalid operation: {spec['operation']}")


class TestResolveAction(unittest.TestCase):
    def test_unknown_action_does_not_crash(self):
        result = connector_resolver.resolve_action("non-existent-action", "acme")
        # resolver returns either {mode: ...} for known actions, or
        # {status: "unknown_action", known_actions: [...]} for unknown ones.
        self.assertTrue("mode" in result or result.get("status") == "unknown_action",
                        f"unexpected shape: {result}")
        if result.get("status") == "unknown_action":
            self.assertIn("known_actions", result)
            self.assertGreater(len(result["known_actions"]), 0)

    def test_known_action_resolves(self):
        first = next(iter(connector_resolver.ACTION_SPECS))
        result = connector_resolver.resolve_action(first, "acme")
        self.assertIn("mode", result)
        self.assertIn(result["mode"],
                      ("real", "manifest_ready", "stub_unconfigured"))

    def test_resolve_action_returns_purpose(self):
        for action_id in list(connector_resolver.ACTION_SPECS)[:3]:
            result = connector_resolver.resolve_action(action_id, "acme")
            self.assertIn("action", result)
            self.assertEqual(result["action"], action_id)


if __name__ == "__main__":
    unittest.main()

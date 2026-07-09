"""Tests for scripts/_common.py — the shared helper module (DMP path canon)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import _common  # noqa: E402


class EnvHomeMixin(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        self._saved = os.environ.get("CLAUDE_MARKETING_HOME")
        os.environ["CLAUDE_MARKETING_HOME"] = str(self.home)

    def tearDown(self):
        if self._saved is None:
            os.environ.pop("CLAUDE_MARKETING_HOME", None)
        else:
            os.environ["CLAUDE_MARKETING_HOME"] = self._saved
        self._tmp.cleanup()


class TestSlugifyBrand(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(_common.slugify_brand("Acme Corp"), "acme-corp")

    def test_punctuation_collapses(self):
        self.assertEqual(_common.slugify_brand("Acme & Co!!"), "acme-co")

    def test_ampersand_matches_across_scripts(self):
        # Regression for the three-slugifier bug: "Acme & Co" must NOT be "acme---co".
        self.assertEqual(_common.slugify_brand("Acme & Co"), "acme-co")

    def test_max_60_chars(self):
        self.assertLessEqual(len(_common.slugify_brand("x" * 200)), 60)

    def test_empty_yields_brand(self):
        self.assertEqual(_common.slugify_brand(""), "brand")
        self.assertEqual(_common.slugify_brand("!!!"), "brand")

    def test_already_slug_unchanged(self):
        self.assertEqual(_common.slugify_brand("acme-corp"), "acme-corp")

    def test_slugify_alias_is_slugify_brand(self):
        self.assertIs(_common.slugify, _common.slugify_brand)


class TestNowIso(unittest.TestCase):
    def test_ends_with_z(self):
        self.assertTrue(_common.now_iso().endswith("Z"))
        self.assertIn("T", _common.now_iso())


class TestAtomicWriteAndLoad(EnvHomeMixin):
    def test_roundtrip(self):
        p = self.home / "sub" / "data.json"
        _common.atomic_write_json(p, {"a": 1, "s": "ünïcode — em"})
        data = _common.load_json_safe(p)
        self.assertEqual(data["a"], 1)
        self.assertEqual(data["s"], "ünïcode — em")

    def test_no_tmp_left_behind(self):
        p = self.home / "data.json"
        _common.atomic_write_json(p, {"x": True})
        self.assertFalse((self.home / "data.json.tmp").exists())

    def test_atomic_write_text_roundtrip(self):
        p = self.home / "note.md"
        _common.atomic_write_text(p, "# Heading — dash")
        self.assertEqual(p.read_text(encoding="utf-8"), "# Heading — dash")

    def test_load_missing_returns_error_dict(self):
        result = _common.load_json_safe(self.home / "nope.json")
        self.assertIn("error", result)
        self.assertTrue(result.get("missing"))
        self.assertIn("recovery", result)

    def test_load_corrupt_returns_error_dict(self):
        p = self.home / "bad.json"
        p.write_text('{"truncated": ', encoding="utf-8")
        result = _common.load_json_safe(p)
        self.assertIn("error", result)
        self.assertTrue(result.get("corrupt"))


class TestWorkspaceAndBrandDir(EnvHomeMixin):
    def test_env_override_wins(self):
        self.assertEqual(_common.workspace_root(), self.home)

    def test_brands_root_has_brands_segment(self):
        self.assertEqual(_common.brands_root(), self.home / "brands")

    def test_brand_dir_uses_slug_when_no_legacy(self):
        self.assertEqual(_common.brand_dir("Acme Corp"), self.home / "brands" / "acme-corp")

    def test_brand_dir_prefers_existing_legacy_raw_dir(self):
        legacy = self.home / "brands" / "Acme Corp"
        legacy.mkdir(parents=True)
        self.assertEqual(_common.brand_dir("Acme Corp"), legacy)

    def test_brand_dir_prefers_legacy_flat_no_brands_dir(self):
        # Old checkpoint/output layout: <workspace>/<slug> (no brands/).
        legacy_flat = self.home / "acme-corp"
        legacy_flat.mkdir(parents=True)
        self.assertEqual(_common.brand_dir("Acme Corp"), legacy_flat)

    def test_get_brand_dir_missing_returns_message(self):
        d, err = _common.get_brand_dir("ghost-brand")
        self.assertIsNone(d)
        self.assertIn("brand-setup", err)

    def test_get_brand_dir_existing(self):
        (self.home / "brands" / "acme").mkdir(parents=True)
        d, err = _common.get_brand_dir("acme")
        self.assertIsNone(err)
        self.assertEqual(d, self.home / "brands" / "acme")

    def test_plugin_data_empty_string_does_not_resolve_to_cwd(self):
        os.environ.pop("CLAUDE_MARKETING_HOME", None)
        saved = os.environ.get("CLAUDE_PLUGIN_DATA")
        os.environ["CLAUDE_PLUGIN_DATA"] = ""
        try:
            home = _common.workspace_root()
            self.assertNotEqual(str(home), ".")
            self.assertEqual(home, Path.home() / ".claude-marketing")
        finally:
            if saved is None:
                os.environ.pop("CLAUDE_PLUGIN_DATA", None)
            else:
                os.environ["CLAUDE_PLUGIN_DATA"] = saved
            os.environ["CLAUDE_MARKETING_HOME"] = str(self.home)

    def test_plugin_data_appends_digital_marketing_pro_segment(self):
        os.environ.pop("CLAUDE_MARKETING_HOME", None)
        saved = os.environ.get("CLAUDE_PLUGIN_DATA")
        os.environ["CLAUDE_PLUGIN_DATA"] = str(self.home)  # exists
        try:
            self.assertEqual(_common.workspace_root(), self.home / "digital-marketing-pro")
        finally:
            if saved is None:
                os.environ.pop("CLAUDE_PLUGIN_DATA", None)
            else:
                os.environ["CLAUDE_PLUGIN_DATA"] = saved
            os.environ["CLAUDE_MARKETING_HOME"] = str(self.home)


class TestConstants(unittest.TestCase):
    def test_six_ai_surfaces(self):
        self.assertEqual(len(_common.AI_VISIBILITY_SURFACES), 6)
        for surface in ("Google AI Mode", "Google AI Overviews", "ChatGPT",
                        "Perplexity", "Gemini", "Copilot"):
            self.assertIn(surface, _common.AI_VISIBILITY_SURFACES)


if __name__ == "__main__":
    unittest.main()

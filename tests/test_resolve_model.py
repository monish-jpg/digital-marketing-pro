"""Model curator (scripts/resolve_model.py) — alias resolution, deprecation check, registry age."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import resolve_model  # noqa: E402  # pyright: ignore[reportMissingImports]  # type: ignore[import-not-found]


class TestAliasResolution(unittest.TestCase):
    def test_resolves_balanced_anthropic(self):
        result = resolve_model.resolve("latest-balanced-anthropic")
        self.assertTrue(result.startswith("claude-sonnet"),
                        f"expected a claude-sonnet variant, got {result}")

    def test_resolves_text_anthropic(self):
        result = resolve_model.resolve("latest-text-anthropic")
        self.assertTrue(result.startswith("claude-opus"),
                        f"expected a claude-opus variant, got {result}")

    def test_resolves_fast_anthropic(self):
        result = resolve_model.resolve("latest-fast-anthropic")
        self.assertTrue(result.startswith("claude-haiku"),
                        f"expected a claude-haiku variant, got {result}")

    def test_resolves_text_openai(self):
        result = resolve_model.resolve("latest-text-openai")
        self.assertTrue(result.startswith("gpt-"),
                        f"expected a gpt-* variant, got {result}")

    def test_resolves_text_google(self):
        result = resolve_model.resolve("latest-text-google")
        self.assertTrue(result.startswith("gemini-"),
                        f"expected a gemini-* variant, got {result}")

    def test_exact_id_passes_through(self):
        result = resolve_model.resolve("claude-opus-4-7")
        self.assertEqual(result, "claude-opus-4-7")

    def test_unknown_alias_raises(self):
        with self.assertRaises(KeyError):
            resolve_model.resolve("latest-imaginary-vendor")


class TestDeprecationCheck(unittest.TestCase):
    def test_deprecated_returns_replacement(self):
        result = resolve_model.resolve("gemini-2.0-flash")
        self.assertNotEqual(result, "gemini-2.0-flash",
                            "deprecated id should fall forward to replacement")

    def test_deprecated_with_allow_flag(self):
        result = resolve_model.resolve("gemini-2.0-flash", allow_deprecated=True)
        self.assertEqual(result, "gemini-2.0-flash",
                         "allow_deprecated=True should return the deprecated id as-is")

    def test_check_returns_status(self):
        status, replacement = resolve_model.check("gemini-2.0-flash")
        self.assertEqual(status, "deprecated")
        self.assertIsNotNone(replacement)

    def test_check_current(self):
        status, _ = resolve_model.check("claude-opus-4-7")
        self.assertEqual(status, "current")

    def test_check_unknown(self):
        status, replacement = resolve_model.check("claude-fake-9000")
        self.assertEqual(status, "unknown")
        self.assertIsNone(replacement)


class TestRegistryAge(unittest.TestCase):
    def test_registry_age_is_int(self):
        age = resolve_model.registry_age_days()
        self.assertIsInstance(age, int, "registry_age_days must return an int")
        self.assertGreaterEqual(age, 0, "registry age cannot be negative")

    def test_get_registry_returns_dict_with_models(self):
        reg = resolve_model.get_registry()
        self.assertIn("models", reg)
        self.assertIsInstance(reg["models"], list)
        self.assertGreater(len(reg["models"]), 0)

    def test_aliases_block_present(self):
        reg = resolve_model.get_registry()
        self.assertIn("aliases", reg)
        self.assertGreater(len(reg["aliases"]), 0)


class TestListFilter(unittest.TestCase):
    def test_filter_by_vendor(self):
        models = resolve_model.list_models(vendor="anthropic")
        for m in models:
            self.assertEqual(m["vendor"], "anthropic")
        self.assertGreater(len(models), 0)

    def test_filter_by_status(self):
        current = resolve_model.list_models(status="current")
        deprecated = resolve_model.list_models(status="deprecated")
        self.assertGreater(len(current), 0)
        self.assertGreater(len(deprecated), 0)
        for m in current:
            self.assertEqual(m["status"], "current")
        for m in deprecated:
            self.assertEqual(m["status"], "deprecated")


if __name__ == "__main__":
    unittest.main()

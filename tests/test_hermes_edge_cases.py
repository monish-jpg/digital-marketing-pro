"""Hermes adapter edge-case tests — what happens when the world is weird.

The adapter must never crash, even when:
- The skills/ directory is missing entirely
- A SKILL.md has malformed YAML frontmatter
- A skill directory exists but has no SKILL.md
- A SKILL.md has no name or no description
- The skills/ directory is present but empty
- ctx is missing register_skill (Hermes API drift)
- ctx.register_skill itself raises on certain inputs
- Multiple skills with the same name (collision)
"""
from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
ADAPTER_PY = PLUGIN_ROOT / "__init__.py"


def _import_adapter_from(plugin_root: Path):
    """Import the adapter as if it were installed at a fresh location."""
    init_path = plugin_root / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        f"dmp_adapter_{plugin_root.name}", init_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_test_plugin(tmp: Path, skills: dict[str, str | None]) -> Path:
    """Create a minimal plugin tree at tmp with the given skills.

    skills: dict of {skill_name: SKILL.md_content_or_None}.
    None means create the directory but NO SKILL.md inside.
    """
    plugin_dir = tmp / "test-plugin"
    plugin_dir.mkdir(parents=True)
    shutil.copy(ADAPTER_PY, plugin_dir / "__init__.py")

    if skills is not None:
        skills_dir = plugin_dir / "skills"
        skills_dir.mkdir()
        for name, content in skills.items():
            sk = skills_dir / name
            sk.mkdir()
            if content is not None:
                (sk / "SKILL.md").write_text(content, encoding="utf-8")
    return plugin_dir


class TestMissingSkillsDirectory(unittest.TestCase):
    def test_register_warns_and_returns_when_skills_dir_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "p"
            plugin_dir.mkdir()
            shutil.copy(ADAPTER_PY, plugin_dir / "__init__.py")
            adapter = _import_adapter_from(plugin_dir)

            class MockCtx:
                def __init__(self): self.registered = []
                def register_skill(self, n, p): self.registered.append((n, p))

            ctx = MockCtx()
            try:
                adapter.register(ctx)
            except Exception as e:
                self.fail(f"register() must not raise on missing skills/; raised: {e}")
            self.assertEqual(ctx.registered, [],
                             "No skills should be registered when skills/ is missing")


class TestEmptySkillsDirectory(unittest.TestCase):
    def test_register_handles_empty_skills_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = _make_test_plugin(Path(tmp), skills={})
            adapter = _import_adapter_from(plugin_dir)
            class MockCtx:
                def __init__(self): self.registered = []
                def register_skill(self, n, p): self.registered.append((n, p))
            ctx = MockCtx()
            adapter.register(ctx)
            self.assertEqual(len(ctx.registered), 0)


class TestSkillDirWithoutSKILLMD(unittest.TestCase):
    def test_register_skips_skill_dir_with_no_SKILL_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = _make_test_plugin(Path(tmp), skills={"empty-skill": None})
            adapter = _import_adapter_from(plugin_dir)
            class MockCtx:
                def __init__(self): self.registered = []
                def register_skill(self, n, p): self.registered.append((n, p))
            ctx = MockCtx()
            adapter.register(ctx)
            self.assertEqual(len(ctx.registered), 0,
                             "Skill dirs without SKILL.md should be silently skipped")


class TestMalformedFrontmatter(unittest.TestCase):
    def test_skill_with_no_frontmatter_uses_dirname_and_empty_description(self):
        skill_md = "Just a plain markdown file with no frontmatter.\n"
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = _make_test_plugin(Path(tmp), skills={"naked-skill": skill_md})
            adapter = _import_adapter_from(plugin_dir)
            audit = adapter.audit()
            self.assertEqual(audit["skill_count"], 1,
                             "Should still register the skill with sensible fallbacks")

    def test_skill_with_broken_yaml_falls_back_gracefully(self):
        skill_md = "---\nname: test\nbroken: : : : \n---\n# Skill body\n"
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = _make_test_plugin(Path(tmp), skills={"broken-yaml": skill_md})
            adapter = _import_adapter_from(plugin_dir)
            try:
                audit = adapter.audit()
            except Exception as e:
                self.fail(f"audit() must not raise on broken YAML; raised: {e}")
            self.assertEqual(audit["skill_count"], 1)


class TestRegisterCtxFailures(unittest.TestCase):
    def test_register_continues_when_single_register_skill_call_raises(self):
        """If ctx.register_skill raises on ONE skill, others should still register."""
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = _make_test_plugin(Path(tmp), skills={
                "good-skill-1": "---\nname: good-skill-1\ndescription: ok\n---\n",
                "bad-skill": "---\nname: bad-skill\ndescription: triggers fail\n---\n",
                "good-skill-2": "---\nname: good-skill-2\ndescription: ok\n---\n",
            })
            adapter = _import_adapter_from(plugin_dir)

            class PickyCtx:
                def __init__(self): self.registered = []
                def register_skill(self, name, path):
                    if name == "bad-skill":
                        raise RuntimeError("simulated registration failure")
                    self.registered.append((name, path))

            ctx = PickyCtx()
            try:
                adapter.register(ctx)
            except Exception as e:
                self.fail(f"register() must not propagate per-skill failures; raised: {e}")
            self.assertEqual(len(ctx.registered), 2,
                             "Other skills should still register when one fails")


class TestPluginWithCollidingSkillNames(unittest.TestCase):
    """Skills with the same `name:` in frontmatter — both should still register
    (Hermes handles namespacing on its side)."""

    def test_two_skills_same_name_both_register(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = _make_test_plugin(Path(tmp), skills={
                "dir-a": "---\nname: collision\ndescription: from dir a\n---\n",
                "dir-b": "---\nname: collision\ndescription: from dir b\n---\n",
            })
            adapter = _import_adapter_from(plugin_dir)
            class MockCtx:
                def __init__(self): self.registered = []
                def register_skill(self, n, p): self.registered.append((n, str(p)))
            ctx = MockCtx()
            adapter.register(ctx)
            self.assertEqual(len(ctx.registered), 2)


class TestProductionAdapterBehavior(unittest.TestCase):
    """Verify the LIVE adapter (against the real DMP repo) behaves as expected."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("dmp_adapter_live", ADAPTER_PY)
        cls.adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.adapter)

    def test_audit_returns_expected_fields(self):
        audit = self.adapter.audit()
        required_keys = {"plugin_root", "plugin_version", "skills_dir",
                         "skills_dir_exists", "skill_count", "first_5_skills"}
        self.assertTrue(required_keys.issubset(audit.keys()),
                        f"audit() missing keys: {required_keys - audit.keys()}")

    def test_audit_first_5_skills_have_name_and_description(self):
        audit = self.adapter.audit()
        for s in audit["first_5_skills"]:
            self.assertIn("name", s)
            self.assertIn("description", s)
            self.assertGreater(len(s["name"]), 0)

    def test_register_with_None_ctx_does_not_crash(self):
        """Hermes guarantees crashes disable but don't crash Hermes — we don't even crash ourselves."""
        try:
            self.adapter.register(None)
        except Exception as e:
            self.fail(f"register(None) must not raise; raised: {e}")


if __name__ == "__main__":
    unittest.main()

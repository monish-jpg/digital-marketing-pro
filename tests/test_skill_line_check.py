"""skill-line-check.py — line-count guardrail for SKILL.md files."""
from __future__ import annotations

import unittest

from _helpers import import_script  # type: ignore[import-not-found]


class TestSkillLineCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.slc = import_script("skill-line-check.py", module_name="skill_line_check")

    def test_collect_returns_skills(self):
        rows = self.slc.collect_skill_sizes()
        self.assertGreater(len(rows), 100)
        for r in rows:
            self.assertIn("skill", r)
            self.assertIn("lines", r)
            self.assertGreaterEqual(r["lines"], 0)

    def test_skills_sorted_by_lines_desc(self):
        rows = self.slc.collect_skill_sizes()
        for i in range(len(rows) - 1):
            self.assertGreaterEqual(rows[i]["lines"], rows[i + 1]["lines"])

    def test_no_skill_exceeds_500_lines(self):
        """Current state assertion: keep SKILL.md under 500 lines per Anthropic guideline."""
        rows = self.slc.collect_skill_sizes()
        over = [r for r in rows if r["lines"] >= 500]
        self.assertEqual(
            len(over), 0,
            f"{len(over)} skills exceed 500 lines: " +
            ", ".join(f"{r['skill']}({r['lines']})" for r in over)
        )


if __name__ == "__main__":
    unittest.main()

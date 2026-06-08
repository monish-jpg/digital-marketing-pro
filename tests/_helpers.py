"""Shared test helpers — keep imports here, not in every test_*.py."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"


def import_script(filename: str, module_name: str | None = None):
    """Import a script that uses a hyphenated filename (not importable as-is)."""
    path = SCRIPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"script not found: {path}")
    name = module_name or filename.replace("-", "_").replace(".py", "")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"cannot create spec for {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

"""Shared test helpers — keep imports here, not in every test_*.py."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"


def run_script(filename: str, *args, marketing_home=None, cwd=None, env=None):
    """Invoke a script as a subprocess so exit codes + argparse behaviour are
    exercised exactly as a real caller would see them. Returns a CompletedProcess
    with .returncode/.stdout/.stderr. Set marketing_home to point CLAUDE_MARKETING_HOME
    at a temp workspace (the canonical test-isolation override)."""
    full_env = dict(os.environ)
    # Ensure a clean workspace resolution unless the caller overrides it.
    full_env.pop("CLAUDE_PLUGIN_DATA", None)
    if marketing_home is not None:
        full_env["CLAUDE_MARKETING_HOME"] = str(marketing_home)
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / filename), *[str(a) for a in args]],
        capture_output=True, text=True, cwd=cwd, env=full_env, timeout=60,
    )


def run_json(filename: str, *args, marketing_home=None, **kw):
    """run_script + parse stdout as JSON. Returns (data, returncode)."""
    proc = run_script(filename, *args, marketing_home=marketing_home, **kw)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"_raw_stdout": proc.stdout, "_stderr": proc.stderr}
    return data, proc.returncode


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

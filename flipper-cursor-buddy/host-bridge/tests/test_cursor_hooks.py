"""Cursor-specific hook adapter tests."""

import importlib.util
from pathlib import Path


SCRIPTS = Path(__file__).parents[2] / "scripts"


def load_script(name: str):
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_permission_detail_for_shell():
    hook = load_script("on-permission-request.py")
    assert hook.extract_detail("Shell", {"command": "ls -la"}) == "ls -la"


def test_permission_detail_for_mcp():
    hook = load_script("on-permission-request.py")
    assert hook.extract_detail("MCP: context7", {}) == "context7"


def test_post_tool_display_names():
    hook = load_script("on-post-tool-use.py")
    assert hook.display_name("Shell") == "Shell"
    assert hook.display_name("MCP: github") == "MCP"


def test_post_tool_sound_mapping():
    hook = load_script("on-post-tool-use.py")
    assert hook.sound_for_tool("Shell") == "cmd"
    assert hook.sound_for_tool("Write") == "enter"
    assert hook.sound_for_tool("Task") is None

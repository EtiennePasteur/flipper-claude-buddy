"""Codex-specific hook adapter tests."""

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


def test_permission_detail_for_apply_patch():
    hook = load_script("on-permission-request.py")
    assert hook.extract_detail("apply_patch", {"command": "*** Begin Patch"}) == "File change"


def test_post_tool_display_names():
    hook = load_script("on-post-tool-use.py")
    assert hook.display_name("apply_patch") == "Edit"
    assert hook.display_name("mcp__github__search") == "mcp_github"
    assert hook.display_name("Bash") == "Bash"


def test_post_tool_failure_shapes():
    hook = load_script("on-post-tool-use.py")
    assert hook.tool_failed({"tool_response": {"exit_code": 1}})
    assert hook.tool_failed({"tool_response": {"success": False}})
    assert hook.tool_failed({"tool_response": {"status": "failed"}})
    assert not hook.tool_failed({"tool_response": {"exit_code": 0}})

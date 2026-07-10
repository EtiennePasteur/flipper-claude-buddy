#!/usr/bin/env python3
"""PostToolUse hook: plays a per-tool sound on the Flipper after each tool call."""

import json
import os
import socket
import sys

SOCKET_PATH = "/tmp/codex-flipper-bridge.sock"
STATS_PATH = "/tmp/codex-flipper-turn-stats.json"

# Map tool names (or prefixes) to sound names.
# Evaluated in order — first match wins.
TOOL_SOUNDS = [
    ({"apply_patch", "Edit", "Write"},           "enter"),   # file write: soft blip
    ({"Bash"},                                   "cmd"),     # shell command: confirm tone
    ({"WebFetch", "WebSearch"},                  "alert"),   # network: attention tone
    ({"Read"},                                   "enter"),   # read-only: soft blip
    ({"Glob", "Grep"},                           None),   # read-only: soft blip
]


def sound_for_tool(tool_name: str) -> str | None:
    for tools, sound in TOOL_SOUNDS:
        if tool_name in tools:
            return sound
    return None  # unknown tools: silent


def send_to_flipper(sound: str, text: str = "", subtext: str = "") -> None:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCKET_PATH)
    msg = json.dumps({"action": "notify", "sound": sound, "vibro": False, "text": text, "subtext": subtext})
    s.sendall(msg.encode())
    s.shutdown(socket.SHUT_WR)
    s.recv(4096)
    s.close()


def tool_detail(tool_name: str, hook_input: dict) -> str:
    """Extract a short detail string from the tool input."""
    tool_input = hook_input.get("tool_input", {})
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        return cmd[:21] if cmd else ""
    if tool_name == "apply_patch":
        return "File change"
    if tool_name in ("Edit", "Write", "Read"):
        path = tool_input.get("file_path", "")
        return os.path.basename(path)[:21] if path else ""
    if tool_name in ("WebFetch", "WebSearch"):
        val = tool_input.get("url") or tool_input.get("query", "")
        for prefix in ("https://", "http://"):
            if val.startswith(prefix):
                val = val[len(prefix):]
                break
        return val[:21]
    return ""


def tool_failed(hook_input: dict) -> bool:
    """Best-effort failure detection across Codex tool response shapes."""
    response = hook_input.get("tool_response")
    if not isinstance(response, dict):
        return False
    if response.get("success") is False:
        return True
    if response.get("status") in {"failed", "error"}:
        return True
    exit_code = response.get("exit_code", response.get("exitCode"))
    return isinstance(exit_code, int) and exit_code != 0


def display_name(tool_name: str) -> str:
    if tool_name == "apply_patch":
        return "Edit"
    if tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        return f"mcp_{parts[1]}" if len(parts) > 1 else "MCP"
    return tool_name or "Tool"


def main():
    if not os.path.exists(SOCKET_PATH):
        sys.exit(0)

    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    shown_name = display_name(tool_name)

    # Skip notification for Bash commands that write to the Flipper socket directly
    # (e.g. the flipper-notify skill) — they already set their own display.
    # Also flag the stop hook to skip "Turn complete" for this turn.
    if tool_name == "Bash":
        cmd = hook_input.get("tool_input", {}).get("command", "")
        if SOCKET_PATH in cmd:
            try:
                open("/tmp/codex-flipper-skip-stop.flag", "w").close()
            except Exception:
                pass
            sys.exit(0)

    # Track tool usage stats for the Stop hook summary
    try:
        stats = json.loads(open(STATS_PATH).read()) if os.path.exists(STATS_PATH) else {}
    except Exception:
        stats = {}
    stats[shown_name] = stats.get(shown_name, 0) + 1
    try:
        open(STATS_PATH, "w").write(json.dumps(stats))
    except Exception:
        pass

    if tool_failed(hook_input):
        try:
            send_to_flipper("error", f"{shown_name} failed", tool_detail(tool_name, hook_input))
        except Exception:
            pass
        sys.exit(0)

    sound = sound_for_tool(tool_name)
    if not sound:
        sys.exit(0)

    detail = tool_detail(tool_name, hook_input)
    try:
        send_to_flipper(sound, shown_name, detail)
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()

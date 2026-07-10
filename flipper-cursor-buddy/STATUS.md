# Flipper Cursor Buddy — status

## Done

- Cursor hook package scaffolded in `flipper-cursor-buddy/`
- `.cursor/hooks.json` with session, tool, compaction, subagent, and stop hooks
- Host bridge adapted for `/tmp/cursor-flipper-bridge.sock` and `cursor_connect`
- Install script: `scripts/install-cursor-hooks.sh`
- `preToolUse` permission flow with Cursor-native `permission` JSON output
- Post-compact workaround via pending flag on first `postToolUse`

## Next

- Install hooks in this repo and verify in a live Cursor agent session
- Test `preToolUse` approval flow on hardware
- Document bridge enable/disable workflow for Cursor users

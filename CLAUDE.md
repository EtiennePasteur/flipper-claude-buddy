# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

### Flipper App (C)
```bash
# Build (requires ufbt: pip3 install ufbt)
cd flipper-app && ufbt build

# Build and flash to connected Flipper
cd flipper-app && ufbt launch

# Or use the script
./scripts/build-flipper.sh           # build only
./scripts/build-flipper.sh --flash   # build + flash
```

### Host Bridge (Python)
```bash
# Install (editable)
cd plugin/host-bridge && pip3 install -e .

# Run bridge daemon
python3 -m bridge

# Run with explicit transport
python3 -m bridge --transport ble   # BLE only
python3 -m bridge --transport usb   # USB only

# Key environment overrides
FLIPPER_BT_NAME="Flipper"          # BLE device name prefix
FLIPPER_TRANSPORT=ble              # force BLE
FLIPPER_LOG_LEVEL=debug            # verbose logs
```

### Testing IPC
```bash
DIR="${FLIPPER_BRIDGE_RUNTIME_DIR:-${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}}"
echo '{"action":"notify","sound":"success","vibro":true,"text":"Test","subtext":""}' \
  | nc -U "${DIR%/}/claude-flipper-bridge.sock"
```

## Architecture

```
Flipper Zero (C app)
  ↕ USB CDC serial  OR  BLE serial
Host Bridge (Python daemon, macOS)
  ↕ Unix socket  $RUNTIME_DIR/claude-flipper-bridge.sock
Claude Code hook scripts (plugin/ or .claude/)
```

The system has three components:

1. **`flipper-app/`** — Flipper Zero FAP (C). Handles button input and audio/haptic feedback. Auto-selects USB or BLE transport at startup based on USB power state.

2. **`plugin/host-bridge/`** — Python asyncio daemon. Bridges serial ↔ Unix socket. Manages BLE/USB connection with auto-reconnect. Serves a Unix socket that hook scripts connect to.

3. **`plugin/`** — Claude Code plugin (self-contained, shareable). Hook scripts that translate Claude Code lifecycle events (notifications, permissions, tool use) into socket messages.

## Threading Model — Critical

### Flipper App
- **BLE/serial RX callback** runs on a worker thread. It must NOT call any UI functions or `transport_send`.
- The callback queues parsed `ProtocolMessage` into a `FuriMessageQueue` and signals the GUI thread via `view_dispatcher_send_custom_event`.
- **GUI thread** (the Furi event loop) drains the queue and calls `transport_send` safely.
- Calling `ble_profile_serial_tx` from inside `bt_serial_event_cb` deadlocks on Momentum firmware — always defer TX to the GUI thread.

### Host Bridge
- Single asyncio event loop. All transport I/O, IPC, and ping tasks are async coroutines.
- `serial_conn.py` runs a reconnect loop that re-establishes the transport on disconnect.
- `transport_bt.py`: `readline()` must handle disconnect without blocking — checks `_closed` flag before and after `_rx_event.clear()`.

## Protocol

JSON lines (`\n`-terminated) over serial (USB or BLE):
```json
{"v": 1, "t": "<type>", "d": {...}}
```

**Host → Flipper:** `ping`, `notify`, `state`, `status`, `menu`, `perm`, `ask`, `dismiss`
**Flipper → Host:** `hello`, `pong`, `enter`, `esc`, `voice`, `down`, `cmd`, `perm_resp`, `ask_resp`

`ask` carries an `AskUserQuestion` call as a pick-list (`hdr`, `q`, pipe-delimited
`opts`, plus `multi` when several options may be picked); `ask_resp` answers with
the chosen `idx` — or, for a multi-select question, a `sel` bitmask of the ticked
options — or `esc` to hand the question back to the terminal. Option labels are
display-only — the answer is an index — so the bridge ASCII-folds them
(`protocol.wire_safe`) to survive the Flipper's escape-less JSON parser and its
LCD font. The hook joins a multi-select answer's labels with `", "`, which is how
the terminal dialog encodes them into the tool's `answers` map.

On the device, a single-select question is answered with OK; a multi-select one
ticks rows with OK and sends with Right. The Send hint is only drawn once
something is ticked, so an empty answer can't be sent. Calls carrying several
questions still fall back to Claude's own dialog.

`dismiss` takes a `perm` or `ask` prompt back off the screen when the host stops
waiting on it, leaving any view the user opened themselves (menu, info) alone.
A prompt shows on the Flipper *and* in the terminal at once, so it has to be
withdrawn three ways, each with its own signal:

| The user… | Detected by | Note |
|---|---|---|
| answers in the terminal | the `notify` that follows | the hook stays alive, blocked on `recv`, until the daemon answers it |
| cancels (Esc / Ctrl-C) | the hook's pid disappearing | Claude Code kills the hook here, unlike above |
| does nothing | the 60s timeout | |

The pid rides along in the IPC request because the socket cannot report this:
the hook calls `shutdown(SHUT_WR)` right after sending, so the daemon sees EOF
while the hook is still very much alive. Without `dismiss` the prompt lingered
until some unrelated notify happened to switch the view — and one carrying no
text never did.

The Flipper sends `hello` on the first received `ping` (from the GUI thread), not at BLE connect time. This is because the host's CCCD write (enabling notifications) hasn't happened yet when the connection status callback fires.

## BLE Transport Details

- RX (Flipper→host, notify): `19ed82ae-ed21-4c9d-4145-228e61fe0000`
- TX (host→Flipper, write): `19ed82ae-ed21-4c9d-4145-228e62fe0000`
- Host writes with `response=False` (write-without-response), chunk size capped to `negotiated_mtu - 3`
- `BT_WRITE_CHUNK = 128` in `config.py` (runtime cap applies)

## Key Files

| File | Purpose |
|------|---------|
| `flipper-app/claude_buddy.c` | App entry point, GUI event loop, message dispatch |
| `flipper-app/transport_bt.c` | BLE transport — RX callback, connection state |
| `flipper-app/ui.c` | Display rendering, button input handlers |
| `flipper-app/protocol.c` | JSON parse/build for all message types |
| `plugin/host-bridge/bridge/daemon.py` | Main event loop, message routing |
| `plugin/host-bridge/bridge/transport_bt.py` | BLE transport (bleak), readline, write |
| `plugin/host-bridge/bridge/serial_conn.py` | Reconnect loop, disconnect detection |
| `plugin/host-bridge/bridge/config.py` | All tunables (timeouts, UUIDs, chunk sizes) |
| `plugin/scripts/` | Hook scripts for each Claude Code lifecycle event |

## Runtime Files

All runtime files live in a **per-user private directory**, resolved
identically by `plugin/scripts/_runtime.sh`, `plugin/scripts/_runtime.py` and
`bridge/config.py` (keep the three in sync):

1. `$FLIPPER_BRIDGE_RUNTIME_DIR` if set (explicit override)
2. `$XDG_RUNTIME_DIR` if it exists — Linux, `/run/user/<uid>`, mode 700
3. `$TMPDIR` — macOS, `/var/folders/…/T`, mode 700
4. `/tmp` — last-resort fallback

They are **not** in the shared `/tmp`: the socket drives permission decisions
and keystroke targeting, so a world-writable path would let any local process
squat it and auto-approve tool permissions on the user's behalf.

Within that directory (`$RUNTIME_DIR` below):
- Socket: `$RUNTIME_DIR/claude-flipper-bridge.sock` — created mode `0600`
- PID: `$RUNTIME_DIR/claude-flipper-bridge.pid`
- Log: `$RUNTIME_DIR/claude-flipper-bridge.log`
- Session refcount: `$RUNTIME_DIR/claude-flipper-bridge.refcount`
- Turn stats: `$RUNTIME_DIR/claude-flipper-turn-stats.json` — tool usage counts written by `on-post-tool-use.py`, read by `on-stop.sh`
- Skip-stop flag: `$RUNTIME_DIR/claude-flipper-skip-stop.flag` — set by hook Bash commands that write directly to the socket, prevents `on-stop.sh` from double-notifying

Outside that directory:
- BT name cache: `$PLUGIN_DATA/bt_name` — auto-detected Bluetooth device name saved after first `hello`; used across sessions to skip re-scanning

`$FLIPPER_BRIDGE_SOCKET` still overrides the socket path on its own.

To inspect bridge activity:
```bash
DIR="${FLIPPER_BRIDGE_RUNTIME_DIR:-${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}}"
tail -f "${DIR%/}/claude-flipper-bridge.log"
```

## Platform Notes

| Feature | macOS | Linux |
|---------|-------|-------|
| USB transport | `/dev/cu.usbmodem*` | `/dev/ttyACM*` (auto-detected) |
| BLE transport | ✓ | not yet supported |
| Keystroke forwarding | AppleScript (`osascript`) | `xdotool` (X11 only; install via `apt install xdotool`) |
| Wayland keystroke | ✗ | not yet supported (`ydotool` needed) |
| Dictation | macOS native (`FLIPPER_DICTATION_BACKEND=macos`) | disabled by default; use `FLIPPER_DICTATION_BACKEND=custom` |

On Linux, `WINDOWID` (set by VTE-based terminals like gnome-terminal and kitty) is used by `xdotool` to focus the correct window. If `WINDOWID` is not set, keystrokes go to the active window.

The bridge daemon, IPC socket, and all hook scripts are otherwise platform-agnostic.

## Command Menu System

The Flipper's button menu is populated from two optional text files (project overrides user):
1. `~/.claude/flipper-commands.txt` — user-level shortcuts
2. `$PROJECT_DIR/.claude/flipper-commands.txt` — project-level shortcuts

Each line is a display label and command separated by a delimiter. The bridge also auto-discovers skill shortcuts from `.claude/commands/`. Commands are sent to the Flipper as a pipe-delimited `menu` message; the Flipper stores abbreviations in `_cmd_map` and expands the selection back to the host.

## Releasing a New Version

1. **Commit any uncommitted changes first** — the version bump should be its own clean commit.
2. **`flipper-app/CHANGELOG.md`** — add a new `## vX.Y` section at the top, summarizing commits since the previous version.
3. **`flipper-app/application.fam`** — update `fap_version`
4. **`flipper-app/ui.c`** — update version string on the About page
5. **`plugin/.claude-plugin/plugin.json`** — update `version`
6. **`plugin/host-bridge/pyproject.toml`** — update `version`
7. Commit, push, then tag:
   ```bash
   git tag X.Y
   git push origin X.Y
   ```
   The CI workflow (`.github/workflows/build-fap.yml`) creates the GitHub release and attaches the built `.fap` automatically.

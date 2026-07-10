# Current Status

Date: 2026-07-10

What is done:
- Codex-specific plugin copy exists in `flipper-codex-buddy/`.
- Host bridge is adapted for Codex sockets, hook payloads, and permission flow.
- Flipper hardware handshake was verified over USB.
- Permission approval from Flipper works end to end.
- Bridge control has a persisted enable/disable flag and Codex slash commands:
  - `/bridge`
  - `/bridge-on`
  - `/bridge-off`
  - `/bridge-status`
- Local Codex marketplace is set up at `.agents/plugins/marketplace.json`
  (`flipper-local`) and installs via `scripts/install-codex-plugin.sh`.
- Bridge defaults to **enabled** when `PLUGIN_DATA/bridge-enabled` is missing.

Open follow-up:
- Trust hooks in Codex (`/hooks`) after install if not done yet.
- Optionally expose the bridge toggle in a place that is easier to discover than slash commands alone.
- Re-run permission approval from a Codex session started after marketplace install.

## v0.8

- Multi-select `AskUserQuestion` calls are answered on the Flipper too: Ok ticks
  the row under the cursor, Right sends the set, Left or Back leaves the question
  to the terminal. The Send hint only appears once something is ticked, so an
  empty answer can't be sent. Calls carrying several questions still fall back to
  Claude's own dialog.
- Ticked options travel back as a `sel` bitmask; single-select answers keep using
  `idx`, so the wire stays backward compatible.
- New `dismiss` message: a permission or question prompt is taken off the screen
  as soon as the host stops waiting on it — answered in the terminal, cancelled,
  or timed out. It used to linger there until an unrelated notification happened
  to carry text and switch the view, and its buttons stayed live in the meantime.


## v0.7

- `AskUserQuestion` now shows its options on the Flipper as a pick-list instead of
  an Allow/Deny prompt: pick with Up/Down + OK, or press Back to leave the question
  to the terminal.
- New `ask` / `ask_resp` protocol messages. Answers travel as an option index, so
  labels on the wire are display-only and get ASCII-folded for the Flipper's parser
  and LCD font.
- Single-select questions with 2-4 options are answered on the device; multi-select
  and multi-question calls fall back to Claude's own dialog.


## v0.6

- Fixed connection/disconnection state handling in Bridge mode.
- Fixed a memory leak in the Flipper app.


## v0.5

- New **Claude Desktop (BLE)** mode: talks directly to the Claude Desktop app over Anthropic's Hardware Buddy protocol. No plugin needed.
- Linux support for the host bridge plugin — thanks to @DanilaE for the contribution!
- Info menu relabels: **Claude Code (USB/BLE)** / **Claude Desktop (BLE)**.
- Help and Transcript pages are now mode-aware.
- Changed Flipper app category from USB to Bluetooth.


## v0.4

- Info menu (Hold ►): Help, Transcript, Plan/Code Mode, About.
- Transcript scrolling with Page Up/Down and jump-to-top/bottom.
- Flipper notifications for tool failures and elicitation prompts.

## v0.3

- Auto-discover slash commands from user/project commands, skills, and enabled plugins.
- Selected menu commands are promoted to the top of the list for convenient re-use.

## v0.2

- Routed remote input to the active runner session, including the correct terminal tab.
- Added Up-button long-press support for Claude voice input.
- Fixed BLE signal bars in the header.
- Fixed slash-command menu refresh so the first selected command matches the item shown on screen.

## v0.1

- Initial release with physical remote control, haptic feedback, USB/BLE transport, and Claude Code plugin integration.

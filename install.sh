#!/bin/sh
# agentmeter installer (or: brew install SaeedNoshadi89/tap/agentmeter)
#   curl -fsSL https://raw.githubusercontent.com/SaeedNoshadi89/agentmeter/main/install.sh | sh
#
# Options (environment variables):
#   AGENTMETER_BIN_DIR      where to put the command  (default: ~/.local/bin)
#   AGENTMETER_KEY          Rex shortcut               (default: shift+cmd+u)
#   AGENTMETER_NO_REX=1     skip the Rex popup setup
#   AGENTMETER_NO_STATUSLINE=1  skip the Claude Code status line question
#   AGENTMETER_UNINSTALL=1  remove agentmeter and its Rex popup
set -eu

RAW="https://raw.githubusercontent.com/SaeedNoshadi89/agentmeter/${AGENTMETER_REF:-main}"
BIN_DIR="${AGENTMETER_BIN_DIR:-$HOME/.local/bin}"
BIN="$BIN_DIR/agentmeter"

if [ "${AGENTMETER_UNINSTALL:-}" = 1 ]; then
  [ -x "$BIN" ] && "$BIN" remove-rex >/dev/null 2>&1 || true
  rm -f "$BIN"
  echo "  agentmeter removed."
  exit 0
fi

command -v python3 >/dev/null 2>&1 || { echo "  agentmeter needs python3."; exit 1; }

mkdir -p "$BIN_DIR"
here=$(cd "$(dirname "$0")" 2>/dev/null && pwd || true)
if [ -n "$here" ] && [ -f "$here/agentmeter" ]; then
  cp "$here/agentmeter" "$BIN"          # running from a clone
else
  curl -fsSL "$RAW/agentmeter" -o "$BIN"
fi
chmod +x "$BIN"
echo "  installed $BIN"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "  note: $BIN_DIR is not on your PATH; add it to run \`agentmeter\` directly." ;;
esac

# One setup step: asks about the Rex popup and the Claude Code status line.
set --
[ "${AGENTMETER_NO_REX:-}" = 1 ] && set -- "$@" --no-rex
[ "${AGENTMETER_NO_STATUSLINE:-}" = 1 ] && set -- "$@" --no-statusline
[ -n "${AGENTMETER_KEY:-}" ] && set -- "$@" --key "$AGENTMETER_KEY"
"$BIN" setup "$@"
